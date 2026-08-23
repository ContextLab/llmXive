"""
Configuration module for the biomarker discovery pipeline.
Defines paths, seeds, thresholds, and resource limits.
"""
import os
from pathlib import Path
from typing import Final, List, Optional

# Project root (relative to this file's location)
_PROJECT_ROOT = Path(__file__).parent.parent.parent

# Random seeds for reproducibility
RANDOM_SEED: Final[int] = 42

# FDR thresholds
FDR_THRESHOLD: Final[float] = 0.05
LOG2FC_THRESHOLD: Final[float] = 1.0

# Resource limits
MAX_MEMORY_GB: Final[float] = 14.0
MAX_CPU_HOURS: Final[float] = 2.0
MAX_VARIANCE_GENES: Final[int] = 10000

# Default GEO IDs
GEO_IDS: Final[List[str]] = ['GSE25055', 'GSE42752']

# TCGA projects (default)
TCGA_PROJECTS: Final[List[str]] = [
    'TCGA-BRCA',
    'TCGA-LUAD',
    'TCGA-LUSC',
    'TCGA-COAD',
    'TCGA-READ'
]

# Minimum sample requirements
MIN_TCGA_TYPES: Final[int] = 3
MIN_TCGA_SAMPLES: Final[int] = 50
MIN_GEO_DATASETS: Final[int] = 2

# Class imbalance threshold
CLASS_IMBALANCE_THRESHOLD: Final[float] = 0.20

# LOO validation requirements
MIN_TYPES_FOR_LOO: Final[int] = 2

def get_project_root() -> Path:
    """Get the project root directory."""
    return _PROJECT_ROOT

def ensure_directories(paths: List[Path]) -> None:
    """Ensure all specified directories exist."""
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)

def get_data_dirs() -> dict:
    """Get data directory paths."""
    root = get_project_root()
    return {
        'raw': root / 'data' / 'raw',
        'processed': root / 'data' / 'processed',
        'results': root / 'results',
        'meta_analysis': root / 'results' / 'meta_analysis',
        'models': root / 'results' / 'models',
        'validation': root / 'results' / 'validation',
        'plots': root / 'results' / 'plots',
    }

def get_schema_dir() -> Path:
    """Get schema directory path."""
    return get_project_root() / 'specs' / '001-chemo-biomarker-discovery' / 'contracts'

def get_state_dir() -> Path:
    """Get state directory path."""
    return get_project_root() / 'state' / 'projects'

def get_log_dir() -> Path:
    """Get log directory path."""
    return get_project_root() / 'logs'

def get_output_path(filename: str, subdir: Optional[str] = None) -> Path:
    """Get full path for an output file."""
    root = get_data_dirs()['results']
    if subdir:
        root = root / subdir
    return root / filename

def main() -> None:
    """Test configuration loading."""
    import logging
    logging.basicConfig(level=logging.INFO)

    logger = logging.getLogger(__name__)
    logger.info(f"Project root: {get_project_root()}")
    logger.info(f"Random seed: {RANDOM_SEED}")
    logger.info(f"FDR threshold: {FDR_THRESHOLD}")
    logger.info(f"GEO IDs: {GEO_IDS}")
    logger.info(f"TCGA projects: {TCGA_PROJECTS}")
    logger.info(f"Data directories: {list(get_data_dirs().keys())}")

if __name__ == '__main__':
    main()