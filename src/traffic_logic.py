"""
Lógica de Negocio y Reglas de Tráfico:
- Detección de eventos críticos.
- Generación de mensajes y estados para el Panel de Mensaje Variable (VMS Virtual).
- Control de semaforización inteligente basado en densidad vehicular.
- Anotación visual sobre frames de video / imagen.
"""

from typing import List, Dict, Any, Tuple
import cv2
import numpy as np
from datetime import datetime

# Paleta de colores para visualización de clases (BGR para OpenCV)
CLASS_COLORS_BGR = {
    "contraflujo": (0, 0, 255),       # Rojo brillante
    
    # Peatones (Rojo, BGR: 0, 0, 255)
    "peaton": (0, 0, 255),
    "person": (0, 0, 255),
    "people": (0, 0, 255),
    "pedestrian": (0, 0, 255),
    
    # Motocicletas (Cyan, BGR: 255, 255, 0)
    "moto": (255, 255, 0),
    "motocicle": (255, 255, 0),
    "motorcycle": (255, 255, 0),
    
    # Bicicletas (Verde, BGR: 0, 255, 0)
    "bicicleta": (0, 255, 0),
    "bicycle": (0, 255, 0),
    
    # Camiones (Naranja/Amarillo, BGR: 0, 165, 255)
    "truck": (0, 165, 255),
    "camion": (0, 165, 255),
    
    # Autobuses (Morado/Magenta, BGR: 255, 0, 255)
    "bus": (255, 0, 255),
    "autobus": (255, 0, 255),
    
    # Carros / Vehículos genéricos (Azul, BGR: 255, 100, 0)
    "vehiculo": (255, 100, 0),
    "car": (255, 100, 0),
    "auto": (255, 100, 0),
    "carro": (255, 100, 0),
    "camioneta": (255, 100, 0),
    
    "default": (200, 200, 200)
}

CLASS_TRANSLATIONS = {
    "car": "CARRO",
    "truck": "CAMIÓN",
    "bus": "AUTOBÚS",
    "motorcycle": "MOTOCICLETA",
    "motocicle": "MOTOCICLETA",
    "bicycle": "BICICLETA",
    "pedestrian": "PEATÓN",
    "person": "PEATÓN",
    "people": "PEATÓN"
}

def get_class_color(class_name: str) -> Tuple[int, int, int]:
    cls_lower = str(class_name).lower().strip()
    for key, color in CLASS_COLORS_BGR.items():
        if key in cls_lower:
            return color
    return CLASS_COLORS_BGR["default"]


