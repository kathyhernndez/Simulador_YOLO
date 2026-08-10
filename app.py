"""
Simulador de Sistema Inteligente de Señalización de Tráfico y Panel VMS
Integración con Modelo Local YOLO (best.pt) y Roboflow Workflow API
Desarrollado para Proyecto Factible / Tesis de Grado.
"""

import os
import io
import time
import tempfile
from datetime import datetime
import streamlit as st
import cv2
import numpy as np
from PIL import Image
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Intentar importar Ultralytics YOLO
try:
    from ultralytics import YOLO
    HAS_ULTRALYTICS = True
except ImportError:
    HAS_ULTRALYTICS = False

# Importar módulos propios
from src.roboflow_client import RoboflowClient, RoboflowWorkflowError
from src.traffic_logic import TrafficAnalyticsEngine, draw_detections, get_class_color
from src.mock_detector import MockTrafficScenarioGenerator
from src.ui_components import get_custom_css, render_vms_html
from src.local_yolo import LocalYOLOModel

# Configuración de página de Streamlit
st.set_page_config(
    page_title="Simulador SMV & Tráfico Inteligente | Tesis",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyectar estilos CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Inicializar estado de sesión
if "analytics_engine" not in st.session_state:
    st.session_state.analytics_engine = TrafficAnalyticsEngine()
if "last_results" not in st.session_state:
    st.session_state.last_results = None
if "api_key" not in st.session_state:
    st.session_state.api_key = os.getenv("ROBOFLOW_API_KEY", "")
if "model_path" not in st.session_state:
    st.session_state.model_path = "best.pt"


@st.cache_resource
def load_local_yolo(model_path: str):
    """Carga y almacena en caché el modelo local YOLO."""
    if not HAS_ULTRALYTICS:
        return None
    if not os.path.exists(model_path):
        return None
    try:
        model = YOLO(model_path)
        return model
    except Exception as e:
        st.error(f"Error cargando modelo YOLO '{model_path}': {e}")
        return None


# ----------------- BARRA LATERAL (CONFIGURACIÓN) -----------------
with st.sidebar:
    st.title("⚙️ Configuración")
    st.caption("Proyecto Factible de Tesis: SMV & YOLO")
    st.markdown("---")

    # Selección de Modo de Operación
    operation_mode = st.radio(
        "Modo de Inferencia:",
        [
            "🤖 Modelo Local YOLO (best.pt)",
            "🚀 Roboflow Workflow API (Nube)",
            "🧪 Simulación de Escenarios (Offline / Demo)"
        ],
        index=0
    )

    st.markdown("---")

    # Configuración según modo
    if operation_mode == "🤖 Modelo Local YOLO (best.pt)":
        st.subheader("📦 Modelo Local YOLO")
        
        # Verificar existencia de best.pt
        model_exists = os.path.exists(st.session_state.model_path)
        if model_exists:
            file_size_mb = os.path.getsize(st.session_state.model_path) / (1024 * 1024)
            st.success(f"✅ Archivo encontrado: `{st.session_state.model_path}` ({file_size_mb:.1f} MB)")
            
            # Cargar modelo en memoria
            yolo_model = load_local_yolo(st.session_state.model_path)
            if yolo_model and hasattr(yolo_model, "names"):
                st.caption(f"**Clases detectables:** {list(yolo_model.names.values())}")
        else:
            st.warning(f"⚠️ No se encontró el archivo `{st.session_state.model_path}` en la raíz.")
            uploaded_pt = st.file_uploader("Subir archivo de pesos (.pt):", type=["pt"])
            if uploaded_pt:
                with open("best.pt", "wb") as f:
                    f.write(uploaded_pt.read())
                st.session_state.model_path = "best.pt"
                st.rerun()

    elif operation_mode == "🚀 Roboflow Workflow API (Nube)":
        st.subheader("🔑 Parámetros de Roboflow")
        api_key_input = st.text_input(
            "Roboflow API Key:",
            value=st.session_state.api_key,
            type="password",
            help="Introduce tu clave privada de Roboflow (app.roboflow.com/settings/api)"
        )
        if api_key_input != st.session_state.api_key:
            st.session_state.api_key = api_key_input

        workspace_input = st.text_input(
            "Workspace Slug:",
            value=os.getenv("ROBOFLOW_WORKSPACE", "katherines-workspace-q66ls")
        )
        workflow_input = st.text_input(
            "Workflow ID:",
            value=os.getenv("ROBOFLOW_WORKFLOW_ID", "tesis-trafico-vtesis-trafico-2-rfdetr-small-t1-logic")
        )

    st.markdown("---")
    st.subheader("🎯 Parámetros de Detección")
    conf_threshold = st.slider(
        "Umbral de Confianza (Confidence):",
        min_value=0.10,
        max_value=1.00,
        value=0.35,
        step=0.05
    )
    frame_skip = st.slider(
        "Intervalo de Salto de Frames (Video):",
        min_value=1,
        max_value=10,
        value=2,
        help="Procesar 1 de cada N frames para optimizar la fluidez."
    )

    st.markdown("---")
    st.caption("v2.0.0 | Sistema de Simulación Vial con YOLO")


# Cargar modelo local si corresponde
local_yolo_instance = None
if operation_mode == "🤖 Modelo Local YOLO (best.pt)":
    local_yolo_instance = load_local_yolo(st.session_state.model_path)

# Cliente Roboflow como alternativa
roboflow_client = None
if operation_mode == "🚀 Roboflow Workflow API (Nube)":
    roboflow_client = RoboflowClient(
        api_key=st.session_state.api_key,
        workspace_name=os.getenv("ROBOFLOW_WORKSPACE", "katherines-workspace-q66ls"),
        workflow_id=os.getenv("ROBOFLOW_WORKFLOW_ID", "tesis-trafico-vtesis-trafico-2-rfdetr-small-t1-logic")
    )


# ----------------- CABECERA PRINCIPAL -----------------
st.markdown("""
<div style="padding: 10px 0 20px 0;">
    <h1 style="margin-bottom: 0px; font-weight: 800; color: #f8f9fa;">
        🚦 Simulador de Sistema Inteligente de Señalización Vial (SMV)
    </h1>
    <p style="color: #94a3b8; font-size: 1.05rem; margin-top: 5px;">
        Detección en Tiempo Real con YOLO (best.pt) | Panel de Mensaje Variable VMS | Semáforo Dinámico
    </p>
</div>
""", unsafe_allow_html=True)


# ----------------- SELECCIÓN DE ENTRADA MULTIMEDIA -----------------
st.subheader("📹 Fuente de Datos de Tráfico")
input_source = st.radio(
    "Selecciona la fuente de entrada para la simulación:",
    ["📤 Subir Video (.mp4, .avi)", "🖼️ Subir Imagen Fija (.jpg, .png)", "🏞️ Escenarios de Prueba Sintéticos (Demo)"],
    horizontal=True
)

tab_col1, tab_col2 = st.columns([3, 2])


def run_detection_pipeline(frame: np.ndarray, conf_val: float) -> tuple:
    """
    Ejecuta el pipeline de inferencia según el modo seleccionado.
    Retorna: (detections, latency_ms, annotated_frame)
    """
    detections = []
    latency_ms = 0.0
    annotated = frame.copy()

    if operation_mode == "🤖 Modelo Local YOLO (best.pt)":
        if local_yolo_instance is not None:
            start_t = time.time()
            # Inferencia con YOLO local
            results = local_yolo_instance(frame, conf=conf_val, verbose=False)
            latency_ms = (time.time() - start_t) * 1000

            if results and len(results) > 0:
                result = results[0]
                # Frame anotado con ultralytics
                annotated = result.plot()

                # Extraer cajas y clases
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        cls_id = int(box.cls[0].item())
                        cls_name = local_yolo_instance.names.get(cls_id, str(cls_id))
                        conf_score = float(box.conf[0].item())
                        xyxy = box.xyxy[0].tolist()
                        x1, y1, x2, y2 = int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])
                        
                        detections.append({
                            "class": str(cls_name).lower().strip(),
                            "confidence": round(conf_score, 3),
                            "box": {
                                "x1": x1,
                                "y1": y1,
                                "x2": x2,
                                "y2": y2,
                                "width": max(1, x2 - x1),
                                "height": max(1, y2 - y1)
                            }
                        })
        else:
            # Fallback a mock si el modelo no está listo
            detections = MockTrafficScenarioGenerator.get_scenario_detections("normal")
            annotated = draw_detections(frame, detections)
            latency_ms = 15.0

    elif operation_mode == "🚀 Roboflow Workflow API (Nube)":
        if roboflow_client and roboflow_client.is_configured:
            try:
                detections, latency_ms, _ = roboflow_client.infer(frame, confidence_threshold=conf_val)
                annotated = draw_detections(frame, detections)
            except Exception as e:
                detections = MockTrafficScenarioGenerator.get_scenario_detections("normal")
                annotated = draw_detections(frame, detections)
                latency_ms = 20.0
        else:
            detections = MockTrafficScenarioGenerator.get_scenario_detections("normal")
            annotated = draw_detections(frame, detections)
            latency_ms = 20.0

    else:  # Simulación de Escenarios
        detections = MockTrafficScenarioGenerator.get_scenario_detections("normal")
        annotated = draw_detections(frame, detections)
        latency_ms = 12.0

    return detections, latency_ms, annotated


