# 🔌 SIPS Client - Cliente Python para Histórico SIPS

Cliente Python que extrae datos históricos de SIPS (Sistema de Información de Puntos de Suministro) desde la base de datos de IGNIS y los guarda en CouchDB.

## 📋 Características

✅ Conexión directa a MySQL de IGNIS  
✅ Extracción de datos históricos por CUPS  
✅ Guardado automático en CouchDB  
✅ CLI fácil de usar  
✅ Exportación a JSON  
✅ Sin dependencias de APIs rotas  

## 🚀 Instalación

### 1. Instalar dependencias

```bash
pip install mysql-connector-python requests python-dotenv
```

### 2. Configurar variables de entorno

Copia el archivo de ejemplo:

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales:

```env
# MySQL (IGNIS Database)
IGNIS_DB_HOST=localhost
IGNIS_DB_USER=root
IGNIS_DB_PASSWORD=tu_password
IGNIS_DB_NAME=ignis

# CouchDB
COUCHDB_URL=https://couchdb.aenergetic.app
COUCHDB_USER=admin
COUCHDB_PASSWORD=tu_password_couch
```

## 📖 Uso

### Uso básico (CLI)

```bash
python sips_client.py ES0031406091590001JF0F
```

### Con parámetros opcionales

```bash
# Especificar ID de factura
python sips_client.py ES0031406091590001JF0F --invoice-id 12345

# Cambiar número de meses
python sips_client.py ES0031406091590001JF0F --months 24

# Optimizar periodo 6
python sips_client.py ES0031406091590001JF0F --optimize-p6

# No guardar en CouchDB (solo mostrar)
python sips_client.py ES0031406091590001JF0F --no-save

# Guardar resultado en archivo JSON
python sips_client.py ES0031406091590001JF0F --output resultado.json
```

### Especificar credenciales manualmente

```bash
python sips_client.py ES0031406091590001JF0F \
  --db-host localhost \
  --db-user root \
  --db-password mipassword \
  --db-name ignis \
  --couch-url https://couchdb.aenergetic.app \
  --couch-user admin \
  --couch-password mipassword_couch
```

## 🐍 Uso como módulo Python

```python
from sips_client import SIPSClient

# Crear cliente
client = SIPSClient(
    db_host='localhost',
    db_user='root',
    db_password='password',
    db_name='ignis',
    couchdb_url='https://couchdb.aenergetic.app',
    couchdb_user='admin',
    couchdb_password='password'
)

# Obtener histórico SIPS
sips_data = client.get_sips_history(
    cups='ES0031406091590001JF0F',
    invoice_id=12345,
    months=12,
    optimize_p6=False,
    save_to_couch=True
)

if sips_data:
    print(f"Registros encontrados: {sips_data['records_found']}")
    print(f"Periodos: {sips_data['periods']}")
    print(f"Potencias actuales: {sips_data['current_powers']}")

# Cerrar conexión
client.disconnect_db()
```

## 📊 Estructura de Datos Devueltos

```json
{
  "cups": "ES0031406091590001JF0F",
  "current_powers": {
    "P1": 3.45,
    "P2": 3.45,
    "P3": 2.30
  },
  "demand_data": [
    {
      "fecha": "2025-01-15T00:00:00",
      "periodo": "P1",
      "consumo_kwh": 45.2,
      "potencia_maxima": 3.1
    }
  ],
  "periods": ["P1", "P2", "P3"],
  "optimize_p6": false,
  "months": 12,
  "records_found": 365,
  "query_date": "2026-02-03T10:30:00"
}
```

## 🗄️ Documento Guardado en CouchDB

```json
{
  "_id": "sips_ES0031406091590001JF0F_1738579800000",
  "type": "sips_data",
  "cups": "ES0031406091590001JF0F",
  "invoice_id": 12345,
  "source": "python_client",
  "current_powers": {...},
  "demand_data": [...],
  "periods": ["P1", "P2", "P3"],
  "optimize_p6": false,
  "consulted_at": "2026-02-03T10:30:00",
  "months_requested": 12,
  "records_found": 365
}
```

## 🔍 Esquema de Base de Datos Esperado

El cliente espera una tabla `consumos_historicos` en MySQL con esta estructura:

```sql
CREATE TABLE consumos_historicos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    cups VARCHAR(50) NOT NULL,
    fecha_lectura DATETIME NOT NULL,
    periodo VARCHAR(10),
    consumo_kwh DECIMAL(10,3),
    potencia_contratada DECIMAL(10,3),
    potencia_maxima DECIMAL(10,3),
    precio_energia DECIMAL(10,6),
    precio_potencia DECIMAL(10,6),
    INDEX idx_cups (cups),
    INDEX idx_fecha (fecha_lectura)
);
```

**⚠️ IMPORTANTE:** Si tu base de datos de IGNIS tiene nombres de tabla o columnas diferentes, deberás modificar la query en el método `get_sips_data_by_cups()` del archivo `sips_client.py`.

## 🔧 Integración con n8n

Para usar este cliente desde n8n, crea un nodo "Execute Command" con:

```bash
python /ruta/a/sips_client.py \
  {{ $json.cups }} \
  --invoice-id {{ $json.invoice_id }} \
  --months 12 \
  --db-host localhost \
  --db-user root \
  --db-password {{ $env.MYSQL_PASSWORD }} \
  --couch-password {{ $env.COUCH_PASSWORD }}
```

O mejor aún, crea un nodo HTTP Request que llame a un API wrapper:

```python
# api_wrapper.py (Flask)
from flask import Flask, request, jsonify
from sips_client import SIPSClient

app = Flask(__name__)

@app.route('/sips/<cups>', methods=['GET'])
def get_sips(cups):
    client = SIPSClient(...)
    data = client.get_sips_history(cups=cups)
    return jsonify(data)

if __name__ == '__main__':
    app.run(port=5000)
```

## ❓ Ayuda

```bash
python sips_client.py --help
```

## 📝 Notas

1. **Rendimiento**: El cliente consulta directamente MySQL, por lo que es muy rápido
2. **Seguridad**: No expongas tus credenciales en el código
3. **Tabla personalizada**: Si tu tabla de IGNIS tiene otro nombre, modifica la query en el código
4. **Índices**: Asegúrate de que la tabla tenga índices en `cups` y `fecha_lectura` para mejor rendimiento

## 🐛 Troubleshooting

### Error: "No se encontraron datos para CUPS"

- Verifica que el CUPS existe en la base de datos
- Verifica que hay datos en el rango de fechas consultado
- Aumenta el parámetro `--months`

### Error: "Error al conectar a MySQL"

- Verifica las credenciales en `.env`
- Asegúrate de que MySQL está corriendo
- Verifica que el usuario tiene permisos en la base de datos

### Error: "Error al guardar en CouchDB"

- Verifica que CouchDB está accesible
- Verifica credenciales de CouchDB
- Verifica que la base de datos `sips_history` existe

## 📜 Licencia

Uso interno - Aenergetic © 2026
