#!/usr/bin/env bash
# Script de build para Render.com

set -o errexit

echo "🚀 Iniciando build..."

# Actualizar pip
echo "📦 Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias de Python
echo "📦 Instalando dependencias de Python..."
pip install -r requirements.txt

echo "✅ Build completado exitosamente"