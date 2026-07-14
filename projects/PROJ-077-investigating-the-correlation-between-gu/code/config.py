"""
Configuration Module.
Defines paths, random seeds, and limits.
"""
import os
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Paths
INPUT_PATHS = {
    'microbiome': str(PROJECT_ROOT / 'data' / 'raw' / 'microbiome_data.csv'),
    'cognitive': str(PROJECT_ROOT / 'data' / 'raw' / 'cognitive_data.csv'),
    'dietary': str(PROJECT_ROOT / 'data' / 'raw' / 'dietary_data.csv')
}

RANDOM_SEED = 42
SAMPLE_LIMIT = 50000

def ensure_directories():
    """Creates required directories if they don't exist."""
    dirs = [
        PROJECT_ROOT / 'data' / 'raw',
        PROJECT_ROOT / 'data' / 'processed',
        PROJECT_ROOT / 'code',
        PROJECT_ROOT / 'tests'
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
