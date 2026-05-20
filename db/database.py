"""Database connection and operations."""

import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from db.models import Channel, Narracion, YoutubeVideo, FacebookVideo


@contextmanager
def get_db_connection(db_path: str):
    """Context manager for database connections."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: str) -> str:
    """Initialize database with schema."""
    db_path = Path(db_path)
    schema_path = db_path.parent / "schema.sql"
    
    if not db_path.exists():
        with open(schema_path, "r") as f:
            schema = f.read()
        
        with get_db_connection(db_path) as conn:
            conn.executescript(schema)
        
        return str(db_path)
    
    return str(db_path)


def add_channel(conn: sqlite3.Connection, nombre: str, client_secret_path: str = None, token_path: str = None) -> int:
    """Add a YouTube channel."""
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO canales (nombre, plataforma, client_secret_path, token_path)
           VALUES (?, 'youtube', ?, ?)""",
        (nombre, client_secret_path, token_path),
    )
    conn.commit()
    return cursor.lastrowid


def get_channel_by_id(conn: sqlite3.Connection, channel_id: int) -> Optional[Dict[str, Any]]:
    """Get channel by ID."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM canales WHERE id = ?", (channel_id,))
    row = cursor.fetchone()
    return dict(row) if row else None


def get_active_channels(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Get all active channels."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM canales WHERE activo = 1")
    return [dict(row) for row in cursor.fetchall()]


def get_pending_videos(conn: sqlite3.Connection, canal_id: int = None) -> List[Dict[str, Any]]:
    """Get videos ready for upload."""
    cursor = conn.cursor()
    
    if canal_id:
        query = """
            SELECT n.*, c.nombre as canal_nombre
            FROM narraciones n
            JOIN canales c ON n.canal_id = c.id
            WHERE n.estado = 'video_done'
            AND n.canal_id = ?
            AND NOT EXISTS (
                SELECT 1 FROM youtube_videos yv
                WHERE yv.narracion_id = n.id
                AND yv.estado_subida IN ('published', 'uploading', 'scheduled')
            )
            ORDER BY n.creado_en ASC
        """
        videos = cursor.execute(query, (canal_id,)).fetchall()
    else:
        query = """
            SELECT n.*, c.nombre as canal_nombre
            FROM narraciones n
            JOIN canales c ON n.canal_id = c.id
            WHERE n.estado = 'video_done'
            AND NOT EXISTS (
                SELECT 1 FROM youtube_videos yv
                WHERE yv.narracion_id = n.id
                AND yv.estado_subida IN ('published', 'uploading', 'scheduled')
            )
            ORDER BY n.creado_en ASC
        """
        videos = cursor.execute(query).fetchall()
    
    return [dict(row) for row in videos]


def mark_uploading(conn: sqlite3.Connection, narracion_id: int, fecha_programada: str = None) -> None:
    """Mark narration as uploading."""
    from datetime import datetime
    now = datetime.now().isoformat()
    
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE narraciones SET estado = 'uploading', fecha_programada = ?, actualizado_en = ? WHERE id = ?",
        (fecha_programada, now, narracion_id),
    )
    cursor.execute(
        """INSERT INTO youtube_videos (narracion_id, estado_subida, fecha_programada, fecha_subida)
           VALUES (?, 'uploading', ?, ?)""",
        (narracion_id, fecha_programada, now),
    )
    conn.commit()


def mark_published(conn: sqlite3.Connection, narracion_id: int, video_id: str, youtube_url: str, fecha_programada: str = None) -> None:
    """Mark narration as published."""
    from datetime import datetime
    now = datetime.now().isoformat()
    
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE narraciones SET estado = 'published', fecha_programada = ?, actualizado_en = ? WHERE id = ?",
        (fecha_programada, now, narracion_id),
    )
    cursor.execute(
        """UPDATE youtube_videos
           SET video_id = ?, youtube_url = ?, estado_subida = 'published', fecha_subida = ?
           WHERE narracion_id = ? AND estado_subida = 'uploading'""",
        (video_id, youtube_url, now, narracion_id),
    )
    conn.commit()


def mark_failed(conn: sqlite3.Connection, narracion_id: int, error_msg: str) -> None:
    """Mark narration as failed."""
    from datetime import datetime
    now = datetime.now().isoformat()
    
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE narraciones SET estado = 'failed', actualizado_en = ? WHERE id = ?",
        (now, narracion_id),
    )
    cursor.execute(
        """UPDATE youtube_videos
           SET estado_subida = 'failed', error_msg = ?
           WHERE narracion_id = ? AND estado_subida = 'uploading'""",
        (error_msg, narracion_id),
    )
    conn.commit()


def get_video_status(conn: sqlite3.Connection, narracion_id: int) -> Optional[Dict[str, Any]]:
    """Get video upload status."""
    cursor = conn.cursor()
    cursor.execute(
        """SELECT yv.*, n.titulo, n.estado as narracion_estado
           FROM youtube_videos yv
           JOIN narraciones n ON yv.narracion_id = n.id
           WHERE yv.narracion_id = ?""",
        (narracion_id,),
    )
    row = cursor.fetchone()
    return dict(row) if row else None


def get_scheduled_videos(conn: sqlite3.Connection, canal_id: int = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Get scheduled and published videos."""
    cursor = conn.cursor()
    
    if canal_id:
        query = """
            SELECT n.*, yv.video_id, yv.youtube_url, yv.estado_subida, yv.fecha_programada
            FROM narraciones n
            LEFT JOIN youtube_videos yv ON n.id = yv.narracion_id
            WHERE n.canal_id = ?
            AND n.fecha_programada IS NOT NULL
            AND n.estado IN ('scheduled', 'published')
            ORDER BY n.fecha_programada ASC
            LIMIT ?
        """
        rows = cursor.execute(query, (canal_id, limit)).fetchall()
    else:
        query = """
            SELECT n.*, yv.video_id, yv.youtube_url, yv.estado_subida, yv.fecha_programada
            FROM narraciones n
            LEFT JOIN youtube_videos yv ON n.id = yv.narracion_id
            WHERE n.fecha_programada IS NOT NULL
            AND n.estado IN ('scheduled', 'published')
            ORDER BY n.fecha_programada ASC
            LIMIT ?
        """
        rows = cursor.execute(query, (limit,)).fetchall()
    
    return [dict(row) for row in rows]


