"""
Configuration constants and path helpers for the llmXive pipeline.
"""
import os
from pathlib import Path
from typing import Final, Dict, Any, List, Optional
from datetime import datetime

# --- Project Root & Directory Paths ---
# Assume code/ is the root for imports, but paths are relative to project root
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent
DATA_ROOT: Final[Path] = PROJECT_ROOT / "data"
DATA_RAW: Final[Path] = DATA_ROOT / "raw"
DATA_CURATED: Final[Path] = DATA_ROOT / "curated"
DATA_RESULTS: Final[Path] = DATA_ROOT / "results"
STATE_ROOT: Final[Path] = PROJECT_ROOT / "state"
SPECS_ROOT: Final[Path] = PROJECT_ROOT / "specs" / "001-llmxive-follow-up-extending-swe-explore"
CONTRACTS_ROOT: Final[Path] = SPECS_ROOT / "contracts"
FIGURES_ROOT: Final[Path] = PROJECT_ROOT / "docs" / "figures"
PAPER_ROOT: Final[Path] = PROJECT_ROOT / "paper"

# --- Deferred / Placeholder Parameters ---
# These are set at runtime or via validation steps (e.g., T012, T024a)
HARD_INSTANCE_PERCENTILE: Optional[float] = None  # [deferred] - set at runtime or via validation
SWEEP_SAMPLE_SIZE: Optional[int] = None  # [deferred] - validated by power analysis
TIE_THRESHOLD: Optional[float] = None  # [deferred] - validated by tie analysis

# --- Fixed Configuration Parameters ---
COVERAGE_COLUMN_NAME: Final[str] = 'initial_coverage'
SWEEP_SEED: Final[int] = 42
TURN_LIMITS: Final[List[int]] = [5, 10, 15]  # low, medium, high (revised per spec)

MIN_SYNTHETIC_ISSUES: Final[int] = 10
VALIDATION_SAMPLE_SIZE: Final[int] = 5
MAX_RUNTIME_HOURS: Final[float] = 6.0
MODEL_PRECISION: Final[str] = '8bit'  # Corresponds to load_in_8bit=True

# --- HuggingFace Dataset Constants ---
HF_DATASET_NAME: Final[str] = "princeton-nlp/SWE-bench"
HF_DATASET_SPLIT: Final[str] = "test"
HF_FILE_NAME: Final[str] = "bench.final.public.jsonl"

# --- Runtime Tracking ---
RUN_TIMESTAMP: Final[str] = datetime.now().isoformat()

def get_path(relative_path: Path) -> Path:
    """
    Resolve a relative path against the project root.
    """
    return PROJECT_ROOT / relative_path

def ensure_directories() -> None:
    """
    Create all required directories if they do not exist.
    """
    dirs = [
        DATA_RAW, DATA_CURATED, DATA_RESULTS, STATE_ROOT,
        CONTRACTS_ROOT, FIGURES_ROOT, PAPER_ROOT
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_config_summary() -> Dict[str, Any]:
    """
    Returns a summary of the current configuration state.
    """
    return {
        "project_root": str(PROJECT_ROOT),
        "data_root": str(DATA_ROOT),
        "hard_instance_percentile": HARD_INSTANCE_PERCENTILE,
        "sweep_sample_size": SWEEP_SAMPLE_SIZE,
        "tie_threshold": TIE_THRESHOLD,
        "coverage_column": COVERAGE_COLUMN_NAME,
        "sweep_seed": SWEEP_SEED,
        "turn_limits": TURN_LIMITS,
        "min_synthetic_issues": MIN_SYNTHETIC_ISSUES,
        "validation_sample_size": VALIDATION_SAMPLE_SIZE,
        "max_runtime_hours": MAX_RUNTIME_HOURS,
        "model_precision": MODEL_PRECISION,
        "hf_dataset": HF_DATASET_NAME,
        "run_timestamp": RUN_TIMESTAMP
    }
