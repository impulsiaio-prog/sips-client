#!/usr/bin/env python3
"""
SIPS History Client - Extrae histórico SIPS desde IGNIS y lo guarda en CouchDB
===============================================================================
Este cliente se conecta directamente a la base de datos de IGNIS para
obtener datos SIPS sin depender de la API rota.

Autor: Aenergetic
Fecha: 2026-02-03
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import mysql.connector
from mysql.connector import Error
import argparse

# Intentar cargar variables de entorno desde .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv no instalado, usar variables de sistema


class SIPSClient:
    """Cliente para extraer histórico SIPS desde IGNIS"""
    
    def __init__(
        self,
        db_host: str = None,
        db_user: str = None,
        db_password: str = None,
        db_name: str = None,
        couchdb_url: str = None,
        couchdb_user: str = None,
        couchdb_password: str = None,
    ):
        """
        Inicializa el cliente SIPS
        
        Args:
            db_host: Host de la base de datos MySQL de IGNIS
            db_user: Usuario de MySQL
            db_password: Password de MySQL
            db_name: Nombre de la base de datos
            couchdb_url: URL de CouchDB
            couchdb_user: Usuario de CouchDB
            couchdb_password: Password de CouchDB
        """
        # Usar variables de entorno como fallback
        self.db_host = db_host or os.getenv('IGNIS_DB_HOST', 'localhost')
        self.db_user = db_user or os.getenv('IGNIS_DB_USER', 'root')
        self.db_password = db_password or os.getenv('IGNIS_DB_PASSWORD', '')
        self.db_name = db_name or os.getenv('IGNIS_DB_NAME', 'ignis')
        
        self.couchdb_url = couchdb_url or os.getenv('COUCHDB_URL', 'https://couchdb.aenergetic.app')
        self.couchdb_user = couchdb_user or os.getenv('COUCHDB_USER', 'admin')
        self.couchdb_password = couchdb_password or os.getenv('COUCHDB_PASSWORD', '')
        self.couchdb_db = os.getenv('COUCHDB_DATABASE', 'sips_history')
        
        self.connection = None
    
    def connect_db(self) -> bool:
        """Conecta a la base de datos MySQL de IGNIS"""
        try:
            self.connection = mysql.connector.connect(
                host=self.db_host,
                user=self.db_user,
                password=self.db_password,
                database=self.db_name
            )
            
            if self.connection.is_connected():
                db_info = self.connection.get_server_info()
                print(f"✅ Conectado a MySQL Server versión {db_info}")
                return True
                
        except Error as e:
            print(f"❌ Error al conectar a MySQL: {e}")
            return False
    
    def disconnect_db(self):
        """Cierra la conexión a MySQL"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("🔌 Conexión a MySQL cerrada")
    
    def get_sips_data_by_cups(
        self,
        cups: str,
        months: int = 12,
        optimize_p6: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Extrae datos SIPS para un CUPS específico
        
        Args:
            cups: CUPS a consultar
            months: Número de meses hacia atrás
            optimize_p6: Si optimizar periodo 6
            
        Returns:
            Dict con datos SIPS o None si hay error
        """
        if not self.connection or not self.connection.is_connected():
            print("❌ No hay conexión a la base de datos")
            return None
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # Calcular fecha límite
            date_limit = datetime.now() - timedelta(days=months * 30)
            
            # Query para obtener datos de consumo histórico
            query = """
                SELECT 
                    cups,
                    fecha_lectura,
                    periodo,
                    consumo_kwh,
                    potencia_contratada,
                    potencia_maxima,
                    precio_energia,
                    precio_potencia
                FROM consumos_historicos
                WHERE cups = %s
                AND fecha_lectura >= %s
                ORDER BY fecha_lectura DESC
            """
            
            cursor.execute(query, (cups, date_limit))
            rows = cursor.fetchall()
            
            if not rows:
                print(f"⚠️ No se encontraron datos para CUPS: {cups}")
                return None
            
            # Procesar datos
            demand_data = []
            current_powers = {}
            periods = set()
            
            for row in rows:
                periodo = row['periodo']
                periods.add(periodo)
                
                # Agregar a demand_data
                demand_data.append({
                    'fecha': row['fecha_lectura'].isoformat() if row['fecha_lectura'] else None,
                    'periodo': periodo,
                    'consumo_kwh': float(row['consumo_kwh']) if row['consumo_kwh'] else 0,
                    'potencia_maxima': float(row['potencia_maxima']) if row['potencia_maxima'] else 0,
                })
                
                # Actualizar potencias actuales (último valor por periodo)
                if periodo not in current_powers:
                    current_powers[periodo] = float(row['potencia_contratada']) if row['potencia_contratada'] else 0
            
            cursor.close()
            
            result = {
                'cups': cups,
                'current_powers': current_powers,
                'demand_data': demand_data,
                'periods': sorted(list(periods)),
                'optimize_p6': optimize_p6,
                'months': months,
                'records_found': len(demand_data),
                'query_date': datetime.now().isoformat()
            }
            
            print(f"✅ Datos SIPS extraídos para {cups}:")
            print(f"   - Registros: {len(demand_data)}")
            print(f"   - Periodos: {', '.join(sorted(periods))}")
            print(f"   - Potencias actuales: {current_powers}")
            
            return result
            
        except Error as e:
            print(f"❌ Error en query: {e}")
            return None
    
    def save_to_couchdb(
        self,
        sips_data: Dict[str, Any],
        invoice_id: Optional[int] = None,
        source: str = "python_client"
    ) -> bool:
        """
        Guarda los datos SIPS en CouchDB
        
        Args:
            sips_data: Datos SIPS a guardar
            invoice_id: ID de factura relacionada (opcional)
            source: Origen de la consulta
            
        Returns:
            True si se guardó correctamente
        """
        if not sips_data:
            print("❌ No hay datos SIPS para guardar")
            return False
        
        # Construir documento para CouchDB
        doc_id = f"sips_{sips_data['cups']}_{int(datetime.now().timestamp() * 1000)}"
        
        document = {
            '_id': doc_id,
            'type': 'sips_data',
            
            # Identificadores
            'cups': sips_data['cups'],
            'invoice_id': invoice_id,
            'source': source,
            
            # Datos SIPS
            'current_powers': sips_data.get('current_powers', {}),
            'demand_data': sips_data.get('demand_data', []),
            'periods': sips_data.get('periods', []),
            'optimize_p6': sips_data.get('optimize_p6', False),
            
            # Metadata
            'consulted_at': datetime.now().isoformat(),
            'months_requested': sips_data.get('months', 12),
            'records_found': sips_data.get('records_found', 0),
        }
        
        # Guardar en CouchDB
        try:
            url = f"{self.couchdb_url}/{self.couchdb_db}"
            
            response = requests.post(
                url,
                auth=(self.couchdb_user, self.couchdb_password),
                headers={'Content-Type': 'application/json'},
                json=document,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                print(f"✅ Guardado en CouchDB:")
                print(f"   - Document ID: {result.get('id')}")
                print(f"   - Revision: {result.get('rev')}")
                return True
            else:
                print(f"❌ Error al guardar en CouchDB: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error de conexión a CouchDB: {e}")
            return False
    
    def get_sips_history(
        self,
        cups: str,
        invoice_id: Optional[int] = None,
        months: int = 12,
        optimize_p6: bool = False,
        save_to_couch: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Método principal para obtener histórico SIPS
        
        Args:
            cups: CUPS a consultar
            invoice_id: ID de factura (opcional)
            months: Meses hacia atrás
            optimize_p6: Optimizar P6
            save_to_couch: Guardar en CouchDB
            
        Returns:
            Datos SIPS o None
        """
        print(f"\n{'='*60}")
        print(f"📊 CONSULTANDO HISTÓRICO SIPS")
        print(f"{'='*60}")
        print(f"CUPS: {cups}")
        print(f"Meses: {months}")
        print(f"Invoice ID: {invoice_id or 'N/A'}")
        print(f"{'='*60}\n")
        
        # Conectar a DB si no está conectado
        if not self.connection or not self.connection.is_connected():
            if not self.connect_db():
                return None
        
        # Obtener datos SIPS
        sips_data = self.get_sips_data_by_cups(cups, months, optimize_p6)
        
        if not sips_data:
            return None
        
        # Guardar en CouchDB si está habilitado
        if save_to_couch:
            self.save_to_couchdb(sips_data, invoice_id, "python_client")
        
        return sips_data


def main():
    """Función principal para uso CLI"""
    parser = argparse.ArgumentParser(
        description='Cliente SIPS - Extrae histórico de consumos desde IGNIS'
    )
    
    parser.add_argument('cups', help='CUPS a consultar')
    parser.add_argument('--invoice-id', type=int, help='ID de factura')
    parser.add_argument('--months', type=int, default=12, help='Meses hacia atrás (default: 12)')
    parser.add_argument('--optimize-p6', action='store_true', help='Optimizar periodo 6')
    parser.add_argument('--no-save', action='store_true', help='No guardar en CouchDB')
    parser.add_argument('--output', help='Archivo JSON de salida')
    
    # Argumentos de conexión DB
    parser.add_argument('--db-host', default='localhost', help='Host de MySQL')
    parser.add_argument('--db-user', default='root', help='Usuario de MySQL')
    parser.add_argument('--db-password', default='', help='Password de MySQL')
    parser.add_argument('--db-name', default='ignis', help='Nombre de la base de datos')
    
    # Argumentos de CouchDB
    parser.add_argument('--couch-url', default='https://couchdb.aenergetic.app', help='URL de CouchDB')
    parser.add_argument('--couch-user', default='admin', help='Usuario de CouchDB')
    parser.add_argument('--couch-password', default='', help='Password de CouchDB')
    
    args = parser.parse_args()
    
    # Crear cliente
    client = SIPSClient(
        db_host=args.db_host,
        db_user=args.db_user,
        db_password=args.db_password,
        db_name=args.db_name,
        couchdb_url=args.couch_url,
        couchdb_user=args.couch_user,
        couchdb_password=args.couch_password,
    )
    
    try:
        # Obtener histórico SIPS
        sips_data = client.get_sips_history(
            cups=args.cups,
            invoice_id=args.invoice_id,
            months=args.months,
            optimize_p6=args.optimize_p6,
            save_to_couch=not args.no_save
        )
        
        if sips_data:
            # Guardar en archivo si se especificó
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(sips_data, f, indent=2, ensure_ascii=False, default=str)
                print(f"\n💾 Datos guardados en: {args.output}")
            
            print("\n✅ Proceso completado exitosamente")
            sys.exit(0)
        else:
            print("\n❌ No se pudieron obtener datos SIPS")
            sys.exit(1)
            
    finally:
        client.disconnect_db()


if __name__ == '__main__':
    main()
