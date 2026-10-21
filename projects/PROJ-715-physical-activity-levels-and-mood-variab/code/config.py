import os
import sys
import logging
import random
from pathlib import Path
from typing import Union, List, Tuple
import yaml
import shutil

# ============================================================
# Configuration Constants (T004)
# ============================================================

# Random seed for reproducibility (Constitution Principle I)
SEED = 42
# Alias used by some analysis modules
RANDOM_SEED = SEED

# Missingness threshold: if a covariate (sleep_duration, baseline_affect)
# is missing for more than this fraction of rows, the model proceeds
# without it rather than imputing (spec Assumptions: 5%).
MISSINGNESS_THRESHOLD = 0.05

# Number of bootstrap iterations for the single-rating sensitivity
# analysis (FR-008).
BOOTSTRAP_ITERATIONS = 1000

# Chunk size (rows) for streaming/chunked processing of bronze data.
CHUNK_SIZE = 100000

# Epsilon offset for the log transformation of mood_std
# (spec Edge Case: log(mood_std + 0.01)).
LOG_EPSILON = 0.01

# Minimum number of valid days for a participant to be retained
# (Edge Case: participants with 1-2 days excluded).
MIN_VALID_DAYS = 3

# ============================================================
# Dataset provenance (StudentLife)
# ============================================================

# OSF DOI for the StudentLife dataset (canonical source, FR-001)
OSF_DOI = "10.17605/OSF.IO/5B1A9"
# Direct download URL derived from the OSF DOI
OSF_URL = "https://osf.io/download/5b1a9f1b9ad5a10018669804/"
# HuggingFace mirror used only as a fallback download location
HF_REPO = "mlfoundations/studentlife"
HF_FILE = "studentlife_ema_steps.zip"
HF_URL = f"https://huggingface.co/datasets/{HF_REPO}/resolve/main/{HF_FILE}"

# Project identifier used for the state file
PROJECT_ID = "PROJ-715-physical-activity-levels-and-mood-variab"
STATE_PATH_REL = ("state", "projects",
                  "PROJ-715-physical-activity-levels-and-mood-variab.yaml")

# ============================================================
# Utilities
# ============================================================

def set_random_seed(seed: int = SEED):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass

def get_path(*parts: Union[str, Path]) -> Path:
    """
    Construct a path relative to the project root and return it as a
    pathlib.Path. Handles a variable number of arguments and list/tuple
    inputs, as well as arguments containing forward slashes (e.g.
    'data/processed'). The parent directory is created if missing; the
    file itself is never created.

    Compatible with all existing call sites:
    - get_path('data', 'processed', 'model_results.json')
    - get_path('data/processed', 'final_report.pdf')
    - get_path("specs", "001-...", "contracts", "x.yaml")
    """
    current_file = Path(__file__).resolve()
    root = current_file.parent.parent

    path_parts = []
    for p in parts:
        if isinstance(p, (list, tuple)):
            path_parts.extend(str(x) for x in p)
        else:
            path_parts.append(str(p))

    # Allow embedded separators like 'data/processed'
    joined = Path(*path_parts) if path_parts else Path()
    full_path = root / joined

    # Ensure the parent directory exists (but never create the file
    # itself, and never create a directory where a file is expected).
    try:
        parent = full_path.parent
        if str(parent) and not parent.exists():
            parent.mkdir(parents=True, exist_ok=True)
    except (OSError, NotADirectoryError):
        # Parent may be blocked by an existing file; leave as-is and
        # let the caller fail loudly with a clear error.
        pass

    return full_path

def init_logger(name: str):
    """Initialize a logger with standard formatting."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger

def ensure_dirs(*paths):
    """
    Ensure directories exist.

    Tolerant of file paths being passed in: if a path has a file
    extension (or already exists as a file), its parent directory is
    created instead. This prevents the IsADirectoryError seen when a
    caller passes a file path like preprocess_stats.json.
    """
    for p in paths:
        if p is None:
            continue
        path = Path(p)
        if path.exists() and path.is_file():
            continue
        if path.suffix and not path.is_dir():
            # Looks like a file path; create its parent directory only.
            parent = path.parent
            if str(parent):
                os.makedirs(parent, exist_ok=True)
            continue
        os.makedirs(path, exist_ok=True)

def update_state_artifact_hash(state_path: str, key: str, value: str):
    """
    Update the state YAML file with a new artifact hash.
    Reads the file, updates the specific key under artifact_hashes,
    and writes back atomically.
    """
    state_path = str(state_path)
    os.makedirs(os.path.dirname(state_path) or ".", exist_ok=True)

    if os.path.exists(state_path):
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {}

    if 'artifact_hashes' not in state or not isinstance(
            state.get('artifact_hashes'), dict):
        state['artifact_hashes'] = {}

    state['artifact_hashes'][key] = value

    temp_path = state_path + '.tmp'
    with open(temp_path, 'w') as f:
        yaml.dump(state, f)

    shutil.move(temp_path, state_path)
    logging.getLogger(__name__).info(f"Updated state hash for {key}")
