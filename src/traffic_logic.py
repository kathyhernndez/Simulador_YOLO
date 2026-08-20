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
    
    # Emergencia (Blanco / Rojo estroboscópico, BGR: 255, 255, 255)
    "ambulancia": (255, 255, 255),
    "ambulance": (255, 255, 255),
    "patrulla": (255, 255, 255),
    
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
    "people": "PEATÓN",
    "ambulance": "AMBULANCIA",
    "ambulancia": "AMBULANCIA",
    "patrulla": "PATRULLA"
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
        Analiza las detecciones de un fotograma y genera el estado para 3 PMVs simultáneos.
        """
        # Contadores de clases
        class_counts: Dict[str, int] = {}
        detected_classes = []

        for d in detections:
            cls = d.get("class", "").lower()
            detected_classes.append(cls)
            class_counts[cls] = class_counts.get(cls, 0) + 1

        # Contar total de vehículos
        vehicle_keys = ["vehiculo", "car", "auto", "truck", "bus", "camion", "moto", "motocicle", "motorcycle", "camioneta", "ambulance", "ambulancia", "patrulla"]
        total_vehicles = sum(count for cls, count in class_counts.items() if any(vk in cls for vk in vehicle_keys))

        # Determinar condiciones
        has_contraflujo = any("contraflujo" in c or "contra_flujo" in c or "wrong_way" in c for c in detected_classes)
        has_emergency = any("ambulan" in c or "patrulla" in c for c in detected_classes)
        bloqueo_interseccion = total_vehicles >= 10  # Asumimos que >=10 es un bloqueo de intersección (LOS E-F)
        
        has_people = any("people" in c or "peaton" in c or "person" in c or "pedestrian" in c for c in detected_classes)
        alta_densidad_peatonal = sum(count for cls, count in class_counts.items() if any(pk in cls for pk in ["people", "peaton", "person", "pedestrian"])) >= 3
        
        has_carga = any("truck" in c or "camion" in c or "bus" in c for c in detected_classes)
        
        # Diccionarios de PMV
        pmv1 = {}
        pmv2 = {}
        pmv3 = {}
        
        alert_level = "NORMAL"

        # Jerarquía de Prioridades (Árbol de Decisión)
        
        if has_contraflujo or has_emergency or bloqueo_interseccion:
            # Prioridad 1 (Peligro Crítico y Emergencia)
            alert_level = "CRITICAL"
            
            pmv1 = {
                "title": "VÍA CONGESTIONADA", "message": "DESVIO OBLIGATORIO\nPOR CALLE FEDERACION",
                "color": "#FF1744", "bg_color": "#3A0007", "icon": "⛔", "is_flashing": True, "speed_limit": "10 KM/H"
            }
            pmv2 = {
                "title": "ESQUINA BLOQUEADA", "message": "NO OBSTRUYA CRUCE\nESPERE EN LINEA",
                "color": "#FF1744", "bg_color": "#3A0007", "icon": "⛔", "is_flashing": True, "speed_limit": "10 KM/H"
            }
            
            if has_emergency:
                pmv3 = {
                    "title": "UNIDAD EMERGENCIA", "message": "CEDA EL PASO YA\nDESPEJE CALZADA",
                    "color": "#FF1744", "bg_color": "#3A0007", "icon": "🚑", "is_flashing": True, "speed_limit": "10 KM/H"
                }
            else:
                pmv3 = {
                    "title": "GIRO COLON CERRADO", "message": "PROHIBIDO GIRO IZQUIERDA\nSIGA A AV MANAURE",
                    "color": "#FF1744", "bg_color": "#3A0007", "icon": "🚫", "is_flashing": True, "speed_limit": "15 KM/H"
                }

        elif has_people and alta_densidad_peatonal:
            # Prioridad 2 (Advertencia por Actores Vulnerables - Peatones)
            alert_level = "WARNING"
            
            pmv1 = {
                "title": "TRAFICO LENTO", "message": "CONGESTIÓN EN CALLE GARCES\nPREVENTIVO FEDERACIÓN",
                "color": "#FFEA00", "bg_color": "#332D00", "icon": "⚠️", "is_flashing": False, "speed_limit": "15 KM/H"
            }
            pmv2 = {
                "title": "ZONA COMERCIAL", "message": "PRIORIDAD PEATON\nREDUZCA VELOCIDAD",
                "color": "#FFEA00", "bg_color": "#332D00", "icon": "🚶", "is_flashing": False, "speed_limit": "10 KM/H"
            }
            pmv3 = {
                "title": "CALLE COLON SATURADA", "message": "SIGA DERECHO\nHACIA AV MANAURE",
                "color": "#FFEA00", "bg_color": "#332D00", "icon": "➡️", "is_flashing": False, "speed_limit": "15 KM/H"
            }
            
        elif has_carga:
            # Prioridad 3 (Precaución por Obstrucciones y Carga/Descarga)
            alert_level = "WARNING"
            
            pmv1 = {
                "title": "GARCES SATURADA", "message": "DESVIO SUGERIDO\nPOR CALLE FEDERACION",
                "color": "#FF9100", "bg_color": "#331600", "icon": "🚧", "is_flashing": False, "speed_limit": "15 KM/H"
            }
            pmv2 = {
                "title": "VEHICULO DETENIDO", "message": "CANAL REDUCIDO\nPASO INTERMITENTE",
                "color": "#FFEA00", "bg_color": "#332D00", "icon": "⚠️", "is_flashing": False, "speed_limit": "10 KM/H"
            }
            pmv3 = {
                "title": "CALLE COLON SATURADA", "message": "SIGA DERECHO\nHACIA AV MANAURE",
                "color": "#FFEA00", "bg_color": "#332D00", "icon": "➡️", "is_flashing": False, "speed_limit": "15 KM/H"
            }

        elif total_vehicles >= 12:
            # Prioridad 4 (Congestión y Retención Moderada - LOS C-D)
            alert_level = "CONGESTION"
            
            pmv1 = {
                "title": "TRAFICO LENTO", "message": "CONGESTIÓN EN CALLE GARCES\nPREVENTIVO FEDERACIÓN",
                "color": "#FFEA00", "bg_color": "#332D00", "icon": "⚠️", "is_flashing": False, "speed_limit": "15 KM/H"
            }
            pmv2 = {
                "title": "CRUCE DESPEJADO", "message": "PASO CONTINUO",
                "color": "#00E676", "bg_color": "#002B13", "icon": "✅", "is_flashing": False, "speed_limit": "20 KM/H"
            }
            pmv3 = {
                "title": "CALLE COLON SATURADA", "message": "SIGA DERECHO\nHACIA AV MANAURE",
                "color": "#FFEA00", "bg_color": "#332D00", "icon": "➡️", "is_flashing": False, "speed_limit": "15 KM/H"
            }

        else:
            # Prioridad 5 (Flujo Libre y Condición Normal - LOS A-B)
            alert_level = "NORMAL"
            
            pmv1 = {
                "title": "ENTRADA LIBRE", "message": "GARCES FLUIDA",
                "color": "#00E676", "bg_color": "#002B13", "icon": "✅", "is_flashing": False, "speed_limit": "20 KM/H"
            }
            pmv2 = {
                "title": "CRUCE DESPEJADO", "message": "PASO CONTINUO",
                "color": "#00E676", "bg_color": "#002B13", "icon": "✅", "is_flashing": False, "speed_limit": "20 KM/H"
            }
            pmv3 = {
                "title": "COLON / MANAURE OK", "message": "GIRO A COLON LIBRE",
                "color": "#00E676", "bg_color": "#002B13", "icon": "✅", "is_flashing": False, "speed_limit": "20 KM/H"
            }

        timestamp_str = datetime.now().strftime("%H:%M:%S")
        # ---------------------------------------------------------
        # ESTRUCTURACIÓN Y DESACOPLAMIENTO (DATA PAYLOAD)
        # ---------------------------------------------------------

        result = {
            "timestamp": timestamp_str,
            "total_detections": len(detections),
            "total_vehicles": total_vehicles,
            "class_counts": class_counts,
            "alert_level": alert_level,
            "pmv1": pmv1,
            "pmv2": pmv2,
            "pmv3": pmv3
        }

        # Registrar en historial para métricas de tesis
        log_entry = {
            "Hora": timestamp_str,
            "Nivel_Alerta": alert_level,
            "Vehiculos": total_vehicles,
            "Clases_Detectadas": ", ".join([f"{k}:{v}" for k, v in class_counts.items()]) if class_counts else "Ninguna",
            "Mensaje_PMV1": pmv1["title"],
            "Limite_Velocidad": pmv1["speed_limit"]
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
