# MCP Server - YouTube Video Upload

Servidor MCP para subir y programar videos automáticamente en YouTube.

## 📁 Estructura del Proyecto

```
/home/sistemas/Dev/mcp-servers/youtube-mcp/
├── .env                          # Credenciales (NO compartir)
├── .env.example                  # Plantilla del .env
├── requirements.txt              # Dependencias Python
├── mcp_server.py                 # Servidor MCP principal
├── youtube/
│   ├── __init__.py
│   ├── auth.py                   # Autenticación OAuth 2.0
│   ├── upload.py                 # Lógica de subida a YouTube
│   └── scheduler.py              # Programación de horarios
├── db/
│   ├── __init__.py
│   ├── models.py                 # Modelos Pydantic
│   └── database.py               # Conexión y operaciones SQLite
└── tests/
    ├── __init__.py
    └── test_upload.py
```

## 🚀 Instalación

```bash
cd /home/sistemas/Dev/mcp-servers/youtube-mcp
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## ⚙️ Configuración

### Archivo `.env`

```env
YOUTUBE_CLIENT_SECRET_PATH=/home/sistemas/Dev/MCP/alma-narradora/youtube/client_secret_pipo_reflexiona.json
YOUTUBE_TOKEN_PATH=/home/sistemas/Dev/MCP/alma-narradora/youtube/token_2.json
YOUTUBE_DB_PATH=/home/sistemas/Dev/MCP/alma-narradora/youtube/alma_narradora.db
YOUTUBE_NARRATIONS_DIR=/home/sistemas/Dev/MCP/alma-narradora/narraciones
TIMEZONE=America/Bogota
YOUTUBE_VIDEOS_PER_DAY=6
YOUTUBE_SCHEDULES=08:00,12:00,16:00,18:00,20:00,22:00
```

## 🛠️ Herramientas Disponibles

### 1. `youtube_upload_video`
Sube un video individual con metadata automática.

**Parámetros:**
- `video_path` (obligatorio): Ruta al archivo de video
- `title`: Título (auto-generado si no se proporciona)
- `description`: Descripción (auto-generada si no se proporciona)
- `primary_hashtags`: Hashtags (auto-generados si no se proporcionan)
- `scheduled_publish_time`: Fecha/hora en formato ISO 8601
- `published`: `true` para publicar inmediatamente, `false` para programar

### 2. `youtube_schedule_all_videos`
Sube TODOS los videos pendientes con distribución automática.

**Parámetros:**
- `narrations_dir`: Carpeta de narraciones
- `primary_hashtags`: Hashtags (auto-generados)
- `gap_hours`: Horas entre videos (por defecto: 4)
- `published`: `true` o `false`

### 3. `youtube_get_video_status`
Consulta el estado de subida de un video.

**Parámetros:**
- `video_id`: El ID del video de YouTube

### 4. `youtube_list_scheduled_videos`
Lista los videos programados y publicados.

**Ejemplo:**
```
¿Qué videos tengo ya programados en YouTube?
```

### 5. `youtube_check_duplicates`
Verifica cuáles videos ya fueron subidos.

**Parámetros:**
- `video_paths`: Lista de rutas a los videos

### 6. `youtube_get_upload_history`
Muestra el historial completo de subidas.

**Ejemplo:**
```
¿Qué videos he subido a YouTube?
```

## 📅 Horarios Automáticos

Por defecto, los videos se programan en estos horarios:
- 08:00 AM
- 12:00 PM
- 04:00 PM
- 06:00 PM
- 08:00 PM
- 10:00 PM

## 📝 Generación Automática de Metadata

### Títulos
Se generan automáticamente desde el nombre del archivo.

### Descripciones
Genera descripción completa con:
- Título formateado
- Frase "El peso de lo no dicho"
- Tema del video
- Hashtags relevantes

### Hashtags
Generados automáticamente desde el título y tema.

## 📊 Control de Duplicados

El sistema usa SQLite para tracking completo:
- Ruta del archivo
- Video ID de YouTube
- URL del video
- Estado de subida
- Fecha de programación
- Fecha de subida

## 🎯 Comandos de Uso

### Subir un video individual
```
Sube /home/sistemas/Dev/MCP/alma-narradora/narraciones/El_Cuchillo_en_la_Sombra/El_Cuchillo_en_la_Sombra.mp4 a YouTube
```

### Subir todos los videos
```
Sube todos los videos de narraciones a YouTube
```

### Verificar duplicados
```
Verifica si estos videos ya fueron subidos a YouTube
```

### Ver historial
```
¿Qué videos he subido a YouTube?
```

## 🔧 Mantenimiento

### Rotar Token de YouTube
Los tokens expiran en 60 días. Para renovar:
1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Generar nuevo OAuth 2.0 client secret
3. Actualizar `.env` y `opencode.json`

### Verificar estado de videos
```
Consulta el estado del video [video_id]
```

## ⚠️ Limitaciones

- Formato de video: mp4, mov, avi, wmv, flv, mkv, webm
- Tamaño máximo: 128 GB (YouTube)
- Duración máxima: 12 horas
- Los videos se suben como privados y se programan

## 🔗 Enlaces Útiles

- [Google Cloud Console](https://console.cloud.google.com/)
- [YouTube Data API Docs](https://developers.google.com/youtube/v3)
- [Documentación MCP](https://modelcontextprotocol.io/)
