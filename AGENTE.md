# YouTube Video Publisher Agent

Agente automatizado para publicar videos en YouTube desde las narraciones de Alma Narradora.

## 🎯 Función

Este agente se encarga automáticamente de:
1. Escanear la carpeta de narraciones
2. Verificar cuáles videos ya fueron subidos a YouTube
3. Subir los videos restantes con distribución inteligente de horarios
4. Generar títulos, descripciones y hashtags automáticamente
5. Programar 6 videos por día en horarios óptimos (8AM, 12PM, 4PM, 6PM, 8PM, 10PM)

## 📁 Ubicación de Videos

```
/home/sistemas/Dev/MCP/alma-narradora/narraciones/
```

Cada video está en una carpeta con su título:
```
narraciones/
├── El_Cuchillo_en_la_Sombra/
│   ├── El_Cuchillo_en_la_Sombra.mp4
│   └── El_Cuchillo_en_la_Sombra.txt
├── El_Silencio_Más_Profundo/
│   ├── El_Silencio_Más_Profundo.mp4
│   └── El_Silencio_Más_Profundo.txt
└── ...
```

## 🚀 Cómo Usar

### Opción 1: Comando Directo (Recomendado)

Simplemente dile al agente:

```
Sube todos los videos de narraciones a YouTube
```

O:

```
Publica todos los videos disponibles en YouTube
```

El agente automáticamente:
- Escanea la carpeta
- Verifica duplicados
- Sube los videos con distribución de 6 por día
- Muestra el resultado

### Opción 2: Subida Individual

```
Sube El_Cuchillo_en_la_Sombra.mp4 a YouTube
```

### Opción 3: Subida Parcial

```
Sube 3 videos de narraciones, programa uno cada 4 horas
```

## 📅 Programación Automática

El agente distribuye los videos así:

| Video | Hora |
|-------|------|
| 1 | 8:00 AM |
| 2 | 12:00 PM |
| 3 | 4:00 PM |
| 4 | 6:00 PM |
| 5 | 8:00 PM |
| 6 | 10:00 PM |

## 📊 Estado del Proceso

Para ver el progreso:

```
¿Qué videos tengo ya programados en YouTube?
¿Cuántos videos me quedan por subir?
¿Cuál es el estado de subida?
```

## 🔄 Flujo de Trabajo

1. **Escaneo**: El agente busca todos los `.mp4` en `/home/sistemas/Dev/MCP/alma-narradora/narraciones/`
2. **Filtrado**: Verifica cuáles ya fueron subidos usando la base de datos SQLite
3. **Distribución**: Asigna 6 videos por día en los horarios óptimos
4. **Subida**: Usa el MCP server para subir cada video con:
   - Título automático desde el nombre del archivo
   - Descripción resumida del archivo `.txt`
   - Hashtags automáticos generados desde el título
5. **Registro**: Guarda el historial en la base de datos SQLite

## ⚙️ Configuración del Agente

El agente usa el MCP Server configurado en:
```
/home/sistemas/.config/opencode/opencode.json
```

Herramienta: `youtube-video-upload`

## 📋 Ejemplos de Uso

### Subir todos los videos
```
Sube todos los videos de narraciones a YouTube
```

### Subir solo los videos de hoy
```
Programa 6 videos para hoy empezando a las 8AM
```

### Verificar estado
```
¿Cuántos videos tengo programados para esta semana?
```

### Ver historial completo
```
¿Qué videos he subido a YouTube?
```

## 🎨 Metadata Automática

### Títulos
- Se generan desde el nombre del archivo
- Ejemplo: `El_Cuchillo_en_la_Sombra.mp4` → "El Cuchillo En La Sombra"

### Descripciones
- Lee el archivo `.txt` junto al video
- Incluye: título, frase "El peso de lo no dicho", tema, hashtags
- Máximo 4000 caracteres (límite de YouTube)

### Hashtags
- Generados automáticamente desde el título y tema
- Incluye tags comunes del nicho
- Ejemplo: `#Cuchillo #Sombra #AlmaNarradora #Reflexion`

## ⚠️ Notas Importantes

1. **Tokens**: Los tokens de Google expiran en 60 días
2. **Duplicados**: El sistema detecta automáticamente videos ya subidos
3. **Horarios**: Los videos se programan en bloques de 6 por día
4. **Formatos**: Solo acepta mp4, mov, avi, wmv, flv, mkv, webm
5. **Tamaño**: Máximo 128 GB por video

## 🔧 Troubleshooting

### Error de conexión
Verifica que el MCP server esté corriendo:
```bash
cd /home/sistemas/Dev/mcp-servers/youtube-mcp
source venv/bin/activate
python mcp_server.py
```

### Token expirado
Genera un nuevo token en [Google Cloud Console](https://console.cloud.google.com/)

### Video no subido
Verifica el historial:
```
¿Cuál es el estado del video con ID [video_id]?
```
