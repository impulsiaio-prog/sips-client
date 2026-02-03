# 🔌 SIPS Client - Cliente Python para Histórico SIPS

Cliente Python que extrae datos históricos de SIPS (Sistema de Información de Puntos de Suministro) desde la base de datos del CRM de Aenergetic y los guarda en CouchDB.

## 🎯 Características principales

✅ Conexión directa a MySQL del CRM  
✅ Extracción de datos desde `sips_cache`  
✅ Guardado automático en CouchDB  
✅ API REST para integración con n8n  
✅ CLI fácil de usar  
✅ Sin dependencias de APIs rotas  

---

## 📚 Versiones disponibles

Este repositorio contiene **dos versiones** del cliente:

### 1️⃣ Versión CRM (Recomendada) ⭐

**Para Mac mini con CRM de Aenergetic**

- Lee datos de la tabla `sips_cache` del CRM
- No depende de IGNIS ni APIs externas
- Usa los datos que ya tienes

**Archivos:**
- `sips_client_crm.py` - Cliente principal
- `sips_api_crm.py` - API REST
- `.env.macmini` - Configuración

**Instalación:** Ver [MAC_MINI_INSTALL.md](MAC_MINI_INSTALL.md)

### 2️⃣ Versión IGNIS (Original)

**Para sistemas con acceso directo a base de datos de IGNIS**

- Consulta directamente la BD de IGNIS
- Requiere tabla `consumos_historicos`
- Para entornos con IGNIS instalado

**Archivos:**
- `sips_client.py` - Cliente original
- `sips_api.py` - API REST original

**Instalación:** Ver [README.md](README.md) o [QUICKSTART.md](QUICKSTART.md)

---

## ⚡ Instalación Rápida (Mac mini)

```bash
# 1. Clonar repositorio
git clone https://github.com/impulsiaio-prog/sips-client.git
cd sips-client

# 2. Instalar dependencias
pip3 install -r requirements.txt

# 3. Configurar
cp .env.macmini .env
nano .env  # Editar password de MySQL

# 4. Iniciar API
python3 sips_api_crm.py
```

**URL para n8n:** `http://172.28.169.57:5000/sips`

---

## 🐳 Instalación con Docker

También incluimos configuración Docker para ejecutar en cualquier sistema:

```bash
# Con docker-compose (recomendado)
docker-compose up -d

# O con Docker directamente
docker build -t sips-api .
docker run -d -p 5000:5000 --env-file .env sips-api
```

Ver [DOCKER_INSTALL.md](DOCKER_INSTALL.md) para más detalles.

---

## 📖 Documentación

| Documento | Descripción |
|-----------|-------------|
| [MAC_MINI_INSTALL.md](MAC_MINI_INSTALL.md) | Guía completa para Mac mini (CRM) |
| [DOCKER_INSTALL.md](DOCKER_INSTALL.md) | Instalación con Docker |
| [QUICKSTART.md](QUICKSTART.md) | Inicio rápido (versión IGNIS) |
| [N8N_INTEGRATION.md](N8N_INTEGRATION.md) | Integración con n8n |
| [README_IGNIS.md](README_IGNIS.md) | Documentación versión IGNIS |

---

## 🔗 Integración con n8n

### Nodo HTTP Request:

**Configuración:**
- **Method:** POST
- **URL:** `http://172.28.169.57:5000/sips` (Mac mini)
- **Body:**

```json
{
  "cups": "{{ $json.cups }}",
  "invoice_id": {{ $json.invoice_id }},
  "save": true
}
```

**Respuesta:**

```json
{
  "success": true,
  "data": {
    "cups": "ES0031406091590001JF0F",
    "current_powers": {...},
    "demand_data": [...],
    "periods": ["P1", "P2", "P3"],
    "records_found": 365
  },
  "saved_to_couchdb": true
}
```

Ver [N8N_INTEGRATION.md](N8N_INTEGRATION.md) para ejemplos completos.

---

## 📊 Estructura del Proyecto

```
sips-client/
├── README.md                    ← Este archivo
├── MAC_MINI_INSTALL.md          ← Guía Mac mini (CRM)
├── DOCKER_INSTALL.md            ← Guía Docker
├── QUICKSTART.md                ← Inicio rápido
├── N8N_INTEGRATION.md           ← Integración n8n
│
├── sips_client_crm.py           ← Cliente CRM (Mac mini)
├── sips_api_crm.py              ← API CRM
├── .env.macmini                 ← Config Mac mini
│
├── sips_client.py               ← Cliente IGNIS
├── sips_api.py                  ← API IGNIS
├── .env.example                 ← Config IGNIS
│
├── requirements.txt             ← Dependencias Python
├── Dockerfile                   ← Imagen Docker
├── docker-compose.yml           ← Orquestación Docker
│
├── example_usage.py             ← Ejemplos de uso
├── check_system.py              ← Verificador sistema
└── n8n_workflow_new_api.json    ← Workflow n8n
```

