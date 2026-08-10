"""
Módulo de Inferencia Local con YOLO (Ultralytics)
Carga el modelo best.pt entrenado para la detección de tráfico y señales.
"""

import os
import time
import logging
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

logger = logging.getLogger("LocalYOLO")

try:
    from ultralytics import YOLO
    HAS_ULTRALYTICS = True
except ImportError:
    HAS_ULTRALYTICS = False
    logger.warning("ultralytics no está instalado.")


class LocalYOLOModel:
    def __init__(self, model_path: str = "best.pt"):
        self.model_path = model_path
        self.model = None
        self.classes = {}
        self._load_model()

    def _load_model(self):
        if not HAS_ULTRALYTICS:
            logger.error("No se puede cargar el modelo porque ultralytics no está disponible.")
            return

        if not os.path.exists(self.model_path):
            logger.warning(f"Archivo de modelo '{self.model_path}' no encontrado.")
            return

        try:
            logger.info(f"Cargando modelo YOLO local desde: {self.model_path}...")
            self.model = YOLO(self.model_path)
            self.classes = self.model.names if hasattr(self.model, "names") else {}
            logger.info(f"Modelo cargado exitosamente. Clases: {self.classes}")
        except Exception as e:
            logger.error(f"Error al cargar modelo YOLO '{self.model_path}': {e}")
            self.model = None

    @property
    def is_loaded(self) -> bool:
        return self.model is not None

    def infer(
        self,
        image: np.ndarray,
        conf: float = 0.40,  # Subir umbral por defecto a 0.40
        iou: float = 0.45
    ) -> Tuple[List[Dict[str, Any]], float, np.ndarray]:
        """
        Ejecuta la inferencia sobre un frame/imagen con el modelo YOLO local.
        """
        if not self.is_loaded:
            raise RuntimeError(f"El modelo YOLO no está cargado. Verifique que exista '{self.model_path}'.")

        start_time = time.time()
        
        # Ejecutar inferencia YOLO con tamaño explícito imgsz=640
        results = self.model(image, conf=conf, iou=iou, imgsz=640, verbose=False)
        latency_ms = (time.time() - start_time) * 1000

        detections = []
        annotated_frame = image.copy()

        if results and len(results) > 0:
            result = results[0]

            # Extraer bounding boxes
            boxes = result.boxes
            if boxes is not None and len(boxes) > 0:
                # Filtrar si los resultados de box contienen NaN
                valid_indices = []
                for idx, box in enumerate(boxes):
                    conf_val = float(box.conf[0].item())
                    # Validar que conf_val sea número real y supere el umbral
                    if not np.isnan(conf_val) and conf_val >= conf:
                        valid_indices.append(idx)
                
                # Si no hay cajas válidas tras filtrar NaNs, devolver el frame limpio
                if not valid_indices:
                    return detections, latency_ms, annotated_frame

                # Generar frame anotado por ultralytics
                annotated_frame = result.plot()

                for idx in valid_indices:
                    box = boxes[idx]
                    cls_id = int(box.cls[0].item())
                    cls_name = self.classes.get(cls_id, str(cls_id))
                    conf_val = float(box.conf[0].item())
                    
                    xyxy = box.xyxy[0].tolist()
                    x1, y1, x2, y2 = int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])

                    detections.append({
                        "class": str(cls_name).lower().strip(),
                        "confidence": round(conf_val, 3),
                        "box": {
                            "x1": x1,
                            "y1": y1,
                            "x2": x2,
                            "y2": y2,
                            "width": max(1, x2 - x1),
                            "height": max(1, y2 - y1)
                        }
                    })

        return detections, latency_ms, annotated_frame
