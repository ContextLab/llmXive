import csv
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# Attempt to import logging utilities from sibling module
try:
    from ingest.logging import get_validate_logger
except ImportError:
    # Fallback if module structure differs during isolated execution
    import logging
    def get_validate_logger(name):
        return logging.getLogger(name)

# Constants
REQUIRED_VARIABLES = [
    "tool_usage",
    "task_time",
    "defect_rate",
    "experience_years",
    "task_complexity",
    "project_type",
    "team_size"
]

SPEC_PATH = Path(__file__).parent.parent.parent / "specs" / "001-code-generation-performance-outcomes" / "spec.md"

def get_logger():
    return get_validate_logger("validate")

def get_validate_logger():
    return get_logger()

def load_verified_datasets_from_spec(spec_path: Optional[Path] = None) -> List[Dict]:
    """
    Parses the spec.md file to extract verified datasets from the '# Verified datasets' block.
    Returns a list of dictionaries containing dataset metadata (url, checksum, variables).
    """
    if spec_path is None:
        spec_path = SPEC_PATH

    if not spec_path.exists():
        logger = get_logger()
        logger.warning(f"Spec file not found at {spec_path}. Cannot load verified datasets.")
        return []

    datasets = []
    in_verified_block = False
    current_dataset = {}

    with open(spec_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        stripped = line.strip()

        if "# Verified datasets" in stripped:
            in_verified_block = True
            continue

        if in_verified_block:
            # End of block if we hit another major header
            if stripped.startswith("# ") and "Verified datasets" not in stripped:
                if current_dataset:
                    datasets.append(current_dataset)
                    current_dataset = {}
                in_verified_block = False
                continue

            if not stripped or stripped.startswith("-"):
                continue

            if ":" in stripped:
                key, value = stripped.split(":", 1)
                key = key.strip().lower()
                value = value.strip()

                if key == "url":
                    if current_dataset:
                        datasets.append(current_dataset)
                    current_dataset = {"url": value}
                elif current_dataset:
                    if key == "checksum":
                        current_dataset["checksum"] = value
                    elif key == "variables":
                        # Parse comma-separated variables
                        vars_list = [v.strip() for v in value.split(",")]
                        current_dataset["variables"] = vars_list

    if current_dataset:
        datasets.append(current_dataset)

    return datasets

def load_csv_header(csv_path: Path) -> List[str]:
    """
    Reads the first line of a CSV file and returns the list of column headers.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
            return [col.strip() for col in header]
        except StopIteration:
            return []

def check_csv_variables(headers: List[str], required_vars: List[str]) -> Tuple[bool, List[str]]:
    """
    Checks if all required variables are present in the CSV headers.
    Returns (is_valid, list_of_missing_variables).
    """
    missing = []
    for var in required_vars:
        if var not in headers:
            missing.append(var)
    return len(missing) == 0, missing

def check_tool_usage_variable(headers: List[str]) -> bool:
    """
    Checks specifically for the 'tool_usage' variable.
    Raises ValueError if missing.
    """
    if "tool_usage" not in headers:
        raise ValueError("Missing required variable: tool_usage")
    return True

def check_task_time_variable(headers: List[str]) -> bool:
    """
    Checks specifically for the 'task_time' variable.
    Raises ValueError if missing.
    """
    if "task_time" not in headers:
        raise ValueError("Missing required variable: task_time")
    return True

def check_defect_rate_variable(headers: List[str]) -> bool:
    """
    Checks specifically for the 'defect_rate' variable.
    Raises ValueError if missing.
    """
    if "defect_rate" not in headers:
        raise ValueError("Missing required variable: defect_rate")
    return True

def check_experience_years_variable(headers: List[str]) -> bool:
    """
    Checks specifically for the 'experience_years' variable.
    Raises ValueError if missing.
    
    This function implements the requirement for T012d.
    It verifies that the 'experience_years' column exists in the provided headers.
    """
    if "experience_years" not in headers:
        raise ValueError("Missing required variable: experience_years")
    return True

def identify_missing_experience_values(df) -> List[int]:
    """
    Identifies row indices where 'experience_years' is missing (NaN or None).
    Assumes df is a pandas DataFrame.
    """
    try:
        import pandas as pd
        if 'experience_years' not in df.columns:
            return []
        missing_mask = df['experience_years'].isna()
        return missing_mask[missing_mask].index.tolist()
    except ImportError:
        return []

def calculate_missing_percentage(total_rows: int, missing_count: int) -> float:
    """
    Calculates the percentage of missing entries.
    """
    if total_rows == 0:
        return 0.0
    return (missing_count / total_rows) * 100.0

def filter_missing_data(df, column: str, threshold_percent: float = 20.0):
    """
    Filters rows where the specified column is missing if the missing percentage exceeds threshold.
    Returns the filtered DataFrame and a flag indicating if filtering occurred.
    """
    try:
        import pandas as pd
        if column not in df.columns:
            return df, False
        
        total = len(df)
        missing_count = df[column].isna().sum()
        percent = calculate_missing_percentage(total, missing_count)
        
        if percent > threshold_percent:
            logger = get_logger()
            logger.warning(f"Missing data for {column} exceeds {threshold_percent}% ({percent:.2f}%). Filtering rows.")
            return df.dropna(subset=[column]), True
        
        return df, False
    except ImportError:
        return df, False

def validate_dataset_from_url(url: str) -> Dict:
    """
    Validates a dataset from a URL by downloading it and checking variables.
    Returns a validation report dictionary.
    """
    from ingest.download import download_dataset, calculate_sha256, verify_checksum
    
    logger = get_logger()
    report = {
        "url": url,
        "status": "unknown",
        "variables_present": False,
        "missing_variables": [],
        "timestamp": datetime.now().isoformat()
    }

    try:
        # Download dataset
        local_path = download_dataset(url)
        if not local_path:
            report["status"] = "download_failed"
            return report

        # Check checksum if available in spec
        datasets = load_verified_datasets_from_spec()
        expected_checksum = None
        for ds in datasets:
            if ds.get("url") == url:
                expected_checksum = ds.get("checksum")
                break

        if expected_checksum:
            calculated = calculate_sha256(local_path)
            if not verify_checksum(calculated, expected_checksum):
                report["status"] = "checksum_mismatch"
                return report

        # Validate variables
        headers = load_csv_header(local_path)
        is_valid, missing = check_csv_variables(headers, REQUIRED_VARIABLES)
        
        report["missing_variables"] = missing
        if is_valid:
            report["status"] = "valid"
            report["variables_present"] = True
        else:
            report["status"] = "invalid_variables"

    except Exception as e:
        logger.error(f"Validation failed for {url}: {str(e)}")
        report["status"] = "error"
        report["error"] = str(e)

    return report

def validate_all_datasets() -> List[Dict]:
    """
    Validates all datasets listed in the verified datasets block of spec.md.
    """
    datasets = load_verified_datasets_from_spec()
    results = []
    for ds in datasets:
        url = ds.get("url")
        if url:
            result = validate_dataset_from_url(url)
            results.append(result)
    return results

def generate_validation_report(results: List[Dict], output_path: Path):
    """
    Generates a JSON validation report.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

def main():
    """
    Main entry point for validation script.
    """
    logger = get_logger()
    logger.info("Starting dataset validation...")
    
    # Example: Validate against a local sample file if provided, or URLs from spec
    # For this task, we demonstrate the function existence and logic via CLI args
    if len(sys.argv) > 1:
        csv_path = Path(sys.argv[1])
        if csv_path.exists():
            headers = load_csv_header(csv_path)
            try:
                check_experience_years_variable(headers)
                print("SUCCESS: experience_years variable found.")
                sys.exit(0)
            except ValueError as e:
                print(f"FAILURE: {e}")
                sys.exit(1)
        else:
            print(f"Error: File not found: {csv_path}")
            sys.exit(1)
    else:
        # Run against spec datasets
        results = validate_all_datasets()
        report_path = Path("data/output/validation_report.json")
        generate_validation_report(results, report_path)
        print(f"Validation report generated at {report_path}")

if __name__ == "__main__":
    main()