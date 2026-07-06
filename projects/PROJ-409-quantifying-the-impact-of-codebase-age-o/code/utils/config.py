"""
Configuration constants, random seeds, and timeout limits for the llmXive pipeline.

This module centralizes all magic numbers and global settings to ensure
consistency across the extraction, inference, and analysis phases.
"""

import os
import random
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Data Directories
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_EXTRACTED_DIR = PROJECT_ROOT / "data" / "extracted"
DATA_AGGREGATED_DIR = PROJECT_ROOT / "data" / "aggregated"
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"
DATA_MODELS_DIR = PROJECT_ROOT / "data" / "models"

# Code Directories
CODE_DIR = PROJECT_ROOT / "code"
CODE_EXTRACTION_DIR = CODE_DIR / "extraction"
CODE_INFERENCE_DIR = CODE_DIR / "inference"
CODE_ANALYSIS_DIR = CODE_DIR / "analysis"
CODE_UTILS_DIR = CODE_DIR / "utils"
CODE_MODELS_FILE = CODE_DIR / "models.py"

# Output Files
EXTRACTION_OUTPUT = DATA_EXTRACTED_DIR / "snippets.csv"
INFERENCE_OUTPUT = DATA_EXTRACTED_DIR / "inference_results.csv"
FILE_METRICS_OUTPUT = DATA_AGGREGATED_DIR / "file_metrics.csv"
FINAL_REPORT_JSON = DATA_RESULTS_DIR / "report.json"
FINAL_REPORT_MD = DATA_RESULTS_DIR / "report.md"

# Random Seeds for Reproducibility
RANDOM_SEED = 42
TORCH_SEED = 42
NUMPY_SEED = 42

def set_all_seeds():
    """Initialize all random seeds for reproducibility."""
    random.seed(RANDOM_SEED)
    try:
        import numpy as np
        np.random.seed(NUMPY_SEED)
    except ImportError:
        pass
    try:
        import torch
        torch.manual_seed(TORCH_SEED)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(TORCH_SEED)
    except ImportError:
        pass

# Timeout Limits (in seconds)
# Derived from the requirement for "-hour timeout limits" (interpreted as 1-hour max per major phase)
# Specific limits for individual operations
GIT_CLONE_TIMEOUT = 600  # 10 minutes per repo
SNIPPET_EXTRACTION_TIMEOUT = 300  # 5 minutes per file
INFERENCE_SNIPPET_TIMEOUT = 60  # 1 minute per snippet
INFERENCE_GLOBAL_TIMEOUT = 3600  # 1 hour total for inference phase

# Model Configuration
MODEL_NAME = "Salesforce/codegen-350M-mono"
MODEL_CACHE_DIR = DATA_MODELS_DIR / "codegen"
QUANTIZATION_BITS = 8  # 8-bit quantization for CPU efficiency
MAX_NEW_TOKENS = 128
MAX_INPUT_LENGTH = 1024

# Extraction Configuration
MIN_TOKEN_LENGTH = 50
MAX_REPOS_TO_PROCESS = 5
MIN_REPOS_REQUIRED = 3
MIN_SNIPPETS_REQUIRED = 800

# Inference Configuration
CPU_ONLY = True
BATCH_SIZE = 1
PERPLEXITY_METHOD = "log_probs"  # Calculate via log probabilities

# Statistical Analysis Configuration
SIGNIFICANCE_THRESHOLD = 0.05
CORRELATION_METHOD = "spearman"

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = PROJECT_ROOT / "logs" / "pipeline.log"

# Ensure directories exist
def ensure_directories():
    """Create all necessary data directories if they don't exist."""
    dirs = [
        DATA_RAW_DIR,
        DATA_EXTRACTED_DIR,
        DATA_AGGREGATED_DIR,
        DATA_RESULTS_DIR,
        DATA_MODELS_DIR,
        LOG_FILE.parent
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# Initialize directories on import
ensure_directories()