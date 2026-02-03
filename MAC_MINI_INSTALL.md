# 🍎 SIPS Client - Instalación en Mac mini

## 📋 Información del sistema

```
SSH: ssh aenergetic@172.28.169.57
User: aenergetic
Password: $Dev*aenergetic.
```

---

## ⚡ Instalación en 5 pasos

### 1️⃣ Conectar por SSH

```bash
# Desde Windows PowerShell o Terminal
ssh aenergetic@172.28.169.57
# Password: $Dev*aenergetic.
```

### 2️⃣ Copiar archivos al Mac mini

**Opción A: Desde Windows con SCP**

```powershell
# Crear carpeta de destino primero
ssh aenergetic@172.28.169.57 "mkdir -p ~/sips_client"

# Copiar todos los archivos
scp sips_client_crm.py aenergetic@172.28.169.57:~/sips_client/
scp sips_api_crm.py aenergetic@172.28.169.57:~/sips_client/
scp requirements.txt aenergetic@172.28.169.57:~/sips_client/
scp .env.macmini aenergetic@172.28.169.57:~/sips_client/.env
```

**Opción B: Manualmente (más fácil)**

1. Abre Finder → Red → Mac mini
2. Copia los archivos a una carpeta temporal
3. Por SSH, muévelos a `~/sips_client/`

### 3️⃣ Instalar dependencias

```bash
# Conectar por SSH
ssh aenergetic@172.28.169.57

# Ir a la carpeta
cd ~/sips_client

# Verificar Python
python3 --version

# Instalar pip si no está
python3 -m ensurepip --upgrade

# Instalar dependencias
pip3 install -r requirements.txt
```

### 4️⃣ Configurar credenciales

```bash
# Editar .env
nano .env
```

Configura estas líneas:

```env
CRM_DB_PASSWORD=TU_PASSWORD_MYSQL_DEL_MAC_MINI
CRM_DB_NAME=aenergetic_crm  # O el nombre real de tu BD
```

Guarda con `Ctrl+O`, Enter, `Ctrl+X`

### 5️⃣ Iniciar la API

```bash
# Método 1: Ejecución directa (para probar)
python3 sips_api_crm.py

# Método 2: En background (recomendado)
nohup python3 sips_api_crm.py > sips_api.log 2>&1 &

# Ver el PID
echo $!

# Ver logs en tiempo real
tail -f sips_api.log
```

---

## ✅ Verificar que funciona

### Desde el Mac mini:

```bash
# Health check
curl http://localhost:5000/health

# Probar consulta (reemplaza con un CUPS real)
curl -X POST http://localhost:5000/sips \
  -H "Content-Type: application/json" \
  -d '{"cups": "ES0031406091590001JF0F", "save": true}'
```

### Desde n8n:

En el nodo HTTP Request:

```
URL: http://172.28.169.57:5000/sips
Method: POST
Body:
{
  "cups": "{{ $json.cups }}",
  "invoice_id": {{ $json.invoice_id }},
  "save": true
}
```

---

## 🔧 Configurar como servicio (opcional pero recomendado)

### Crear archivo de servicio:

```bash
# Crear archivo plist para launchd
nano ~/Library/LaunchAgents/com.aenergetic.sips-api.plist
```

Contenido:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aenergetic.sips-api</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/aenergetic/sips_client/sips_api_crm.py</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>/Users/aenergetic/sips_client</string>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <true/>
    
    <key>StandardOutPath</key>
    <string>/Users/aenergetic/sips_client/sips_api.log</string>
    
    <key>StandardErrorPath</key>
    <string>/Users/aenergetic/sips_client/sips_api.error.log</string>
</dict>
</plist>
```

### Cargar el servicio:

```bash
# Cargar servicio
launchctl load ~/Library/LaunchAgents/com.aenergetic.sips-api.plist

# Verificar que está corriendo
launchctl list | grep sips-api

# Para detener
launchctl unload ~/Library/LaunchAgents/com.aenergetic.sips-api.plist