---

## 🛠️ Uso CLI

### Versión CRM:

```bash
# Consultar un CUPS
python3 sips_client_crm.py ES0031406091590001JF0F

# Con invoice_id
python3 sips_client_crm.py ES0031406091590001JF0F --invoice-id 12345

# Sin guardar en CouchDB
python3 sips_client_crm.py ES0031406091590001JF0F --no-save

# Guardar en archivo JSON
python3 sips_client_crm.py ES0031406091590001JF0F --output resultado.json
```

### Versión IGNIS:

```bash
# Consultar un CUPS
python3 sips_client.py ES0031406091590001JF0F --months 12

# Ver todas las opciones
python3 sips_client.py --help
```

---

## 🔧 Configuración

### Variables de entorno (.env):

**Para versión CRM (Mac mini):**

```env
# MySQL del CRM
CRM_DB_HOST=localhost
CRM_DB_USER=root
CRM_DB_PASSWORD=tu_password
CRM_DB_NAME=aenergetic_crm

# CouchDB
COUCHDB_URL=https://couchdb.aenergetic.app
COUCHDB_USER=admin
COUCHDB_PASSWORD=7fGT1Lxk0fcRX6LnVqdFq97mawaMx797MclOJHeuTIU=
COUCHDB_DATABASE=sips_history
```

**Para versión IGNIS:**

```env
# MySQL de IGNIS
IGNIS_DB_HOST=localhost
IGNIS_DB_USER=root
IGNIS_DB_PASSWORD=tu_password
IGNIS_DB_NAME=ignis

# CouchDB (igual que arriba)
```

---

## 🆘 Troubleshooting

### Error: "No se encontraron datos SIPS en la caché"

**Causa:** El CUPS no tiene datos en la tabla `sips_cache` del CRM.

**Solución:** Procesa una factura con ese CUPS en el CRM primero.

### Error: "Can't connect to MySQL server"

**Solución:**
```bash
# Verificar que MySQL está corriendo
mysql -u root -p

# Verificar credenciales en .env
cat .env
```

### Error: "Table 'sips_cache' doesn't exist"

**Solución:** La tabla se crea automáticamente al procesar facturas en el CRM. Si no existe, créala manualmente:

```sql
CREATE TABLE IF NOT EXISTS sips_cache (
    cups VARCHAR(30) PRIMARY KEY,
    data LONGTEXT,
    date_add DATETIME NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### La API no responde

```bash
# Verificar que está corriendo
curl http://localhost:5000/health

# Ver logs
tail -f sips_api.log

# Reiniciar
pkill -f sips_api_crm.py
python3 sips_api_crm.py
```

Ver documentación completa en [MAC_MINI_INSTALL.md](MAC_MINI_INSTALL.md)

---

## 📞 Información del Sistema

**Mac mini (Producción):**
- IP: 172.28.169.57
- User: aenergetic
- SSH: `ssh aenergetic@172.28.169.57`
- API: http://172.28.169.57:5000

**CouchDB:**
- URL: https://couchdb.aenergetic.app
- Database: sips_history

---

## 🔄 Actualizar

```bash
# Desde el Mac mini
cd ~/sips-client
git pull origin main

# Reiniciar servicio si está configurado
launchctl unload ~/Library/LaunchAgents/com.aenergetic.sips-api.plist
launchctl load ~/Library/LaunchAgents/com.aenergetic.sips-api.plist
```

---

## 📜 Licencia

Uso interno - Aenergetic © 2026

---

## 🤝 Contribuir

Para contribuir o reportar issues:
1. Fork el repositorio
2. Crea una branch: `git checkout -b feature/nueva-funcionalidad`
3. Commit: `git commit -am 'Añade nueva funcionalidad'`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Crea un Pull Request

---

## 📚 Recursos adicionales

- [Documentación CouchDB](https://docs.couchdb.org/)
- [n8n Documentation](https://docs.n8n.io/)
- [MySQL Python Connector](https://dev.mysql.com/doc/connector-python/en/)
- [Flask Documentation](https://flask.palletsprojects.com/)

---

**⭐ Recomendación:** Para producción, usa la versión CRM en el Mac mini con configuración como servicio (launchd).
