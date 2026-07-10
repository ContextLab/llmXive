import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
from scipy import stats

# Add parent to path to allow imports if run as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger, log_fallback

logger = get_logger(__name__)

# Constants
MIN_STUDIES_FOR_EGGER = 10
SKIP_REASON = "Skipped: Insufficient studies (N < 10) for Egger's regression"
INPUT_FILE = Path("data/derived/meta_analysis_result.json")
OUTPUT_FILE = Path("data/derived/bias_assessment.json")


def load_study_count_from_json(file_path: Path) -> int:
    """
    Loads the study_count from the meta-analysis result JSON.
    """
    if not file_path.exists():
        logger.error(f"Input file not found: {file_path}")
        raise FileNotFoundError(f"Input file not found: {file_path}")

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        count = data.get('study_count', 0)
        if not isinstance(count, int):
            logger.warning(f"study_count is not an integer, got {type(count)}")
            return 0
        return count
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {file_path}: {e}")
        raise


def load_effect_sizes_and_se(file_path: Path) -> Tuple[np.ndarray, np.ndarray]:
    """
    Loads effect sizes (r) and standard errors (se) from the meta-analysis result.
    Assumes the structure: {'studies': [{'effect_size_r': float, 'se_r': float}, ...]}
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        studies = data.get('studies', [])
        if not studies:
            return np.array([]), np.array([])

        effects = []
        ses = []
        
        for study in studies:
            r = study.get('effect_size_r')
            se = study.get('se_r')
            
            if r is not None and se is not None:
                effects.append(float(r))
                ses.append(float(se))
            else:
                logger.warning(f"Skipping study with missing r or se: {study}")

        return np.array(effects), np.array(ses)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {file_path}: {e}")
        raise


def run_eggerr_regression(effects: np.ndarray, ses: np.ndarray) -> Dict[str, Any]:
    """
    Performs Egger's linear regression test.
    Model: Standardized Effect = Intercept + Slope * Precision + Error
    Precision = 1 / SE
    
    Returns dict with intercept, p-value, and t-statistic.
    """
    n = len(effects)
    if n < 2:
        raise ValueError("Need at least 2 studies to run regression.")

    # Standardized Effect = Effect / SE
    standardized_effects = effects / ses
    # Precision = 1 / SE
    precision = 1.0 / ses

    # Fit linear regression: y = intercept + slope * x
    # Using scipy.stats.linregress
    slope, intercept, r_value, p_value, std_err = stats.linregress(precision, standardized_effects)

    return {
        "intercept": float(intercept),
        "p_value": float(p_value),
        "slope": float(slope),
        "r_squared": float(r_value**2),
        "n_studies": n
    }


def run_bias_assessment() -> Dict[str, Any]:
    """
    Main function to run the bias assessment (Egger's test).
    Checks study count, runs regression if eligible, and saves results.
    """
    logger.info("Starting bias assessment (Egger's regression test).")
    
    # 1. Load study count
    study_count = load_study_count_from_json(INPUT_FILE)
    logger.info(f"Loaded study count: {study_count}")

    result: Dict[str, Any] = {
        "study_count": study_count,
        "egger_test_performed": False,
        "egger_skipped_reason": None,
        "results": None
    }

    # 2. Check skip condition
    if study_count < MIN_STUDIES_FOR_EGGER:
        msg = SKIP_REASON
        logger.warning(msg)
        result["egger_skipped_reason"] = msg
        result["egger_test_performed"] = False
    else:
        # 3. Load data
        try:
            effects, ses = load_effect_sizes_and_se(INPUT_FILE)
            if len(effects) < 2:
                msg = "Skipped: Insufficient data points for regression."
                logger.warning(msg)
                result["egger_skipped_reason"] = msg
                result["egger_test_performed"] = False
            else:
                # 4. Run regression
                reg_results = run_eggerr_regression(effects, ses)
                result["egger_test_performed"] = True
                result["results"] = reg_results
                logger.info(f"Egger's test completed. Intercept: {reg_results['intercept']:.4f}, p-value: {reg_results['p_value']:.4f}")
        except Exception as e:
            logger.error(f"Error during Egger's test execution: {e}")
            result["egger_skipped_reason"] = f"Error: {str(e)}"
            result["egger_test_performed"] = False

    # 5. Save results
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Bias assessment results saved to {OUTPUT_FILE}")
    return result


def main():
    """Entry point for script execution."""
    try:
        run_bias_assessment()
    except Exception as e:
        logger.critical(f"Pipeline failed in bias assessment: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()