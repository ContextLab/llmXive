"""
Semantic Outcome Oracle logic and utilities for T021a and T021d.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def load_oracle_labels(oracle_path: str) -> List[float]:
    """
    Load oracle labels from a JSON file.
    Expected format: {'labels': [0.0, 1.0, ...]} or a list of labels.
    """
    with open(oracle_path, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'labels' in data:
        return data['labels']
    else:
        raise ValueError(f"Unexpected oracle labels format in {oracle_path}")


def derive_oracle_labels_from_schema(
    raw_logs_path: str,
    error_schema_path: str,
    output_path: str
) -> List[float]:
    """
    Derive oracle labels based on error schema and rule-based logic.
    Rule: correctable = (error_type in ['syntax', 'token_mismatch'] AND error_type not in ['semantic_error', 'reasoning_gap'])
    """
    # Load error schema
    with open(error_schema_path, 'r') as f:
        error_schema = json.load(f)
    
    # Load raw logs
    with open(raw_logs_path, 'r') as f:
        raw_logs = [json.loads(line) for line in f]
    
    # Define correctable error types
    correctable_types = {'syntax', 'token_mismatch'}
    non_correctable_types = {'semantic_error', 'reasoning_gap'}
    
    labels = []
    for log in raw_logs:
        error_type = log.get('error_type', '').lower()
        
        # Apply rule-based logic
        if error_type in correctable_types and error_type not in non_correctable_types:
            labels.append(1.0)  # Correctable
        else:
            labels.append(0.0)  # Not correctable
    
    # Save labels to output
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump({'labels': labels}, f, indent=2)
    
    return labels


def validate_oracle_labels(
    raw_logs_path: str,
    error_schema_path: str,
    oracle_labels_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Validate that oracle labels are deterministic and consistent on a small sample.
    """
    # Load raw logs
    with open(raw_logs_path, 'r') as f:
        raw_logs = [json.loads(line) for line in f]
    
    # Load existing oracle labels
    with open(oracle_labels_path, 'r') as f:
        oracle_data = json.load(f)
    existing_labels = oracle_data.get('labels', [])
    
    if len(existing_labels) != len(raw_logs):
        raise ValueError("Length mismatch between raw logs and existing oracle labels")
    
    # Re-derive labels
    new_labels = derive_oracle_labels_from_schema(raw_logs_path, error_schema_path, oracle_labels_path)
    
    # Compare
    if new_labels != existing_labels:
        mismatch_count = sum(1 for a, b in zip(new_labels, existing_labels) if a != b)
        report = {
            'status': 'fail',
            'mismatch_count': mismatch_count,
            'total_count': len(new_labels),
            'issues': [f"Found {mismatch_count} mismatches between re-derived and existing labels"]
        }
    else:
        report = {
            'status': 'pass',
            'mismatch_count': 0,
            'total_count': len(new_labels),
            'issues': []
        }
    
    # Save report
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report


def main():
    """Main entry point for oracle utilities."""
    print("Oracle module utilities available.")
    print("Functions: derive_oracle_labels_from_schema, validate_oracle_labels, load_oracle_labels")


if __name__ == "__main__":
    main()