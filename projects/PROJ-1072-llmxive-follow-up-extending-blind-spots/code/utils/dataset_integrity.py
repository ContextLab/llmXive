"""
Module: utils/dataset_integrity.py
Task: T007, T014a
Description: Strict field validation and integrity checking.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
from .logging_config import get_logger
from .hashing_utils import compute_dict_hash

class IntegrityError(Exception):
    """Custom exception for integrity failures."""
    pass

def validate_record_fields(record: Dict[str, Any], required_fields: Set[str]) -> List[str]:
    """
    Validate that a record contains all required fields.
    Returns list of missing fields.
    """
    missing = []
    for field in required_fields:
        if field not in record or record[field] is None:
            missing.append(field)
    return missing

def validate_dataset_records(records: List[Dict[str, Any]], required_fields: Set[str]) -> Dict[str, Any]:
    """
    Validate a list of records.
    Returns a report with counts and specific errors.
    """
    errors = []
    valid_count = 0
    
    for i, record in enumerate(records):
        missing = validate_record_fields(record, required_fields)
        if missing:
            errors.append({
                "index": i,
                "task_id": record.get("task_id", "UNKNOWN"),
                "missing_fields": missing
            })
        else:
            valid_count += 1
    
    return {
        "total": len(records),
        "valid": valid_count,
        "invalid": len(errors),
        "errors": errors
    }

def generate_integrity_report(errors: List[Dict[str, Any]], output_path: Path) -> None:
    """Generate a JSON report for integrity errors."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "status": "FAIL",
        "error_count": len(errors),
        "errors": errors,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

def load_and_validate_jsonl(file_path: Path, required_fields: Set[str]) -> Tuple[List[Dict], Dict]:
    """
    Load JSONL and validate in one go.
    Returns (records, report).
    """
    records = []
    errors = []
    line_num = 0
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line_num += 1
            try:
                record = json.loads(line)
                missing = validate_record_fields(record, required_fields)
                if missing:
                    errors.append({
                        "line": line_num,
                        "task_id": record.get("task_id", "UNKNOWN"),
                        "missing_fields": missing
                    })
                else:
                    records.append(record)
            except json.JSONDecodeError as e:
                errors.append({
                    "line": line_num,
                    "task_id": "UNKNOWN",
                    "error": f"JSON Decode Error: {e}"
                })
    
    report = {
        "total_lines": line_num,
        "valid_records": len(records),
        "invalid_records": len(errors),
        "errors": errors
    }
    return records, report

def verify_record_hash(record: Dict[str, Any], expected_hash: str) -> bool:
    """Verify a record's hash matches expected."""
    computed = compute_dict_hash(record)
    return computed == expected_hash
