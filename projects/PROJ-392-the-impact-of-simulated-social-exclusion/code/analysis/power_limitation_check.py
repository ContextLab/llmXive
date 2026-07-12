"""
Power Limitation Check for Social Exclusion fMRI Study.

This module implements the power limitation check required for T029.
It reads the beta estimates or summary statistics to determine sample sizes
per group (Excluded vs Included). If N < 20 per group, it flags the study
as exploratory and appends a recommendation for future studies (>=30 participants)
to the summary report.

Dependencies:
- code/utils/framing_validator.py (for report manipulation consistency)
- code/config/loader.py (for path configuration)
"""

import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Import config loader to ensure paths are consistent with project structure
# Using the existing API surface: code/config/loader.py
try:
    from config.loader import get_config, get_path
except ImportError:
    # Fallback for direct execution context if config/loader.py is not in path
    # In a real run, the pipeline runner sets up the path correctly.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from config.loader import get_config, get_path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

MIN_EXPLORATORY_THRESHOLD = 20
RECOMMENDED_SAMPLE_SIZE = 30

def load_sample_sizes_from_betas(betas_path: Path) -> Dict[str, int]:
    """
    Loads beta estimates CSV and counts unique participants per group.
    
    Expected columns: participant_id, group, roi, event_type, beta_value
    Returns: Dict mapping group name to count of unique participants.
    """
    if not betas_path.exists():
        logger.warning(f"Beta estimates file not found at {betas_path}. Cannot calculate sample size.")
        return {"excluded": 0, "included": 0}

    participants_by_group: Dict[str, set] = {"excluded": set(), "included": set()}
    
    try:
        with open(betas_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                group = row.get('group', '').lower()
                pid = row.get('participant_id', '')
                if group in participants_by_group and pid:
                    participants_by_group[group].add(pid)
    except Exception as e:
        logger.error(f"Failed to read beta estimates: {e}")
        return {"excluded": 0, "included": 0}

    return {k: len(v) for k, v in participants_by_group.items()}

def load_sample_sizes_from_metrics(metrics_path: Path) -> Dict[str, int]:
    """
    Attempts to load sample sizes from preprocessing metrics if betas are not available.
    Fallback method.
    """
    if not metrics_path.exists():
        return {"excluded": 0, "included": 0}
    
    try:
        with open(metrics_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Assuming metrics might contain group counts directly or derived from subject lists
            # This is a heuristic based on common pipeline outputs
            if 'group_counts' in data:
                return data['group_counts']
            if 'subjects' in data:
                # Count by group if structure allows
                return {"excluded": 0, "included": 0} # Simplified fallback
    except Exception as e:
        logger.error(f"Failed to read metrics: {e}")
    
    return {"excluded": 0, "included": 0}

def check_power_limitation(sample_sizes: Dict[str, int]) -> Tuple[bool, str]:
    """
    Evaluates if sample size meets the threshold.
    
    Returns:
        Tuple[is_exploratory, message]
    """
    min_n = min(sample_sizes.get('excluded', 0), sample_sizes.get('included', 0))
    
    if min_n < MIN_EXPLORATORY_THRESHOLD:
        msg = (
            f"⚠ POWER LIMITATION DETECTED: Sample size ({min_n} per group) is below "
            f"the recommended threshold of {MIN_EXPLORATORY_THRESHOLD} participants per group. "
            f"Findings are flagged as EXPLORATORY. "
            f"Future studies should aim for at least {RECOMMENDED_SAMPLE_SIZE} participants per group "
            f"to achieve adequate statistical power (80%) for medium effect sizes."
        )
        return True, msg
    
    msg = (
        f"Sample size ({min_n} per group) meets the minimum threshold of {MIN_EXPLORATORY_THRESHOLD}. "
        f"Results are considered robust for the current sample."
    )
    return False, msg

def append_to_report(report_path: Path, message: str) -> bool:
    """
    Appends the power limitation message to the summary report.
    Ensures the report exists first.
    """
    if not report_path.parent.exists():
        report_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Check if report exists and has content
        if report_path.exists():
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Avoid duplicate appends if run multiple times (simple check)
            if "POWER LIMITATION" in content:
                logger.info("Power limitation note already present in report.")
                return True
        else:
            content = "# Summary Report\n\n"

        with open(report_path, 'a', encoding='utf-8') as f:
            f.write("\n---\n")
            f.write("## Power Analysis & Limitations\n\n")
            f.write(f"{message}\n")
        
        logger.info(f"Power limitation check appended to {report_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to append to report: {e}")
        return False

def run_power_limitation_check(
    betas_path: Optional[Path] = None,
    metrics_path: Optional[Path] = None,
    report_path: Optional[Path] = None
) -> bool:
    """
    Main execution function for T029.
    """
    # Resolve paths if not provided
    if report_path is None:
        report_path = get_path("data/results/summary_report.md")
    
    if betas_path is None:
        betas_path = get_path("data/results/beta_estimates.csv")
    
    if metrics_path is None:
        metrics_path = get_path("data/results/preprocessing_metrics.json")

    logger.info(f"Checking power limits. Betas: {betas_path}, Report: {report_path}")

    # 1. Load sample sizes
    sample_sizes = load_sample_sizes_from_betas(betas_path)
    
    # Fallback to metrics if betas are missing (though betas are preferred for group counts)
    if sample_sizes['excluded'] == 0 and sample_sizes['included'] == 0:
        logger.info("No participants found in betas. Trying metrics...")
        sample_sizes = load_sample_sizes_from_metrics(metrics_path)

    # 2. Check power
    is_exploratory, message = check_power_limitation(sample_sizes)
    
    # 3. Update report
    if is_exploratory:
        success = append_to_report(report_path, message)
        if not success:
            logger.error("Failed to update report with power limitation warning.")
            return False
    else:
        # Even if not exploratory, we might want to log the status in the report
        # but the task specifically asks to flag if N < 20.
        logger.info(f"Sample size sufficient ({sample_sizes}). No exploratory flag needed.")
        # Optional: Append a confirmation note if the report is empty or for completeness
        # For now, we only modify the report if the limitation exists, as per strict task description.
    
    return True

def main():
    parser = argparse.ArgumentParser(description="T029: Power Limitation Check")
    parser.add_argument("--betas", type=str, help="Path to beta_estimates.csv")
    parser.add_argument("--metrics", type=str, help="Path to preprocessing_metrics.json")
    parser.add_argument("--report", type=str, help="Path to summary_report.md")
    
    args = parser.parse_args()
    
    betas = Path(args.betas) if args.betas else None
    metrics = Path(args.metrics) if args.metrics else None
    report = Path(args.report) if args.report else None
    
    success = run_power_limitation_check(betas, metrics, report)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()