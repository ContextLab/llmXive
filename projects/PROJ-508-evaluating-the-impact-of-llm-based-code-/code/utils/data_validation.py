import re
from typing import Dict, Any, List, Optional, Tuple, Set
from pathlib import Path
import json
import csv

class ValidationResult:
    def __init__(self, is_valid: bool, errors: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []

def scan_for_pii(text: str) -> List[str]:
    """
    Scan text for potential PII patterns (email, IP, etc.).
    """
    patterns = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "ip": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    }
    found = []
    for name, pattern in patterns.items():
        if re.search(pattern, text):
            found.append(name)
    return found

def scan_file_for_pii(file_path: Path) -> List[str]:
    """
    Scan a file for PII.
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    return scan_for_pii(content)

def validate_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> ValidationResult:
    """
    Validate a dictionary against a schema.
    """
    errors = []
    for key, expected_type in schema.items():
        if key not in data:
            errors.append(f"Missing key: {key}")
        elif not isinstance(data[key], expected_type):
            errors.append(f"Invalid type for {key}: expected {expected_type}, got {type(data[key])}")
    return ValidationResult(len(errors) == 0, errors)

def validate_csv_schema(file_path: Path, required_columns: List[str]) -> ValidationResult:
    """
    Validate a CSV file has the required columns.
    """
    errors = []
    if not file_path.exists():
        return ValidationResult(False, ["File does not exist"])
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            if not headers:
                return ValidationResult(False, ["No headers found"])
            
            missing = set(required_columns) - set(headers)
            if missing:
                errors.append(f"Missing columns: {missing}")
    except Exception as e:
        errors.append(f"Error reading file: {e}")
    
    return ValidationResult(len(errors) == 0, errors)

def validate_json_schema(file_path: Path, schema: Dict[str, Any]) -> ValidationResult:
    """
    Validate a JSON file against a schema.
    """
    errors = []
    if not file_path.exists():
        return ValidationResult(False, ["File does not exist"])
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if isinstance(data, list):
            for i, item in enumerate(data):
                res = validate_schema(item, schema)
                if not res.is_valid:
                    errors.extend([f"Item {i}: {e}" for e in res.errors])
        else:
            res = validate_schema(data, schema)
            if not res.is_valid:
                errors.extend(res.errors)
    except Exception as e:
        errors.append(f"Error reading file: {e}")
    
    return ValidationResult(len(errors) == 0, errors)

def generate_pii_report(file_paths: List[Path]) -> Dict[str, List[str]]:
    """
    Generate a report of PII found in files.
    """
    report = {}
    for path in file_paths:
        pii = scan_file_for_pii(path)
        if pii:
            report[str(path)] = pii
    return report
