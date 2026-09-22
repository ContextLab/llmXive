import json
import sys
from pathlib import Path
from typing import List, Dict, Any

def load_dataset_records(file_path: str) -> List[Dict[str, Any]]:
    """
    Load records from a JSONL file.
    Raises FileNotFoundError if the file does not exist.
    Raises JSONDecodeError if the file is malformed.
    """
    records = []
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON at line {line_num}: {e}")
    return records

def check_for_manual_labels(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Scan records for fields indicating manual labeling.
    Checks for common keys: 'manual_label', 'human_annotation', 'human_label', 
    'is_manual', 'label_source' == 'manual'.
    Returns a list of findings (dictionaries with 'record_index' and 'field_name').
    """
    manual_indicators = [
        'manual_label', 'human_annotation', 'human_label', 'is_manual', 
        'label_source'
    ]
    findings = []

    for idx, record in enumerate(records):
        for key in record.keys():
            if key in manual_indicators:
                findings.append({
                    'record_index': idx,
                    'field_name': key,
                    'value': record[key],
                    'reason': 'Explicit manual label field detected'
                })
            elif key == 'label_source' and record[key] == 'manual':
                findings.append({
                    'record_index': idx,
                    'field_name': 'label_source',
                    'value': 'manual',
                    'reason': 'label_source explicitly set to manual'
                })
    
    return findings

def run_enforcement_check(
    input_file: str, 
    output_file: str
) -> Dict[str, Any]:
    """
    Main enforcement logic:
    1. Load real data.
    2. Scan for manual labels.
    3. If found, raise an error and write the error report.
    4. If clean, write a success report.
    """
    print(f"Loading dataset from: {input_file}")
    records = load_dataset_records(input_file)
    print(f"Loaded {len(records)} records.")

    print("Scanning for manual labels...")
    findings = check_for_manual_labels(records)

    report = {
        'status': 'pass',
        'dataset_file': input_file,
        'total_records_scanned': len(records),
        'manual_labels_found': False,
        'findings': [],
        'message': 'No manual labels detected. Rule-based enforcement passed.'
    }

    if findings:
        report['status'] = 'fail'
        report['manual_labels_found'] = True
        report['findings'] = findings
        report['message'] = f'ERROR: {len(findings)} manual label instances detected. Halting execution.'
        
        # Write the failure report before raising
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        raise RuntimeError(report['message'])

    # Write success report
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"Enforcement check passed. Report saved to: {output_file}")
    return report

def main():
    # Default paths based on project structure
    input_path = "data/processed/triplets.jsonl"
    output_path = "data/results/rule_based_enforcement.json"
    
    # Allow override via command line
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]

    try:
        run_enforcement_check(input_path, output_path)
    except RuntimeError as e:
        # Re-raise to signal failure to the pipeline
        print(f"FATAL: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
