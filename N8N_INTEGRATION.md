# 🔗 Integración SIPS Client con n8n

Esta guía explica cómo integrar el SIPS Client con n8n usando la API REST.

## 📋 Tabla de Contenidos

1. [Opción 1: API REST (Recomendado)](#opción-1-api-rest-recomendado)
2. [Opción 2: Comando directo](#opción-2-comando-directo)
3. [Ejemplos de workflows](#ejemplos-de-workflows)

---

## Opción 1: API REST (Recomendado)

### 1️⃣ Iniciar el servidor API

```bash
# Desde el directorio del proyecto
python3 sips_api.py
```

El servidor estará disponible en `http://localhost:5000`

### 2️⃣ Crear nodo HTTP Request en n8n

**Configuración del nodo:**

- **Method:** `POST`
- **URL:** `http://localhost:5000/sips`
- **Send Body:** `✓ Enabled`
- **Body Content Type:** `JSON`

**Body JSON:**

```json
{
  "cups": "{{ $json.cups }}",
  "invoice_id": {{ $json.invoice_id }},
  "months": 12,
  "optimize_p6": false,
  "save": true
}
```

### 3️⃣ Procesar la respuesta

La API devuelve:

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

Puedes acceder a los datos con:

```javascript
$json.data.cups
$json.data.records_found
$json.data.current_powers
```

### 4️⃣ Workflow completo

Importa el workflow `n8n_workflow_new_api.json`:

1. Ve a n8n → Workflows
2. Click en "..." → Import from File
3. Selecciona `n8n_workflow_new_api.json`

---

## Opción 2: Comando directo

Si prefieres ejecutar el script Python directamente desde n8n:

### 1️⃣ Crear nodo Execute Command

**Command:**

```bash
python3 /ruta/completa/a/sips_client.py \
  {{ $json.cups }} \
  --invoice-id {{ $json.invoice_id }} \
  --months 12 \
  --output /tmp/sips_{{ $json.cups }}.json
```

### 2️⃣ Leer el resultado

Añade un nodo "Read Binary File":

- **File Path:** `/tmp/sips_{{ $json.cups }}.json`

Luego un nodo "JSON" para parsear el contenido.

---

## Ejemplos de workflows

### Ejemplo 1: Procesar una factura y obtener SIPS

```
Webhook → Extract CUPS → Call SIPS API → Save Result
```

**Nodo "Call SIPS API":**

```json
{
  "method": "POST",
  "url": "http://localhost:5000/sips",
  "body": {
    "cups": "{{ $json.contract_details.cups }}",
    "invoice_id": {{ $json.crm.invoice_id }},
    "months": 12,
    "save": true
  }
}
```

### Ejemplo 2: Procesar múltiples CUPS en batch

**Nodo "Prepare Batch":**

```javascript
// Crear array de CUPS
const invoices = $input.all();
const cupsList = invoices.map(item => ({
  cups: item.json.cups,
  invoice_id: item.json.invoice_id
}));

return [{
  json: {
    cups_list: cupsList,
    months: 12,
    save: true
  }
}];
```

**Nodo "Call Batch API":**

```json
{
  "method": "POST",
  "url": "http://localhost:5000/sips/batch",
  "body": "={{ $json }}"
}
```

### Ejemplo 3: Workflow completo con ENTRYPOINT

```
ENTRYPOINT Webhook
    ↓
Extract CUPS from Invoice
    ↓
Call SIPS API (async)
    ↓
Save to CouchDB (ya hecho por API)
    ↓
Notify CRM
```

**Modificación al ENTRYPOINT existente:**

En el nodo "Call SIPS+CUPS Workflow1", cambia:

```json
{
  "workflowId": "ID_DEL_NUEVO_WORKFLOW",
  "waitForResult": false
}
```

Esto ejecutará el workflow de SIPS de forma asíncrona sin bloquear el ENTRYPOINT.

---

## 🔧 Configuración avanzada

### Ejecutar API como servicio (systemd)

Crea `/etc/systemd/system/sips-api.service`:

```ini
[Unit]
Description=SIPS API Service
After=network.target mysql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/ruta/a/sips_client
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 /ruta/a/sips_client/sips_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Activar servicio:

```bash
sudo systemctl daemon-reload
sudo systemctl enable sips-api
sudo systemctl start sips-api
sudo systemctl status sips-api
```

### Reverse proxy con Nginx

```nginx
location /api/sips {
    proxy_pass http://localhost:5000/sips;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Ahora puedes usar: `https://tu-dominio.com/api/sips` en n8n.

---

## 📊 Monitoreo y logs

### Ver logs de la API

```bash
# Si usas systemd
journalctl -u sips-api -f

# Si ejecutas manualmente
# Los logs aparecen en la consola
```

### Health check

```bash
curl http://localhost:5000/health
```

Respuesta:

```json
{
  "status": "ok",
  "service": "SIPS API",
  "timestamp": "2026-02-03T10:30:00",
  "version": "1.0.0"
}
```

---

## 🐛 Troubleshooting

### Error: "Connection refused"

- Verifica que la API esté corriendo: `curl http://localhost:5000/health`
- Revisa el puerto: `netstat -tuln | grep 5000`

### Error: "No se encontraron datos para el CUPS"

- Verifica que el CUPS existe en la base de datos de IGNIS
- Revisa las credenciales de MySQL en `.env`
- Aumenta el parámetro `months`

### Error: "Timeout"

- Aumenta el timeout en n8n: Options → Timeout → 60000
- Optimiza las queries de MySQL (añadir índices)

---

## ✅ Checklist de implementación

- [ ] Instalar dependencias: `pip install -r requirements.txt`
- [ ] Configurar `.env` con credenciales
- [ ] Probar cliente CLI: `python3 sips_client.py TEST_CUPS`
- [ ] Iniciar API: `python3 sips_api.py`
- [ ] Probar health check: `curl http://localhost:5000/health`
- [ ] Importar workflow en n8n
- [ ] Probar workflow con un CUPS real
- [ ] Configurar servicio systemd (producción)
- [ ] Configurar reverse proxy (opcional)
- [ ] Configurar monitoreo

---

## 📞 Soporte

Si encuentras problemas:

1. Revisa los logs de la API
2. Verifica las credenciales en `.env`
3. Prueba el cliente CLI directamente
4. Verifica que MySQL y CouchDB estén accesibles
