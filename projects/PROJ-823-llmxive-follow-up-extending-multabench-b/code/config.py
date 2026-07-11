"""
Global configuration settings for the llmXive pipeline.
"""
import os
from pathlib import Path

# Project Root
ROOT_DIR = Path(__file__).parent.parent
CODE_DIR = ROOT_DIR / "code"
DATA_DIR = ROOT_DIR / "data"
TESTS_DIR = ROOT_DIR / "tests"

# Data Subdirectories
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
ARTIFACTS_DIR = DATA_DIR / "artifacts"
FIGURES_DIR = DATA_DIR / "figures"

# Random Seed for reproducibility
RANDOM_SEED = 42

# Memory Limits (MB)
MEMORY_LIMIT_MB = 7000  # 7GB limit as per constraints

# Model Settings
DEFAULT_BATCH_SIZE = 32
MAX_BATCH_SIZE = 64
DEVICE = "cpu"  # Force CPU for CI compatibility

# Embedding Settings
CLIP_MODEL_NAME = "clip/ViT-B/32"
SBERT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Paths for specific artifacts
EMBEDDINGS_OUTPUT_PATH = PROCESSED_DATA_DIR / "embeddings_{run_id}.parquet"
METADATA_STATS_OUTPUT_PATH = PROCESSED_DATA_DIR / "metadata_stats_summary.csv"
SENSITIVITY_AGGREGATED_PATH = ARTIFACTS_DIR / "frozen_baseline_aggregated_{run_id}.json"
CONDITIONED_METRICS_PATH = ARTIFACTS_DIR / "metrics_conditioned_{run_id}.json"
CORRELATION_REPORT_PATH = ARTIFACTS_DIR / "correlation_report_{run_id}.json"

def ensure_directories():
    """Ensure all required data directories exist."""
    for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, ARTIFACTS_DIR, FIGURES_DIR]:
        directory.mkdir(parents=True, exist_ok=True)