# Plan de Implementación: Simulador Inteligente de Señalización de Tráfico y Paneles VMS con Docker y Roboflow

Este proyecto desarrolla una plataforma completa e interactiva en **Streamlit** empaquetada en un contenedor **Docker**, diseñada para un **Proyecto Factible de Tesis de Grado**. La plataforma separa la arquitectura de visión artificial e inferencia (mediante la API de Roboflow con el Workflow entrenado) de la interfaz de usuario, simulación en tiempo real y panel de mensajería variable (VMS / Pórtico LED inteligente).

## Componentes y Arquitectura

```
  +-------------------------------------------------------------+
  |              Streamlit Interactive Web UI (Docker)          |
  |                                                             |
  |  +---------------------+   +-----------------------------+  |
  |  |  Entrada Multimedia |   | Panel LED VMS Virtual       |  |
  |  |  (Video/Imagen/Demo)|   | (Matriz de mensajes dinámicos) |
  |  +----------+----------+   +--------------^--------------+  |
  |             |                             |                 |
  |             v                             |                 |
  |  +---------------------+   +--------------+--------------+  |
  |  | Motor de Inferencia |-->| Reglas de Alerta & Lógica   |  |
  |  | (Roboflow Client)   |   | Intersección / Semáforos    |  |
  |  +---------------------+   +-----------------------------+  |
  |             |                             |                 |
  |             v                             v                 |
  |       +-----------------------------------------+           |
  |       |   Métricas de Tesis (Latencia, Conteo,  |           |
  |       |     Gráficas Plotly, Exportar CSV)      |           |
  |       +-----------------------------------------+           |
  +-------------------------------------------------------------+
```

---

## User Review Required

> [!IMPORTANT]
> - **Clave API de Roboflow**: La aplicación permitirá ingresar la `ROBOFLOW_API_KEY` tanto por archivo `.env` como interactivamente desde la barra lateral de Streamlit.
> - **Modo Híbrido / Resiliencia**: Además del cliente oficial de Roboflow Workflow (`inference-sdk` y REST), se incluirá un motor de simulación de prueba con escenarios sintéticos para poder presentar la tesis incluso si no se cuenta con conexión a internet o cuota de API en el momento de la defensa.
> - **Contenedor Docker**: Se configurará `Dockerfile` y `docker-compose.yml` exponiendo el puerto `8501` con montaje de volúmenes para desarrollo en vivo.

---

## Proposed Changes

### 1. Configuración de Entorno y Docker

#### [NEW] [Dockerfile](file:///c:/Users/TheGhost/Desktop/TESIS_TRAFICO/Dockerfile)
- Imagen base `python:3.11-slim`.
- Instalación de dependencias de sistema mínimas para OpenCV y procesamiento de imágenes (`libgl1`, `libglib2.0-0`).
- Configuración del puerto `8501` y comando `streamlit run app.py --server.port=8501 --server.address=0.0.0.0`.

#### [NEW] [docker-compose.yml](file:///c:/Users/TheGhost/Desktop/TESIS_TRAFICO/docker-compose.yml)
- Definición del servicio `tesis-trafico-app`.
- Mapeo de puertos `8501:8501`.
- Carga de variables de entorno desde `.env`.
- Mapeo de volumen para persistencia y cambios en caliente.

#### [NEW] [requirements.txt](file:///c:/Users/TheGhost/Desktop/TESIS_TRAFICO/requirements.txt)
- `streamlit>=1.35.0`
- `inference-sdk>=0.9.0`
- `requests>=2.31.0`
- `opencv-python-headless>=4.9.0`
- `pillow>=10.2.0`
- `numpy>=1.26.0`
- `pandas>=2.2.0`
- `plotly>=5.20.0`
- `python-dotenv>=1.0.0`

#### [NEW] [.env.example](file:///c:/Users/TheGhost/Desktop/TESIS_TRAFICO/.env.example)
- Plantilla con `ROBOFLOW_API_KEY`, `ROBOFLOW_WORKSPACE=katherines-workspace-q66ls`, `ROBOFLOW_WORKFLOW_ID=tesis-trafico-vtesis-trafico-2-rfdetr-small-t1-logic`.

