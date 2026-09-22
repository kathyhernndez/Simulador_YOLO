# 🚦 Simulador de Sistema Inteligente de Señalización Vial (SMV) y Pórtico VMS

**Título del proyecto:** Simulador y módulo de visión artificial para análisis de flujo.

**Contexto de aplicación:** "Desarrollado como soporte tecnológico y prototipo experimental para el Trabajo Especial de Grado de Ingeniería Civil, presentado por ING. Civil (E) Francisco Lindado."

**Créditos:** Desarrolladora del software: ING. Informática (E) Katherine Hernández.

> Sistema de Señalización Inteligente en Intersecciones y Vías Rápidas con Detección de Objetos, Paneles de Mensajería Variable (VMS).

---

## 📄 Licencia

Este proyecto está distribuido bajo la **Licencia MIT**. Consulta el archivo [LICENSE](LICENSE) para más detalles.

Copyright (c) 2026 Katherine Hernández

---

## 🌟 Descripción General

Esta plataforma interactiva desarrollada en **Streamlit** y empaquetada en **Docker** permite simular y evaluar en tiempo real la respuesta de un **Sistema Inteligente de Mensajes Variables (VMS / Panel LED)**, basándose en la inferencia de visión artificial proporcionada por modelos **YOLO locales**.

### 🎯 Características Principales
1. **Sistema Multi-Panel (PMV):** Simulación simultánea de 3 Paneles de Mensajería Variable ubicados en puntos estratégicos (Sector Mercado Viejo) que responden a un Motor Analítico de 5 Prioridades:
   - **Prioridad 1 (Peligro Crítico/Emergencia):** 🚨 Contraflujos, ambulancias o bloqueos totales. Activa desvíos obligatorios, velocidad de 10 km/h y destellos rojos (Ej: `VÍA CONGESTIONADA / DESVIO OBLIGATORIO`).
   - **Prioridad 2 (Advertencia Peatonal):** 🚶 Alta densidad de peatones. Reduce la velocidad a 10 km/h con advertencias amarillas (Ej: `PRIORIDAD PEATON`).
   - **Prioridad 3 (Obstrucciones):** 🚧 Vehículos detenidos o carga/descarga. Advierte paso intermitente (Ej: `CANAL REDUCIDO / PASO INTERMITENTE`).
   - **Prioridad 4 (Congestión):** ⚠️ Tráfico denso. Recomienda desvíos con alertas amarillas (Ej: `CONGESTIÓN EN CALLE GARCES / PREVENTIVO FEDERACIÓN`).
   - **Prioridad 5 (Flujo Libre):** ✅ Vías despejadas. Permite paso continuo a 20 km/h en verde fijo (Ej: `CRUCE DESPEJADO / PASO CONTINUO`).
2. **Detección de Múltiples Clases:** Identifica automóviles, vehículos en contraflujo, motocicletas, ciclistas y peatones interactuando con la vía.
3. **Métricas Académicas para Tesis:** Tacómetros de latencia (ms), distribución de alertas, gráficos interactivos con Plotly y descarga del registro de auditoría en formato **CSV**.
4. **Modo Resiliencia / Demo Offline:** Incluye escenarios sintéticos calibrados para presentaciones y defensas sin dependencia de conexión externa.

---

## 🚀 Despliegue Rápido con Docker

### Requisitos Previos
- Tener instalado [Docker Desktop](https://www.docker.com/products/docker-desktop/).

### 1. Clonar o abrir el repositorio
Navega a la carpeta del proyecto:
```bash
cd c:/Users/TheGhost/Desktop/TESIS_TRAFICO
```

### 2. Construir y Levantar el Contenedor
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
SMV/
├── Dockerfile                  # Imagen Docker optimizada (Python 3.11-slim + OpenCV)
├── docker-compose.yml          # Configuración de orquestación y puertos (8501:8501)
├── requirements.txt            # Dependencias del proyecto
├── app.py                      # Aplicación principal Streamlit
├── smoke_test.py               # Pruebas de integración
|__ best.pt                     # Pesos entrenados YOLOv11
└── src/
    ├── traffic_logic.py        # Motor de reglas viales y alertas VMS
    ├── mock_detector.py        # Generador de escenarios sintéticos para demo
    └── ui_components.py        # Componentes CSS/HTML para pórtico LED virtual
```
