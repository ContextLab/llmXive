import json
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

# Configure logging to file, ensuring directory exists
LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "matching_report.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_json_file(path: str) -> Dict[str, Any]:
    """Load a JSON file from the given path."""
    logger.info(f"Loading JSON file: {path}")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Required input file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_baseline_stats(metrics_data: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate baseline statistics (mean LOC and mean CC) from the provided metrics.
    This serves as the reference point for the ±15% tolerance check.
    """
    if not metrics_data:
        logger.warning("No metrics data provided for baseline calculation.")
        return {"loc_mean": 0.0, "cc_mean": 0.0}

    loc_values = [m.get("loc", 0) for m in metrics_data if m.get("loc") is not None]
    cc_values = [m.get("cc", 0) for m in metrics_data if m.get("cc") is not None]

    loc_mean = sum(loc_values) / len(loc_values) if loc_values else 0.0
    cc_mean = sum(cc_values) / len(cc_values) if cc_values else 0.0

    logger.info(f"Baseline LOC Mean: {loc_mean:.2f}, CC Mean: {cc_mean:.2f}")
    return {"loc_mean": loc_mean, "cc_mean": cc_mean}

def evaluate_matching_quality(
    metrics_data: List[Dict[str, Any]],
    baseline: Dict[str, float],
    tolerance_pct: float = 15.0
) -> Dict[str, Any]:
    """
    Evaluate matching quality by comparing each repo's LOC/CC against the baseline.
    Calculates the mean difference and the percentage of repos within the tolerance.
    IMPORTANT: This is descriptive only. No repos are excluded.
    """
    if not baseline.get("loc_mean") or not baseline.get("cc_mean"):
        logger.error("Baseline statistics are missing or zero. Cannot evaluate matching.")
        return {}

    loc_baseline = baseline["loc_mean"]
    cc_baseline = baseline["cc_mean"]

    within_loc_tolerance = 0
    within_cc_tolerance = 0
    total_repos = len(metrics_data)
    diffs = []

    for repo in metrics_data:
        loc = repo.get("loc", 0)
        cc = repo.get("cc", 0)
        
        # Calculate absolute percentage difference
        loc_diff_pct = abs((loc - loc_baseline) / loc_baseline * 100) if loc_baseline > 0 else 0
        cc_diff_pct = abs((cc - cc_baseline) / cc_baseline * 100) if cc_baseline > 0 else 0

        diffs.append({
            "repo_id": repo.get("repo_id", "unknown"),
            "loc_diff_pct": loc_diff_pct,
            "cc_diff_pct": cc_diff_pct
        })

        if loc_diff_pct <= tolerance_pct:
            within_loc_tolerance += 1
        if cc_diff_pct <= tolerance_pct:
            within_cc_tolerance += 1

    mean_loc_diff = sum(d["loc_diff_pct"] for d in diffs) / total_repos if total_repos > 0 else 0
    mean_cc_diff = sum(d["cc_diff_pct"] for d in diffs) / total_repos if total_repos > 0 else 0

    result = {
        "baseline": baseline,
        "tolerance_threshold_pct": tolerance_pct,
        "total_repos_analyzed": total_repos,
        "mean_loc_difference_pct": mean_loc_diff,
        "mean_cc_difference_pct": mean_cc_diff,
        "repos_within_loc_tolerance_pct": (within_loc_tolerance / total_repos * 100) if total_repos > 0 else 0,
        "repos_within_cc_tolerance_pct": (within_cc_tolerance / total_repos * 100) if total_repos > 0 else 0,
        "individual_differences": diffs,
        "note": "This report is for descriptive statistics only. Matching exclusion is replaced by ANCOVA (T021g, T036a)."
    }

    logger.info(f"Matching evaluation complete. Mean LOC diff: {mean_loc_diff:.2f}%, Mean CC diff: {mean_cc_diff:.2f}%")
    return result

def main():
    """
    Main entry point for T021d: Execute quantitative matching logic.
    Reads repo_metrics.json, calculates baseline, evaluates matching quality,
    and writes repo_matching_report.json.
    """
    logger.info("Starting T021d: Quantitative Matching Logic")

    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    input_path = project_root / "data" / "raw" / "repo_metrics.json"
    output_path = project_root / "data" / "raw" / "repo_matching_report.json"

    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Load input data
        metrics_data = load_json_file(str(input_path))
        if not isinstance(metrics_data, list):
            metrics_data = [metrics_data]

        # Calculate baseline stats
        baseline = calculate_baseline_stats(metrics_data)

        # Evaluate matching quality
        report = evaluate_matching_quality(metrics_data, baseline)

        # Write output
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Successfully wrote matching report to {output_path}")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during matching report generation: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
