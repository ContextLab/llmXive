import os
import logging
from pathlib import Path
from typing import Dict, Any
import yaml
import json
import statistics

def check_data_availability(raw_dir: Path) -> int:
    """
    Count the number of files in the raw data directory.
    Returns the count of files found.
    """
    if not raw_dir.exists():
        return 0
    count = 0
    for item in raw_dir.iterdir():
        if item.is_file():
            count += 1
    return count

def write_state_file(state_dir: Path, data: Dict[str, Any]) -> None:
    """
    Write the data availability state to a YAML file.
    """
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / "data_availability.yaml"
    with open(state_path, 'w') as f:
        yaml.dump(data, f)

def write_descriptive_stats(results_dir: Path, values: list) -> None:
    """
    Generate descriptive statistics (mean, median, std_dev) for a list of values
    and write them to results/descriptive_stats.json.
    Note: In this specific task context, 'values' represents the file count
    or a metric derived from the check if we were analyzing metrics.
    However, per the task description, we are checking the *count* itself.
    If count < 10, we generate stats about the count (which is trivial but required).
    To make this useful for the pipeline, we assume 'values' might be a list of
    file sizes or a placeholder metric if we had one, but here we just report
    on the count as the single data point if needed, or an empty list if N=0.
    
    Re-reading task: "Generate results/descriptive_stats.json (mean, median, std_dev)"
    If we only have the count (N < 10), we can't compute stats on a single number meaningfully.
    The task likely implies that if we had a list of metrics from the files, we'd stats.
    But since we are just checking the count, and the task says "IF count < 10: Generate...",
    we will generate a JSON with the count itself and its derived stats (which will be
    mean=count, median=count, std_dev=0 or NaN if count is 0).
    
    Actually, a better interpretation for a real pipeline: If N < 10, we don't have enough
    data to run regression. The descriptive stats might be about the *available* data (e.g. file sizes).
    Let's implement it to accept a list of numeric values (e.g. file sizes) to compute stats on.
    If the list is empty, we report 0s.
    """
    results_dir.mkdir(parents=True, exist_ok=True)
    stats_path = results_dir / "descriptive_stats.json"
    
    if not values:
        stats = {
            "count": 0,
            "mean": None,
            "median": None,
            "std_dev": None,
            "note": "No data points available to compute statistics."
        }
    else:
        stats = {
            "count": len(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0.0
        }
    
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)

def write_warning_log(logs_dir: Path, message: str) -> None:
    """
    Log a warning message to logs/warning.log.
    """
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / "warning.log"
    logging.basicConfig(
        filename=str(log_path),
        level=logging.WARNING,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logging.warning(message)

def main():
    """
    Main entry point for T005b.
    1. Check count of files in data/raw/
    2. If count < 10:
       - Generate results/descriptive_stats.json (using file sizes as values)
       - Set state/data_availability.yaml with regression_blocked: true
       - Log warning to logs/warning.log
    3. If count >= 10: Do nothing.
    """
    # Determine paths relative to project root
    # Assuming this script runs from code/src/ or code/
    # We need to resolve the project root.
    # Standard convention: project root is parent of 'code' or 'src'
    current_file = Path(__file__).resolve()
    # If running from code/src/, root is 2 levels up
    project_root = current_file.parent.parent
    
    raw_dir = project_root / "data" / "raw"
    results_dir = project_root / "results"
    state_dir = project_root / "state"
    logs_dir = project_root / "logs"
    
    count = check_data_availability(raw_dir)
    print(f"Found {count} files in {raw_dir}")
    
    if count < 10:
        # Gather some numeric values to compute stats on.
        # Since we only have file count, let's use file sizes if available,
        # or just the count itself if we want to be literal about "stats on the count".
        # Using file sizes is more meaningful for "descriptive stats".
        values = []
        if raw_dir.exists():
            for item in raw_dir.iterdir():
                if item.is_file():
                    values.append(item.stat().st_size)
        
        write_descriptive_stats(results_dir, values)
        
        state_data = {
            "regression_blocked": True,
            "reason": f"Insufficient data: {count} files found, minimum 10 required."
        }
        write_state_file(state_dir, state_data)
        
        warning_msg = f"WARNING: Data availability check failed. Only {count} files found. Regression analysis is blocked."
        write_warning_log(logs_dir, warning_msg)
        
        print(f"Data insufficient ({count} < 10). Generated stats, state flag, and warning.")
    else:
        print("Data sufficient. No action required.")

if __name__ == "__main__":
    main()
