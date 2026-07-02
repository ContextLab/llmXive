"""
Task T006: Run power analysis and write result to logs/power_analysis.log.

Uses the utility functions from code/utils/power_analysis.py.
Reads sample counts from the search result files generated in T002/T003.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.utils.power_analysis import (
    calculate_sample_size_for_correlation,
    calculate_power_for_correlation,
    run_analysis
)

# Configuration
TARGET_CORRELATION = 0.5
ALPHA = 0.05
TARGET_POWER = 0.80
MIN_SAMPLE_SIZE = 28

def load_search_results(file_path: Path) -> List[Dict[str, Any]]:
    """Load JSON search results and count unique samples."""
    if not file_path.exists():
        return []
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Extract series IDs or sample counts depending on structure
    # Based on T002/T003, these files contain list of series metadata
    items = data if isinstance(data, list) else data.get('results', [])
    return items

def count_unique_samples(items: List[Dict[str, Any]]) -> int:
    """Estimate unique samples from search results."""
    # Heuristic: Sum 'total_count' if available, or count items if they represent samples
    total = 0
    for item in items:
        if 'total_count' in item:
            total += item['total_count']
        elif 'samples' in item:
            total += len(item['samples'])
        else:
            # Fallback: treat each item as a series with at least 1 sample
            total += 1
    return total

def main():
    # Setup logging to file
    log_dir = project_root / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'power_analysis.log'
    
    # Clear existing handlers to avoid duplicates if run multiple times
    logger = logging.getLogger('power_analysis')
    logger.setLevel(logging.INFO)
    logger.handlers = []
    
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Also print to stdout for immediate feedback
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.info("Starting Power Analysis (Task T006)")
    logger.info(f"Target Correlation (r): {TARGET_CORRELATION}")
    logger.info(f"Alpha: {ALPHA}")
    logger.info(f"Target Power: {TARGET_POWER}")
    logger.info(f"Minimum Required Sample Size: {MIN_SAMPLE_SIZE}")
    logger.info("-" * 50)

    # Load data from previous tasks
    geo_arabidopsis_file = project_root / 'data' / 'raw' / 'geo_arabidopsis_search.json'
    geo_solanum_file = project_root / 'data' / 'raw' / 'geo_solanum_search.json'

    arabidopsis_items = load_search_results(geo_arabidopsis_file)
    solanum_items = load_search_results(geo_solanum_file)

    n_arabidopsis = count_unique_samples(arabidopsis_items)
    n_solanum = count_unique_samples(solanum_items)
    total_n = n_arabidopsis + n_solanum

    logger.info(f"Available samples (Arabidopsis): {n_arabidopsis}")
    logger.info(f"Available samples (Solanum): {n_solanum}")
    logger.info(f"Total available samples: {total_n}")

    # Calculate required sample size for target power
    required_n = calculate_sample_size_for_correlation(
        r=TARGET_CORRELATION,
        alpha=ALPHA,
        power=TARGET_POWER
    )
    
    logger.info(f"Required sample size for r={TARGET_CORRELATION}, power={TARGET_POWER}: {required_n}")

    # Calculate actual power with available samples
    if total_n > 3:
        actual_power = calculate_power_for_correlation(
            n=total_n,
            r=TARGET_CORRELATION,
            alpha=ALPHA
        )
    else:
        actual_power = 0.0

    logger.info(f"Actual statistical power with n={total_n}: {actual_power:.4f}")

    # Determine status
    is_sufficient = total_n >= MIN_SAMPLE_SIZE and actual_power >= TARGET_POWER
    
    log_entry = {
        "task_id": "T006",
        "target_r": TARGET_CORRELATION,
        "alpha": ALPHA,
        "target_power": TARGET_POWER,
        "available_n": total_n,
        "required_n": required_n,
        "actual_power": actual_power,
        "meets_minimum_n": total_n >= MIN_SAMPLE_SIZE,
        "meets_power_target": actual_power >= TARGET_POWER,
        "status": "PASS" if is_sufficient else "WARNING"
    }

    logger.info("-" * 50)
    if is_sufficient:
        logger.info("Power analysis PASSED. Pipeline can proceed to modeling.")
    else:
        logger.warning("Power analysis WARNING: Sample size or power is insufficient.")
        if total_n < MIN_SAMPLE_SIZE:
            logger.warning(f"Sample size ({total_n}) is below minimum threshold ({MIN_SAMPLE_SIZE}).")
            logger.warning("Modeling HALTED due to insufficient sample size.")
        if actual_power < TARGET_POWER:
            logger.warning(f"Statistical power ({actual_power:.4f}) is below target ({TARGET_POWER}).")
            logger.warning("Modeling HALTED due to low statistical power.")
    
    logger.info("Analysis complete. Results written to logs/power_analysis.log")

    # Write summary to a JSON file for programmatic access if needed
    # (Optional, but good practice for pipeline state)
    # However, task specifically asks for logs/power_analysis.log which we did.
    # We ensure the log file contains the critical decision.

    if not is_sufficient:
        # If power is insufficient, we don't abort the whole pipeline (as per T006 spec),
        # but we log that modeling should halt.
        # The task says: "halt **modeling** (do not abort the entire pipeline)"
        # This is a log message, downstream tasks (modeling) should check this log or return code.
        pass

if __name__ == "__main__":
    main()
