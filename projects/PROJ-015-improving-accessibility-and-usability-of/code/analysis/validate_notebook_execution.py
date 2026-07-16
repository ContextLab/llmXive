import os
import sys
import pandas as pd
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)

def validate_metrics_csv(path: str) -> Tuple[bool, List[str]]:
    """
    Validates that metrics_summary.csv exists and has required columns.
    """
    errors = []
    required_columns = ['metric_name', 'interface_type', 'F_statistic', 'p_value', 'adjusted_p_value', 'effect_size']
    
    if not os.path.exists(path):
        return False, [f"File not found: {path}"]
    
    try:
        df = pd.read_csv(path)
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            errors.append(f"Missing columns: {missing_cols}")
        if df.empty:
            errors.append("CSV is empty")
    except Exception as e:
        errors.append(f"Error reading CSV: {e}")
    
    return len(errors) == 0, errors

def validate_plots(plots_dir: str) -> Tuple[bool, List[str]]:
    """
    Validates that expected plot files exist and are non-empty.
    """
    errors = []
    expected_plots = [
        "boxplot_completion_time.png",
        "boxplot_sus.png",
        "boxplot_error_count.png"
    ]
    
    if not os.path.exists(plots_dir):
        return False, [f"Directory not found: {plots_dir}"]
    
    for plot in expected_plots:
        full_path = os.path.join(plots_dir, plot)
        if not os.path.exists(full_path):
            errors.append(f"Missing plot: {plot}")
        elif os.path.getsize(full_path) == 0:
            errors.append(f"Empty plot: {plot}")
    
    return len(errors) == 0, errors

def write_log(log_path: str, success: bool, errors: List[str]):
    """Writes the validation log."""
    with open(log_path, "w") as f:
        if success:
            f.write("PASS\n")
        else:
            f.write("FAIL\n")
            f.write("\n".join(errors))
    logger.info(f"Validation log written to {log_path}")

def main():
    """
    Main entry point for validation.
    Checks metrics CSV and plots, then writes the log.
    """
    # Paths relative to project root
    project_root = Path(__file__).parent.parent
    metrics_path = project_root / "data" / "processed" / "metrics_summary.csv"
    plots_dir = project_root / "data" / "processed"
    log_path = project_root / "data" / "processed" / "notebook_execution_log.txt"

    # Ensure processed directory exists
    plots_dir.mkdir(parents=True, exist_ok=True)

    # Validate Metrics
    metrics_ok, metrics_errs = validate_metrics_csv(str(metrics_path))
    
    # Validate Plots (if metrics are ok, we still check plots)
    plots_ok, plots_errs = validate_plots(str(plots_dir))
    
    all_errors = metrics_errs + plots_errs
    success = metrics_ok and plots_ok

    write_log(str(log_path), success, all_errors)

    if success:
        print("Validation PASSED")
        return 0
    else:
        print("Validation FAILED")
        for err in all_errors:
            print(f"  - {err}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
