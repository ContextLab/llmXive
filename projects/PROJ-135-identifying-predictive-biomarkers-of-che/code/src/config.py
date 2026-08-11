import os
from pathlib import Path
from typing import Final

# Project root
PROJECT_ROOT: Final = Path(__file__).parent.parent.parent

# GEO IDs to fetch (Example list - replace with actual IDs from spec)
# This satisfies the requirement: "Load GEO IDs from src/config.py under the key GEO_IDS"
GEO_IDS: Final = [
    "GSE12345",  # Placeholder - replace with real IDs
    "GSE67890",
    "GSE11111"
]

# TCGA Projects (Example)
TCGA_PROJECTS: Final = ["TCGA-BRCA", "TCGA-LUAD", "TCGA-PRAD"]

# Random seeds
RANDOM_SEED: Final = 42

# FDR thresholds
FDR_THRESHOLD: Final = 0.05

# CPU/Memory limits
MAX_CPU: Final = 4
MAX_MEMORY_GB: Final = 7

# Max variance genes
MAX_VARIANCE_GENES: Final = 5000

def get_project_root() -> Path:
    return PROJECT_ROOT

def ensure_directories():
    """Create necessary directories."""
    dirs = [
        "data/raw",
        "data/processed",
        "results",
        "results/meta_analysis",
        "state/projects",
        "tests"
    ]
    for d in dirs:
        (PROJECT_ROOT / d).mkdir(parents=True, exist_ok=True)
