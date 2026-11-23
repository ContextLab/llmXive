"""
Review Script for Power and Sensitivity Analysis Results.

Validates that power analysis and sensitivity analysis artifacts
meet the requirements for SC-002 and SC-005.
"""
import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

def load_json_file(file_path: str) -> dict:
    """Load a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def load_csv_file(file_path: str) -> list:
    """Load a CSV file as a list of dicts."""
    import csv
    rows = []
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def validate_power_analysis(power_report_path: str) -> dict:
    """
    Validate power analysis report.
    
    Checks for SC-005:
    - Presence of 'power_status'
    - Presence of 'observed_n' and 'required_n'
    - Presence of 'effect_sizes' and 'power_levels' breakdown
    """
    result = {
        "status": "PASSED",
        "issues": []
    }
    
    if not os.path.exists(power_report_path):
        result["status"] = "FAILED"
        result["issues"].append("Power analysis report file not found.")
        return result
    
    try:
        report = load_json_file(power_report_path)
    except json.JSONDecodeError:
        result["status"] = "FAILED"
        result["issues"].append("Invalid JSON in power analysis report.")
        return result
    
    # Check required fields
    required_fields = ["power_status", "observed_n", "required_n"]
    for field in required_fields:
        if field not in report:
            result["issues"].append(f"Missing required field: {field}")
    
    # Check for detailed breakdown (SC-005 enhancement)
    if "effect_sizes" not in report:
        result["issues"].append("Missing 'effect_sizes' breakdown.")
    if "power_levels" not in report:
        result["issues"].append("Missing 'power_levels' breakdown.")
    
    if result["issues"]:
        result["status"] = "FAILED"
    
    return result

def validate_sensitivity_analysis(sensitivity_csv_path: str) -> dict:
    """
    Validate sensitivity analysis results.
    
    Checks for SC-002:
    - Presence of thresholds (p<0.01, p<0.05, p<0.10)
    - Presence of significant finding counts
    """
    result = {
        "status": "PASSED",
        "issues": []
    }
    
    if not os.path.exists(sensitivity_csv_path):
        result["status"] = "FAILED"
        result["issues"].append("Sensitivity analysis CSV file not found.")
        return result
    
    try:
        rows = load_csv_file(sensitivity_csv_path)
    except Exception as e:
        result["status"] = "FAILED"
        result["issues"].append(f"Error reading CSV: {str(e)}")
        return result
    
    if not rows:
        result["issues"].append("Sensitivity analysis CSV is empty.")
        result["status"] = "FAILED"
        return result
    
    # Check for expected columns
    expected_columns = ["threshold", "significant_count"]
    first_row = rows[0]
    for col in expected_columns:
        if col not in first_row:
            result["issues"].append(f"Missing column in CSV: {col}")
    
    # Check for required thresholds
    thresholds = {row["threshold"] for row in rows}
    required_thresholds = ["0.01", "0.05", "0.10"]
    for thresh in required_thresholds:
        if thresh not in thresholds:
            result["issues"].append(f"Missing threshold: {thresh}")
    
    if result["issues"]:
        result["status"] = "FAILED"
    
    return result

def main():
    parser = argparse.ArgumentParser(description="Review power and sensitivity analysis results.")
    parser.add_argument("--power-report", type=str, default="data/results/power_analysis_report.json", help="Path to power analysis report")
    parser.add_argument("--sensitivity-csv", type=str, default="data/results/sensitivity_analysis.csv", help="Path to sensitivity analysis CSV")
    parser.add_argument("--output", type=str, default="data/results/power_sensitivity_review.json", help="Output review report path")
    
    args = parser.parse_args()
    
    print("Starting power and sensitivity review...")
    
    power_result = validate_power_analysis(args.power_report)
    sensitivity_result = validate_sensitivity_analysis(args.sensitivity_csv)
    
    review_report = {
        "timestamp": str(datetime.now()),
        "power_analysis": power_result,
        "sensitivity_analysis": sensitivity_result,
        "overall_status": "PASSED" if power_result["status"] == "PASSED" and sensitivity_result["status"] == "PASSED" else "FAILED"
    }
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(review_report, f, indent=2)
    
    print(f"Review report written to {output_path}")
    print(f"Overall Status: {review_report['overall_status']}")
    
    if review_report["overall_status"] == "FAILED":
        print("REVIEW FAILED. Please address the issues.")
        sys.exit(1)
    else:
        print("REVIEW PASSED.")
        sys.exit(0)

if __name__ == "__main__":
    main()
