#!/usr/bin/env bash
# Script de build para Render.com

set -o errexit

echo "🚀 Iniciando build..."

# Actualizar pip
echo "📦 Actualizando pip..."
pip install --upgrade pip

# Intentar instalar dependencias del sistema (Render puede no tener apt-get)
echo "📦 Instalando dependencias del sistema para WeasyPrint..."
apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-dejavu \
    fonts-liberation \
    || echo "⚠️  Continuando sin algunas dependencias del sistema"

# Instalar dependencias de Python
echo "📦 Instalando dependencias de Python..."
pip install -r requirements.txt

echo "✅ Build completado exitosamente"