# =====================================================================
# Proyecto: Simulador de Flujo e Inferencia Visual
# Asesoría Técnica: Tesis de Grado en Ingeniería Civil
# Autor y Desarrollo de Software: Katherine Hernández
# Año: 2026
# Licencia: MIT
# =====================================================================

# Script de inicio rápido para Docker en Windows PowerShell
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "🚦 Levantando Simulador de Tráfico y VMS con Docker..." -ForegroundColor Yellow
Write-Host "====================================================" -ForegroundColor Cyan

docker compose up --build -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Contenedor iniciado exitosamente!" -ForegroundColor Green
    Write-Host "👉 Abre tu navegador en: http://localhost:8501" -ForegroundColor Cyan
} else {
    Write-Host "`n❌ Ocurrió un error al levantar Docker. Asegúrate de tener Docker Desktop abierto." -ForegroundColor Red
}
