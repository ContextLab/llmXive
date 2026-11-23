import os
import re
import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from utils.logging_utils import get_logger

# Define sensitive data patterns (PII, credentials, secrets)
SENSITIVE_PATTERNS: List[re.Pattern] = [
    re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),  # Email
    re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),  # SSN
    re.compile(r'\b\d{16}\b'),  # Credit Card
    re.compile(r'\b\d{3}[\s-]?\d{3}[\s-]?\d{4}\b'),  # Phone
    re.compile(r'(?i)(password|passwd|pwd)\s*[=:]\s*\S+'),  # Password assignment
    re.compile(r'(?i)(api_key|apikey|secret|token)\s*[=:]\s*\S+'),  # API Keys/Tokens
    re.compile(r'(?i)(aws_access_key_id|aws_secret_access_key)\s*[=:]\s*\S+'),  # AWS Keys
    re.compile(r'(?i)-----BEGIN (RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----'),  # Private Keys
]

# Specific fields known to contain sensitive data in this project's logs
SENSITIVE_FIELDS: Set[str] = {
    'participant_name', 'full_name', 'email', 'phone', 'address',
    'ip_address', 'user_agent', 'session_token', 'auth_token',
    'consent_form_id', 'raw_consent_data'
}

logger = get_logger(__name__)

def setup_security_logger(log_path: Optional[str] = None) -> logging.Logger:
    """
    Sets up a dedicated logger for security scanning operations.
    Logs are written to a secure location if provided, otherwise defaults to the project log path.
    """
    if log_path:
        handler = logging.FileHandler(log_path)
    else:
        # Default to the project's standard log path if configured
        handler = logging.FileHandler('data/interaction_logs/security_scan.log')
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    security_logger = logging.getLogger('security_hardening')
    security_logger.setLevel(logging.INFO)
    if not security_logger.handlers:
        security_logger.addHandler(handler)
    
    return security_logger

def sanitize_value(value: Any) -> str:
    """
    Sanitizes a single string value by redacting sensitive patterns.
    Returns '[REDACTED]' if sensitive data is detected, otherwise returns the original string.
    """
    if value is None:
        return ""
    
    str_val = str(value)
    
    # Check against regex patterns
    for pattern in SENSITIVE_PATTERNS:
        if pattern.search(str_val):
            logger.warning(f"Sensitive data pattern detected and redacted: {pattern.pattern}")
            return "[REDACTED]"
    
    # Check for known sensitive field names if the value looks like a key-value pair
    # This handles cases where the value itself is a key (e.g. "password")
    if str_val.lower() in [f.lower() for f in SENSITIVE_FIELDS]:
         return "[REDACTED]"
    
    return str_val

def sanitize_dict(data: Dict[str, Any], exclude_keys: Optional[Set[str]] = None) -> Dict[str, Any]:
    """
    Recursively sanitizes a dictionary, redacting sensitive values and keys.
    """
    if exclude_keys is None:
        exclude_keys = set()
    
    sanitized = {}
    for key, value in data.items():
        # Skip keys explicitly excluded from sanitization (e.g., internal IDs)
        if key in exclude_keys:
            sanitized[key] = value
            continue
        
        # Sanitize the key name itself if it looks like a sensitive field
        clean_key = key
        if key.lower() in SENSITIVE_FIELDS:
            logger.warning(f"Sensitive field name detected in dict key: {key}")
            clean_key = "[REDACTED_KEY]"
        
        # Sanitize the value
        if isinstance(value, dict):
            sanitized[clean_key] = sanitize_dict(value, exclude_keys)
        elif isinstance(value, list):
            sanitized[clean_key] = [sanitize_value(item) if isinstance(item, str) else item for item in value]
        else:
            sanitized[clean_key] = sanitize_value(value)
    
    return sanitized

def sanitize_csv_file(input_path: str, output_path: str, exclude_columns: Optional[Set[str]] = None) -> int:
    """
    Reads a CSV file, sanitizes all values, and writes to a new file.
    Returns the number of rows processed.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input CSV file not found: {input_path}")
    
    sanitized_count = 0
    with open(path, 'r', encoding='utf-8') as infile, open(output_path, 'w', encoding='utf-8', newline='') as outfile:
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
        writer.writeheader()
        
        for row in reader:
            sanitized_row = {}
            for col, val in row.items():
                if exclude_columns and col in exclude_columns:
                    sanitized_row[col] = val
                else:
                    sanitized_row[col] = sanitize_value(val)
            
            writer.writerow(sanitized_row)
            sanitized_count += 1
    
    logger.info(f"Sanitized {sanitized_count} rows in {input_path} -> {output_path}")
    return sanitized_count

def sanitize_json_file(input_path: str, output_path: str) -> None:
    """
    Reads a JSON file, sanitizes all values, and writes to a new file.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input JSON file not found: {input_path}")
    
    with open(path, 'r', encoding='utf-8') as infile:
        data = json.load(infile)
    
    sanitized_data = sanitize_dict(data)
    
    with open(output_path, 'w', encoding='utf-8') as outfile:
        json.dump(sanitized_data, outfile, indent=2)
    
    logger.info(f"Sanitized JSON file: {input_path} -> {output_path}")