def get_upload_history(conn: sqlite3.Connection, limit: int = 50) -> List[Dict[str, Any]]:
    """Get upload history."""
    cursor = conn.cursor()
    cursor.execute(
        """SELECT n.id, n.titulo, n.archivo_mp4, n.creado_en, n.actualizado_en,
                  c.nombre as canal_nombre,
                  yv.video_id, yv.youtube_url, yv.estado_subida, yv.fecha_programada
           FROM narraciones n
           JOIN canales c ON n.canal_id = c.id
           LEFT JOIN youtube_videos yv ON n.id = yv.narracion_id
           WHERE n.estado IN ('published', 'failed')
           ORDER BY n.actualizado_en DESC
           LIMIT ?""",
        (limit,),
    )
    return [dict(row) for row in cursor.fetchall()]


def check_video_uploaded(conn: sqlite3.Connection, video_path: str) -> Optional[Dict[str, Any]]:
    """Check if a video file was already uploaded."""
    cursor = conn.cursor()
    cursor.execute(
        """SELECT n.id, n.titulo, n.archivo_mp4, yv.video_id, yv.youtube_url, 
                  yv.estado_subida, yv.fecha_programada, yv.fecha_subida
           FROM narraciones n
           LEFT JOIN youtube_videos yv ON n.id = yv.narracion_id
           WHERE n.archivo_mp4 = ?
           AND yv.estado_subida IN ('published', 'uploading', 'scheduled')""",
        (video_path,),
    )
    row = cursor.fetchone()
    return dict(row) if row else None