#### [NEW] [.dockerignore](file:///c:/Users/TheGhost/Desktop/TESIS_TRAFICO/.dockerignore)

---

### 2. Motor de Inferencia y Cliente Roboflow

#### [NEW] [src/roboflow_client.py](file:///c:/Users/TheGhost/Desktop/TESIS_TRAFICO/src/roboflow_client.py)
- Implementación de cliente robusto con `InferenceHTTPClient` y REST API como fallback.
- Soporte para el workflow `tesis-trafico-vtesis-trafico-2-rfdetr-small-t1-logic`.
- Manejo de reintentos con backoff exponencial y timeouts.
- Decodificación y normalización de detecciones (bounding boxes, clases, confianzas) para fácil renderizado.

#### [NEW] [src/traffic_logic.py](file:///c:/Users/TheGhost/Desktop/TESIS_TRAFICO/src/traffic_logic.py)
- Lógica de negocio de la tesis:
  - Detección de maquinaria $\rightarrow$ Alerta ámbar de reducción de velocidad.
  - Detección de contraflujo $\rightarrow$ Alerta roja de peligro / sentido contrario.
  - Detección de arena / obstáculos $\rightarrow$ Alerta roja / ámbar de acumulación de arena en calzada.
  - Conteo de vehículos $\rightarrow$ Determinación de nivel de congestión (Fluido, Moderado, Crítico) y cálculo de tiempos óptimos para semáforos.

---

### 3. Interfaz Gráfica de Usuario (Streamlit)

#### [NEW] [app.py](file:///c:/Users/TheGhost/Desktop/TESIS_TRAFICO/app.py)
- Interfaz moderna y profesional con estética oscura/vibrante para tesis.
- Barra lateral:
  - Entrada de API Key y selección de modo (Roboflow Workflow API / Simulación de Escenarios).
  - Ajuste de umbral de confianza (Confidence Threshold) e IoU.
  - Opciones de origen: Subir Video, Subir Imagen, Escenario de Prueba Precargado.
- Panel Central:
  - Visualizador de Video/Cámara con cajas delimitadoras anotadas y etiquetas con colores por categoría.
  - **Componente VMS Virtual**: Simulación de pantalla LED de matriz física con animación de glow (verde, ámbar, rojo parpadeante), tipografía monoespaciada LED y alertas audibles/visuales.
  - **Semáforo Inteligente Virtual**: Representación visual de semáforo con fases dinámicas calculadas por flujo vehicular.
- Sección de Métricas Académicas:
  - Tacómetro de latencia de inferencia (ms) y FPS.
  - Gráfico de distribución de detecciones (Vehículos, Arena, Maquinaria, etc.).
  - Historial de eventos y alertas registradas con botón para **Descargar Reporte de Tesis en CSV**.

#### [NEW] [src/ui_components.py](file:///c:/Users/TheGhost/Desktop/TESIS_TRAFICO/src/ui_components.py)
- Componentes CSS personalizados para el panel LED VMS, tarjetas de métricas y semáforos.

---

### 4. Pruebas y Documentación

#### [NEW] [smoke_test.py](file:///c:/Users/TheGhost/Desktop/TESIS_TRAFICO/smoke_test.py)
- Script de verificación para probar el cliente Roboflow con una imagen de muestra sintética y validar la respuesta.

#### [NEW] [README.md](file:///c:/Users/TheGhost/Desktop/TESIS_TRAFICO/README.md)
- Instrucciones claras para iniciar con Docker (`docker compose up --build`).
- Explicación de la arquitectura para la memoria de grado/tesis.

---

## Verification Plan

### Automated Tests
- Ejecutar `smoke_test.py` para validar la lógica del cliente y la normalización de salidas.
- Validar la sintaxis de `app.py`, `src/roboflow_client.py` y `src/traffic_logic.py`.

### Docker Verification
- Construir la imagen Docker con `docker compose build`.
- Levantar el contenedor con `docker compose up -d`.
- Verificar que el contenedor esté corriendo y responda en `http://localhost:8501`.
