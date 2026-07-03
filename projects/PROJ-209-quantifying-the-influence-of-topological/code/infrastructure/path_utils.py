"""
Path utilities to ensure no hardcoded paths in the project.
All paths are resolved relative to the project root.
"""
import os
from pathlib import Path
from typing import Union

# Define project root relative to this file (3 levels up: code/infrastructure -> code -> root)
# Assuming this file is at: code/infrastructure/path_utils.py
_CURRENT_FILE_PATH = Path(__file__).resolve()
PROJECT_ROOT = _CURRENT_FILE_PATH.parent.parent.parent

# Ensure project root is set correctly
if not PROJECT_ROOT.exists():
    raise RuntimeError(f"Could not determine project root from {_CURRENT_FILE_PATH}")

# Common directories relative to project root
DIR_CODE = PROJECT_ROOT / "code"
DIR_DATA_RAW = PROJECT_ROOT / "data" / "raw"
DIR_DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DIR_DATA_VALIDATION = PROJECT_ROOT / "data" / "validation"
DIR_FIGURES = PROJECT_ROOT / "figures"
DIR_NOTEBOOKS = PROJECT_ROOT / "notebooks"
DIR_SPECS = PROJECT_ROOT / "specs"
DIR_TESTS = PROJECT_ROOT / "tests"
DIR_SCRIPTS = PROJECT_ROOT / "scripts"

# Specific file paths
FILE_PRISTINE_STRUCTURES = DIR_DATA_RAW / "pristine_structures.csv"
FILE_DEFECT_DATASET = DIR_DATA_RAW / "defect_dataset_2022.csv"
FILE_SYNTHETIC_TRAIN = DIR_DATA_RAW / "synthetic_train.csv"
FILE_SYNTHETIC_HOLDOUT = DIR_DATA_RAW / "synthetic_holdout.csv"
FILE_SYNTHETIC_FALLBACK = DIR_DATA_RAW / "synthetic_defect_fallback.csv"
FILE_FEATURES = DIR_DATA_PROCESSED / "features.csv"
FILE_TARGETS = DIR_DATA_PROCESSED / "targets.csv"
FILE_FEATURE_SELECTION_LOG = DIR_DATA_PROCESSED / "feature_selection_log.json"
FILE_MODELS_DIR = DIR_DATA_PROCESSED / "models"
FILE_METRICS = DIR_DATA_PROCESSED / "metrics.json"
FILE_VALIDATION_REPORT = DIR_DATA_VALIDATION / "Validation_Report.json"
FILE_STATE = PROJECT_ROOT / "state" / "projects" / "PROJ-209-quantifying-the-influence-of-topological.yaml"
FILE_GIT_HASH = PROJECT_ROOT / ".git_hash"

# External validation data path
DIR_EXTERNAL_VALIDATION = DIR_DATA_VALIDATION / "external"
ID_EXP_DEFECT_GRAPHENE_MOS2_V1 = "exp_defect_graphene_mos2_v1"
FILE_EXTERNAL_DATA = DIR_EXTERNAL_VALIDATION / f"{ID_EXP_DEFECT_GRAPHENE_MOS2_V1}.csv"

def get_project_root() -> Path:
    """Return the project root directory."""
    return PROJECT_ROOT

def resolve_path(path: Union[str, Path]) -> Path:
    """
    Resolve a path relative to project root if it's a relative path.
    If absolute, return as-is.
    """
    path_obj = Path(path)
    if path_obj.is_absolute():
        return path_obj
    return PROJECT_ROOT / path_obj

def ensure_dir(path: Union[str, Path]) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    path_obj = resolve_path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj

def get_output_path(relative_path: Union[str, Path]) -> Path:
    """
    Get a full output path relative to the appropriate data directory.
    This ensures no hardcoded paths in the code.
    """
    return resolve_path(relative_path)

# Backward compatibility aliases (to be used by existing code)
def get_repo_root() -> Path:
    """Alias for get_project_root() for backward compatibility."""
    return get_project_root()

def create_directories():
    """Create all necessary directories."""
    ensure_dir(DIR_CODE)
    ensure_dir(DIR_DATA_RAW)
    ensure_dir(DIR_DATA_PROCESSED)
    ensure_dir(DIR_DATA_VALIDATION)
    ensure_dir(DIR_FIGURES)
    ensure_dir(DIR_NOTEBOOKS)
    ensure_dir(DIR_TESTS)
    ensure_dir(DIR_SCRIPTS)
    ensure_dir(DIR_MODELS_DIR)
    ensure_dir(DIR_EXTERNAL_VALIDATION)
