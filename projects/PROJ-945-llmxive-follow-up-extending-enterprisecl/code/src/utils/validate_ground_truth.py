"""
Validates the existence and integrity of ground truth labels in the raw dataset.
Produces a validation report at data/results/ground_truth_validation.json.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import csv
import hashlib

# Add project root to path to allow imports if run directly
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import get_config

def load_raw_dataset_metadata(raw_data_dir: Path) -> List[Dict[str, Any]]:
    """
    Scans the raw data directory for dataset files (CSV/JSON/JSONL)
    and loads metadata about records including their labels.
    Assumes the dataset downloaded by T011 follows a standard structure
    where a 'label' or 'status' field indicates success/failure.
    """
    records = []
    
    # Common extensions for raw data
    extensions = ['.csv', '.json', '.jsonl', '.tsv']
    found_files = []
    
    for ext in extensions:
        found_files.extend(list(raw_data_dir.glob(f'*{ext}')))
    
    if not found_files:
        raise FileNotFoundError(f"No data files found in {raw_data_dir}")

    # Heuristic: Look for the largest file or a specific name if known
    # For EnterpriseClawBench, we assume a primary log file exists
    primary_file = max(found_files, key=lambda p: p.stat().st_size)
    
    if primary_file.suffix == '.csv':
        with open(primary_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
    elif primary_file.suffix in ['.json', '.jsonl']:
        with open(primary_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content.startswith('['):
                # JSON array
                data = json.loads(content)
                if isinstance(data, list):
                    records = data
            else:
                # JSONL
                for line in content.split('\n'):
                    if line.strip():
                        records.append(json.loads(line))
    else:
        raise ValueError(f"Unsupported file format: {primary_file.suffix}")
    
    return records

def identify_label_field(records: List[Dict[str, Any]]) -> Optional[str]:
    """
    Identifies the field name that contains the success/failure label.
    Looks for common keys: 'label', 'status', 'outcome', 'result'.
    """
    if not records:
        return None
    
    first_record = records[0]
    candidates = ['label', 'status', 'outcome', 'result', 'ground_truth', 'is_success']
    
    for key in candidates:
        if key in first_record:
            return key
    
    # Fallback: check if any key contains 'status' or 'label' case-insensitively
    for key in first_record.keys():
        if 'status' in key.lower() or 'label' in key.lower():
            return key
    
    return None

def validate_labels(records: List[Dict[str, Any]], label_field: str) -> Dict[str, Any]:
    """
    Validates that the identified label field exists and contains valid values.
    Returns a report dictionary.
    """
    total_records = len(records)
    valid_count = 0
    issues = []
    valid_values = {'success', 'failure', 'passed', 'failed', '1', '0', True, False}
    
    # Normalize valid values set to strings for comparison
    valid_values_str = {'success', 'failure', 'passed', 'failed', '1', '0', 'true', 'false'}
    
    for i, record in enumerate(records):
        if label_field not in record:
            issues.append(f"Record {i} missing label field '{label_field}'")
            continue
        
        value = record[label_field]
        # Normalize to string for comparison
        str_value = str(value).lower().strip()
        
        if str_value in valid_values_str:
            valid_count += 1
        else:
            issues.append(f"Record {i} has invalid label value: '{value}'")
    
    return {
        'total_records': total_records,
        'valid_count': valid_count,
        'issues': issues
    }

def main():
    """
    Main entry point for ground truth validation.
    """
    config = get_config()
    raw_data_dir = Path(config['paths']['raw_data'])
    output_dir = Path(config['paths']['results'])
    output_file = output_dir / 'ground_truth_validation.json'
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load raw data
        print(f"Loading raw dataset from {raw_data_dir}...")
        records = load_raw_dataset_metadata(raw_data_dir)
        
        if not records:
            raise ValueError("No records found in the raw dataset.")
        
        # Identify label field
        label_field = identify_label_field(records)
        if not label_field:
            raise ValueError("Could not identify a label field in the dataset.")
        
        print(f"Identified label field: '{label_field}'")
        
        # Validate labels
        validation_result = validate_labels(records, label_field)
        
        total = validation_result['total_records']
        valid = validation_result['valid_count']
        issues = validation_result['issues']
        
        # Calculate pass rate
        pass_rate = (valid / total) * 100 if total > 0 else 0.0
        
        # Determine status based on criteria: >95% labels exist and are valid
        status = 'pass' if pass_rate > 95.0 else 'fail'
        
        report = {
            'status': status,
            'issues': issues[:100],  # Limit issues in report to avoid huge files
            'sample_size': total,
            'pass_criteria': 'pass if >95% labels exist and are valid',
            'details': {
                'label_field': label_field,
                'total_records': total,
                'valid_labels': valid,
                'invalid_labels': total - valid,
                'pass_rate_percent': round(pass_rate, 2)
            }
        }
        
        # Write report
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        print(f"Validation report written to {output_file}")
        print(f"Status: {status} ({valid}/{total} valid labels, {pass_rate:.2f}%)")
        
        if status == 'fail':
            print(f"WARNING: Pass rate ({pass_rate:.2f}%) is below 95% threshold.")
            if issues:
                print(f"Sample issues: {issues[:5]}")
            
    except Exception as e:
        print(f"ERROR: Validation failed with exception: {e}")
        # Write a failure report
        error_report = {
            'status': 'fail',
            'issues': [str(e)],
            'sample_size': 0,
            'pass_criteria': 'pass if >95% labels exist and are valid',
            'details': {
                'error': str(e)
            }
        }
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(error_report, f, indent=2)
        sys.exit(1)

if __name__ == '__main__':
    main()
