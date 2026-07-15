"""
Task T004a: Verify existence and integrity of initial success/failure ground truth labels.

This script loads the raw dataset (produced by T011), checks for the presence
and validity of 'success' or 'failure' labels, and writes a validation report.

Output: data/results/ground_truth_validation.json
"""
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure we can import from the project root if running as a script
# but primarily rely on relative imports if part of a package.
# The project structure assumes src/ at root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configuration paths based on T001/T011 conventions
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
RESULTS_DIR = PROJECT_ROOT / "data" / "results"
OUTPUT_FILE = RESULTS_DIR / "ground_truth_validation.json"

# Expected label field names (common variations)
LABEL_FIELDS = ["label", "status", "outcome", "success", "failure", "ground_truth"]

def load_raw_dataset_sample(data_dir: Path, max_samples: int = 1000) -> List[Dict[str, Any]]:
    """
    Loads a sample of records from the raw dataset.
    Assumes the dataset is in JSONL, JSON, or CSV format in data/raw/.
    
    Raises FileNotFoundError or ValueError if data is missing or malformed.
    Does NOT fall back to synthetic data.
    """
    if not data_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {data_dir}")

    samples = []
    
    # Try JSONL first (common for logs)
    jsonl_files = list(data_dir.glob("*.jsonl"))
    if not jsonl_files:
        # Try JSON
        json_files = list(data_dir.glob("*.json"))
        if json_files:
            # Assume single file or first file
            file_path = json_files[0]
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    samples = data
                elif isinstance(data, dict) and 'data' in data:
                    samples = data['data']
                else:
                    # If it's a single object, wrap it
                    samples = [data]
        else:
            # Try CSV (fallback)
            csv_files = list(data_dir.glob("*.csv"))
            if csv_files:
                import csv
                file_path = csv_files[0]
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    samples = list(reader)
            else:
                raise FileNotFoundError(f"No supported data files (jsonl, json, csv) found in {data_dir}")
    else:
        # Process JSONL
        file_path = jsonl_files[0]
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        samples.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue # Skip malformed lines
    
    if not samples:
        raise ValueError("Dataset appears to be empty.")

    # Return a sample if too large
    if len(samples) > max_samples:
        return samples[:max_samples]
    
    return samples

def validate_labels(samples: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validates the existence and integrity of ground truth labels in the sample.
    
    Returns a report dict with status, issues, sample_size, and pass_criteria.
    """
    issues = []
    valid_count = 0
    total_count = len(samples)
    
    # Check each sample
    for i, sample in enumerate(samples):
        if not isinstance(sample, dict):
            issues.append(f"Sample {i} is not a dictionary.")
            continue
        
        found_label = False
        label_value = None
        
        for field in LABEL_FIELDS:
            if field in sample:
                val = sample[field]
                # Check if value is valid (non-empty string or boolean)
                if val is not None and val != "":
                    # Normalize boolean strings if necessary
                    if isinstance(val, str):
                        val_lower = val.lower()
                        if val_lower in ['true', 'false', 'success', 'failure', '1', '0', 'yes', 'no']:
                            found_label = True
                            label_value = val_lower
                            break
                    elif isinstance(val, bool):
                        found_label = True
                        label_value = val
                        break
                    elif isinstance(val, (int, float)):
                        if val in [0, 1]:
                            found_label = True
                            label_value = val
                            break
                    
        if not found_label:
            # Check for specific failure patterns if no label found
            # e.g., if 'error' field exists but no 'status'
            if 'error' in sample or 'exception' in sample:
                # Assume this might be a failure trace but lacks explicit label
                issues.append(f"Sample {i}: Contains error info but missing explicit label.")
            else:
                issues.append(f"Sample {i}: No valid ground truth label found.")
        else:
            valid_count += 1

    # Calculate pass rate
    pass_rate = (valid_count / total_count) if total_count > 0 else 0.0
    threshold = 0.95
    status = "pass" if pass_rate >= threshold else "fail"
    
    report = {
        "status": status,
        "issues": issues[:100], # Limit issues to avoid huge files
        "sample_size": total_count,
        "valid_labels_count": valid_count,
        "pass_rate": pass_rate,
        "pass_criteria": f"pass if >{int(threshold*100)}% labels exist",
        "threshold_met": pass_rate >= threshold
    }
    
    return report

def main():
    """Main entry point for T004a."""
    print(f"Starting T004a: Ground Truth Validation")
    print(f"Raw Data Dir: {RAW_DATA_DIR}")
    
    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load data
        print("Loading raw dataset sample...")
        samples = load_raw_dataset_sample(RAW_DATA_DIR)
        print(f"Loaded {len(samples)} samples.")
        
        # Validate
        print("Validating labels...")
        report = validate_labels(samples)
        
        # Write report
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        print(f"Validation report written to: {OUTPUT_FILE}")
        print(f"Status: {report['status']}")
        print(f"Pass Rate: {report['pass_rate']:.2%}")
        
        if report['status'] == 'fail':
            print("WARNING: Validation failed. Check issues in report.")
            # Do not exit with error code to allow pipeline to continue if needed,
            # but the report clearly indicates failure.
        
    except Exception as e:
        print(f"ERROR: Failed to validate ground truth: {e}")
        # Fail loudly as per constraints
        error_report = {
            "status": "fail",
            "issues": [f"Critical error during execution: {str(e)}"],
            "sample_size": 0,
            "pass_criteria": "pass if >95% labels exist",
            "error": str(e)
        }
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(error_report, f, indent=2)
        sys.exit(1)

if __name__ == "__main__":
    main()