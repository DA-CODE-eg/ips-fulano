#!/usr/bin/env bash
# Script de build para Render.com
# Este script se ejecuta automáticamente durante el deploy

set -o errexit  # Salir si hay algún error

echo "🚀 Iniciando build..."

# Actualizar pip
echo "📦 Actualizando pip..."
python -m pip install --upgrade pip

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements.txt

echo "✅ Build completado exitosamente"
# NOTA: NO ejecutamos init_db.py porque ya se ejecuta en app/__init__.py