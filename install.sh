#!/bin/bash

# ===============================================
# INSTALADOR SIPS CLIENT
# ===============================================

set -e

echo "================================================"
echo "  🔌 INSTALANDO SIPS CLIENT"
echo "================================================"
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no está instalado"
    exit 1
fi

echo "✅ Python encontrado: $(python3 --version)"
echo ""

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements.txt --break-system-packages

echo ""
echo "================================================"
echo "  ✅ INSTALACIÓN COMPLETADA"
echo "================================================"
echo ""
echo "Próximos pasos:"
echo ""
echo "1. Copia el archivo de configuración:"
echo "   cp .env.example .env"
echo ""
echo "2. Edita .env con tus credenciales:"
echo "   nano .env"
echo ""
echo "3. Prueba el cliente:"
echo "   python3 sips_client.py --help"
echo ""
echo "4. Consulta un CUPS:"
echo "   python3 sips_client.py ES0031406091590001JF0F"
echo ""