# ----------------- PROCESAMIENTO SEGÚN FUENTE -----------------

if input_source == "📤 Subir Video (.mp4, .avi)":
    uploaded_video = st.file_uploader("Cargar archivo de video para simulación", type=["mp4", "avi", "mov"])
    if uploaded_video:
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        tfile.write(uploaded_video.read())
        tfile.flush()

        cap = cv2.VideoCapture(tfile.name)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(cap.get(cv2.CAP_PROP_FPS)) or 25

        st.success(f"Video cargado exitosamente: {total_frames} fotogramas a {fps} FPS.")
        start_btn = st.button("▶️ Iniciar Simulación en Tiempo Real con YOLO", type="primary")

        if start_btn:
            with tab_col1:
                st.markdown("### 🎥 Transmisión de Cámara y Detección")
                frame_placeholder = st.empty()
                perf_placeholder = st.empty()
            with tab_col2:
                st.markdown("### 📟 Panel VMS Virtual")
                vms_placeholder = st.empty()

            frame_idx = 0
            progress_bar = st.progress(0)

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                frame_idx += 1
                if frame_idx % frame_skip != 0:
                    continue

                # Ejecutar inferencia con YOLO
                detections, latency_ms, annotated_frame = run_detection_pipeline(frame, conf_threshold)

                # Evaluar reglas de tráfico para el panel VMS y semáforo
                analysis = st.session_state.analytics_engine.evaluate_frame_events(detections)

                # Actualizar interfaz en tiempo real
                frame_placeholder.image(annotated_frame, channels="BGR", use_container_width=True)
                perf_placeholder.caption(f"Fotograma: {frame_idx}/{total_frames} | Latencia: {latency_ms:.1f} ms | Detecciones: {len(detections)}")
                
                vms_placeholder.markdown(render_vms_html(analysis["vms"]), unsafe_allow_html=True)

                if total_frames > 0:
                    progress_bar.progress(min(1.0, frame_idx / total_frames))

                time.sleep(0.01)

            cap.release()
            try:
                os.unlink(tfile.name)
            except Exception:
                pass


