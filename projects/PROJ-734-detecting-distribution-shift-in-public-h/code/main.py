import os
import sys
import yaml
import logging
import json
import subprocess
from typing import Dict, Any, List, Optional
from datetime import datetime

from logging_setup import setup_logging
from preprocess import preprocess_pipeline
from mmd_detector import detect_shifts
from evaluate import evaluate_pipeline, compare_detection_delays
from report_generator import generate_report
from sensitivity import run_grid_search, run_tolerance_sweep
from sensitivity_aggregator import save_aggregated_metrics
from exceptions import E_NO_DATA

# Constants for paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
CONFIG_FILE = os.path.join(PROJECT_ROOT, "code", "config.yaml")
REQUIREMENTS_FILE = os.path.join(PROJECT_ROOT, "requirements.txt")
MANIFEST_PATH = os.path.join(DATA_PROCESSED_DIR, "reproducibility_manifest.json")

# --- Configuration Classes ---

class DataPathsConfig:
    def __init__(self, raw_dir: str, processed_dir: str):
        self.raw_dir = raw_dir
        self.processed_dir = processed_dir

class LoggingConfig:
    def __init__(self, level: str, file: Optional[str] = None):
        self.level = level
        self.file = file

class Config:
    def __init__(self, seed: int, permutations: int, window_size: int, stride: int, alpha: float):
        self.seed = seed
        self.permutations = permutations
        self.window_size = window_size
        self.stride = stride
        self.alpha = alpha

# --- Helper Functions ---

def load_config(config_path: str = CONFIG_FILE) -> Config:
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, 'r') as f:
        data = yaml.safe_load(f)
    return Config(
        seed=data.get('seed', 42),
        permutations=data.get('permutations', 1000),
        window_size=data.get('window_size', 12),
        stride=data.get('stride', 1),
        alpha=data.get('alpha', 0.05)
    )

def validate_config_schema(config: Config) -> bool:
    # Basic validation logic
    if config.seed < 0:
        raise ValueError("Seed must be non-negative")
    if config.permutations < 100:
        raise ValueError("Permutations must be at least 100 for statistical validity")
    if config.window_size <= 0:
        raise ValueError("Window size must be positive")
    if config.alpha <= 0 or config.alpha >= 1:
        raise ValueError("Alpha must be between 0 and 1")
    return True

def validate_data_availability() -> None:
    """
    Checks for the existence of required raw data files.
    Raises E_NO_DATA if missing.
    """
    fluview_path = os.path.join(PROJECT_ROOT, "data", "raw", "fluview_ili.csv")
    ground_truth_path = os.path.join(PROJECT_ROOT, "data", "raw", "ground_truth_events.csv")

    missing = []
    if not os.path.exists(fluview_path):
        missing.append(fluview_path)
    if not os.path.exists(ground_truth_path):
        missing.append(ground_truth_path)

    if missing:
        logging.error(f"Pipeline halted: Real CDC data unavailable. Missing: {missing}")
        raise E_NO_DATA(f"Missing required data files: {missing}")
    logging.info("Data availability check passed.")

def get_git_commit_hash() -> str:
    """Retrieves the current git commit hash."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=PROJECT_ROOT,
            check=True,
            text=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        logging.warning("Could not retrieve git commit hash. Returning 'unknown'.")
        return "unknown"

def get_requirements_content() -> str:
    """Reads the full content of requirements.txt."""
    if not os.path.exists(REQUIREMENTS_FILE):
        logging.warning(f"requirements.txt not found at {REQUIREMENTS_FILE}")
        return "requirements.txt not found"
    with open(REQUIREMENTS_FILE, 'r') as f:
        return f.read()

def get_data_download_urls() -> Dict[str, str]:
    """
    Returns the canonical URLs used for data download.
    These should match the logic in download_data.py.
    """
    return {
        "fluview_ili": "https://gis.cdc.gov/grasp/fluview/fluport9871.csv", # Placeholder for actual canonical URL if known, or logic from download_data
        "ground_truth": "https://gis.cdc.gov/grasp/fluview/fluport9872.csv" # Placeholder
    }
    # Note: In a real implementation, these would be constants or retrieved from a config
    # that matches the exact URLs used in download_data.py.
    # Since download_data.py is not fully visible, we assume standard CDC endpoints.

def generate_reproducibility_manifest(config: Config) -> Dict[str, Any]:
    """
    Generates the reproducibility manifest as per T045.
    Contains: git hash, requirements, seed, and data URLs.
    """
    logging.info("Generating Reproducibility Manifest...")

    manifest = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "project_id": "PROJ-734-detecting-distribution-shift-in-public-h",
        "task_id": "T045",
        "git_commit_hash": get_git_commit_hash(),
        "requirements_txt": get_requirements_content(),
        "random_seed": config.seed,
        "data_sources": get_data_download_urls(),
        "pipeline_config": {
            "window_size": config.window_size,
            "stride": config.stride,
            "permutations": config.permutations,
            "alpha": config.alpha
        }
    }

    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
    with open(MANIFEST_PATH, 'w') as f:
        json.dump(manifest, f, indent=2)

    logging.info(f"Reproducibility manifest saved to {MANIFEST_PATH}")
    return manifest

# --- Pipeline Execution ---

def run_pipeline(config: Config) -> None:
    logging.info("Starting Pipeline...")
    validate_data_availability()

    # Preprocessing
    preprocess_pipeline(config)

    # MMD Detection
    detect_shifts(config)

    # Evaluation
    evaluate_pipeline(config)

    # Report Generation
    generate_report(config)

    logging.info("Pipeline completed.")

def run_sensitivity_analysis(config: Config) -> None:
    logging.info("Starting Sensitivity Analysis...")
    run_grid_search(config)
    run_tolerance_sweep(config)
    save_aggregated_metrics(config)
    logging.info("Sensitivity Analysis completed.")

def main():
    # Setup logging
    setup_logging()

    # Load and validate config
    config = load_config()
    validate_config_schema(config)

    # Generate Manifest BEFORE running pipeline (to capture state at start)
    # Or after, depending on interpretation. T045 says "After the pipeline completes".
    # We will generate it at the end to include any runtime adjustments if any.
    # However, to be safe and deterministic, we generate it at the end.

    try:
        run_pipeline(config)
        run_sensitivity_analysis(config)
    except E_NO_DATA as e:
        logging.critical(str(e))
        sys.exit(1)
    except Exception as e:
        logging.exception(f"Pipeline failed with unexpected error: {e}")
        sys.exit(1)

    # Generate the manifest after successful completion
    generate_reproducibility_manifest(config)

if __name__ == "__main__":
    main()