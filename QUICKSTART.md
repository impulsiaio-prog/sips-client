# ⚡ INICIO RÁPIDO - SIPS Client

## 🚀 Instalación en 3 pasos

### 1. Instalar dependencias

```bash
chmod +x install.sh
./install.sh
```

O manualmente:

```bash
pip install -r requirements.txt --break-system-packages
```

### 2. Configurar credenciales

```bash
cp .env.example .env
nano .env
```

Edita `.env` y configura:
- `IGNIS_DB_PASSWORD` con tu password de MySQL
- Las demás credenciales si son diferentes

### 3. Verificar instalación

```bash
python3 check_system.py
```

Si todo está ✅, ¡estás listo!

---

## 📖 Uso básico

### Opción A: CLI (Línea de comandos)

```bash
# Consultar un CUPS
python3 sips_client.py ES0031406091590001JF0F

# Con parámetros
python3 sips_client.py ES0031406091590001JF0F --invoice-id 12345 --months 6

# Ver ayuda
python3 sips_client.py --help
```

### Opción B: API REST (Para n8n)

```bash
# 1. Iniciar el servidor
python3 sips_api.py

# 2. En otra terminal, probar:
curl http://localhost:5000/health

# 3. Consultar un CUPS:
curl -X POST http://localhost:5000/sips \
  -H "Content-Type: application/json" \
  -d '{"cups": "ES0031406091590001JF0F", "months": 12}'
```

---

## 🔗 Integración con n8n

### Importar workflow

1. Abre n8n
2. Workflows → Import from File
3. Selecciona `n8n_workflow_new_api.json`
4. Activa el workflow

### Configurar nodo HTTP Request

- **Method:** POST
- **URL:** `http://localhost:5000/sips`
- **Body:**

```json
{
  "cups": "{{ $json.cups }}",
  "invoice_id": {{ $json.invoice_id }},
  "months": 12,
  "save": true
}
```

Ver `N8N_INTEGRATION.md` para más detalles.

---

## 🗂️ Archivos incluidos

| Archivo | Descripción |
|---------|-------------|
| `sips_client.py` | Cliente Python principal |
| `sips_api.py` | API REST wrapper |
| `check_system.py` | Verificador del sistema |
| `example_usage.py` | Ejemplos de uso |
| `requirements.txt` | Dependencias Python |
| `install.sh` | Script de instalación |
| `.env.example` | Plantilla de configuración |
| `README.md` | Documentación completa |
| `N8N_INTEGRATION.md` | Guía de integración n8n |
| `n8n_workflow_new_api.json` | Workflow de ejemplo |

---

## 📊 ¿Qué hace este sistema?

1. **Extrae datos SIPS** de la base de datos MySQL de IGNIS
2. **Consulta históricos** de consumo por CUPS
3. **Guarda automáticamente** en CouchDB
4. **Expone API REST** para integrarse con n8n
5. **Sin dependencias** de APIs rotas

---

## ❓ Problemas comunes

### "No module named 'mysql.connector'"

```bash
pip install mysql-connector-python --break-system-packages
```

### "Connection refused to MySQL"

1. Verifica que MySQL esté corriendo: `sudo systemctl status mysql`
2. Revisa las credenciales en `.env`
3. Prueba la conexión: `mysql -u root -p`

### "API no responde"

1. Verifica que esté corriendo: `curl http://localhost:5000/health`
2. Revisa el puerto: `netstat -tuln | grep 5000`
3. Revisa los logs de la API

### "No se encontraron datos para el CUPS"

1. Verifica que el CUPS existe en la BD
2. Aumenta `--months`
3. Revisa el nombre de la tabla en el código

---

## 📚 Documentación completa

- **README.md** → Documentación completa del cliente
- **N8N_INTEGRATION.md** → Guía detallada de integración con n8n

---

## 🆘 Ayuda

```bash
python3 sips_client.py --help
python3 check_system.py
```

---

**¡Listo! Ya puedes consultar históricos SIPS sin depender de la API rota.**
