import os
from pathlib import Path

# Project Root: Assumes code/ is one level deep from root
# If running from code/, adjust accordingly.
# Standard assumption: PROJECT_ROOT is the repo root.
_current_file = Path(__file__).resolve()
_code_dir = _current_file.parent
PROJECT_ROOT = _code_dir.parent

# Configuration Keys
# T006: Setup configuration management for batch sizes, CPU offloading limits, and VARIANCE_THRESHOLD key

# Variance Threshold for flagging high-variance prompts (used in T035)
VARIANCE_THRESHOLD = 0.01

# Inference Batching Configuration
BATCH_SIZE = 1  # CPU batch size default (conservative for memory constraints)

# Memory Management
CPU_OFFLOAD_LIMIT = 2048  # MB limit for CPU offloading

# Reproducibility
SEED = 42

# T006b: Official SHA-256 checksum for Qwen-Image-2.0 weights
# Source: Qwen-Image-2.0 Technical Report / Hugging Face Model Card verification
# This constant is required by T014 (verify_checksums.py) to validate downloaded weights.
# If the downloaded model files do not match this hash, the verification must abort.
QWEN_IMAGE_2_0_SHA256 = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2"  # Placeholder: Replace with official value from Technical Report before T014 execution

# Paths
DATA_DIR = PROJECT_ROOT / "data"
PROMPTS_DIR = DATA_DIR / "prompts"
MODELS_DIR = DATA_DIR / "models"
OUTPUTS_DIR = DATA_DIR / "outputs"
RESULTS_DIR = DATA_DIR / "results"
REPORTS_DIR = DATA_DIR / "reports"
FIGURES_DIR = DATA_DIR / "figures"

# Ensure directories exist (lazy initialization helper)
def ensure_dirs():
    """Create all project data directories if they don't exist."""
    for dir_path in [DATA_DIR, PROMPTS_DIR, MODELS_DIR, OUTPUTS_DIR, RESULTS_DIR, REPORTS_DIR, FIGURES_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)