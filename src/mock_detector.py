"""
Generador de Escenarios de Prueba y Detecciones Simuladas (Modo Resiliencia / Demo)
Permite demostrar el sistema de pórtico VMS y semáforos sin depender exclusivamente de cuota de API.
"""

from typing import Dict, Any, List, Tuple
import cv2
import numpy as np


class MockTrafficScenarioGenerator:
    SCENARIOS = {
        "normal": {
            "name": "🟢 Escenario 1: Tráfico Normal y Fluido",
            "desc": "Autopista con vehículos circulando a velocidad permitida en sentido reglamentario.",
            "detections": [
                {"class": "vehiculo", "confidence": 0.94, "box": {"x1": 180, "y1": 240, "x2": 290, "y2": 350}},
                {"class": "vehiculo", "confidence": 0.89, "box": {"x1": 420, "y1": 260, "x2": 520, "y2": 370}},
                {"class": "vehiculo", "confidence": 0.82, "box": {"x1": 310, "y1": 200, "x2": 380, "y2": 270}}
            ]
        },
        "motos": {
            "name": "🏍️ Escenario 2: Motocicletas en la Vía",
            "desc": "Motocicletas circulando entre canales y acercándose a la intersección.",
            "detections": [
                {"class": "moto", "confidence": 0.96, "box": {"x1": 450, "y1": 200, "x2": 520, "y2": 320}},
                {"class": "vehiculo", "confidence": 0.91, "box": {"x1": 150, "y1": 250, "x2": 270, "y2": 360}}
            ]
        },
        "peatones": {
            "name": "🚶 Escenario 3: Peatones en Calzada",
            "desc": "Peatones cruzando la vía de forma imprudente.",
            "detections": [
                {"class": "peaton", "confidence": 0.92, "box": {"x1": 380, "y1": 270, "x2": 420, "y2": 420}},
                {"class": "vehiculo", "confidence": 0.88, "box": {"x1": 120, "y1": 230, "x2": 240, "y2": 340}}
            ]
        },
        "contraflujo": {
            "name": "🚨 Escenario 4: Peligro Crítico de Vehículo en Contraflujo",
            "desc": "Vehículo circulando en sentido contrario al flujo establecido del canal rápido.",
            "detections": [
                {"class": "contraflujo", "confidence": 0.97, "box": {"x1": 260, "y1": 210, "x2": 390, "y2": 340}},
                {"class": "vehiculo", "confidence": 0.90, "box": {"x1": 460, "y1": 260, "x2": 580, "y2": 380}}
            ]
        },
        "congestion": {
            "name": "🚦 Escenario 5: Congestión de Intersección",
            "desc": "Alta densidad vehicular en aproximación a intersección semaforizada.",
            "detections": [
                {"class": "vehiculo", "confidence": 0.95, "box": {"x1": 80, "y1": 280, "x2": 190, "y2": 400}},
                {"class": "vehiculo", "confidence": 0.93, "box": {"x1": 210, "y1": 260, "x2": 320, "y2": 380}},
                {"class": "vehiculo", "confidence": 0.91, "box": {"x1": 340, "y1": 270, "x2": 450, "y2": 390}},
                {"class": "vehiculo", "confidence": 0.87, "box": {"x1": 470, "y1": 250, "x2": 570, "y2": 370}},
                {"class": "vehiculo", "confidence": 0.84, "box": {"x1": 230, "y1": 190, "x2": 300, "y2": 260}},
                {"class": "vehiculo", "confidence": 0.81, "box": {"x1": 360, "y1": 180, "x2": 430, "y2": 250}}
            ]
        }
    }

    @classmethod
    def generate_synthetic_road_image(cls, scenario_key: str, width: int = 640, height: int = 480) -> np.ndarray:
        """
        Dibuja una escena sintética vectorial de autopista/intersección de alta calidad para pruebas visuales.
        """
        img = np.zeros((height, width, 3), dtype=np.uint8)

        # 1. Cielo (Gradiente crepúsculo / día)
        for y in range(int(height * 0.45)):
            alpha = y / (height * 0.45)
            b = int(220 * (1 - alpha * 0.4))
            g = int(160 * (1 - alpha * 0.3))
            r = int(90 * (1 - alpha * 0.2))
            img[y, :] = [b, g, r]

        # 2. Paisaje / Desierto / Vegetación en el horizonte
        horizon_y = int(height * 0.45)
        img[horizon_y:int(height * 0.55), :] = [60, 110, 140]  # Tono tierra/arena

        # 3. Asfalto de la carretera con perspectiva
        pts_road = np.array([
            [int(width * 0.35), horizon_y],
            [int(width * 0.65), horizon_y],
            [width + 50, height],
            [-50, height]
        ], np.int32)
        cv2.fillPoly(img, [pts_road], (45, 45, 48))

        # 4. Líneas divisorias de carril (Perspectiva)
        # Línea central punteada amarilla
        for i in range(7):
            t1 = i / 7.0
            t2 = (i + 0.5) / 7.0
            y_start = int(horizon_y + t1 * (height - horizon_y))
            y_end = int(horizon_y + t2 * (height - horizon_y))
            x_center_start = int(width * 0.5 + (0.5 - 0.5) * (y_start - horizon_y))
            x_center_end = int(width * 0.5 + (0.5 - 0.5) * (y_end - horizon_y))
            thick = int(2 + t1 * 6)
            cv2.line(img, (x_center_start, y_start), (x_center_end, y_end), (0, 215, 255), thick)

        # Líneas laterales blancas continuas
        cv2.line(img, (int(width * 0.35), horizon_y), (-30, height), (240, 240, 240), 4)
        cv2.line(img, (int(width * 0.65), horizon_y), (width + 30, height), (240, 240, 240), 4)

        # 5. Dibujar elementos característicos del escenario
        scenario = cls.SCENARIOS.get(scenario_key, cls.SCENARIOS["normal"])
        for d in scenario["detections"]:
            cls_name = d["class"]
            b = d["box"]
            x1, y1, x2, y2 = b["x1"], b["y1"], b["x2"], b["y2"]

            if cls_name in ["vehiculo", "contraflujo"]:
                # Dibujar silueta básica de automóvil
                car_color = (0, 0, 180) if cls_name == "contraflujo" else (160, 60, 40)
                # Chasis
                cv2.rectangle(img, (x1 + 10, y1 + int((y2 - y1) * 0.3)), (x2 - 10, y2 - 10), car_color, -1)
                # Techo
                cv2.rectangle(img, (x1 + 25, y1 + 10), (x2 - 25, y1 + int((y2 - y1) * 0.45)), car_color, -1)
                # Luces
                light_color = (0, 255, 255) if cls_name == "contraflujo" else (0, 0, 240)
                cv2.circle(img, (x1 + 20, y2 - 20), 8, light_color, -1)
                cv2.circle(img, (x2 - 20, y2 - 20), 8, light_color, -1)
            elif cls_name in ["moto", "motocicle", "motorcycle"]:
                # Motocicleta (cuerpo y ruedas)
                cv2.circle(img, (x1 + 20, y2 - 20), 15, (30, 30, 30), 4)
                cv2.circle(img, (x2 - 20, y2 - 20), 15, (30, 30, 30), 4)
                cv2.rectangle(img, (x1 + 10, y1 + 30), (x2 - 10, y2 - 30), (0, 200, 50), -1)
            elif cls_name in ["peaton", "person", "people"]:
                # Peatón (cabeza y cuerpo)
                cv2.circle(img, (int((x1 + x2) / 2), y1 + 20), 15, (150, 150, 150), -1)
                cv2.line(img, (int((x1 + x2) / 2), y1 + 35), (int((x1 + x2) / 2), y2 - 20), (200, 50, 50), 10)
            elif cls_name == "bicicleta":
                # Bicicleta
                cv2.circle(img, (x1 + 15, y2 - 15), 14, (20, 20, 20), 3)
                cv2.circle(img, (x2 - 15, y2 - 15), 14, (20, 20, 20), 3)
                cv2.line(img, (x1 + 15, y2 - 15), (x2 - 15, y2 - 15), (0, 200, 100), 3)

        return img

    @classmethod
    def get_scenario_detections(cls, scenario_key: str) -> List[Dict[str, Any]]:
        scenario = cls.SCENARIOS.get(scenario_key, cls.SCENARIOS["normal"])
        return scenario["detections"]