class TrafficAnalyticsEngine:
    def __init__(self):
        self.history_logs: List[Dict[str, Any]] = []

    def evaluate_frame_events(self, detections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analiza las detecciones de un fotograma y genera el estado del VMS y semáforo.
        """
        # Contadores de clases
        class_counts: Dict[str, int] = {}
        detected_classes = []

        for d in detections:
            cls = d.get("class", "").lower()
            detected_classes.append(cls)
            class_counts[cls] = class_counts.get(cls, 0) + 1

        # Contar total de vehículos
        vehicle_keys = ["vehiculo", "car", "auto", "truck", "bus", "camion", "moto", "motocicle", "motorcycle", "camioneta"]
        total_vehicles = sum(count for cls, count in class_counts.items() if any(vk in cls for vk in vehicle_keys))

        # Reglas de Prioridad para el Panel VMS
        # 1. CONTRAFLUJO (Peligro crítico)
        has_contraflujo = any("contraflujo" in c or "contra_flujo" in c or "wrong_way" in c for c in detected_classes)
        # 2. PEATÓN / PERSONAS
        has_people = any("people" in c or "peaton" in c or "person" in c for c in detected_classes)
        # 3. CICLISTA
        has_bicicleta = any("bicicleta" in c or "bicycle" in c or "ciclista" in c for c in detected_classes)
        # 4. MOTOS
        has_moto = any("moto" in c or "motocicle" in c or "motorcycle" in c for c in detected_classes)

        timestamp_str = datetime.now().strftime("%H:%M:%S")

        if has_contraflujo:
            alert_level = "CRITICAL"
            vms_title = "¡PELIGRO EXTREMO!"
            vms_message = "VEHÍCULO EN CONTRAFLUJO DETECTADO\nNO ADELANTAR - REDUZCA VELOCIDAD"
            vms_color = "#FF1744"  # Rojo Neón
            vms_bg = "#3A0007"
            vms_icon = "🚨 ⛔"
            speed_limit = "20 KM/H"
            is_flashing = True
        elif has_moto:
            alert_level = "INFO"
            vms_title = "PRECAUCIÓN VIAL"
            vms_message = "MOTOCICLETAS EN LA VÍA\nMANTENGA SU DISTANCIA"
            vms_color = "#C6FF00"  # Verde Lima LED
            vms_bg = "#1A2300"
            vms_icon = "🏍️ ⚠️"
            speed_limit = "60 KM/H"
            is_flashing = False
        elif has_people:
            alert_level = "WARNING"
            vms_title = "PRECAUCIÓN - PEATONES"
            vms_message = "PEATONES EN CALZADA DETECTADOS\nCEDA EL PASO - VELOCIDAD MÁX 30 KM/H"
            vms_color = "#00E5FF"  # Cyan Neón
            vms_bg = "#002B33"
            vms_icon = "🚶 ⚠️"
            speed_limit = "30 KM/H"
            is_flashing = True
        elif has_bicicleta:
            alert_level = "INFO"
            vms_title = "PRECAUCIÓN VIAL"
            vms_message = "CICLISTA EN CALZADA - DISTANCIA MÍNIMA 1.5M"
            vms_color = "#00E5FF"  # Cyan LED
            vms_bg = "#002B33"
            vms_icon = "🚴 ⚠️"
            speed_limit = "50 KM/H"
            is_flashing = False
        elif total_vehicles >= 6:
            alert_level = "CONGESTION"
            vms_title = "VÍA CONGESTIONADA"
            vms_message = f"ALTO FLUJO VEHICULAR ({total_vehicles} VEHÍCULOS)\nREDUZCA LA VELOCIDAD Y ESPERE SU TURNO"
            vms_color = "#FF6D00"
            vms_bg = "#331600"
            vms_icon = "⚠️ 🚗"
            speed_limit = "40 KM/H"
            is_flashing = False
        elif total_vehicles > 0:
            alert_level = "NORMAL"
            vms_title = "TRÁFICO FLUIDO"
            vms_message = f"TRÁFICO NORMAL EN VÍA ({total_vehicles} DETECTADOS)\nRESPETE EL LÍMITE DE VELOCIDAD"
            vms_color = "#00E676"  # Verde Neón
            vms_bg = "#002B13"
            vms_icon = "🛣️ ✅"
            speed_limit = "80 KM/H"
            is_flashing = False
        else:
            alert_level = "NORMAL"
            vms_title = "VÍA DESPEJADA"
            vms_message = "SIN INCIDENCIAS REPORTADAS\nMANEJE CON SEGURIDAD"
            vms_color = "#00E676"
            vms_bg = "#002B13"
            vms_icon = "🛣️ 🟢"
            speed_limit = "80 KM/H"
            is_flashing = False

        result = {
            "timestamp": timestamp_str,
            "total_detections": len(detections),
            "total_vehicles": total_vehicles,
            "class_counts": class_counts,
            "alert_level": alert_level,
            "vms": {
                "title": vms_title,
                "message": vms_message,
                "color": vms_color,
                "bg_color": vms_bg,
                "icon": vms_icon,
                "is_flashing": is_flashing,
                "speed_limit": speed_limit
            }
        }

        # Registrar en historial para métricas de tesis
        log_entry = {
            "Hora": timestamp_str,
            "Nivel_Alerta": alert_level,
            "Vehiculos": total_vehicles,
            "Clases_Detectadas": ", ".join([f"{k}:{v}" for k, v in class_counts.items()]) if class_counts else "Ninguna",
            "Mensaje_VMS": vms_title,
            "Limite_Velocidad": speed_limit
        }
        self.history_logs.append(log_entry)
        # Mantener últimos 200 registros
        if len(self.history_logs) > 200:
            self.history_logs.pop(0)

        return result


def draw_detections(
    image: np.ndarray,
    detections: List[Dict[str, Any]],
    show_confidence: bool = True
) -> np.ndarray:
    """
    Dibuja cajas delimitadoras profesionales con fondos semitransparentes y etiquetas.
    """
    annotated = image.copy()
    h, w = annotated.shape[:2]

    for d in detections:
        box = d.get("box", {})
        x1 = int(box.get("x1", 0))
        y1 = int(box.get("y1", 0))
        x2 = int(box.get("x2", 0))
        y2 = int(box.get("y2", 0))

        # Asegurar límites dentro de la imagen
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w - 1, x2), min(h - 1, y2)

        cls_name = d.get("class", "objeto").lower()
        display_name = CLASS_TRANSLATIONS.get(cls_name, cls_name).upper()
        conf = d.get("confidence", 1.0)
        color = get_class_color(cls_name)

        # Dibujar caja con grosor según relevancia
        thickness = 3 if "contraflujo" in cls_name.lower() else 2
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)

        # Etiqueta de texto
        label = f"{display_name}"
        if show_confidence:
            label += f" {conf * 100:.0f}%"

        # Medir tamaño del texto
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.55
        font_thickness = 1
        (tw, th), baseline = cv2.getTextSize(label, font, font_scale, font_thickness)

        # Fondo de la etiqueta
        label_y1 = max(0, y1 - th - 8)
        label_y2 = y1
        cv2.rectangle(annotated, (x1, label_y1), (x1 + tw + 10, label_y2), color, -1)

        # Texto en contraste (negro sobre color claro)
        cv2.putText(annotated, label, (x1 + 5, label_y2 - 4), font, font_scale, (0, 0, 0), font_thickness, cv2.LINE_AA)

    return annotated
