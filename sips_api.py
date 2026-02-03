#!/usr/bin/env python3
"""
SIPS API - Wrapper REST para el SIPS Client
============================================
API REST simple que expone el SIPS Client para ser consumido por n8n

Endpoints:
    GET  /sips/<cups>                - Obtener histórico SIPS
    POST /sips                       - Obtener histórico SIPS (body JSON)
    GET  /health                     - Health check

Autor: Aenergetic
Fecha: 2026-02-03
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from sips_client import SIPSClient
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Habilitar CORS para llamadas desde n8n

# Cliente global (reutilizable)
sips_client = None


def get_client():
    """Obtiene o crea el cliente SIPS"""
    global sips_client
    if sips_client is None:
        sips_client = SIPSClient()
        sips_client.connect_db()
    return sips_client


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'SIPS API',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })


@app.route('/sips/<cups>', methods=['GET'])
def get_sips_by_cups(cups):
    """
    Obtener histórico SIPS por CUPS (método GET)
    
    Query params:
        - invoice_id: ID de factura (opcional)
        - months: Número de meses (default: 12)
        - optimize_p6: true/false (default: false)
        - save: true/false - guardar en CouchDB (default: true)
    
    Ejemplo:
        GET /sips/ES0031406091590001JF0F?months=12&invoice_id=12345
    """
    try:
        # Parsear parámetros
        invoice_id = request.args.get('invoice_id', type=int)
        months = request.args.get('months', default=12, type=int)
        optimize_p6 = request.args.get('optimize_p6', default='false').lower() == 'true'
        save_to_couch = request.args.get('save', default='true').lower() == 'true'
        
        # Validar CUPS
        if not cups or len(cups) < 10:
            return jsonify({
                'error': 'CUPS inválido',
                'cups': cups
            }), 400
        
        # Obtener cliente
        client = get_client()
        
        # Consultar datos
        sips_data = client.get_sips_history(
            cups=cups,
            invoice_id=invoice_id,
            months=months,
            optimize_p6=optimize_p6,
            save_to_couch=save_to_couch
        )
        
        if sips_data:
            return jsonify({
                'success': True,
                'data': sips_data,
                'saved_to_couchdb': save_to_couch
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'No se encontraron datos para el CUPS',
                'cups': cups
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/sips', methods=['POST'])
def get_sips_post():
    """
    Obtener histórico SIPS (método POST)
    
    Body JSON:
        {
            "cups": "ES0031406091590001JF0F",
            "invoice_id": 12345,         // opcional
            "months": 12,                // opcional, default: 12
            "optimize_p6": false,        // opcional, default: false
            "save": true                 // opcional, default: true
        }
    
    Ejemplo desde n8n:
        POST /sips
        Body: {{ $json }}
    """
    try:
        # Parsear body JSON
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Body JSON vacío'
            }), 400
        
        cups = data.get('cups')
        invoice_id = data.get('invoice_id')
        months = data.get('months', 12)
        optimize_p6 = data.get('optimize_p6', False)
        save_to_couch = data.get('save', True)
        
        # Validar CUPS
        if not cups or len(cups) < 10:
            return jsonify({
                'error': 'CUPS inválido o no proporcionado',
                'cups': cups
            }), 400
        
        # Obtener cliente
        client = get_client()
        
        # Consultar datos
        sips_data = client.get_sips_history(
            cups=cups,
            invoice_id=invoice_id,
            months=months,
            optimize_p6=optimize_p6,
            save_to_couch=save_to_couch
        )
        
        if sips_data:
            return jsonify({
                'success': True,
                'data': sips_data,
                'saved_to_couchdb': save_to_couch
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'No se encontraron datos para el CUPS',
                'cups': cups
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/sips/batch', methods=['POST'])
def get_sips_batch():
    """
    Procesar múltiples CUPS en batch
    
    Body JSON:
        {
            "cups_list": [
                {"cups": "ES...", "invoice_id": 123},
                {"cups": "ES...", "invoice_id": 124}
            ],
            "months": 12,
            "save": true
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'cups_list' not in data:
            return jsonify({
                'error': 'Falta cups_list en el body'
            }), 400
        
        cups_list = data['cups_list']
        months = data.get('months', 12)
        save_to_couch = data.get('save', True)
        
        client = get_client()
        results = []
        
        for item in cups_list:
            cups = item.get('cups')
            invoice_id = item.get('invoice_id')
            
            if not cups:
                results.append({
                    'cups': None,
                    'success': False,
                    'error': 'CUPS vacío'
                })
                continue
            
            sips_data = client.get_sips_history(
                cups=cups,
                invoice_id=invoice_id,
                months=months,
                save_to_couch=save_to_couch
            )
            
            results.append({
                'cups': cups,
                'invoice_id': invoice_id,
                'success': sips_data is not None,
                'records_found': sips_data.get('records_found', 0) if sips_data else 0
            })
        
        return jsonify({
            'success': True,
            'processed': len(results),
            'results': results
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handler para rutas no encontradas"""
    return jsonify({
        'error': 'Endpoint no encontrado',
        'available_endpoints': [
            'GET  /health',
            'GET  /sips/<cups>',
            'POST /sips',
            'POST /sips/batch'
        ]
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handler para errores internos"""
    return jsonify({
        'error': 'Error interno del servidor',
        'message': str(error)
    }), 500


if __name__ == '__main__':
    # Configuración desde variables de entorno
    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', 5000))
    debug = os.getenv('API_DEBUG', 'false').lower() == 'true'
    
    print("\n" + "="*60)
    print("🚀 SIPS API - Iniciando servidor")
    print("="*60)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print("\nEndpoints disponibles:")
    print("  GET  /health")
    print("  GET  /sips/<cups>")
    print("  POST /sips")
    print("  POST /sips/batch")
    print("="*60 + "\n")
    
    app.run(host=host, port=port, debug=debug)
