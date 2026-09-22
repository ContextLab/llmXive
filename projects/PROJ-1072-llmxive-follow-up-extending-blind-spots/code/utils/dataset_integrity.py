import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
from .logging_config import get_logger
from .hashing_utils import compute_dict_hash

logger = get_logger(__name__)

class IntegrityError(Exception):
    """Custom exception for dataset integrity failures."""
    pass

def validate_record_fields(record: Dict[str, Any], required_fields: Set[str]) -> bool:
    """
    Check if a record contains all required fields with non-empty values.
    
    Args:
        record: The record dictionary.
        required_fields: Set of field names that must exist.
        
    Returns:
        True if valid, False otherwise.
    """
    for field in required_fields:
        if field not in record:
            logger.debug(f"Record missing required field: {field}")
            return False
        if record[field] is None or (isinstance(record[field], str) and not record[field].strip()):
            logger.debug(f"Record has empty required field: {field}")
            return False
    return True

def validate_dataset_records(records: List[Dict[str, Any]], required_fields: Set[str]) -> List[Dict[str, Any]]:
    """
    Validate a list of records against required fields.
    
    Args:
        records: List of records.
        required_fields: Set of required field names.
        
    Returns:
        List of invalid records (empty if all valid).
    """
    invalid = []
    for idx, record in enumerate(records):
        if not validate_record_fields(record, required_fields):
            invalid.append({
                "index": idx,
                "record_id": record.get("task_id", "unknown"),
                "missing_fields": [f for f in required_fields if f not in record or not record.get(f)]
            })
    return invalid

def generate_integrity_report(invalid_records: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Generate a JSON report of integrity failures.
    
    Args:
        invalid_records: List of invalid record details.
        output_path: Path to write the report.
    """
    report = {
        "status": "FAILED",
        "total_invalid": len(invalid_records),
        "invalid_records": invalid_records,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    
    logger.warning(f"Integrity report generated: {output_path}")

def load_and_validate_jsonl(file_path: Path, required_fields: Set[str]) -> List[Dict[str, Any]]:
    """
    Load a JSONL file and validate each record.
    
    Args:
        file_path: Path to the JSONL file.
        required_fields: Set of required fields.
        
    Returns:
        List of valid records.
        
    Raises:
        IntegrityError: If any records are invalid.
    """
    records = []
    invalid_records = []
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                if validate_record_fields(record, required_fields):
                    records.append(record)
                else:
                    invalid_records.append({
                        "line": line_num,
                        "record_id": record.get("task_id", "unknown"),
                        "missing_fields": [f for f in required_fields if f not in record or not record.get(f)]
                    })
            except json.JSONDecodeError as e:
                invalid_records.append({
                    "line": line_num,
                    "error": f"JSON Decode Error: {e}"
                })
    
    if invalid_records:
        raise IntegrityError(f"Found {len(invalid_records)} invalid records in {file_path}")
    
    return records

def verify_record_hash(record: Dict[str, Any], expected_hash: str) -> bool:
    """
    Verify the hash of a record matches the expected hash.
    
    Args:
        record: The record dictionary.
        expected_hash: The expected hash string.
        
    Returns:
        True if hashes match, False otherwise.
    """
    actual_hash = compute_dict_hash(record)
    return actual_hash == expected_hash
