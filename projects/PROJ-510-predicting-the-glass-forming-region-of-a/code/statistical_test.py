"""
Statistical test module for comparing model performance against null model.
Performs paired t-test on cross-validation scores.
"""
import json
import os
import sys
import logging
from typing import Dict, Any, List
import numpy as np
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/statistical_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

CV_METRICS_PATH = "data/models/cv_metrics.json"
NULL_MODEL_PATH = "data/models/null_model_cv_scores.json"
OUTPUT_PATH = "data/models/statistical_comparison.json"
MODELS_DIR = "data/models"

os.makedirs(MODELS_DIR, exist_ok=True)

def load_json(path: str) -> Dict[str, Any]:
    """Load JSON file."""
    with open(path, 'r') as f:
        return json.load(f)

def save_json(data: Dict[str, Any], path: str):
    """Save data to JSON file."""
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def load_processed_data():
    """Load processed data (not used here, but kept for interface)."""
    pass

def run_cross_validation_scores():
    """Load CV scores from files (not used here, but kept for interface)."""
    pass

def bootstrap_null_distribution():
    """Bootstrap null distribution (not used here, but kept for interface)."""
    pass

def run_statistical_test():
    """
    Perform paired t-test between model CV scores and null model CV scores.
    """
    logger.info("Running statistical test")

    # Load CV metrics
    model_cv = load_json(CV_METRICS_PATH)
    null_cv = load_json(NULL_MODEL_PATH)

    model_scores = np.array(model_cv['fold_scores'])
    null_scores = np.array(null_cv['fold_scores'])

    # Perform paired t-test
    t_stat, p_value = stats.ttest_rel(model_scores, null_scores)

    # Determine if SC-002 is met
    sc002_met = p_value < 0.05

    result = {
        "p_value": float(p_value),
        "t_statistic": float(t_stat),
        "sc002_met": bool(sc002_met)
    }

    save_json(result, OUTPUT_PATH)
    logger.info(f"Statistical test result: {result}")

    return result

def main():
    """Main entry point."""
    run_statistical_test()

if __name__ == "__main__":
    main()
