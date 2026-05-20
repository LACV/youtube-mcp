"""Pydantic models for YouTube database."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Channel(BaseModel):
    """Canal de YouTube."""
    id: Optional[int] = None
    nombre: str
    plataforma: str = "youtube"
    channel_id: Optional[str] = None
    client_secret_path: Optional[str] = None
    token_path: Optional[str] = None
    activo: int = 1
    creado_en: Optional[str] = None


class Narracion(BaseModel):
    """Narracion con metadata."""
    id: Optional[int] = None
    titulo: str
    tema: Optional[str] = None
    canal_id: Optional[int] = None
    estado: str = "pending"
    archivo_txt: Optional[str] = None
    archivo_wav: Optional[str] = None
    archivo_mp4: Optional[str] = None
    duracion_segundos: Optional[float] = None
    palabra_clave: Optional[str] = None
    tags: Optional[str] = None
    descripcion: Optional[str] = None
    categoria_youtube: Optional[str] = None
    thumbnail_path: Optional[str] = None
    creado_en: Optional[str] = None
    actualizado_en: Optional[str] = None
    fecha_programada: Optional[str] = None


class YoutubeVideo(BaseModel):
    """Video subido a YouTube."""
    id: Optional[int] = None
    narracion_id: int
    video_id: Optional[str] = None
    youtube_url: Optional[str] = None
    estado_subida: str = "pending"
    fecha_programada: Optional[str] = None
    fecha_subida: Optional[str] = None
    error_msg: Optional[str] = None
    creado_en: Optional[str] = None


class FacebookVideo(BaseModel):
    """Video subido a Facebook."""
    id: Optional[int] = None
    narracion_id: int
    video_id: Optional[str] = None
    facebook_url: Optional[str] = None
    video_path: Optional[str] = None
    video_hash: Optional[str] = None
    estado: str = "pending"
    fecha_subida: Optional[str] = None
    error_msg: Optional[str] = None
    creado_en: Optional[str] = None
