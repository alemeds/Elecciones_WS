# 🏍️ WS GCA — Sistema de Elecciones

App de votación para el Widows Sons Grand Chapter of Argentina.

## Archivos del proyecto

```
ws_votacion/
├── app.py              # App principal Streamlit
├── requirements.txt    # Dependencias Python
├── secrets.example.toml # Ejemplo de configuración de secrets
├── .gitignore          # Excluye archivos sensibles
└── README.md
```

## Deploy en Streamlit Community Cloud

### 1. Crear Service Account en Google Cloud

1. Entrá a https://console.cloud.google.com
2. Creá un proyecto nuevo (o usá uno existente)
3. Activá las APIs:
   - Google Sheets API
   - Google Drive API
4. Andá a **IAM → Service Accounts → Crear cuenta de servicio**
5. Nombre: `ws-votacion`
6. Clic en la cuenta creada → **Claves → Agregar clave → JSON**
7. Descargá el archivo JSON — lo vas a necesitar para los secrets

### 2. Compartir la planilla con el Service Account

1. Abrí el archivo JSON descargado
2. Copiá el valor de `client_email` (algo como `ws-votacion@proyecto.iam.gserviceaccount.com`)
3. Abrí tu planilla de Google Sheets
4. Clic en **Compartir** → pegá ese email → rol **Editor** → Compartir

### 3. Subir el código a GitHub

```bash
git init
git add .
git commit -m "WS GCA Sistema de Elecciones"
git remote add origin https://github.com/alemeds/ws-elecciones
git push -u origin main
```

### 4. Deploy en Streamlit Cloud

1. Entrá a https://share.streamlit.io
2. **New app** → conectá tu repo `alemeds/ws-elecciones`
3. Branch: `main` / File: `app.py`
4. Clic en **Advanced settings → Secrets**
5. Pegá esto (reemplazando con tu JSON real):

```toml
ADMIN_PASSWORD = "wsgca2025"

GOOGLE_CREDENTIALS = '''
{
  "type": "service_account",
  "project_id": "...",
  ... (pegá el contenido completo del JSON)
}
'''
```

6. Clic en **Deploy** — en 2 minutos tenés la URL pública

## Uso

- **Votar**: los hermanos acceden a la URL y votan con su nombre
- **Administrar**: contraseña requerida — abrís/cerrás/reseteás cargos
- **Resultados**: contraseña requerida — ves votos en tiempo real con detección de empate

## Cambiar contraseña de administrador

En Streamlit Cloud → Settings → Secrets → cambiá el valor de `ADMIN_PASSWORD`