# Para reiniciar
launchctl unload ~/Library/LaunchAgents/com.aenergetic.sips-api.plist
launchctl load ~/Library/LaunchAgents/com.aenergetic.sips-api.plist
```

---

## 📊 Estructura del sistema

```
~/sips_client/
├── .env                    ← Credenciales (EDITAR)
├── sips_client_crm.py      ← Cliente principal
├── sips_api_crm.py         ← API REST
├── requirements.txt        ← Dependencias
├── sips_api.log           ← Logs (se crea automáticamente)
└── sips_api.error.log     ← Errores (se crea automáticamente)
```

---

## 🔍 Cómo funciona

1. **sips_client_crm.py** consulta la tabla `sips_cache` en la BD del CRM
2. Lee los datos SIPS almacenados en formato JSON
3. Los guarda en CouchDB con metadata adicional
4. **sips_api_crm.py** expone una API REST que n8n puede consumir

**Ventajas:**
- ✅ No depende de la API de IGNIS (que está rota)
- ✅ Usa los datos que ya tienes en el CRM
- ✅ Rápido (consulta directa a MySQL)
- ✅ Guarda automáticamente en CouchDB

---

## 🛠️ Troubleshooting

### Error: "Can't connect to MySQL server"

```bash
# Verificar que MySQL está corriendo
mysql -u root -p

# Si no arranca, verificar el servicio
sudo systemctl status mysql  # Linux
brew services list           # Mac

# Verificar que el password es correcto en .env
```

### Error: "Table 'sips_cache' doesn't exist"

La tabla se crea automáticamente en el CRM cuando procesas facturas. Si no existe:

```sql
-- Conectar a MySQL
mysql -u root -p

-- Usar la BD del CRM
USE aenergetic_crm;

-- Crear tabla manualmente
CREATE TABLE IF NOT EXISTS sips_cache (
    cups VARCHAR(30) PRIMARY KEY,
    data LONGTEXT,
    date_add DATETIME NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### Error: "No se encontraron datos SIPS en la caché"

Esto significa que el CUPS no tiene datos en `sips_cache`. Para solucionarlo:

1. Procesa una factura con ese CUPS en el CRM
2. O inserta datos manualmente en `sips_cache`

### El servicio no arranca automáticamente

```bash
# Ver logs del sistema
log show --predicate 'process == "launchd"' --last 5m

# Ver logs de la API
tail -f ~/sips_client/sips_api.log
tail -f ~/sips_client/sips_api.error.log

# Verificar permisos
ls -la ~/sips_client/sips_api_crm.py
chmod +x ~/sips_client/sips_api_crm.py
```

---

## 📋 Comandos útiles

```bash
# Ver procesos Python corriendo
ps aux | grep python

# Matar proceso de la API
pkill -f sips_api_crm.py

# Ver puerto 5000
lsof -i :5000

# Reiniciar la API
pkill -f sips_api_crm.py && nohup python3 ~/sips_client/sips_api_crm.py > ~/sips_client/sips_api.log 2>&1 &

# Ver logs
tail -f ~/sips_client/sips_api.log

# Probar conexión a MySQL
mysql -u root -p -e "SHOW DATABASES;"

# Ver tablas del CRM
mysql -u root -p aenergetic_crm -e "SHOW TABLES LIKE 'sips%';"

# Ver un registro de ejemplo
mysql -u root -p aenergetic_crm -e "SELECT cups, date_add FROM sips_cache LIMIT 1;"
```

---

## 🔄 Actualizar el código

```bash
# Detener servicio
launchctl unload ~/Library/LaunchAgents/com.aenergetic.sips-api.plist

# Editar archivo
nano ~/sips_client/sips_api_crm.py

# Reiniciar servicio
launchctl load ~/Library/LaunchAgents/com.aenergetic.sips-api.plist

# Ver logs
tail -f ~/sips_client/sips_api.log
```

---

## 🆘 Checklist de instalación

- [ ] Conectar por SSH al Mac mini
- [ ] Copiar archivos a `~/sips_client/`
- [ ] Instalar dependencias: `pip3 install -r requirements.txt`
- [ ] Configurar `.env` con password de MySQL
- [ ] Probar cliente CLI: `python3 sips_client_crm.py --help`
- [ ] Iniciar API: `python3 sips_api_crm.py`
- [ ] Verificar: `curl http://localhost:5000/health`
- [ ] Configurar como servicio (opcional)
- [ ] Configurar n8n para usar `http://172.28.169.57:5000/sips`

---

## 📞 Información del sistema

**Mac mini:**
- IP: 172.28.169.57
- User: aenergetic
- SSH: `ssh aenergetic@172.28.169.57`

**MySQL:**
- Host: localhost (en el Mac mini)
- User: root
- Base de datos: aenergetic_crm (o el nombre que uses)

**CouchDB:**
- URL: https://couchdb.aenergetic.app
- User: admin
- Database: sips_history

**API:**
- URL local: http://localhost:5000
- URL red: http://172.28.169.57:5000

---

¡Listo! Ya puedes consultar históricos SIPS desde el CRM sin depender de APIs externas.
