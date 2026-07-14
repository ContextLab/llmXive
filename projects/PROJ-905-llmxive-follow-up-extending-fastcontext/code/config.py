"""
Configuration management for llmXive FastContext follow-up project.

This module centralizes all environment-dependent settings including:
- Dataset paths and identifiers
- Model IDs and revision tags
- Hyperparameters and weights for scoring
- File system paths relative to the project root
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

# Determine project root based on standard layout
# Assumes code/ is a subdirectory of the project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_CODE_DIR = _PROJECT_ROOT / "code"
_DATA_DIR = _PROJECT_ROOT / "data"
_DATA_RAW = _DATA_DIR / "raw"
_DATA_PROCESSED = _DATA_DIR / "processed"
_DATA_RESULTS = _DATA_DIR / "results"
_STATE_DIR = _PROJECT_ROOT / "state"
_PROJECT_STATE_FILE = _STATE_DIR / "projects" / "PROJ-905-llmxive-follow-up-extending-fastcontext.yaml"

# Dataset Configuration
DATASET_NAME: str = "princeton-nlp/SWE-bench_Lite"
DATASET_REVISION: str = "v0"  # Specific version tag
DATASET_SPLIT: str = "test"

# Model Configuration
LITE_MODEL_ID: str = "princeton-nlp/fastcontext-lite"  # Placeholder for actual Lite model
BASELINE_MODEL_ID: str = "princeton-nlp/fastcontextb"  # Original FastContext 4B
BASELINE_REVISION: str = "main"
BASELINE_PROMPT_TEMPLATE: str = "fastcontext-v"
BASELINE_DEVICE_MAP: str = "cpu"

# Static Analysis Weights (for regularity_score)
# Formula: dir_score + w1 * test_score + w2 * import_score
WEIGHT_DIR: float = 1.0
WEIGHT_TEST: float = 1.0
WEIGHT_IMPORT: float = 1.0

# TF-IDF Parameters
TFIDF_NGRAM_RANGE: tuple = (1, 2)
TFIDF_MAX_FEATURES: int = 10000
TFIDF_ANALYZER: str = "word"

# Baseline Execution Constraints
BASELINE_MAX_MEMORY_GB: int = 7
BASELINE_TIMEOUT_SECONDS: int = 300

# Output Paths
GROUND_TRUTH_CSV_PATH: Path = _DATA_RAW / "ground_truth_annotations.csv"
REGULARITY_SCORES_CSV_PATH: Path = _DATA_PROCESSED / "regularity_scores.csv"
EXPLORATION_LOGS_JSONL_PATH: Path = _DATA_RESULTS / "exploration_logs.jsonl"
STATISTICAL_SUMMARY_JSON_PATH: Path = _DATA_RESULTS / "statistical_summary.json"

def get_path(relative_path: str) -> Path:
    """
    Resolve a relative path against the project root.

    Args:
        relative_path: Path string relative to project root.

    Returns:
        Absolute Path object.
    """
    return _PROJECT_ROOT / relative_path

def ensure_directories() -> None:
    """
    Create all necessary directories if they do not exist.
    This should be called once at the start of the pipeline.
    """
    directories = [
        _DATA_RAW,
        _DATA_PROCESSED,
        _DATA_RESULTS,
        _STATE_DIR,
        _PROJECT_STATE_FILE.parent,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

def get_config_dict() -> Dict[str, Any]:
    """
    Export all configuration values as a dictionary.
    Useful for logging or passing to downstream components.
    """
    return {
        "dataset_name": DATASET_NAME,
        "dataset_revision": DATASET_REVISION,
        "dataset_split": DATASET_SPLIT,
        "lite_model_id": LITE_MODEL_ID,
        "baseline_model_id": BASELINE_MODEL_ID,
        "baseline_revision": BASELINE_REVISION,
        "baseline_prompt_template": BASELINE_PROMPT_TEMPLATE,
        "baseline_device_map": BASELINE_DEVICE_MAP,
        "weights": {
            "dir": WEIGHT_DIR,
            "test": WEIGHT_TEST,
            "import": WEIGHT_IMPORT,
        },
        "tfidf": {
            "ngram_range": TFIDF_NGRAM_RANGE,
            "max_features": TFIDF_MAX_FEATURES,
            "analyzer": TFIDF_ANALYZER,
        },
        "baseline_limits": {
            "max_memory_gb": BASELINE_MAX_MEMORY_GB,
            "timeout_seconds": BASELINE_TIMEOUT_SECONDS,
        },
        "paths": {
            "project_root": str(_PROJECT_ROOT),
            "data_raw": str(_DATA_RAW),
            "data_processed": str(_DATA_PROCESSED),
            "data_results": str(_DATA_RESULTS),
            "ground_truth_csv": str(GROUND_TRUTH_CSV_PATH),
            "regularity_scores_csv": str(REGULARITY_SCORES_CSV_PATH),
            "exploration_logs": str(EXPLORATION_LOGS_JSONL_PATH),
            "statistical_summary": str(STATISTICAL_SUMMARY_JSON_PATH),
        },
    }