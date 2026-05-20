"""YouTube upload utilities."""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from youtube.scheduler import format_date_for_youtube


def generate_title(titulo: str) -> str:
    """Format title for YouTube."""
    titulo = titulo.replace("_", " ").strip()
    return " ".join(word.capitalize() for word in titulo.split())


def generate_hashtags(titulo: str, tema: Optional[str] = None) -> str:
    """Generate relevant hashtags from title and theme."""
    titulo_clean = generate_title(titulo)
    stop_words = {"y", "de", "la", "el", "en", "un", "es", "al", "del", "lo", "su", "no", "una", "por", "con"}
    
    palabras = [p for p in titulo_clean.split() if len(p) > 3 and p.lower() not in stop_words]
    hashtags = [f"#{p}" for p in palabras[:3]]
    
    if tema:
        for p in tema.split():
            p = p.strip()
            if len(p) > 3:
                hashtag = f"#{p}"
                if hashtag not in hashtags:
                    hashtags.append(hashtag)
            if len(hashtags) >= 5:
                break
    
    if len(hashtags) < 3:
        hashtags.append("#AlmaNarradora")
    if len(hashtags) < 3:
        hashtags.append("#Reflexion")
    
    return " ".join(hashtags[:5])


def generate_description(titulo: str, tema: Optional[str] = None) -> str:
    """Generate complete description with hashtags."""
    titulo_display = generate_title(titulo)
    hashtags = generate_hashtags(titulo, tema)
    
    return (
        f"Alma Narradora - {titulo_display}\n\n"
        f"El peso de lo no dicho\n\n"
        f"{tema or ''}\n\n"
        f"{hashtags}"
    )


def upload_video(
    service: Any,
    video_path: str,
    title: str,
    description: str,
    category: str = "22",
    tags: Optional[List[str]] = None,
    fecha_programada: Optional[str] = None,
) -> Dict[str, Any]:
    """Upload video to YouTube with scheduling.
    
    Args:
        service: YouTube API service object.
        video_path: Path to video file.
        title: Video title.
        description: Video description.
        category: YouTube category ID.
        tags: List of tags.
        fecha_programada: Scheduled publish datetime.
    
    Returns:
        Dict with video_id and url.
    """
    publish_at = None
    if fecha_programada:
        publish_at = format_date_for_youtube(fecha_programada)
        if not publish_at:
            publish_at = None
    
    body = {
        "snippet": {
            "title": title,
            "description": description,
        },
        "status": {
            "privacyStatus": "private",
            "selfDeclaredMadeForKids": False,
        },
    }
    
    if publish_at:
        body["status"]["publishAt"] = publish_at
    
    if tags:
        body["snippet"]["tags"] = [t.strip() for t in tags if t.strip()]
    
    if category:
        body["snippet"]["categoryId"] = str(category)
    
    file_size = os.path.getsize(video_path)
    print(f"     Subiendo: {video_path} ({file_size / 1024 / 1024:.1f} MB)")
    
    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
    )
    
    insert_request = service.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media,
    )
    
    try:
        for _ in range(100):
            try:
                status, response = insert_request.next_chunk()
                if status:
                    pct = status.progress * 100
                    print(f"     Progreso: {pct:.1f}%")
                if response:
                    video_id = response["id"]
                    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                    print(f"     ✅ Subida completa!")
                    if fecha_programada:
                        print(f"     📅 Programado para: {fecha_programada}")
                    return {
                        "video_id": video_id,
                        "url": youtube_url,
                    }
            except HttpError as e:
                if e.resp.status in [200, 201]:
                    response = e.res
                    video_id = response["id"]
                    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                    return {
                        "video_id": video_id,
                        "url": youtube_url,
                    }
                elif e.resp.status >= 500 or e.resp.status == 403:
                    print(f"     ⚠️  Error {e.resp.status}, reintentando...")
                    continue
                else:
                    raise
            except Exception as e:
                print(f"     ⚠️  Error de conexión: {e}, reintentando...")
                continue
    
    except HttpError as e:
        error_msg = e.content.decode()
        print(f"  ❌ Error HTTP: {error_msg}")
        raise
    
    print("  ❌ Error: Timeout en subida")
    raise Exception("Timeout subiendo video")


def get_categories(service: Any) -> dict:
    """Get available YouTube categories."""
    try:
        response = service.videoCategories().list(
            part="snippet",
            regionCode="AR",
        ).execute()
        categories = {}
        for cat in response.get("items", []):
            categories[cat["id"]] = cat["snippet"]["title"]
        return categories
    except Exception as e:
        print(f"  ⚠️  Error obteniendo categorias: {e}")
        return {}
