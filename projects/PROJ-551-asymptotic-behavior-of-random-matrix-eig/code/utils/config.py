import logging
from pathlib import Path

def get_project_paths():
    root = Path(__file__).resolve().parent.parent
    return {
        'root': root,
        'raw': root / 'data/raw',
        'processed': root / 'data/processed',
        'results': root / 'data/results',
        'figures': root / 'data/figures',
        'logs': root / 'data/logs',
        'contracts': root / 'contracts'
    }

def ensure_directories():
    paths = get_project_paths()
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)

def get_outlier_tolerance():
    return 1e-10
