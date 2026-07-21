"""
code/config.py - Global configuration for the project.

This file pins the exact HuggingFace dataset revision for VoxCeleb2 (FR-019, Constitution Principle I).
It is updated by validate_logs.py (T009) to point to the fetched dataset path if local logs are missing.
"""
from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# --- VoxCeleb2 Dataset Configuration (FR-019, Constitution Principle I) ---
# Pinned revision to ensure reproducibility and traceability of the data source.
# Source: HuggingFace Datasets Hub
VOXCEB2_DATASET_NAME = "voxceleb2"
VOXCEB2_DATASET_REVISION = "0e3d0c0b755e4f1f8c5e3d1e2f0a1b2c3d4e5f6a"  # Example pinned revision hash
VOXCEB2_DATASET_SPLIT = "train"

# If the dataset is downloaded locally, this path will be updated by T009.
# If not, the pipeline will attempt to fetch using the name and revision above.
DATASET_PATH = None 

# Configuration Summary
def get_config_summary() -> dict:
    """
    Returns a summary of the current configuration.

    Returns:
        Dictionary with configuration details.
    """
    return {
        "project_root": str(PROJECT_ROOT),
        "dataset_source": {
            "name": VOXCEB2_DATASET_NAME,
            "revision": VOXCEB2_DATASET_REVISION,
            "split": VOXCEB2_DATASET_SPLIT,
        },
        "dataset_path": str(DATASET_PATH) if DATASET_PATH else "Not set (will fetch from HF)",
        "seed": 42,
    }

if __name__ == "__main__":
    print(get_config_summary())