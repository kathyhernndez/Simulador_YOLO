# 🚦 Simulador de Sistema Inteligente de Señalización Vial (SMV) y Pórtico VMS

> **Proyecto Factible / Tesis de Grado en Ingeniería:**
> Sistema de Señalización Inteligente en Intersecciones y Vías Rápidas con Detección de Objetos en Roboflow, Paneles de Mensajería Variable (VMS) y Semáforos Adaptativos.

---

## 🌟 Descripción General

Esta plataforma interactiva desarrollada en **Streamlit** y empaquetada en **Docker** permite simular y evaluar en tiempo real la respuesta de un **Sistema de Mensajes Variables (VMS / Panel LED)** y de **Semáforos Inteligentes**, basándose en la inferencia de visión artificial proporcionada por **Roboflow Workflows**.

### 🎯 Características Principales
1. **Pórtico VMS Virtual:** Pantalla LED de alta visibilidad que muestra advertencias automáticas según el evento detectado:
   - 🚨 `¡PELIGRO! VEHÍCULO EN CONTRAFLUJO - NO ADELANTAR` (Rojo Neón intermitente).
   - 🚧 `¡ALERTA! MAQUINARIA TRABAJANDO - REDUZCA VELOCIDAD A 30 KM/H` (Naranja / Ámbar).
   - 🏜️ `¡PELIGRO! ALTA ACUMULACIÓN DE ARENA - USE CARRIL IZQUIERDO` (Amarillo Arena).
   - 🚦 `CONGESTIÓN VEHICULAR - VELOCIDAD MÁX 40 KM/H` (Control de tiempos de semáforo).
   - 🛣️ `TRÁFICO FLUIDO - RESPETE EL LÍMITE DE VELOCIDAD` (Verde).
2. **Semáforo Inteligente Adaptativo:** Ajusta el tiempo de la fase verde según la densidad de vehículos en cola.
3. **Integración con Roboflow:** Conectado mediante el SDK oficial y endpoint REST con reintentos y tolerancia a fallos.
4. **Métricas Académicas para Tesis:** Tacómetros de latencia (ms), distribución de alertas, gráficos interactivos con Plotly y descarga del registro de auditoría en formato **CSV**.
5. **Modo Resiliencia / Demo Offline:** Incluye escenarios sintéticos calibrados para presentaciones y defensas sin dependencia de conexión externa.

---

## 🚀 Despliegue Rápido con Docker

### Requisitos Previos
- Tener instalado [Docker Desktop](https://www.docker.com/products/docker-desktop/).

### 1. Clonar o abrir el repositorio
Navega a la carpeta del proyecto:
```bash
cd c:/Users/TheGhost/Desktop/TESIS_TRAFICO
```

### 2. Configurar la clave de Roboflow (Opcional en .env)
Copia el archivo de ejemplo o edita `.env`:
```bash
cp .env.example .env
```
Agrega tu clave `ROBOFLOW_API_KEY` (también puedes ingresarla directamente desde la interfaz web).

### 3. Construir y Levantar el Contenedor
Ejecuta el siguiente comando:
```bash
docker compose up --build -d
```

### 4. Acceder a la Aplicación
Abre tu navegador en:
👉 **[http://localhost:8501](http://localhost:8501)**

---

## 🛠️ Comandos de Mantenimiento de Docker

- **Ver logs en tiempo real:**
  ```bash
  docker compose logs -f
  ```
- **Detener el contenedor:**
  ```bash
  docker compose down
  ```
- **Reiniciar el contenedor:**
  ```bash
  docker compose restart
  ```

---

## 📂 Estructura del Código

```
TESIS_TRAFICO/
├── Dockerfile                  # Imagen Docker optimizada (Python 3.11-slim + OpenCV)
├── docker-compose.yml          # Configuración de orquestación y puertos (8501:8501)
├── requirements.txt            # Dependencias del proyecto
├── .env.example                # Plantilla de variables de entorno
├── app.py                      # Aplicación principal Streamlit
├── smoke_test.py               # Pruebas de integración
└── src/
    ├── roboflow_client.py      # Cliente de Roboflow Workflow con SDK & REST
    ├── traffic_logic.py        # Motor de reglas viales, alertas VMS y semáforos
    ├── mock_detector.py        # Generador de escenarios sintéticos para demo
    └── ui_components.py        # Componentes CSS/HTML para pórtico LED y semáforos
```