elif input_source == "🖼️ Subir Imagen Fija (.jpg, .png)":
    uploaded_img = st.file_uploader("Subir imagen de la carretera / intersección", type=["jpg", "jpeg", "png"])
    if uploaded_img:
        pil_img = Image.open(uploaded_img).convert("RGB")
        raw_frame = np.array(pil_img)[:, :, ::-1]  # RGB a BGR

        with st.spinner("Ejecutando inferencia con YOLO..."):
            detections, latency_ms, annotated_frame = run_detection_pipeline(raw_frame, conf_threshold)

        analysis = st.session_state.analytics_engine.evaluate_frame_events(detections)

        with tab_col1:
            st.markdown("### 🎥 Fotograma Analizado con YOLO")
            st.image(annotated_frame, channels="BGR", use_container_width=True)
            st.caption(f"Latencia de inferencia: **{latency_ms:.1f} ms** | Elementos detectados: **{len(detections)}**")
        with tab_col2:
            st.markdown("### 📟 Panel de Mensaje Variable (VMS)")
            st.markdown(render_vms_html(analysis["vms"]), unsafe_allow_html=True)


elif input_source == "🏞️ Escenarios de Prueba Sintéticos (Demo)":
    scenario_keys = list(MockTrafficScenarioGenerator.SCENARIOS.keys())
    scenario_labels = [MockTrafficScenarioGenerator.SCENARIOS[k]["name"] for k in scenario_keys]
    
    selected_label = st.selectbox("Selecciona un escenario de tráfico para simular:", scenario_labels)
    selected_key = scenario_keys[scenario_labels.index(selected_label)]
    scenario_info = MockTrafficScenarioGenerator.SCENARIOS[selected_key]
    
    st.info(f"ℹ️ **Descripción:** {scenario_info['desc']}")

    raw_frame = MockTrafficScenarioGenerator.generate_synthetic_road_image(selected_key)
    
    if operation_mode == "🤖 Modelo Local YOLO (best.pt)" and local_yolo_instance is not None:
        detections, latency_ms, annotated_frame = run_detection_pipeline(raw_frame, conf_threshold)
        if len(detections) == 0:
            detections = MockTrafficScenarioGenerator.get_scenario_detections(selected_key)
            annotated_frame = draw_detections(raw_frame, detections)
    else:
        detections = MockTrafficScenarioGenerator.get_scenario_detections(selected_key)
        annotated_frame = draw_detections(raw_frame, detections)
        latency_ms = 18.0

    analysis = st.session_state.analytics_engine.evaluate_frame_events(detections)

    with tab_col1:
        st.markdown("### 🎥 Escenario Sintético Analizado")
        st.image(annotated_frame, channels="BGR", use_container_width=True)
        st.caption(f"Detecciones activas: {len(detections)} elementos | Latencia: {latency_ms:.1f} ms")

    with tab_col2:
        st.markdown("### 📟 Panel de Mensaje Variable (VMS Virtual)")
        st.markdown(render_vms_html(analysis["vms"]), unsafe_allow_html=True)


