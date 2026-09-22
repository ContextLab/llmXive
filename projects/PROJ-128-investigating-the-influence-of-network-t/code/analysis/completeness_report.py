import os
import json
import sys
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List

# Ensure we can import from the project root if run as a script
# The project structure expects imports relative to the root
try:
    from config import get_config_dict
except ImportError:
    # Fallback if run directly without path setup
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from config import get_config_dict


def load_exclusion_log(log_path: str) -> List[Dict[str, Any]]:
    """Load the exclusion log JSON file."""
    if not os.path.exists(log_path):
        return []
    try:
        with open(log_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load exclusion log at {log_path}: {e}")
        return []


def load_structural_metrics(csv_path: str) -> pd.DataFrame:
    """Load the structural metrics CSV file."""
    if not os.path.exists(csv_path):
        return pd.DataFrame()
    try:
        return pd.read_csv(csv_path)
    except (pd.errors.EmptyDataError, IOError) as e:
        print(f"Warning: Could not load structural metrics at {csv_path}: {e}")
        return pd.DataFrame()


def calculate_completeness_report(
    exclusion_log: List[Dict[str, Any]],
    structural_metrics: pd.DataFrame,
    total_cohort_size: int
) -> Dict[str, Any]:
    """
    Calculate the data completeness report.

    Args:
        exclusion_log: List of exclusion records from data/logs/exclusion_log.json
        structural_metrics: DataFrame of processed structural metrics
        total_cohort_size: Total number of subjects in the original cohort

    Returns:
        Dictionary containing the completeness report metrics
    """
    # Count processed subjects
    processed_count = len(structural_metrics)
    excluded_count = len(exclusion_log)

    # Calculate percentage
    if total_cohort_size > 0:
        completion_percentage = (processed_count / total_cohort_size) * 100
        exclusion_percentage = (excluded_count / total_cohort_size) * 100
    else:
        completion_percentage = 0.0
        exclusion_percentage = 0.0

    # Categorize exclusion reasons
    reason_counts: Dict[str, int] = {}
    for record in exclusion_log:
        reason = record.get('reason', 'unknown')
        reason_counts[reason] = reason_counts.get(reason, 0) + 1

    report = {
        "total_cohort_size": total_cohort_size,
        "processed_count": processed_count,
        "excluded_count": excluded_count,
        "completion_percentage": round(completion_percentage, 2),
        "exclusion_percentage": round(exclusion_percentage, 2),
        "exclusion_reasons": reason_counts,
        "report_generated_from": {
            "exclusion_log_path": "data/logs/exclusion_log.json",
            "structural_metrics_path": "data/processed/structural_metrics.csv"
        }
    }

    return report


def main():
    """Main entry point for generating the completeness report."""
    config = get_config_dict()
    base_dir = Path(config.get('PROJECT_ROOT', Path.cwd()))
    
    # Define paths based on project structure
    exclusion_log_path = base_dir / "data" / "logs" / "exclusion_log.json"
    structural_metrics_path = base_dir / "data" / "processed" / "structural_metrics.csv"
    output_path = base_dir / "data" / "processed" / "completeness_report.json"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load data
    exclusion_log = load_exclusion_log(str(exclusion_log_path))
    structural_metrics = load_structural_metrics(str(structural_metrics_path))

    # Determine total cohort size
    # We infer this from the union of processed and excluded subjects if possible,
    # or rely on a known constant if the cohort size is fixed in the config.
    # For HCP 1200, the cohort is typically 1200, but we might have a smaller subset.
    # We will try to infer from the unique subject IDs in the exclusion log + metrics.
    
    processed_subjects = set(structural_metrics['subject_id'].tolist()) if not structural_metrics.empty else set()
    excluded_subjects = set(record['subject_id'] for record in exclusion_log if 'subject_id' in record)
    
    inferred_cohort_size = len(processed_subjects | excluded_subjects)
    
    # If we can't infer, we might need to check a manifest or config. 
    # For now, we use the inferred size. If 0, we report 0 to avoid division by zero.
    total_cohort_size = inferred_cohort_size if inferred_cohort_size > 0 else 0

    print(f"Processing completeness report...")
    print(f"  - Exclusion log entries: {len(exclusion_log)}")
    print(f"  - Processed subjects: {len(processed_subjects)}")
    print(f"  - Inferred cohort size: {total_cohort_size}")

    if total_cohort_size == 0:
        print("Warning: Could not determine cohort size. Report will show 0% completion.")
        report = calculate_completeness_report(exclusion_log, structural_metrics, 0)
    else:
        report = calculate_completeness_report(exclusion_log, structural_metrics, total_cohort_size)

    # Save report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"Completeness report saved to: {output_path}")
    print(f"  - Completion rate: {report['completion_percentage']}%")
    print(f"  - Exclusion breakdown: {report['exclusion_reasons']}")

    return report


if __name__ == "__main__":
    main()
