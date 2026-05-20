"""Scheduler for YouTube video publishing."""

import os
from datetime import datetime, timedelta
from typing import List, Optional
import pytz


TIMEZONE = os.environ.get("TIMEZONE", "America/Bogota")
zona_local = pytz.timezone(TIMEZONE)
YOUTUBE_VIDEOS_PER_DAY = int(os.environ.get("YOUTUBE_VIDEOS_PER_DAY", "6"))
YOUTUBE_SCHEDULES = [h.strip() for h in os.environ.get("YOUTUBE_SCHEDULES", "08:00,12:00,16:00,18:00,20:00,22:00").split(",")]


def calculate_next_schedule(
    scheduled_videos: List[dict],
    offset: int = 0,
) -> str:
    """Calculate next available schedule slot.
    
    Args:
        scheduled_videos: List of already scheduled videos with 'fecha_programada' key.
        offset: Position in available slots.
    
    Returns:
        ISO format datetime string for next available slot.
    """
    ahora_local = zona_local.localize(datetime.now())
    dia_actual = ahora_local.date()
    
    # Get occupied slots from DB
    ocupados = set()
    for video in scheduled_videos:
        fecha = video.get("fecha_programada")
        if fecha:
            try:
                dt = datetime.strptime(fecha, "%Y-%m-%d %H:%M:%S")
                ocupados.add((dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M")))
            except (ValueError, TypeError):
                pass
    
    # Search for available slots in next 30 days
    for dias_en_futuro in range(30):
        fecha_actual = dia_actual + timedelta(days=dias_en_futuro)
        fecha_str = fecha_actual.strftime("%Y-%m-%d")
        
        # Build available slots for this day
        disponibles = []
        for hora in YOUTUBE_SCHEDULES:
            if (fecha_str, hora) in ocupados:
                continue
            
            fecha_programada = f"{fecha_str} {hora}:00"
            fecha_dt = zona_local.localize(datetime.strptime(fecha_programada, "%Y-%m-%d %H:%M:%S"))
            
            if fecha_dt > ahora_local:
                disponibles.append(fecha_programada)
        
        # Assign slot if available
        if len(disponibles) > offset:
            return disponibles[offset]
        
        offset -= len(disponibles)
    
    # Fallback: first slot in 30 days
    fecha_final = dia_actual + timedelta(days=30)
    return f"{fecha_final} {YOUTUBE_SCHEDULES[0]}:00"


def format_date_for_youtube(fecha_str: str) -> Optional[str]:
    """Convert local datetime to UTC for YouTube API.
    
    Args:
        fecha_str: Local datetime string (YYYY-MM-DD HH:MM:SS).
    
    Returns:
        UTC datetime string for YouTube API or None if invalid.
    """
    try:
        dt_local = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
        ahora_local = zona_local.localize(datetime.now())
        dt_local_local = zona_local.localize(dt_local)
        
        if dt_local_local < ahora_local:
            return None
        
        if (dt_local_local - ahora_local).total_seconds() < 1800:
            return None
        
        dt_utc = dt_local_local.astimezone(pytz.utc)
        return dt_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    except Exception:
        return None


def get_schedules_for_day(fecha_str: str, occupied: set) -> List[str]:
    """Get available schedules for a specific day.
    
    Args:
        fecha_str: Date string (YYYY-MM-DD).
        occupied: Set of occupied (date, time) tuples.
    
    Returns:
        List of available time slots.
    """
    disponibles = []
    for hora in YOUTUBE_SCHEDULES:
        if (fecha_str, hora) not in occupied:
            disponibles.append(f"{fecha_str} {hora}:00")
    return disponibles
