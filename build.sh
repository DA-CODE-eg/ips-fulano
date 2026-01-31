#!/usr/bin/env bash
# Script de build para Render.com
# Este script se ejecuta automáticamente durante el deploy

set -o errexit  # Salir si hay algún error

echo "🚀 Iniciando build..."

# Actualizar pip
echo "📦 Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements.txt

# Inicializar la base de datos
echo "🗄️  Inicializando base de datos..."
python init_db.py

echo "✅ Build completado exitosamente"