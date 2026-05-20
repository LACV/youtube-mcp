"""
MCP Server para subir videos programados a YouTube.

Proyecto: Alma Narradora - YouTube MCP Server
Autor: LACV
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Cargar variables de entorno
load_dotenv()

# Configuración
YOUTUBE_CLIENT_SECRET_PATH = os.environ.get("YOUTUBE_CLIENT_SECRET_PATH")
YOUTUBE_TOKEN_PATH = os.environ.get("YOUTUBE_TOKEN_PATH")
YOUTUBE_DB_PATH = os.environ.get("YOUTUBE_DB_PATH", "/home/sistemas/Dev/MCP/alma-narradora/youtube/alma_narradora.db")
YOUTUBE_NARRATIONS_DIR = os.environ.get("YOUTUBE_NARRATIONS_DIR", "/home/sistemas/Dev/MCP/alma-narradora/narraciones")
TIMEZONE = os.environ.get("TIMEZONE", "America/Bogota")

# Crear el servidor MCP
mcp = FastMCP("youtube-video-upload", json_response=True)


def get_db_path():
    """Obtener ruta de la base de datos."""
    return YOUTUBE_DB_PATH


def get_credentials():
    """Obtener credenciales de YouTube."""
    from youtube.auth import authenticate
    if not YOUTUBE_CLIENT_SECRET_PATH or not YOUTUBE_TOKEN_PATH:
        raise ValueError("YOUTUBE_CLIENT_SECRET_PATH y YOUTUBE_TOKEN_PATH deben estar configurados")
    return authenticate(YOUTUBE_CLIENT_SECRET_PATH, YOUTUBE_TOKEN_PATH)


@mcp.tool()
async def youtube_upload_video(
    video_path: str,
    title: str = "",
    description: str = "",
    primary_hashtags: str = "",
    scheduled_publish_time: str = "",
    published: bool = False
) -> dict:
    """
    Sube un video a YouTube y lo programa para publicar.
    
    Args:
        video_path: Ruta absoluta al archivo de video (mp4).
        title: Título del video. Si no se proporciona, se genera desde el nombre del archivo.
        description: Descripción del video. Si no se proporciona, se genera automáticamente.
        primary_hashtags: Hashtags separados por coma. Si no se proporcionan, se generan automáticamente.
        scheduled_publish_time: Fecha/hora de programación en formato ISO 8601.
                               Si no se proporciona, se programa automáticamente.
        published: Si es True, publica inmediatamente. Si es False, programa la publicación.
    
    Returns:
        Dict con el video_id, status y URL del video subido.
    """
    from youtube.upload import generate_title, generate_hashtags, generate_description, upload_video
    from db.database import get_db_connection, check_video_uploaded, mark_uploading, mark_published, mark_failed
    
    # Validar archivo
    if not os.path.isfile(video_path):
        return {"error": f"El archivo no existe: {video_path}", "status": "failed"}
    
    video_extensions = ['.mp4', '.mov', '.avi', '.wmv', '.flv', '.mkv', '.webm']
    _, ext = os.path.splitext(video_path)
    if ext.lower() not in video_extensions:
        return {"error": f"Formato inválido: {ext}", "status": "failed"}
    
    # Verificar duplicados
    with get_db_connection(get_db_path()) as conn:
        duplicate = check_video_uploaded(conn, video_path)
        if duplicate:
            return {
                "already_uploaded": True,
                "video_id": duplicate.get("video_id"),
                "youtube_url": duplicate.get("youtube_url"),
                "status": "duplicate"
            }
    
    # Generar metadata
    if not title:
        title = generate_title(Path(video_path).stem)
    if not description:
        description = generate_description(title)
    if not primary_hashtags:
        primary_hashtags = generate_hashtags(title)
    
    try:
        # Autenticar
        creds = get_credentials()
        if not creds:
            return {"error": "Error de autenticación con YouTube", "status": "failed"}
        
        from googleapiclient.discovery import build
        service = build("youtube", "v3", credentials=creds)
        
        # Calcular horario
        if scheduled_publish_time:
            from youtube.scheduler import format_date_for_youtube
            publish_at = format_date_for_youtube(scheduled_publish_time)
            if not publish_at and not published:
                return {"error": "Fecha inválida", "status": "failed"}
        else:
            publish_at = None
        
        # Subir video
        result = upload_video(
            service=service,
            video_path=video_path,
            title=title,
            description=description,
            tags=[h.lstrip('#') for h in primary_hashtags.split(',') if h.strip()] if primary_hashtags else None,
            fecha_programada=scheduled_publish_time if scheduled_publish_time else None,
        )
        
        with get_db_connection(get_db_path()) as conn:
            mark_published(
                conn,
                narracion_id=0,
                video_id=result["video_id"],
                youtube_url=result["url"],
                fecha_programada=scheduled_publish_time
            )
        
        return {
            "video_id": result["video_id"],
            "youtube_url": result["url"],
            "title": title,
            "description": description[:200] + "..." if len(description) > 200 else description,
            "primary_hashtags": primary_hashtags,
            "scheduled_publish_time": scheduled_publish_time,
            "status": "scheduled" if not published else "published",
            "message": f"Video subido exitosamente. Programado para: {scheduled_publish_time or 'inmediatamente'}"
        }
    
    except Exception as e:
        error_msg = str(e)[:200]
        print(f"Error uploading video: {error_msg}")
        return {"error": error_msg, "status": "failed"}


@mcp.tool()
async def youtube_schedule_all_videos(
    narrations_dir: str = "",
    primary_hashtags: str = "",
    gap_hours: float = 4.0,
    published: bool = False
) -> dict:
    """
    Sube todos los videos pendientes de la carpeta de narraciones con distribución automática.
    
    Args:
        narrations_dir: Ruta a la carpeta de narraciones. Si no se proporciona, usa la configurada.
        primary_hashtags: Hashtags separados por coma. Si no se proporcionan, se generan automáticamente.
        gap_hours: Horas mínimo entre cada video (por defecto: 4).
        published: Si es True, publica todos inmediatamente. Si es False, programa los videos.
    
    Returns:
        Dict con el resultado de cada video subido.
    """
    from youtube.upload import generate_title, generate_hashtags, generate_description, upload_video
    from youtube.scheduler import calculate_next_schedule
    from db.database import get_db_connection, get_pending_videos, mark_uploading, mark_published, mark_failed
    
    narrations_dir = narrations_dir or YOUTUBE_NARRATIONS_DIR
    if not os.path.isdir(narrations_dir):
        return {"error": f"Directorio no encontrado: {narrations_dir}", "status": "failed"}
    
    # Encontrar videos pendientes
    with get_db_connection(get_db_path()) as conn:
        videos = get_pending_videos(conn)
    
    if not videos:
        return {"message": "No hay videos pendientes para subir", "status": "success"}
    
    # Autenticar
    creds = get_credentials()
    if not creds:
        return {"error": "Error de autenticación con YouTube", "status": "failed"}
    
    from googleapiclient.discovery import build
    service = build("youtube", "v3", credentials=creds)
    
    results = []
    errors = []
    skipped = []
    
    # Obtener videos ya programados
    scheduled_videos = []
    with get_db_connection(get_db_path()) as conn:
        scheduled_videos = [
            {"fecha_programada": v.get("fecha_programada")}
            for v in get_pending_videos(conn) if v.get("fecha_programada")
        ]
    
    for i, video in enumerate(videos):
        video_path = video.get("archivo_mp4")
        if not video_path or not os.path.isfile(video_path):
            errors.append({"video": video.get("titulo"), "error": "Archivo no encontrado"})
            continue
        
        # Verificar duplicados
        with get_db_connection(get_db_path()) as conn:
            duplicate = check_video_uploaded(conn, video_path)
            if duplicate:
                skipped.append({
                    "video": video.get("titulo"),
                    "video_id": duplicate.get("video_id"),
                    "url": duplicate.get("youtube_url")
                })
                continue
        
        title = generate_title(video.get("titulo", ""))
        description = generate_description(title, video.get("tema"))
        
        if not primary_hashtags:
            primary_hashtags_for_video = generate_hashtags(title, video.get("tema"))
        else:
            primary_hashtags_for_video = primary_hashtags
        
        # Calcular horario
        offset = i
        scheduled_time = calculate_next_schedule(scheduled_videos, offset)
        
        try:
            result = upload_video(
                service=service,
                video_path=video_path,
                title=title,
                description=description,
                tags=[h.lstrip('#') for h in primary_hashtags_for_video.split(',') if h.strip()],
                fecha_programada=scheduled_time,
            )
            
            with get_db_connection(get_db_path()) as conn:
                mark_published(
                    conn,
                    narracion_id=video["id"],
                    video_id=result["video_id"],
                    youtube_url=result["url"],
                    fecha_programada=scheduled_time
                )
            
            results.append({
                "video": video.get("titulo"),
                "video_id": result["video_id"],
                "youtube_url": result["url"],
                "scheduled_time": scheduled_time,
                "status": "scheduled" if not published else "published"
            })
        
        except Exception as e:
            error_msg = str(e)[:200]
            errors.append({"video": video.get("titulo"), "error": error_msg})
    
    return {
        "total_videos": len(videos),
        "successful": len(results),
        "failed": len(errors),
        "skipped": len(skipped),
        "results": results,
        "errors": errors,
        "skipped_videos": skipped,
        "status": "completed_with_errors" if errors else ("success" if results else "failed")
    }


@mcp.tool()
async def youtube_get_video_status(video_id: str) -> dict:
    """
    Consulta el estado de un video en YouTube.
    
    Args:
        video_id: El ID del video de YouTube.
    
    Returns:
        Dict con el estado actual del video.
    """
    from db.database import get_db_connection, get_scheduled_videos
    
    with get_db_connection(get_db_path()) as conn:
        videos = get_scheduled_videos(conn)
    
    for video in videos:
        if video.get("video_id") == video_id:
            return {
                "video_id": video_id,
                "title": video.get("titulo"),
                "status": video.get("estado_subida"),
                "scheduled_time": video.get("fecha_programada"),
                "youtube_url": video.get("youtube_url"),
                "message": f"Estado: {video.get('estado_subida')}"
            }
    
    return {"error": f"Video {video_id} no encontrado", "status": "not_found"}


@mcp.tool()
async def youtube_list_scheduled_videos() -> dict:
    """
    Lista los videos programados y publicados en YouTube.
    
    Returns:
        Dict con la lista de videos programados.
    """
    from db.database import get_db_connection, get_scheduled_videos
    
    with get_db_connection(get_db_path()) as conn:
        videos = get_scheduled_videos(conn)
    
    return {
        "scheduled_videos": videos,
        "total_scheduled": len(videos),
        "message": f"Total de videos programados/publicados: {len(videos)}"
    }


@mcp.tool()
async def youtube_check_duplicates(video_paths: list) -> dict:
    """
    Verifica cuáles videos ya fueron subidos a YouTube.
    
    Args:
        video_paths: Lista de rutas absolutas a los archivos de video.
    
    Returns:
        Dict con el estado de cada video.
    """
    from db.database import get_db_connection
    
    results = {
        "total": len(video_paths),
        "already_uploaded": [],
        "not_uploaded": []
    }
    
    with get_db_connection(get_db_path()) as conn:
        for video_path in video_paths:
            check = check_video_uploaded(conn, video_path)
            if check:
                results["already_uploaded"].append({
                    "file_path": video_path,
                    "title": check.get("titulo"),
                    "video_id": check.get("video_id"),
                    "youtube_url": check.get("youtube_url"),
                    "upload_date": check.get("fecha_subida")
                })
            else:
                results["not_uploaded"].append({"file_path": video_path})
    
    return results


@mcp.tool()
async def youtube_get_upload_history() -> dict:
    """
    Muestra el historial completo de subidas a YouTube.
    
    Returns:
        Dict con el historial de subidas.
    """
    from db.database import get_db_connection, get_upload_history
    
    with get_db_connection(get_db_path()) as conn:
        history = get_upload_history(conn)
    
    return {
        "total_uploads": len(history),
        "uploads": history
    }


if __name__ == "__main__":
    mcp.run()