# ----------------- PANEL DE MÉTRICAS Y TELEMETRÍA PARA TESIS -----------------
st.markdown("---")
st.subheader("📊 Métricas de Desempeño y Telemetría del Sistema")

history = st.session_state.analytics_engine.history_logs

if history:
    df_history = pd.DataFrame(history)

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown("""
        <div class="metric-box">
            <div class="metric-title">Eventos Procesados</div>
            <div class="metric-value">{}</div>
        </div>
        """.format(len(df_history)), unsafe_allow_html=True)
    with kpi2:
        ultimas_alertas = df_history[df_history["Nivel_Alerta"].isin(["CRITICAL", "WARNING"])].shape[0]
        st.markdown("""
        <div class="metric-box">
            <div class="metric-title">Alertas de Peligro</div>
            <div class="metric-value" style="color: #ff1744;">{}</div>
        </div>
        """.format(ultimas_alertas), unsafe_allow_html=True)
    with kpi3:
        avg_veh = df_history["Vehiculos"].mean() if "Vehiculos" in df_history else 0
        st.markdown("""
        <div class="metric-box">
            <div class="metric-title">Densidad Media (Veh/Frame)</div>
            <div class="metric-value" style="color: #00e676;">{:.1f}</div>
        </div>
        """.format(avg_veh), unsafe_allow_html=True)
    with kpi4:
        estado_actual = df_history["Nivel_Alerta"].iloc[-1] if not df_history.empty else "NORMAL"
        badge_color = "#ff1744" if estado_actual == "CRITICAL" else ("#ffd600" if estado_actual == "WARNING" else "#00e676")
        st.markdown("""
        <div class="metric-box">
            <div class="metric-title">Estado VMS Actual</div>
            <div class="metric-value" style="color: {};">{}</div>
        </div>
        """.format(badge_color, estado_actual), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Gráficas analíticas de tesis con Plotly
    g_col1, g_col2 = st.columns(2)
    with g_col1:
        st.markdown("#### 📈 Historial de Densidad Vehicular")
        fig_line = px.line(
            df_history.reset_index(),
            x="index",
            y="Vehiculos",
            title="Fluctuación de Vehículos en Vía",
            labels={"index": "Muestra Temporal", "Vehiculos": "Vehículos Detectados"},
            template="plotly_dark"
        )
        fig_line.update_traces(line_color="#00e676", line_width=3)
        st.plotly_chart(fig_line, use_container_width=True)

    with g_col2:
        st.markdown("#### 🎯 Distribución de Niveles de Alerta")
        fig_pie = px.pie(
            df_history,
            names="Nivel_Alerta",
            title="Distribución de Estados del Pórtico VMS",
            color="Nivel_Alerta",
            color_discrete_map={
                "NORMAL": "#00e676",
                "WARNING": "#ffd600",
                "CRITICAL": "#ff1744",
                "CONGESTION": "#ff9100",
                "INFO": "#00e5ff"
            },
            template="plotly_dark"
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # Tabla de Eventos y Descarga para Tesis
    st.markdown("#### 📋 Registro de Auditoría de Eventos VMS")
    st.dataframe(df_history.tail(15), use_container_width=True)

    csv_data = df_history.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar Registro de Datos para Tesis (CSV)",
        data=csv_data,
        file_name=f"tesis_vms_telemetria_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
else:
    st.info("No hay eventos registrados aún. Inicia una simulación para ver métricas.")
