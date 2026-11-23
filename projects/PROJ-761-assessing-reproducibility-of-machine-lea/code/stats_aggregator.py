"""
Stat Summary Aggregator for User Story 2.
Aggregates outputs from T025 (t-tests), T027 (LME), T028 (Bland-Altman),
T029 (Heterogeneity), and T030b (Failure Log) into a single stat_summary.json.
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
REPORTS_DIR = ARTIFACTS_DIR / "reports"
LOGS_DIR = ARTIFACTS_DIR / "logs"

# Input files (produced by previous tasks)
TTEST_RESULTS_PATH = REPORTS_DIR / "ttest_results.json"
LME_RESULTS_PATH = REPORTS_DIR / "lme_results.json"
HETEROGENEITY_PATH = REPORTS_DIR / "heterogeneity_metrics.json"
FAILURE_LOG_PATH = LOGS_DIR / "failure_log.json"
BLAND_ALTMAN_META_PATH = REPORTS_DIR / "bland_altman_metadata.json"

# Output file
OUTPUT_PATH = REPORTS_DIR / "stat_summary.json"


def load_json_file(path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file, returning None if it doesn't exist or is empty."""
    if not path.exists():
        logger.warning(f"File not found: {path}")
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not data:
                logger.warning(f"File is empty or contains null: {path}")
                return None
            return data
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON in {path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error reading {path}: {e}")
        return None


def load_ttest_results() -> Optional[Dict[str, Any]]:
    """Load paired t-test results from T025."""
    return load_json_file(TTEST_RESULTS_PATH)


def load_lme_results() -> Optional[Dict[str, Any]]:
    """Load mixed-effects model results from T027."""
    return load_json_file(LME_RESULTS_PATH)


def load_bland_altman_info() -> Optional[Dict[str, Any]]:
    """Load Bland-Altman plot metadata (filenames) from T028."""
    return load_json_file(BLAND_ALTMAN_META_PATH)


def load_heterogeneity_info() -> Optional[Dict[str, Any]]:
    """Load heterogeneity (I²) and pooled effect size from T029."""
    return load_json_file(HETEROGENEITY_PATH)


def load_failure_log_summary() -> Optional[Dict[str, Any]]:
    """Load the failure log summary from T030b."""
    # T030b produces failure_log.json which is a list of objects.
    # We might want to aggregate this into counts or a summary,
    # but for the stat_summary.json we can include the raw list or a summary.
    # Per SC-002/SC-004, we need to ensure keys are present.
    data = load_json_file(FAILURE_LOG_PATH)
    if data:
        # If it's a list, we can compute a simple summary of failure modes
        if isinstance(data, list):
            failure_counts = {}
            for item in data:
                mode = item.get("failure_mode", "unknown")
                failure_counts[mode] = failure_counts.get(mode, 0) + 1
            return {
                "total_failures": len(data),
                "failure_counts": failure_counts,
                "raw_log": data
            }
        return data
    return None


def aggregate_stat_summary(
    ttest_data: Optional[Dict[str, Any]],
    lme_data: Optional[Dict[str, Any]],
    bland_altman_data: Optional[Dict[str, Any]],
    hetero_data: Optional[Dict[str, Any]],
    failure_data: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Merge all statistical results into a single dictionary.
    Ensures all keys required by SC-002 and SC-004 are present.
    """
    summary: Dict[str, Any] = {
        "t_test_results": ttest_data or {},
        "mixed_effects_model": lme_data or {},
        "bland_altman_plots": bland_altman_data or {},
        "heterogeneity": hetero_data or {},
        "failure_log_summary": failure_data or {},
        "metadata": {
            "aggregated_at": None,  # Will be set by caller if needed, or left null
            "source_tasks": ["T025", "T027", "T028", "T029", "T030b"]
        }
    }

    # Ensure SC-002 keys (t-test) are present (even if empty dict if missing)
    # SC-002 requires t-test p-values.
    if not summary["t_test_results"]:
        logger.warning("No t-test results found; ensuring structure exists.")
        summary["t_test_results"] = {
            "mae": {"t_statistic": None, "p_value": None, "significant": None},
            "r2": {"t_statistic": None, "p_value": None, "significant": None},
            "rho": {"t_statistic": None, "p_value": None, "significant": None},
            "bonferroni_corrected": False # Or True if applied
        }

    # Ensure SC-004 keys (LME variance explained) are present
    # SC-004 requires 'variance_explained_original_factors'
    if not summary["mixed_effects_model"]:
        logger.warning("No LME results found; ensuring structure exists.")
        summary["mixed_effects_model"] = {
            "variance_explained_original_factors": None,
            "random_intercepts_variance": None,
            "residual_variance": None,
            "fixed_effects": {}
        }

    # Ensure Bland-Altman filenames are recorded
    if not summary["bland_altman_plots"]:
        summary["bland_altman_plots"] = {"filenames": []}

    # Ensure Heterogeneity metrics are present
    if not summary["heterogeneity"]:
        summary["heterogeneity"] = {
            "I2": None,
            "pooled_effect_size": None,
            "confidence_interval": None
        }

    return summary


def main():
    """Main entry point for the Stat Summary Aggregator."""
    logger.info("Starting Stat Summary Aggregation (T031)...")

    # Ensure output directory exists
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Load all components
    ttest_data = load_ttest_results()
    lme_data = load_lme_results()
    bland_altman_data = load_bland_altman_info()
    hetero_data = load_heterogeneity_info()
    failure_data = load_failure_log_summary()

    # Aggregate
    final_summary = aggregate_stat_summary(
        ttest_data,
        lme_data,
        bland_altman_data,
        hetero_data,
        failure_data
    )

    # Write output
    try:
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(final_summary, f, indent=2)
        logger.info(f"Successfully wrote stat summary to {OUTPUT_PATH}")
        print(f"Output written to: {OUTPUT_PATH}")
    except Exception as e:
        logger.error(f"Failed to write output file: {e}")
        raise

    return final_summary


if __name__ == "__main__":
    main()