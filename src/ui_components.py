"""
Componentes Visuales y Estilos CSS Personalizados para el Simulador VMS y Semáforo Inteligente
Diseñado con estética profesional para Tesis de Grado.
"""

def get_custom_css() -> str:
    return """
    <style>
        /* Importar fuentes modernas */
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Inter:wght@400;600;800&display=swap');

        /* Contenedor del Panel VMS Físico (Pórtico) */
        .vms-gantry-container {
            background: linear-gradient(180deg, #1e2229 0%, #111419 100%);
            border: 4px solid #3b4252;
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.7), inset 0 0 15px rgba(0,0,0,0.9);
            margin-bottom: 20px;
            position: relative;
        }

        /* Franja de seguridad superior/inferior del pórtico */
        .vms-hazard-stripe {
            height: 8px;
            background: repeating-linear-gradient(
                -45deg,
                #ffd600,
                #ffd600 15px,
                #111 15px,
                #111 30px
            );
            border-radius: 4px;
            margin-bottom: 12px;
        }
        .vms-hazard-stripe-bottom {
            height: 8px;
            background: repeating-linear-gradient(
                -45deg,
                #ffd600,
                #ffd600 15px,
                #111 15px,
                #111 30px
            );
            border-radius: 4px;
            margin-top: 12px;
        }

        /* Pantalla LED de Matriz Negra */
        .vms-display {
            background-color: #050608;
            background-image: radial-gradient(#151922 15%, transparent 16%);
            background-size: 6px 6px;
            border: 2px solid #2e3440;
            border-radius: 8px;
            padding: 24px 18px;
            text-align: center;
            min-height: 180px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            box-shadow: inset 0 0 25px rgba(0,0,0,0.95);
        }

        .vms-title {
            font-family: 'Share Tech Mono', monospace, 'Courier New';
            font-size: 1.55rem;
            font-weight: 800;
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-bottom: 10px;
            line-height: 1.2;
        }

        .vms-body {
            font-family: 'Share Tech Mono', monospace, 'Courier New';
            font-size: 1.15rem;
            font-weight: 600;
            letter-spacing: 1.5px;
            white-space: pre-line;
            line-height: 1.4;
        }

        .vms-badge {
            display: inline-block;
            margin-top: 12px;
            padding: 4px 12px;
            border-radius: 20px;
            font-family: 'Inter', sans-serif;
            font-size: 0.85rem;
            font-weight: 700;
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }


        /* Tarjeta de Métricas */
        .metric-box {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 14px;
            text-align: center;
        }
        .metric-title {
            color: #8f9ba8;
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 4px;
        }
        .metric-value {
            font-size: 1.6rem;
            font-weight: 700;
            color: #ffffff;
            font-family: 'Share Tech Mono', monospace;
        }

        /* Animación de parpadeo para alertas críticas */
        @keyframes pulse-vms {
            0% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.85; transform: scale(0.995); }
            100% { opacity: 1; transform: scale(1); }
        }
        .pulse-animation {
            animation: pulse-vms 1.2s infinite;
        }
        /* Ajuste para evitar desbordamiento de medios en Streamlit al hacer zoom */
        [data-testid="stImage"] img,
        [data-testid="stVideo"] video {
            max-width: 100% !important;
            max-height: 65vh !important;
            height: auto !important;
            object-fit: contain !important;
        }
        
        [data-testid="stImage"] {
            overflow: hidden;
            width: 100% !important;
            display: flex;
            justify-content: center;
        }
    </style>
    """


def render_vms_html(vms_data: dict) -> str:
    """Genera el HTML con estilo LED para el panel de mensajes variables."""
    title = vms_data.get("title", "SISTEMA ACTIVO")
    message = vms_data.get("message", "TRÁFICO NORMAL")
    color = vms_data.get("color", "#00e676")
    icon = vms_data.get("icon", "🛣️")
    is_flashing = vms_data.get("is_flashing", False)
    speed_limit = vms_data.get("speed_limit", "80 KM/H")

    pulse_class = "pulse-animation" if is_flashing else ""

    glow_style = f"color: {color}; text-shadow: 0 0 10px {color}, 0 0 20px {color};"

    html = f"""
    <div class="vms-gantry-container {pulse_class}">
        <div class="vms-hazard-stripe"></div>
        <div class="vms-display">
            <div class="vms-title" style="{glow_style}">
                {icon} {title}
            </div>
            <div class="vms-body" style="{glow_style}">
                {message}
            </div>
            <div class="vms-badge" style="color: {color}; border-color: {color};">
                ⚡ VELOCIDAD MÁXIMA RECOMENDADA: <b>{speed_limit}</b>
            </div>
        </div>
        <div class="vms-hazard-stripe-bottom"></div>
    </div>
    """
    return html



