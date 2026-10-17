import logging
from pathlib import Path
from llmxive_toolkit import paths

def get_project_paths():
    return {
        "root": paths.root,
        "raw": paths.data("raw"),
        "processed": paths.data("processed"),
        "logs": paths.data("logs"),
        "figures": paths.figures(),
    }

def ensure_directories():
    p = get_project_paths()
    for folder in p.values():
        folder.mkdir(parents=True, exist_ok=True)

OUTLIER_TOLERANCE = 0.05
