import os
import json
import sys
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List
from config import get_config_dict

def load_exclusion_log(log_path: str) -> List[Dict[str, Any]]:
    """
    Load the exclusion log JSON file.
    Returns an empty list if the file does not exist or is empty.
    """
    path = Path(log_path)
    if not path.exists():
        return []
    try:
        with open(path, 'r') as f:
            data = json.load(f)
            if not isinstance(data, list):
                return []
            return data
    except (json.JSONDecodeError, IOError):
        return []

def load_structural_metrics(csv_path: str) -> pd.DataFrame:
    """
    Load the structural metrics CSV file.
    Returns an empty DataFrame if the file does not exist.
    """
    path = Path(csv_path)
    if not path.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(path)
        return df
    except (pd.errors.EmptyDataError, IOError):
        return pd.DataFrame()

def calculate_completeness_report(
    exclusion_log: List[Dict[str, Any]],
    structural_metrics: pd.DataFrame,
    total_cohort_size: int
) -> Dict[str, Any]:
    """
    Calculate the data completeness report based on exclusion logs and processed metrics.

    Args:
        exclusion_log: List of exclusion records from data/logs/exclusion_log.json
        structural_metrics: DataFrame from data/processed/structural_metrics.csv
        total_cohort_size: Total number of subjects in the cohort

    Returns:
        Dictionary containing completeness statistics
    """
    processed_count = len(structural_metrics)
    excluded_count = len(exclusion_log)

    # Calculate percentage
    if total_cohort_size > 0:
        completion_percentage = (processed_count / total_cohort_size) * 100
    else:
        completion_percentage = 0.0

    # Categorize exclusion reasons
    reason_counts: Dict[str, int] = {}
    for entry in exclusion_log:
        reason = entry.get('reason', 'unknown')
        reason_counts[reason] = reason_counts.get(reason, 0) + 1

    report = {
        "total_cohort_size": total_cohort_size,
        "processed_subjects": processed_count,
        "excluded_subjects": excluded_count,
        "completion_percentage": round(completion_percentage, 2),
        "exclusion_reasons": reason_counts
    }

    return report

def main():
    """
    Main entry point to generate the data completeness report.
    Reads exclusion log and structural metrics, calculates statistics,
    and saves the report to data/processed/completeness_report.json.
    """
    config = get_config_dict()
    base_dir = Path(config.get('PROJECT_ROOT', '.'))

    exclusion_log_path = base_dir / 'data' / 'logs' / 'exclusion_log.json'
    structural_metrics_path = base_dir / 'data' / 'processed' / 'structural_metrics.csv'
    output_path = base_dir / 'data' / 'processed' / 'completeness_report.json'

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load data
    exclusion_log = load_exclusion_log(str(exclusion_log_path))
    structural_metrics = load_structural_metrics(str(structural_metrics_path))

    # Determine total cohort size
    # If structural_metrics exists, we can infer cohort size from processed + excluded
    # Otherwise, we need a way to know the total. For now, we assume the sum of processed and excluded
    # is the best estimate if no external config provides the total.
    total_cohort_size = structural_metrics['subject_id'].nunique() + len(exclusion_log)

    if total_cohort_size == 0:
        print("Warning: No data found to calculate completeness. Cohort size is 0.")
        report = {
            "total_cohort_size": 0,
            "processed_subjects": 0,
            "excluded_subjects": 0,
            "completion_percentage": 0.0,
            "exclusion_reasons": {},
            "message": "No data available. Ensure data loading pipeline has run."
        }
    else:
        report = calculate_completeness_report(
            exclusion_log,
            structural_metrics,
            total_cohort_size
        )

    # Save report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"Completeness report saved to: {output_path}")
    print(f"Total Cohort: {report['total_cohort_size']}, Processed: {report['processed_subjects']}, Excluded: {report['excluded_subjects']}")
    print(f"Completion Rate: {report['completion_percentage']}%")
    if report['exclusion_reasons']:
        print(f"Exclusion Reasons: {report['exclusion_reasons']}")

if __name__ == '__main__':
    main()