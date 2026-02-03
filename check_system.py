#!/usr/bin/env python3
"""
SIPS Client - Script de verificación del sistema
=================================================
Verifica que todas las dependencias y configuraciones estén correctas
"""

import sys
import os

def print_header(text):
    """Imprime un header con formato"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def check_python():
    """Verifica versión de Python"""
    print("🐍 Verificando Python...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor} - Se requiere 3.8+")
        return False

def check_dependencies():
    """Verifica que las dependencias estén instaladas"""
    print("\n📦 Verificando dependencias...")
    
    dependencies = {
        'mysql.connector': 'mysql-connector-python',
        'requests': 'requests',
        'flask': 'flask',
        'flask_cors': 'flask-cors',
    }
    
    all_ok = True
    
    for module, package in dependencies.items():
        try:
            __import__(module)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - No instalado")
            all_ok = False
    
    # Verificar dotenv (opcional)
    try:
        __import__('dotenv')
        print(f"   ✅ python-dotenv")
    except ImportError:
        print(f"   ⚠️  python-dotenv - Opcional, usa variables de sistema")
    
    return all_ok

def check_env_file():
    """Verifica que exista el archivo .env"""
    print("\n⚙️  Verificando configuración...")
    
    if os.path.exists('.env'):
        print("   ✅ Archivo .env encontrado")
        
        # Intentar cargar
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print("   ✅ Archivo .env cargado")
        except:
            pass
        
        return True
    else:
        print("   ⚠️  Archivo .env no encontrado")
        print("      Copia .env.example a .env y configúralo")
        return False

def check_mysql_connection():
    """Verifica conexión a MySQL"""
    print("\n🗄️  Verificando conexión a MySQL...")
    
    try:
        import mysql.connector
        from dotenv import load_dotenv
        load_dotenv()
        
        host = os.getenv('IGNIS_DB_HOST', 'localhost')
        user = os.getenv('IGNIS_DB_USER', 'root')
        password = os.getenv('IGNIS_DB_PASSWORD', '')
        database = os.getenv('IGNIS_DB_NAME', 'ignis')
        
        if not password:
            print("   ⚠️  Password de MySQL no configurado en .env")
            return False
        
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            connect_timeout=5
        )
        
        if connection.is_connected():
            db_info = connection.get_server_info()
            print(f"   ✅ Conectado a MySQL {db_info}")
            
            # Verificar tabla
            cursor = connection.cursor()
            cursor.execute("SHOW TABLES LIKE 'consumos_historicos'")
            result = cursor.fetchone()
            
            if result:
                print(f"   ✅ Tabla 'consumos_historicos' existe")
            else:
                print(f"   ⚠️  Tabla 'consumos_historicos' no encontrada")
                print(f"      Verifica el nombre de la tabla en tu BD")
            
            cursor.close()
            connection.close()
            return True
        
    except Exception as e:
        print(f"   ❌ Error al conectar a MySQL: {e}")
        return False

def check_couchdb_connection():
    """Verifica conexión a CouchDB"""
    print("\n🛋️  Verificando conexión a CouchDB...")
    
    try:
        import requests
        from dotenv import load_dotenv
        load_dotenv()
        
        url = os.getenv('COUCHDB_URL', 'https://couchdb.aenergetic.app')
        user = os.getenv('COUCHDB_USER', 'admin')
        password = os.getenv('COUCHDB_PASSWORD', '')
        database = os.getenv('COUCHDB_DATABASE', 'sips_history')
        
        if not password:
            print("   ⚠️  Password de CouchDB no configurado en .env")
            return False
        
        # Verificar servidor
        response = requests.get(
            url,
            auth=(user, password),
            timeout=5
        )
        
        if response.status_code == 200:
            print(f"   ✅ CouchDB accesible en {url}")
            
            # Verificar base de datos
            db_response = requests.get(
                f"{url}/{database}",
                auth=(user, password),
                timeout=5
            )
            
            if db_response.status_code == 200:
                print(f"   ✅ Base de datos '{database}' existe")
            else:
                print(f"   ⚠️  Base de datos '{database}' no encontrada")
                print(f"      Créala en CouchDB o cambia COUCHDB_DATABASE en .env")
            
            return True
        else:
            print(f"   ❌ Error al conectar: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error al conectar a CouchDB: {e}")
        return False

def check_files():
    """Verifica que los archivos necesarios existan"""
    print("\n📁 Verificando archivos...")
    
    files = [
        'sips_client.py',
        'sips_api.py',
        'requirements.txt',
        '.env.example',
    ]
    
    all_ok = True
    for file in files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} - No encontrado")
            all_ok = False
    
    return all_ok

def main():
    """Ejecuta todas las verificaciones"""
    print_header("🔍 VERIFICACIÓN DEL SISTEMA SIPS CLIENT")
    
    checks = [
        ("Python", check_python),
        ("Dependencias", check_dependencies),
        ("Archivos", check_files),
        ("Configuración", check_env_file),
        ("MySQL", check_mysql_connection),
        ("CouchDB", check_couchdb_connection),
    ]
    
    results = {}
    
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n❌ Error en verificación de {name}: {e}")
            results[name] = False
    
    # Resumen
    print_header("📊 RESUMEN")
    
    all_passed = True
    for name, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"{status} {name}")
        if not passed:
            all_passed = False
    
    print()
    
    if all_passed:
        print("🎉 ¡Todo está configurado correctamente!")
        print("\nPróximos pasos:")
        print("  1. Prueba el cliente: python3 sips_client.py --help")
        print("  2. Inicia la API: python3 sips_api.py")
        print("  3. Importa el workflow en n8n")
        sys.exit(0)
    else:
        print("⚠️  Hay problemas que resolver")
        print("\nRevisa la documentación:")
        print("  - README.md")
        print("  - N8N_INTEGRATION.md")
        sys.exit(1)

if __name__ == '__main__':
    main()
