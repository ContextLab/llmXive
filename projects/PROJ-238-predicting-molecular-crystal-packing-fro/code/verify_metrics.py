import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.config import setup_logging, get_config

# Configure logging
logger = setup_logging("verify_metrics")

REQUIRED_ROOT_KEYS = [
    "model_metrics",
    "statistical_tests",
    "metadata"
]

REQUIRED_MODEL_KEYS = [
    "random_forest",
    "gradient_boosting",
    "mean_baseline",
    "control_analysis"
]

REQUIRED_METRIC_KEYS = [
    "r2",
    "mae",
    "rmse"
]

REQUIRED_STATS_KEYS = [
    "paired_t_tests",
    "bonferroni_correction"
]

REQUIRED_BONFERRONI_KEYS = [
    "alpha_corrected",
    "flag_significance"
]

REQUIRED_METADATA_KEYS = [
    "random_seed",
    "timestamp",
    "scikit_learn_version"
]

def load_metrics_file(file_path: str) -> Optional[Dict[str, Any]]:
    """Load and parse the metrics JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Metrics file not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in metrics file: {e}")
        return None

def validate_structure(data: Dict[str, Any]) -> bool:
    """Validate the top-level structure of the metrics file."""
    missing_keys = [key for key in REQUIRED_ROOT_KEYS if key not in data]
    if missing_keys:
        logger.error(f"Missing required top-level keys: {missing_keys}")
        return False
    return True

def validate_model_metrics(model_metrics: Dict[str, Any]) -> bool:
    """Validate metrics for each model."""
    missing_models = [key for key in REQUIRED_MODEL_KEYS if key not in model_metrics]
    if missing_models:
        logger.error(f"Missing model metrics for: {missing_models}")
        return False

    for model_name, metrics in model_metrics.items():
        missing_metric_keys = [key for key in REQUIRED_METRIC_KEYS if key not in metrics]
        if missing_metric_keys:
            logger.error(f"Missing metric keys for {model_name}: {missing_metric_keys}")
            return False
    return True

def validate_statistical_tests(stats: Dict[str, Any]) -> bool:
    """Validate statistical test results."""
    missing_keys = [key for key in REQUIRED_STATS_KEYS if key not in stats]
    if missing_keys:
        logger.error(f"Missing statistical test keys: {missing_keys}")
        return False
    return True

def validate_bonferroni_flag(stats: Dict[str, Any]) -> bool:
    """Validate the Bonferroni correction data."""
    if "bonferroni_correction" not in stats:
        logger.error("Missing 'bonferroni_correction' in statistical_tests")
        return False

    bonf_data = stats["bonferroni_correction"]
    missing_keys = [key for key in REQUIRED_BONFERRONI_KEYS if key not in bonf_data]
    if missing_keys:
        logger.error(f"Missing Bonferroni keys: {missing_keys}")
        return False

    # Verify alpha_corrected is a number
    if not isinstance(bonf_data.get("alpha_corrected"), (int, float)):
        logger.error("alpha_corrected must be a number")
        return False

    # Verify flag_significance is a boolean or list of booleans
    flag = bonf_data.get("flag_significance")
    if isinstance(flag, list):
        if not all(isinstance(f, bool) for f in flag):
            logger.error("flag_significance list must contain only booleans")
            return False
    elif not isinstance(flag, bool):
        logger.error("flag_significance must be a boolean or list of booleans")
        return False

    return True

def main():
    """Main entry point for verification."""
    config = get_config()
    metrics_path = config.get("DATA_PATH", "results") / "metrics.json"

    logger.info(f"Verifying metrics file: {metrics_path}")

    if not metrics_path.exists():
        logger.error(f"Metrics file does not exist at {metrics_path}")
        return 1

    data = load_metrics_file(str(metrics_path))
    if data is None:
        return 1

    if not validate_structure(data):
        return 1

    if not validate_model_metrics(data["model_metrics"]):
        return 1

    if not validate_statistical_tests(data["statistical_tests"]):
        return 1

    if not validate_bonferroni_flag(data["statistical_tests"]):
        return 1

    # Validate metadata
    if "metadata" in data:
        missing_meta = [key for key in REQUIRED_METADATA_KEYS if key not in data["metadata"]]
        if missing_meta:
            logger.warning(f"Missing metadata keys (non-fatal): {missing_meta}")

    logger.info("Verification PASSED: All required fields and Bonferroni flag present.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
