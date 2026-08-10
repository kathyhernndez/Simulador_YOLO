"""
Cliente de Integración con Roboflow Workflows
Soporta el workflow: Tesis Trafico vtesis-trafico-2-rfdetr-small-t1 Logic
Workspace: katherines-workspace-q66ls
Workflow ID: tesis-trafico-vtesis-trafico-2-rfdetr-small-t1-logic
"""

import os
import io
import time
import base64
import logging
from typing import Dict, Any, List, Optional, Tuple
import requests
from PIL import Image
import numpy as np

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RoboflowClient")

# Intentar importar inference-sdk oficial
try:
    from inference_sdk import InferenceHTTPClient
    HAS_INFERENCE_SDK = True
except ImportError:
    HAS_INFERENCE_SDK = False
    logger.warning("inference-sdk no disponible, se usará cliente REST nativo.")


class RoboflowWorkflowError(Exception):
    """Excepción personalizada para errores del workflow de Roboflow."""
    pass


class RoboflowClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        workspace_name: str = "katherines-workspace-q66ls",
        workflow_id: str = "tesis-trafico-vtesis-trafico-2-rfdetr-small-t1-logic",
        api_url: str = "https://serverless.roboflow.com",
        timeout: int = 25,
        max_retries: int = 3
    ):
        self.api_key = api_key or os.getenv("ROBOFLOW_API_KEY", "").strip()
        self.workspace_name = workspace_name or os.getenv("ROBOFLOW_WORKSPACE", "katherines-workspace-q66ls")
        self.workflow_id = workflow_id or os.getenv("ROBOFLOW_WORKFLOW_ID", "tesis-trafico-vtesis-trafico-2-rfdetr-small-t1-logic")
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._sdk_client = None

        if HAS_INFERENCE_SDK and self.api_key:
            try:
                self._sdk_client = InferenceHTTPClient(
                    api_url=self.api_url,
                    api_key=self.api_key
                )
            except Exception as e:
                logger.warning(f"No se pudo inicializar InferenceHTTPClient: {e}. Se usará REST directo.")
                self._sdk_client = None

    def update_api_key(self, api_key: str):
        """Actualiza la clave de API dinámicamente."""
        self.api_key = api_key.strip()
        if HAS_INFERENCE_SDK and self.api_key:
            try:
                self._sdk_client = InferenceHTTPClient(
                    api_url=self.api_url,
                    api_key=self.api_key
                )
            except Exception as e:
                logger.warning(f"Error reinicializando SDK: {e}")
                self._sdk_client = None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 5)

    def _image_to_base64(self, image: Any) -> str:
        """Convierte una imagen (PIL, numpy array o bytes) a cadena Base64."""
        if isinstance(image, str):
            if image.startswith("data:image"):
                return image.split(",")[1]
            if os.path.exists(image):
                with open(image, "rb") as f:
                    return base64.b64encode(f.read()).decode("utf-8")
            return image
        
        if isinstance(image, np.ndarray):
            # Convertir array OpenCV BGR/RGB a PIL
            if len(image.shape) == 3 and image.shape[2] == 3:
                # Asumimos RGB
                pil_img = Image.fromarray(image)
            else:
                pil_img = Image.fromarray(image)
            buf = io.BytesIO()
            pil_img.save(buf, format="JPEG", quality=90)
            return base64.b64encode(buf.getvalue()).decode("utf-8")

        if isinstance(image, Image.Image):
            buf = io.BytesIO()
            image.save(buf, format="JPEG", quality=90)
            return base64.b64encode(buf.getvalue()).decode("utf-8")

        if isinstance(image, (bytes, bytearray)):
            return base64.b64encode(image).decode("utf-8")

        raise ValueError(f"Formato de imagen no soportado: {type(image)}")

    def run_workflow_rest(
        self,
        image_base64: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Ejecuta el workflow utilizando llamada REST directa con reintentos."""
        endpoint = f"{self.api_url}/{self.workspace_name}/workflows/{self.workflow_id}"
        
        payload: Dict[str, Any] = {
            "api_key": self.api_key,
            "inputs": {
                "image": {
                    "type": "base64",
                    "value": image_base64
                }
            }
        }
        
        if parameters:
            payload["parameters"] = parameters

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                start_time = time.time()
                response = requests.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )
                latency = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    data = response.json()
                    return {"result": data, "latency_ms": latency}
                
                # Manejo de respuestas no 200
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.warning(f"Intento {attempt}/{self.max_retries} falló: {error_msg}")
                last_error = error_msg
                
                if response.status_code in [401, 403]:
                    # Error de autenticación, no reintentar
                    raise RoboflowWorkflowError(f"Error de autenticación con Roboflow (Verifique API Key): {response.text}")
                
            except requests.exceptions.RequestException as req_err:
                logger.warning(f"Intento {attempt}/{self.max_retries} error de conexión: {req_err}")
                last_error = str(req_err)
            
            # Backoff exponencial: 1s, 2s, 4s...
            if attempt < self.max_retries:
                time.sleep(2 ** (attempt - 1))

        raise RoboflowWorkflowError(f"Fallaron todos los reintentos contra el endpoint de Roboflow. Último error: {last_error}")

    def infer(
        self,
        image: Any,
        confidence_threshold: float = 0.35,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], float, Dict[str, Any]]:
        """
        Ejecuta la inferencia sobre una imagen y retorna las predicciones parseadas.
        
        Retorna:
            (detections_list, latency_ms, raw_response)
        """
        if not self.is_configured:
            raise RoboflowWorkflowError("La API Key de Roboflow no está configurada.")

        # Obtener dimensiones originales para normalización
        orig_w, orig_h = 640, 480
        if isinstance(image, np.ndarray):
            orig_h, orig_w = image.shape[:2]
        elif isinstance(image, Image.Image):
            orig_w, orig_h = image.size

        img_b64 = self._image_to_base64(image)
        
        # Intentar ejecutar con el SDK si está disponible
        raw_result = None
        latency_ms = 0.0

        if self._sdk_client is not None:
            try:
                start_t = time.time()
                workflow_res = self._sdk_client.run_workflow(
                    workspace_name=self.workspace_name,
                    workflow_id=self.workflow_id,
                    images=[img_b64],
                    parameters=parameters or {}
                )
                latency_ms = (time.time() - start_t) * 1000
                raw_result = workflow_res
            except Exception as e:
                logger.warning(f"Falla en SDK client ({e}), recurriendo a REST directo...")
                raw_result = None

        if raw_result is None:
            res_dict = self.run_workflow_rest(img_b64, parameters)
            raw_result = res_dict["result"]
            latency_ms = res_dict["latency_ms"]

        # Parsear detecciones de forma segura y genérica
        detections = self._parse_detections(raw_result, orig_w, orig_h, confidence_threshold)
        
        return detections, latency_ms, raw_result

    def _parse_detections(
        self,
        raw_data: Any,
        img_w: int,
        img_h: int,
        min_conf: float
    ) -> List[Dict[str, Any]]:
        """
        Extrae y normaliza las detecciones de cualquier formato de salida de Roboflow Workflow.
        """
        parsed = []

        # Extraer el contenedor de salida
        outputs = []
        if isinstance(raw_data, list):
            outputs = raw_data
        elif isinstance(raw_data, dict):
            if "outputs" in raw_data and isinstance(raw_data["outputs"], list):
                outputs = raw_data["outputs"]
            elif "result" in raw_data:
                outputs = [raw_data["result"]] if isinstance(raw_data["result"], dict) else raw_data["result"]
            else:
                outputs = [raw_data]

        # Buscar listas de predicciones recursivamente
        def find_predictions(obj: Any) -> List[Dict[str, Any]]:
            preds = []
            if isinstance(obj, dict):
                # Si tiene x, y, width, height o class_name directamente
                if ("x" in obj and "y" in obj and "width" in obj and "height" in obj) or \
                   ("box" in obj) or ("bbox" in obj) or ("class" in obj and "confidence" in obj):
                    preds.append(obj)
                else:
                    for k, v in obj.items():
                        # Si es imagen base64 de salida, ignorar para no sobrecargar memoria
                        if isinstance(v, str) and (len(v) > 2000 or v.startswith("data:image")):
                            continue
                        preds.extend(find_predictions(v))
            elif isinstance(obj, list):
                for item in obj:
                    preds.extend(find_predictions(item))
            return preds

        raw_preds = find_predictions(outputs)

        for p in raw_preds:
            try:
                # Extraer clase
                cls_name = p.get("class") or p.get("class_name") or p.get("label") or p.get("name") or "objeto"
                
                # Extraer confianza
                conf = float(p.get("confidence") or p.get("score") or p.get("conf") or 1.0)
                if conf < min_conf:
                    continue

                # Extraer coordenadas
                x1, y1, x2, y2 = 0, 0, 0, 0
                if "x" in p and "width" in p:
                    cx = float(p["x"])
                    cy = float(p["y"])
                    w = float(p["width"])
                    h = float(p["height"])
                    x1 = int(max(0, cx - w / 2))
                    y1 = int(max(0, cy - h / 2))
                    x2 = int(min(img_w, cx + w / 2))
                    y2 = int(min(img_h, cy + h / 2))
                elif "box" in p:
                    b = p["box"]
                    x1, y1, x2, y2 = int(b.get("x1", 0)), int(b.get("y1", 0)), int(b.get("x2", 0)), int(b.get("y2", 0))
                elif "bbox" in p:
                    b = p["bbox"]
                    if isinstance(b, list) and len(b) == 4:
                        x1, y1, x2, y2 = int(b[0]), int(b[1]), int(b[2]), int(b[3])
                else:
                    continue

                parsed.append({
                    "class": str(cls_name).lower(),
                    "confidence": round(conf, 3),
                    "box": {
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2,
                        "width": max(1, x2 - x1),
                        "height": max(1, y2 - y1)
                    }
                })
            except Exception as ex:
                logger.debug(f"Error procesando predicción individual: {ex}")
                continue

        return parsed
