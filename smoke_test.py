# =====================================================================
# Proyecto: Simulador de Flujo e Inferencia Visual
# Asesoría Técnica: Tesis de Grado en Ingeniería Civil
# Autor y Desarrollo de Software: Katherine Hernández
# Año: 2026
# Licencia: MIT
# =====================================================================
"""
Smoke Test para Validar la Integración de Módulos del Simulador
"""

import sys
import numpy as np

def run_smoke_tests():
    print("=" * 60)
    print("🚀 INICIANDO PRUEBAS DE INTEGRACIÓN (SMOKE TESTS)")
    print("=" * 60)

    # 1. Probar generador de escenarios
    from src.mock_detector import MockTrafficScenarioGenerator
    print("[TEST 1/4] Probando MockTrafficScenarioGenerator...")
    for key in MockTrafficScenarioGenerator.SCENARIOS.keys():
        img = MockTrafficScenarioGenerator.generate_synthetic_road_image(key)
        assert img is not None and img.shape == (480, 640, 3), f"Error generando imagen para escenario {key}"
        dets = MockTrafficScenarioGenerator.get_scenario_detections(key)
        assert isinstance(dets, list), f"Detecciones no son lista en {key}"
    print("  -> PASÓ: Todos los 5 escenarios sintéticos generados correctamente.")

    # 2. Probar motor de lógica de tráfico y VMS
    from src.traffic_logic import TrafficAnalyticsEngine, draw_detections
    print("[TEST 2/4] Probando TrafficAnalyticsEngine y Reglas VMS...")
    engine = TrafficAnalyticsEngine()

    # Caso A: Contraflujo
    cf_dets = [{"class": "contraflujo", "confidence": 0.95, "box": {"x1": 100, "y1": 100, "x2": 200, "y2": 200}}]
    res_cf = engine.evaluate_frame_events(cf_dets)
    assert res_cf["alert_level"] == "CRITICAL", f"Alerta esperada CRITICAL, obtenida: {res_cf['alert_level']}"
    assert "CONTRAFLUJO" in res_cf["vms"]["message"]

    # Caso B: Maquinaria
    mq_dets = [{"class": "maquinaria", "confidence": 0.9, "box": {"x1": 100, "y1": 100, "x2": 200, "y2": 200}}]
    res_mq = engine.evaluate_frame_events(mq_dets)
    assert res_mq["alert_level"] == "WARNING", f"Alerta esperada WARNING, obtenida: {res_mq['alert_level']}"

    # Caso C: Arena
    ar_dets = [{"class": "arena", "confidence": 0.88, "box": {"x1": 100, "y1": 100, "x2": 200, "y2": 200}}]
    res_ar = engine.evaluate_frame_events(ar_dets)
    assert res_ar["alert_level"] == "WARNING"

    # Caso D: Tráfico normal
    norm_dets = [{"class": "vehiculo", "confidence": 0.92, "box": {"x1": 100, "y1": 100, "x2": 200, "y2": 200}}]
    res_norm = engine.evaluate_frame_events(norm_dets)
    assert res_norm["alert_level"] == "NORMAL"

    print("  -> PASÓ: Evaluación de reglas VMS (Contraflujo, Maquinaria, Arena, Normal) validada con éxito.")

    # 3. Probar renderizador OpenCV
    print("[TEST 3/4] Probando renderizado visual con OpenCV...")
    test_img = np.zeros((480, 640, 3), dtype=np.uint8)
    annotated = draw_detections(test_img, cf_dets)
    assert annotated.shape == (480, 640, 3)
    print("  -> PASÓ: Renderizado de cajas delimitadoras y etiquetas completado.")

    # 4. Probar componentes UI
    from src.ui_components import get_custom_css, render_vms_html, render_traffic_light_html
    print("[TEST 4/4] Probando renderizado HTML/CSS de componentes...")
    css = get_custom_css()
    assert len(css) > 100
    vms_html = render_vms_html(res_cf["vms"])
    assert "vms-gantry-container" in vms_html
    tl_html = render_traffic_light_html("GREEN", 15)
    assert "traffic-light-housing" in tl_html
    print("  -> PASÓ: Componentes de VMS y semáforo listos.")

    # 5. Probar LocalYOLOModel con best.pt
    from src.local_yolo import LocalYOLOModel
    print("[TEST 5/5] Probando carga e inferencia de modelo local YOLO (best.pt)...")
    yolo_local = LocalYOLOModel("best.pt")
    assert yolo_local.is_loaded, "El modelo local best.pt debería estar cargado."
    assert len(yolo_local.classes) > 0, "El modelo debe tener clases detectables."
    dummy_img = np.zeros((480, 640, 3), dtype=np.uint8)
    dets, lat, ann = yolo_local.infer(dummy_img, conf=0.35)
    assert ann is not None and ann.shape == (480, 640, 3)
    print(f"  -> PASÓ: Modelo best.pt cargado exitosamente. Clases: {yolo_local.classes} | Latencia de prueba: {lat:.1f}ms")

    print("=" * 60)
    print("🎉 ¡TODOS LOS SMOKE TESTS (5/5) PASARON EXITOSAMENTE!")
    print("=" * 60)

if __name__ == "__main__":
    run_smoke_tests()

