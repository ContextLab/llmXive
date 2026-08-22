import json
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

# Ensure project root is in path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from validation import load_json_file, save_json_file, calculate_file_checksum, update_checksums

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATA_RAW_DIR = project_root / "data" / "raw"
LOC_FILE = DATA_RAW_DIR / "repo_loc_raw.json"
CC_FILE = DATA_RAW_DIR / "repo_cc_raw.json"
RUBRIC_INTERMEDIATE_FILE = DATA_RAW_DIR / "repo_selection_rubric_intermediate.json"
OUTPUT_SELECTION_FILE = DATA_RAW_DIR / "repo_selection_rubric.json"
OUTPUT_REPORT_FILE = DATA_RAW_DIR / "repo_matching_report.json"

TOLERANCE_PERCENT = 0.15  # ±15% tolerance

def load_metrics_data() -> Dict[str, Dict[str, Any]]:
    """
    Loads LOC, CC, and Rubric data, merging them into a single structure keyed by repo.
    """
    loc_data = load_json_file(LOC_FILE)
    cc_data = load_json_file(CC_FILE)
    rubric_data = load_json_file(RUBRIC_INTERMEDIATE_FILE)

    merged = {}

    # Index LOC by repo path (assuming key is repo path or name)
    for repo, metrics in loc_data.items():
        merged[repo] = {"loc": metrics.get("total", 0)}

    # Index CC
    for repo, metrics in cc_data.items():
        if repo in merged:
            merged[repo]["cc"] = metrics.get("total", 0)
        else:
            # If repo exists in CC but not LOC, initialize
            merged[repo] = {"loc": 0, "cc": metrics.get("total", 0)}

    # Index Rubric scores (only those that passed the rubric filter)
    for repo, score in rubric_data.items():
        if repo in merged:
            merged[repo]["doc_score"] = score
        else:
            # If repo passed rubric but missing metrics, skip or handle
            logger.warning(f"Repo {repo} passed rubric but missing LOC/CC data. Skipping.")
            del merged[repo]

    return merged

def calculate_baseline_stats(metrics: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculates the median LOC and CC of the initial candidate pool.
    """
    loc_values = [m["loc"] for m in metrics.values()]
    cc_values = [m["cc"] for m in metrics.values()]

    if not loc_values or not cc_values:
        raise ValueError("No data available to calculate baseline stats.")

    # Sort for median calculation
    loc_values.sort()
    cc_values.sort()

    def median(vals):
        n = len(vals)
        mid = n // 2
        if n % 2 == 0:
            return (vals[mid - 1] + vals[mid]) / 2
        return vals[mid]

    return {
        "median_loc": median(loc_values),
        "median_cc": median(cc_values)
    }

def filter_by_thresholds(metrics: Dict[str, Dict[str, Any]], baseline: Dict[str, float]) -> tuple:
    """
    Filters repositories based on the ±15% tolerance of the baseline median.
    Returns (accepted_repos, rejected_repos, report_details).
    """
    accepted = {}
    rejected = {}
    report_details = []

    lower_loc = baseline["median_loc"] * (1 - TOLERANCE_PERCENT)
    upper_loc = baseline["median_loc"] * (1 + TOLERANCE_PERCENT)
    lower_cc = baseline["median_cc"] * (1 - TOLERANCE_PERCENT)
    upper_cc = baseline["median_cc"] * (1 + TOLERANCE_PERCENT)

    logger.info(f"Baseline Median LOC: {baseline['median_loc']}, CC: {baseline['median_cc']}")
    logger.info(f"Acceptable Range LOC: [{lower_loc:.2f}, {upper_loc:.2f}]")
    logger.info(f"Acceptable Range CC: [{lower_cc:.2f}, {upper_cc:.2f}]")

    for repo, data in metrics.items():
        loc = data["loc"]
        cc = data["cc"]
        doc_score = data.get("doc_score", 0)

        loc_pass = lower_loc <= loc <= upper_loc
        cc_pass = lower_cc <= cc <= upper_cc

        status = "accepted" if (loc_pass and cc_pass) else "rejected"
        reason = []
        if not loc_pass:
            reason.append(f"LOC {loc} outside range [{lower_loc:.0f}, {upper_loc:.0f}]")
        if not cc_pass:
            reason.append(f"CC {cc} outside range [{lower_cc:.0f}, {upper_cc:.0f}]")

        entry = {
            "repo": repo,
            "loc": loc,
            "cc": cc,
            "doc_score": doc_score,
            "status": status,
            "reason": "; ".join(reason) if reason else "Within tolerance"
        }
        report_details.append(entry)

        if status == "accepted":
            accepted[repo] = {
                "loc": loc,
                "cc": cc,
                "doc_score": doc_score
            }
        else:
            rejected[repo] = entry

    return accepted, rejected, report_details

def main():
    """
    Main entry point for T021f: Filter repositories based on metric thresholds.
    """
    logger.info("Starting T021f: Repository Metric Threshold Filtering")

    # Ensure output directory exists
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Load Data
        logger.info("Loading metric data...")
        metrics = load_metrics_data()

        if not metrics:
            raise ValueError("No repository metrics found. Ensure T021a, T021b, and T021d have run.")

        # 2. Calculate Baseline
        logger.info("Calculating baseline statistics...")
        baseline = calculate_baseline_stats(metrics)

        # 3. Filter by Thresholds
        logger.info("Filtering repositories by thresholds...")
        accepted, rejected, report_details = filter_by_thresholds(metrics, baseline)

        # 4. Save Outputs
        logger.info(f"Saving {len(accepted)} accepted repos to {OUTPUT_SELECTION_FILE}")
        save_json_file(OUTPUT_SELECTION_FILE, accepted)

        logger.info(f"Saving matching report ({len(report_details)} entries) to {OUTPUT_REPORT_FILE}")
        report_payload = {
            "baseline_stats": baseline,
            "tolerance_percent": TOLERANCE_PERCENT,
            "accepted_count": len(accepted),
            "rejected_count": len(rejected),
            "details": report_details
        }
        save_json_file(OUTPUT_REPORT_FILE, report_payload)

        # Update checksums
        update_checksums(OUTPUT_SELECTION_FILE)
        update_checksums(OUTPUT_REPORT_FILE)

        logger.info("T021f completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Missing input file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
