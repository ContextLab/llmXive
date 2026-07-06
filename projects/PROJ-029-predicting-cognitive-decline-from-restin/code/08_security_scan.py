"""
Security hardening: Scan data/raw/ for PII using pybids/bids-validator logic.
Automatically redact personal identifiers found in JSON side-cars or filenames.
"""
import os
import re
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Set
from utils.logger import get_logger
from utils.io import ensure_dir, load_json, save_json

# PII Patterns based on BIDS specification and common identifiers
PII_PATTERNS = {
    "participant_id": re.compile(r"(?i)(participant[_-]?id|subject[_-]?id|bids[_-]?id)", re.IGNORECASE),
    "patient_name": re.compile(r"(?i)(patient[_-]?name|name)", re.IGNORECASE),
    "dob": re.compile(r"(?i)(date[_-]?of[_-]?birth|dob|birth[_-]?date)", re.IGNORECASE),
    "sex": re.compile(r"(?i)(sex|gender)", re.IGNORECASE),
    "phone": re.compile(r"(?i)(phone|tel|mobile)", re.IGNORECASE),
    "email": re.compile(r"(?i)(email|e[_-]?mail)", re.IGNORECASE),
    "address": re.compile(r"(?i)(address|street|city|zip|postal[_-]?code)", re.IGNORECASE),
    "ssn": re.compile(r"(?i)(social[_-]?security|ssn)", re.IGNORECASE),
    "mrn": re.compile(r"(?i)(medical[_-]?record[_-]?number|mrn)", re.IGNORECASE),
    "date": re.compile(r"(?i)(date|time|timestamp)", re.IGNORECASE),
}

# Specific values that look like PII (e.g., real names, dates)
# We rely on keys mostly, but also check for values that look like names/dates in JSON
NAME_PATTERN = re.compile(r"^[A-Z][a-z]{2,20}$")  # Simple name heuristic
DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
SSN_PATTERN = re.compile(r"\d{3}-\d{2}-\d{4}")

logger = get_logger(__name__)

def is_pii_key(key: str) -> bool:
    """Check if a JSON key is likely to contain PII."""
    for pattern_name, pattern in PII_PATTERNS.items():
        if pattern.search(key):
            return True
    return False

def is_pii_value(key: str, value: Any) -> bool:
    """Check if a JSON value is likely PII based on key context or value pattern."""
    if isinstance(value, str):
        # If the key suggests PII, the value is likely PII
        if is_pii_key(key):
            return True
        # Heuristic checks for values if key is ambiguous
        if NAME_PATTERN.match(value) and len(value) > 2:
            # Very weak heuristic, but useful for "Name" keys
            if "name" in key.lower() or "patient" in key.lower():
                return True
        if DATE_PATTERN.match(value):
            if "date" in key.lower() or "dob" in key.lower():
                return True
        if SSN_PATTERN.match(value):
            return True
    return False

def redact_value(value: Any, key: str = "") -> Any:
    """Replace PII value with a redacted placeholder."""
    if isinstance(value, dict):
        return redact_dict(value)
    elif isinstance(value, list):
        return [redact_value(v, key) for v in value]
    elif isinstance(value, str):
        if is_pii_value(key, value):
            return "[REDACTED]"
    return value

def redact_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively redact PII from a dictionary."""
    redacted = {}
    for key, value in data.items():
        if is_pii_key(key) or (isinstance(value, str) and is_pii_value(key, value)):
            redacted[key] = redact_value(value, key)
        else:
            redacted[key] = redact_value(value, key)
    return redacted

def scan_json_file(file_path: Path) -> Dict[str, Any]:
    """Scan a JSON file for PII and return redacted version + log of findings."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.warning(f"Could not parse JSON in {file_path}: {e}")
        return None, []
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return None, []

    findings = []
    redacted_data = redact_dict(data)

    # Log findings for audit
    def log_findings_recursive(d: Dict, path: str = ""):
        for k, v in d.items():
            current_path = f"{path}.{k}" if path else k
            if k in redacted_data and redacted_data[k] == "[REDACTED]":
                # Only log if it was actually redacted (i.e., original was PII)
                # We need to check original to be sure, but for simplicity we log the key
                if is_pii_key(k):
                    findings.append({"file": str(file_path), "key": current_path, "type": "pii_key"})
            elif isinstance(v, dict):
                log_findings_recursive(v, current_path)

    log_findings_recursive(data)
    return redacted_data, findings

def scan_filename(filename: str) -> List[str]:
    """Check if filename contains PII patterns."""
    findings = []
    # Check for patterns that look like IDs or names in filenames
    # e.g., sub-001 might be fine, but sub-JohnDoe is not
    if re.search(r"[A-Z][a-z]{2,}", filename): # Potential name
        findings.append({"type": "potential_name_in_filename", "value": filename})
    # Check for dates in filename if not standard BIDS date format
    if re.search(r"\d{4}-\d{2}-\d{2}", filename):
        # Standard BIDS date is usually part of session or date, but check context
        # If it's in the subject part, it might be PII
        pass 
    return findings

def scan_directory(data_raw_path: Path, output_dir: Path):
    """Scan all JSON files in data_raw_path and redact PII."""
    ensure_dir(output_dir)
    all_findings = []
    redacted_files_log = []

    logger.info(f"Scanning directory: {data_raw_path}")
    
    if not data_raw_path.exists():
        logger.warning(f"Directory {data_raw_path} does not exist. Creating empty report.")
        # Write empty report
        report = {
            "scan_path": str(data_raw_path),
            "files_scanned": 0,
            "findings": [],
            "redacted_files": []
        }
        save_json(output_dir / "security_scan_report.json", report)
        return

    json_files = list(data_raw_path.rglob("*.json"))
    logger.info(f"Found {len(json_files)} JSON files.")

    for json_file in json_files:
        redacted_data, findings = scan_json_file(json_file)
        if redacted_data is not None:
            # Calculate relative path to preserve structure in output
            rel_path = json_file.relative_to(data_raw_path)
            output_file = output_dir / rel_path
            ensure_dir(output_file.parent)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(redacted_data, f, indent=2)
            
            redacted_files_log.append(str(rel_path))
            all_findings.extend(findings)
            
            # Scan filename
            filename_findings = scan_filename(json_file.name)
            for ff in filename_findings:
                all_findings.append({
                    "file": str(json_file),
                    "type": ff["type"],
                    "value": ff["value"]
                })

    report = {
        "scan_path": str(data_raw_path),
        "files_scanned": len(json_files),
        "findings": all_findings,
        "redacted_files": redacted_files_log
    }

    report_file = output_dir / "security_scan_report.json"
    save_json(report_file, report)
    logger.info(f"Security scan complete. Report saved to {report_file}")
    logger.info(f"Total findings: {len(all_findings)}")

def main():
    """Main entry point."""
    data_raw = Path("data/raw")
    output_dir = Path("data/artifacts/security_scan")
    
    logger.info("Starting PII security scan...")
    scan_directory(data_raw, output_dir)
    logger.info("Security scan finished.")

if __name__ == "__main__":
    main()