def sanitize_interaction_logs(input_dir: str, output_dir: str) -> Dict[str, int]:
    """
    Scans a directory for CSV and JSON log files and sanitizes them.
    Returns a summary of files processed.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    for file_path in input_path.iterdir():
        if file_path.suffix == '.csv':
            out_file = output_path / f"sanitized_{file_path.name}"
            count = sanitize_csv_file(str(file_path), str(out_file))
            results[str(file_path)] = count
        elif file_path.suffix == '.json':
            out_file = output_path / f"sanitized_{file_path.name}"
            sanitize_json_file(str(file_path), str(out_file))
            results[str(file_path)] = 1
    
    return results

def scan_directory_for_sensitive_data(directory: str) -> List[Dict[str, Any]]:
    """
    Scans a directory recursively for potential sensitive data leaks in text files.
    Returns a list of findings.
    """
    findings = []
    dir_path = Path(directory)
    
    if not dir_path.exists():
        logger.error(f"Directory does not exist: {directory}")
        return findings
    
    for file_path in dir_path.rglob('*'):
        if file_path.is_file() and file_path.suffix in ['.csv', '.json', '.log', '.txt']:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    for i, line in enumerate(content.splitlines()):
                        for pattern in SENSITIVE_PATTERNS:
                            if pattern.search(line):
                                findings.append({
                                    "file": str(file_path),
                                    "line_number": i + 1,
                                    "pattern": pattern.pattern,
                                    "snippet": line[:100] + "..." if len(line) > 100 else line
                                })
            except Exception as e:
                logger.warning(f"Could not scan file {file_path}: {e}")
    
    return findings

def enforce_data_protection_policy(logs_dir: str, output_dir: str) -> bool:
    """
    Main entry point to enforce data protection policy on interaction logs.
    1. Scans for sensitive data.
    2. If found, sanitizes the files to the output directory.
    3. Returns True if policy is satisfied (no sensitive data in output).
    """
    logger.info(f"Starting data protection policy enforcement for {logs_dir}")
    
    # Step 1: Scan for sensitive data
    findings = scan_directory_for_sensitive_data(logs_dir)
    if findings:
        logger.warning(f"Found {len(findings)} potential sensitive data leaks. Initiating sanitization.")
        sanitize_interaction_logs(logs_dir, output_dir)
    else:
        logger.info("No sensitive data patterns found in raw logs. Copying files safely.")
        import shutil
        for file_path in Path(logs_dir).iterdir():
            if file_path.is_file():
                shutil.copy2(file_path, Path(output_dir) / file_path.name)
    
    # Step 2: Verify output is clean
    final_findings = scan_directory_for_sensitive_data(output_dir)
    if final_findings:
        logger.error(f"CRITICAL: Sensitive data still detected in sanitized output: {final_findings}")
        return False
    
    logger.info("Data protection policy enforced successfully. All sensitive data redacted.")
    return True

def main():
    """
    CLI entry point for security hardening.
    Usage: python code/utils/security_hardening.py --input data/interaction_logs/raw_logs.csv --output data/interaction_logs/anonymized_logs.csv
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Security Hardening: Sanitize logs and enforce data protection.")
    parser.add_argument("--input", type=str, required=True, help="Path to input log file or directory")
    parser.add_argument("--output", type=str, required=True, help="Path to output sanitized file or directory")
    parser.add_argument("--mode", type=str, choices=["file", "directory"], default="directory", help="Mode of operation")
    
    args = parser.parse_args()
    
    setup_security_logger()
    
    if args.mode == "file":
        if Path(args.input).suffix == '.csv':
            sanitize_csv_file(args.input, args.output)
        elif Path(args.input).suffix == '.json':
            sanitize_json_file(args.input, args.output)
        else:
            logger.error("Unsupported file format for single file mode.")
            return 1
    else:
        success = enforce_data_protection_policy(args.input, args.output)
        if not success:
            return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
