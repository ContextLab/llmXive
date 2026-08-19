"""
T021d: Execute quantitative matching logic per Spec FR-009.

Compares LOC/CC of candidate repos against a baseline to filter and exclude
repos failing the ±15% tolerance.

Inputs:
  - data/raw/repo_metrics.json (Output of T021c)
  - data/raw/baseline_metrics.json (Hardcoded baseline per spec)

Outputs:
  - data/raw/repo_selection_rubric.json (Accepted repos)
  - data/raw/repo_matching_report.json (Excluded repos, stats)
"""
import json
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any

# Configure logging to stdout for execution visibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
TOLERANCE_PERCENTAGE = 0.15  # ±15%
INPUT_METRICS_PATH = "data/raw/repo_metrics.json"
BASELINE_METRICS_PATH = "data/raw/baseline_metrics.json"
OUTPUT_RUBRIC_PATH = "data/raw/repo_selection_rubric.json"
OUTPUT_REPORT_PATH = "data/raw/repo_matching_report.json"

def load_json_file(path: str) -> Dict[str, Any]:
    """Load JSON from a file path."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Required input file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(path: str, data: Any) -> None:
    """Save data to a JSON file, ensuring directory exists."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved output to: {path}")

def calculate_baseline_stats(baseline_data: Dict[str, Any]) -> Dict[str, float]:
    """Calculate mean LOC and CC from baseline repos."""
    repos = baseline_data.get("repos", [])
    if not repos:
        raise ValueError("Baseline metrics file contains no repos.")
    
    locs = [r["loc"] for r in repos]
    ccs = [r["cc"] for r in repos]
    
    return {
        "mean_loc": sum(locs) / len(locs),
        "mean_cc": sum(ccs) / len(ccs)
    }

def evaluate_matching_quality(
    candidate_metrics: Dict[str, Any],
    baseline_stats: Dict[str, float]
) -> Dict[str, Any]:
    """
    Compare candidate repos against baseline stats.
    Filter out repos where LOC or CC deviates > 15% from baseline mean.
    
    Returns:
      Dictionary containing:
        - accepted_repos: List of repos passing tolerance
        - excluded_repos: List of repos failing tolerance with reasons
        - mean_difference_loc: Mean absolute % difference of accepted repos
        - mean_difference_cc: Mean absolute % difference of accepted repos
        - total_accepted: Count
        - total_excluded: Count
    """
    candidates = candidate_metrics.get("repos", [])
    mean_loc = baseline_stats["mean_loc"]
    mean_cc = baseline_stats["mean_cc"]
    
    accepted = []
    excluded = []
    loc_diffs = []
    cc_diffs = []
    
    for repo in candidates:
        repo_id = repo.get("repo_id")
        loc = repo.get("loc")
        cc = repo.get("cc")
        
        if loc is None or cc is None:
            excluded.append({
                "repo_id": repo_id,
                "reason": "Missing LOC or CC metrics"
            })
            continue
        
        # Calculate percentage deviation
        loc_deviation = abs(loc - mean_loc) / mean_loc
        cc_deviation = abs(cc - mean_cc) / mean_cc
        
        is_accepted = True
        reasons = []
        
        if loc_deviation > TOLERANCE_PERCENTAGE:
            is_accepted = False
            reasons.append(f"LOC deviation {loc_deviation:.2%} > {TOLERANCE_PERCENTAGE:.0%}")
        
        if cc_deviation > TOLERANCE_PERCENTAGE:
            is_accepted = False
            reasons.append(f"CC deviation {cc_deviation:.2%} > {TOLERANCE_PERCENTAGE:.0%}")
        
        if is_accepted:
            accepted.append(repo)
            loc_diffs.append(loc_deviation)
            cc_diffs.append(cc_deviation)
        else:
            excluded.append({
                "repo_id": repo_id,
                "loc": loc,
                "cc": cc,
                "reasons": reasons
            })
    
    # Calculate mean differences for accepted repos
    mean_loc_diff = sum(loc_diffs) / len(loc_diffs) if loc_diffs else 0.0
    mean_cc_diff = sum(cc_diffs) / len(cc_diffs) if cc_diffs else 0.0
    
    return {
        "accepted_repos": accepted,
        "excluded_repos": excluded,
        "mean_difference_loc": mean_loc_diff,
        "mean_difference_cc": mean_cc_diff,
        "total_accepted": len(accepted),
        "total_excluded": len(excluded),
        "baseline_stats": baseline_stats,
        "tolerance_applied": TOLERANCE_PERCENTAGE
    }

def main():
    """Main entry point for T021d execution."""
    logger.info("Starting T021d: Repository Matching & Filtering")
    
    # 1. Load Input Data
    try:
        candidate_metrics = load_json_file(INPUT_METRICS_PATH)
        logger.info(f"Loaded candidate metrics from {INPUT_METRICS_PATH}")
        
        baseline_metrics = load_json_file(BASELINE_METRICS_PATH)
        logger.info(f"Loaded baseline metrics from {BASELINE_METRICS_PATH}")
    except FileNotFoundError as e:
        logger.error(str(e))
        logger.error("T021d cannot proceed without input files. Ensure T021c has run.")
        sys.exit(1)
    
    # 2. Calculate Baseline Statistics
    baseline_stats = calculate_baseline_stats(baseline_metrics)
    logger.info(f"Baseline Stats: Mean LOC={baseline_stats['mean_loc']:.2f}, Mean CC={baseline_stats['mean_cc']:.2f}")
    
    # 3. Evaluate Matching & Filter
    results = evaluate_matching_quality(candidate_metrics, baseline_stats)
    
    # 4. Generate Outputs
    
    # Output A: repo_selection_rubric.json (Accepted repos only)
    rubric_output = {
        "accepted_repos": results["accepted_repos"],
        "criteria": f"LOC/CC within ±{int(TOLERANCE_PERCENTAGE*100)}% of baseline",
        "baseline_stats": baseline_stats
    }
    save_json_file(OUTPUT_RUBRIC_PATH, rubric_output)
    
    # Output B: repo_matching_report.json (Full report including excluded)
    report_output = {
        "summary": {
            "total_accepted": results["total_accepted"],
            "total_excluded": results["total_excluded"],
            "mean_difference_loc": results["mean_difference_loc"],
            "mean_difference_cc": results["mean_difference_cc"]
        },
        "excluded_repos": results["excluded_repos"],
        "tolerance_percentage": TOLERANCE_PERCENTAGE
    }
    save_json_file(OUTPUT_REPORT_PATH, report_output)
    
    logger.info("T021d completed successfully.")
    logger.info(f"Accepted: {results['total_accepted']}, Excluded: {results['total_excluded']}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
