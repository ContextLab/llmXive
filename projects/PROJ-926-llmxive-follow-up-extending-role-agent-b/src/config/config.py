"""
Configuration module for llmXive project.

Defines pinned random seeds, data paths, model identifiers, and ALFWorld
hyperparameters required for reproducible experiments.
"""

import os
from pathlib import Path
from typing import Any, Dict, Final

# Project Root
_PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent.parent

# Random Seeds (Pinned for Reproducibility)
SEED: Final[int] = 42

# Data Paths
DATA_PATH: Final[Path] = _PROJECT_ROOT / "data"
RAW_DATA_PATH: Final[Path] = DATA_PATH / "raw"
DERIVED_DATA_PATH: Final[Path] = DATA_PATH / "derived"
STATE_PATH: Final[Path] = _PROJECT_ROOT / "state"
DOCS_PATH: Final[Path] = _PROJECT_ROOT / "docs"

# Model Configuration
MODEL_ID: Final[str] = "meta-llama/Llama-3-8B-Instruct"
# Fallback for CPU-only or restricted environments (4-bit quantized)
MODEL_ID_CPU: Final[str] = "meta-llama/Llama-3-8B-Instruct" 
# Note: In actual execution, quantization config is applied via transformers pipeline
# or bitsandbytes if available, otherwise fallback to smaller model if memory constrained.

# ALFWorld Hyperparameters
ALFWORLD_CONFIG: Final[Dict[str, Any]] = {
    "env_name": "alfworld",
    "max_steps": 50,
    "temperature": 0.7,
    "top_p": 0.95,
    "repetition_penalty": 1.1,
    "max_new_tokens": 128,
    "stop_sequences": ["</s>", "\n"],
    "task_types": [
        "pick_and_place",
        "pick_clean_then_place",
        "pick_heat_then_place",
        "pick_cool_then_place",
        "look_at_obj",
        "pick_two_obj"
    ],
    "evaluation_mode": "expert",
    "use_demonstrations": True,
    "demonstration_path": str(_PROJECT_ROOT / "data" / "raw" / "alfworld_demonstrations.json"),
}

# Execution Constraints (CPU Mode)
CPU_DEVICE: Final[bool] = True
MAX_RAM_GB: Final[int] = 7
TORCH_NUM_THREADS: Final[int] = 4

# Output Paths for Generated Artifacts
BASELINE_FAILURES_PATH: Final[Path] = RAW_DATA_PATH / "baseline_failures.json"
DEGRADED_FAILURES_PATH: Final[Path] = RAW_DATA_PATH / "degraded_failures.json"
INTERVENTION_FAILURES_PATH: Final[Path] = RAW_DATA_PATH / "intervention_failures.json"
GROUND_TRUTH_RAW_PATH: Final[Path] = RAW_DATA_PATH / "ground_truth_raw.json"
EXCLUSION_LOG_PATH: Final[Path] = RAW_DATA_PATH / "excluded_log.json"

# Derived Output Paths
POWER_ANALYSIS_REPORT_PATH: Final[Path] = DERIVED_DATA_PATH / "power_analysis_report.json"
DEGRADED_STATS_PATH: Final[Path] = DERIVED_DATA_PATH / "degraded_stats.json"
INTERVENTION_STATS_PATH: Final[Path] = DERIVED_DATA_PATH / "intervention_stats.json"
FINAL_STATS_PATH: Final[Path] = DERIVED_DATA_PATH / "final_stats.csv"

def ensure_directories() -> None:
    """Ensure all required data and state directories exist."""
    for path in [
        DATA_PATH,
        RAW_DATA_PATH,
        DERIVED_DATA_PATH,
        STATE_PATH,
        DOCS_PATH,
    ]:
        path.mkdir(parents=True, exist_ok=True)

def get_config_summary() -> Dict[str, Any]:
    """Return a summary of the current configuration."""
    return {
        "seed": SEED,
        "model_id": MODEL_ID,
        "data_path": str(DATA_PATH),
        "cpu_device": CPU_DEVICE,
        "max_ram_gb": MAX_RAM_GB,
        "alfworld_config": ALFWORLD_CONFIG,
    }