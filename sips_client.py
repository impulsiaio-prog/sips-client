#!/usr/bin/env python3
"""
SIPS History Client - Extrae histórico SIPS desde CRM de Aenergetic
====================================================================
Este cliente se conecta directamente a la base de datos MySQL del CRM
para obtener datos de SIPS desde la tabla sips_cache y los guarda en CouchDB.

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
    """Cliente para extraer histórico SIPS desde CRM"""
    
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
            db_host: Host de la base de datos MySQL del CRM
            db_user: Usuario de MySQL
            db_password: Password de MySQL
            db_name: Nombre de la base de datos del CRM
            couchdb_url: URL de CouchDB
            couchdb_user: Usuario de CouchDB
            couchdb_password: Password de CouchDB
        """
        # Usar variables de entorno como fallback
        self.db_host = db_host or os.getenv('CRM_DB_HOST', 'localhost')
        self.db_user = db_user or os.getenv('CRM_DB_USER', 'root')
        self.db_password = db_password or os.getenv('CRM_DB_PASSWORD', '')
        self.db_name = db_name or os.getenv('CRM_DB_NAME', 'aenergetic_crm')
        
        self.couchdb_url = couchdb_url or os.getenv('COUCHDB_URL', 'https://couchdb.aenergetic.app')
        self.couchdb_user = couchdb_user or os.getenv('COUCHDB_USER', 'admin')
        self.couchdb_password = couchdb_password or os.getenv('COUCHDB_PASSWORD', '')
        self.couchdb_db = os.getenv('COUCHDB_DATABASE', 'sips_history')
        
        self.connection = None
    
    def connect_db(self) -> bool:
        """Conecta a la base de datos MySQL del CRM"""
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
                print(f"   Base de datos: {self.db_name}")
                return True
                
        except Error as e:
            print(f"❌ Error al conectar a MySQL: {e}")
            return False
    
    def disconnect_db(self):
        """Cierra la conexión a MySQL"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("🔌 Conexión a MySQL cerrada")
    
    def get_sips_from_cache(self, cups: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene datos SIPS desde la tabla sips_cache
        
        Args:
            cups: CUPS a consultar
            
        Returns:
            Dict con datos SIPS o None si no existe
        """
        if not self.connection or not self.connection.is_connected():
            print("❌ No hay conexión a la base de datos")
            return None
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # Consultar sips_cache
            query = """
                SELECT cups, data, date_add
                FROM sips_cache
                WHERE cups = %s
                ORDER BY date_add DESC
                LIMIT 1
            """
            
            cursor.execute(query, (cups,))
            row = cursor.fetchone()
            cursor.close()
            
            if not row:
                print(f"⚠️  No se encontraron datos SIPS en caché para: {cups}")
                return None
            
            # Parsear el JSON almacenado
            try:
                sips_data = json.loads(row['data'])
            except json.JSONDecodeError as e:
                print(f"❌ Error al parsear JSON de sips_cache: {e}")
                return None
            
            print(f"✅ Datos SIPS obtenidos desde caché:")
            print(f"   - CUPS: {cups}")
            print(f"   - Fecha caché: {row['date_add']}")
            
            return sips_data
            
        except Error as e:
            print(f"❌ Error en query: {e}")
            return None
    
    def get_invoice_data(self, invoice_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene datos de una factura específica
        
        Args:
            invoice_id: ID de la factura
            
        Returns:
            Dict con datos de la factura o None
        """
        if not self.connection or not self.connection.is_connected():
            return None
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            query = """
                SELECT 
                    id_invoice,
                    cups,
                    invoice_number,
                    invoice_date,
                    billing_start,
                    billing_end,
                    contracted_power_p1,
                    contracted_power_p2,
                    contracted_power_p3,
                    contracted_power_p4,
                    contracted_power_p5,
                    contracted_power_p6
                FROM invoices
                WHERE id_invoice = %s
            """
            
            cursor.execute(query, (invoice_id,))
            row = cursor.fetchone()
            cursor.close()
            
            return row
            
        except Error as e:
            print(f"❌ Error al obtener datos de factura: {e}")
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
        
        # Extraer CUPS
        cups = sips_data.get('cups') or sips_data.get('CUPS')
        if not cups:
            print("❌ No se encontró CUPS en los datos SIPS")
            return False
        
        # Construir documento para CouchDB
        doc_id = f"sips_{cups}_{int(datetime.now().timestamp() * 1000)}"
        
        document = {
            '_id': doc_id,
            'type': 'sips_data',
            
            # Identificadores
            'cups': cups,
            'invoice_id': invoice_id,
            'source': source,
            
            # Datos SIPS completos (tal cual vienen de la caché)
            'sips_raw_data': sips_data,
            
            # Extraer algunos campos útiles si existen
            'current_powers': sips_data.get('current_powers', {}),
            'demand_data': sips_data.get('demand_data', []),
            'periods': sips_data.get('periods', []),
            
            # Metadata
            'consulted_at': datetime.now().isoformat(),
            'records_found': len(sips_data.get('demand_data', [])),
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
        save_to_couch: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Método principal para obtener histórico SIPS
        
        Args:
            cups: CUPS a consultar
            invoice_id: ID de factura (opcional)
            save_to_couch: Guardar en CouchDB
            
        Returns:
            Datos SIPS o None
        """
        print(f"\n{'='*60}")
        print(f"📊 CONSULTANDO HISTÓRICO SIPS")
        print(f"{'='*60}")
        print(f"CUPS: {cups}")
        print(f"Invoice ID: {invoice_id or 'N/A'}")
        print(f"{'='*60}\n")
        
        # Conectar a DB si no está conectado
        if not self.connection or not self.connection.is_connected():
            if not self.connect_db():
                return None
        
        # Obtener datos SIPS desde caché
        sips_data = self.get_sips_from_cache(cups)
        
        if not sips_data:
            return None
        
        # Si hay invoice_id, enriquecer con datos de la factura
        if invoice_id:
            invoice_data = self.get_invoice_data(invoice_id)
            if invoice_data:
                sips_data['invoice_data'] = invoice_data
        
        # Guardar en CouchDB si está habilitado
        if save_to_couch:
            self.save_to_couchdb(sips_data, invoice_id, "python_client")
        
        return sips_data


def main():
    """Función principal para uso CLI"""
    parser = argparse.ArgumentParser(
        description='Cliente SIPS - Extrae histórico desde CRM de Aenergetic'
    )
    
    parser.add_argument('cups', help='CUPS a consultar')
    parser.add_argument('--invoice-id', type=int, help='ID de factura')
    parser.add_argument('--no-save', action='store_true', help='No guardar en CouchDB')
    parser.add_argument('--output', help='Archivo JSON de salida')
    
    # Argumentos de conexión DB
    parser.add_argument('--db-host', help='Host de MySQL')
    parser.add_argument('--db-user', help='Usuario de MySQL')
    parser.add_argument('--db-password', help='Password de MySQL')
    parser.add_argument('--db-name', help='Nombre de la base de datos')
    
    # Argumentos de CouchDB
    parser.add_argument('--couch-url', help='URL de CouchDB')
    parser.add_argument('--couch-user', help='Usuario de CouchDB')
    parser.add_argument('--couch-password', help='Password de CouchDB')
    
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
    main()        """Cierra la conexión a MySQL"""
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
