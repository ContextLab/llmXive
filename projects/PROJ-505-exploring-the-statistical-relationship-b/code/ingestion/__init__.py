"""
Ingestion module for solar wind composition and geomagnetic indices data.

This package handles the downloading, parsing, and initial alignment of
time-series data from ACE/WIND and NOAA sources.
"""
from utils.mkdirs import ensure_dirs
import os
from pathlib import Path

def setup_ingestion_directories():
    """Ensure all required ingestion subdirectories exist."""
    base_path = Path(__file__).parent.parent.parent
    config = {
        'raw': base_path / 'data' / 'raw',
        'processed': base_path / 'data' / 'processed',
    }
    ensure_dirs(config)
    return config

# Execute directory setup on import if needed (idempotent)
# This ensures the directory structure exists for downstream tasks
try:
    setup_ingestion_directories()
except Exception:
    # Fail silently during import; let explicit scripts handle errors
    pass