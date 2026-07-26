"""
Security hardening module for llmXive project.

Implements data sanitization and log scrubbing to ensure no sensitive data
(PII, credentials, tokens) leaks into logs or analysis outputs.

Addresses Task T042: Security hardening (ensure no sensitive data leaks in logs)
"""
import os
import re
import json
import csv
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from utils.logging_utils import get_logger, setup_logging
from utils.config_manager import get_config

# Patterns for sensitive data detection
SENSITIVE_PATTERNS = {
    'email': re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'),
    'phone': re.compile(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'),
    'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
    'credit_card': re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
    'api_key': re.compile(r'\b(?:api[_-]?key|apikey|access[_-]?token|bearer)\s*[=:]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?'),
    'password': re.compile(r'\b(?:password|passwd|pwd|secret)\s*[=:]\s*["\']?([^\s"\'"]+)["\']?'),
    'ip_address': re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
    'jwt_token': re.compile(r'\beyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*\b'),
    'aws_key': re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
    'git_token': re.compile(r'\b(?:ghp|gho|ghu|ghs|ghr)[a-zA-Z0-9]{36,}\b'),
}

# Default redaction string
REDACTION_STRING = "[REDACTED]"

def setup_security_logger() -> logging.Logger:
    """Setup a dedicated logger for security operations."""
    return get_logger("security_hardening")

def sanitize_value(value: str, pattern_name: str = None) -> str:
    """
    Sanitize a single string value by replacing sensitive patterns.
    
    Args:
        value: The string to sanitize
        pattern_name: Optional specific pattern to apply (if None, applies all)
        
    Returns:
        Sanitized string with sensitive data replaced
    """
    if not isinstance(value, str):
        return value
        
    result = value
    patterns_to_apply = [pattern_name] if pattern_name else SENSITIVE_PATTERNS.keys()
    
    for name in patterns_to_apply:
        if name in SENSITIVE_PATTERNS:
            pattern = SENSITIVE_PATTERNS[name]
            result = pattern.sub(REDACTION_STRING, result)
            
    return result

def sanitize_dict(data: Dict[str, Any], recursive: bool = True) -> Dict[str, Any]:
    """
    Recursively sanitize all string values in a dictionary.
    
    Args:
        data: Dictionary to sanitize
        recursive: Whether to recurse into nested dicts/lists
        
    Returns:
        Sanitized dictionary
    """
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_value(value)
        elif recursive and isinstance(value, dict):
            sanitized[key] = sanitize_dict(value, recursive)
        elif recursive and isinstance(value, list):
            sanitized[key] = [
                sanitize_dict(item, recursive) if isinstance(item, dict)
                else sanitize_value(item) if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            sanitized[key] = value
    return sanitized

def sanitize_csv_file(input_path: Union[str, Path], output_path: Union[str, Path]) -> Dict[str, int]:
    """
    Sanitize a CSV file by redacting sensitive patterns in all string fields.
    
    Args:
        input_path: Path to input CSV file
        output_path: Path to write sanitized CSV
        
    Returns:
        Dictionary with counts of redactions per pattern type
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    logger = setup_security_logger()
    logger.info(f"Sanitizing CSV file: {input_path} -> {output_path}")
    
    redaction_counts = {pattern: 0 for pattern in SENSITIVE_PATTERNS.keys()}
    
    with open(input_path, 'r', encoding='utf-8') as infile, \
         open(output_path, 'w', encoding='utf-8', newline='') as outfile:
        
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
        writer.writeheader()
        
        for row in reader:
            sanitized_row = {}
            for field, value in row.items():
                if value is None:
                    sanitized_row[field] = value
                    continue
                    
                original_value = value
                for pattern_name, pattern in SENSITIVE_PATTERNS.items():
                    matches = pattern.findall(value)
                    if matches:
                        redaction_counts[pattern_name] += len(matches)
                        value = pattern.sub(REDACTION_STRING, value)
                
                sanitized_row[field] = value
            
            writer.writerow(sanitized_row)
    
    logger.info(f"Sanitization complete. Redaction counts: {redaction_counts}")
    return redaction_counts

def sanitize_json_file(input_path: Union[str, Path], output_path: Union[str, Path]) -> Dict[str, int]:
    """
    Sanitize a JSON file by redacting sensitive patterns in all string values.
    
    Args:
        input_path: Path to input JSON file
        output_path: Path to write sanitized JSON
        
    Returns:
        Dictionary with counts of redactions per pattern type
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    logger = setup_security_logger()
    logger.info(f"Sanitizing JSON file: {input_path} -> {output_path}")
    
    with open(input_path, 'r', encoding='utf-8') as infile:
        data = json.load(infile)
    
    # Count redactions before sanitization
    redaction_counts = {pattern: 0 for pattern in SENSITIVE_PATTERNS.keys()}
    
    def count_redactions(obj):
        if isinstance(obj, dict):
            for value in obj.values():
                count_redactions(value)
        elif isinstance(obj, list):
            for item in obj:
                count_redactions(item)
        elif isinstance(obj, str):
            for pattern_name, pattern in SENSITIVE_PATTERNS.items():
                matches = pattern.findall(obj)
                redaction_counts[pattern_name] += len(matches)
    
    count_redactions(data)
    
    # Sanitize the data
    sanitized_data = sanitize_dict(data)
    
    with open(output_path, 'w', encoding='utf-8') as outfile:
        json.dump(sanitized_data, outfile, indent=2, ensure_ascii=False)
    
    logger.info(f"Sanitization complete. Redaction counts: {redaction_counts}")
    return redaction_counts

def sanitize_interaction_logs(input_path: Union[str, Path], output_path: Union[str, Path]) -> Dict[str, int]:
    """
    Specifically sanitize interaction log files to remove PII while preserving
    research-relevant data (timestamps, task IDs, line selections).
    
    Args:
        input_path: Path to raw interaction logs CSV
        output_path: Path to write sanitized logs
        
    Returns:
        Dictionary with counts of redactions per pattern type
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    logger = setup_security_logger()
    logger.info(f"Sanitizing interaction logs: {input_path} -> {output_path}")
    
    # Fields that should NEVER be redacted (research data)
    safe_fields = {
        'participant_id',  # This is already anonymized in T016
        'task_id',
        'condition',
        'timestamp_ms',
        'selected_line',
        'ground_truth_line',
        'method_name',
        'bug_id',
        'project_id',
        'session_id',
    }
    
    redaction_counts = {pattern: 0 for pattern in SENSITIVE_PATTERNS.keys()}
    
    with open(input_path, 'r', encoding='utf-8') as infile, \
         open(output_path, 'w', encoding='utf-8', newline='') as outfile:
        
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
        writer.writeheader()
        
        for row in reader:
            sanitized_row = {}
            for field, value in row.items():
                if value is None:
                    sanitized_row[field] = value
                    continue
                    
                # Skip redaction for safe fields
                if field in safe_fields:
                    sanitized_row[field] = value
                    continue
                
                # Apply redaction to other fields
                original_value = value
                for pattern_name, pattern in SENSITIVE_PATTERNS.items():
                    matches = pattern.findall(value)
                    if matches:
                        redaction_counts[pattern_name] += len(matches)
                        value = pattern.sub(REDACTION_STRING, value)
                
                sanitized_row[field] = value
            
            writer.writerow(sanitized_row)
    
    logger.info(f"Interaction log sanitization complete. Redaction counts: {redaction_counts}")
    return redaction_counts

def scan_directory_for_sensitive_data(directory: Union[str, Path], 
                                     output_report: Union[str, Path] = None) -> Dict[str, Any]:
    """
    Scan a directory for files containing sensitive data patterns.
    
    Args:
        directory: Path to directory to scan
        output_report: Optional path to write a JSON report
        
    Returns:
        Dictionary with scan results
    """
    directory = Path(directory)
    logger = setup_security_logger()
    logger.info(f"Scanning directory for sensitive data: {directory}")
    
    results = {
        'scan_time': datetime.now().isoformat(),
        'directory': str(directory),
        'files_scanned': 0,
        'files_with_sensitive_data': 0,
        'findings': []
    }
    
    for file_path in directory.rglob('*'):
        if file_path.is_file() and file_path.suffix in ['.csv', '.json', '.log', '.txt']:
            results['files_scanned'] += 1
            file_findings = []
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                for pattern_name, pattern in SENSITIVE_PATTERNS.items():
                    matches = pattern.findall(content)
                    if matches:
                        file_findings.append({
                            'pattern': pattern_name,
                            'count': len(matches),
                            'sample': matches[0][:50] + '...' if len(matches[0]) > 50 else matches[0]
                        })
                
                if file_findings:
                    results['files_with_sensitive_data'] += 1
                    results['findings'].append({
                        'file': str(file_path),
                        'findings': file_findings
                    })
                    
            except Exception as e:
                logger.warning(f"Could not scan file {file_path}: {e}")
    
    if output_report:
        with open(output_report, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Scan report written to: {output_report}")
    
    return results

def enforce_data_protection_policy(input_dir: Union[str, Path], 
                                  output_dir: Union[str, Path],
                                  consent_dir: Union[str, Path] = None) -> Dict[str, Any]:
    """
    Enforce comprehensive data protection by sanitizing all output files
    and ensuring consent data is properly excluded.
    
    Args:
        input_dir: Directory containing raw data to process
        output_dir: Directory for sanitized output
        consent_dir: Optional path to consent data (will be excluded)
        
    Returns:
        Summary of protection actions taken
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    logger = setup_security_logger()
    
    logger.info("Enforcing data protection policy")
    
    actions_taken = {
        'files_processed': 0,
        'files_sanitized': 0,
        'consent_files_excluded': 0,
        'sensitive_patterns_found': 0,
        'details': []
    }
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process CSV files
    for csv_file in input_dir.rglob('*.csv'):
        if consent_dir and str(csv_file).startswith(str(consent_dir)):
            actions_taken['consent_files_excluded'] += 1
            actions_taken['details'].append(f"Excluded consent file: {csv_file}")
            continue
            
        output_file = output_dir / csv_file.relative_to(input_dir)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        if 'interaction' in csv_file.name.lower():
            counts = sanitize_interaction_logs(csv_file, output_file)
            actions_taken['files_processed'] += 1
            actions_taken['files_sanitized'] += 1
            actions_taken['sensitive_patterns_found'] += sum(counts.values())
            actions_taken['details'].append(f"Sanitized interaction logs: {csv_file.name}")
        else:
            # Generic CSV sanitization
            counts = sanitize_csv_file(csv_file, output_file)
            actions_taken['files_processed'] += 1
            actions_taken['files_sanitized'] += 1
            actions_taken['sensitive_patterns_found'] += sum(counts.values())
            actions_taken['details'].append(f"Sanitized CSV: {csv_file.name}")
    
    # Process JSON files
    for json_file in input_dir.rglob('*.json'):
        if consent_dir and str(json_file).startswith(str(consent_dir)):
            actions_taken['consent_files_excluded'] += 1
            actions_taken['details'].append(f"Excluded consent file: {json_file}")
            continue
            
        output_file = output_dir / json_file.relative_to(input_dir)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        counts = sanitize_json_file(json_file, output_file)
        actions_taken['files_processed'] += 1
        actions_taken['files_sanitized'] += 1
        actions_taken['sensitive_patterns_found'] += sum(counts.values())
        actions_taken['details'].append(f"Sanitized JSON: {json_file.name}")
    
    logger.info(f"Data protection enforcement complete. {actions_taken['files_sanitized']} files sanitized.")
    return actions_taken

def main():
    """
    Main entry point for security hardening operations.
    
    Usage:
        python code/utils/security_hardening.py --action <action> --input <path> --output <path>
        
    Actions:
        - sanitize_csv: Sanitize a CSV file
        - sanitize_json: Sanitize a JSON file
        - sanitize_logs: Sanitize interaction logs
        - scan: Scan directory for sensitive data
        - protect: Enforce full data protection policy
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Security hardening for llmXive project')
    parser.add_argument('--action', required=True, choices=[
        'sanitize_csv', 'sanitize_json', 'sanitize_logs', 'scan', 'protect'
    ], help='Action to perform')
    parser.add_argument('--input', required=True, help='Input file or directory path')
    parser.add_argument('--output', required=True, help='Output file or directory path')
    parser.add_argument('--consent-dir', help='Path to consent directory (for protect action)')
    
    args = parser.parse_args()
    
    setup_logging()
    logger = setup_security_logger()
    
    try:
        if args.action == 'sanitize_csv':
            counts = sanitize_csv_file(args.input, args.output)
            logger.info(f"Sanitization complete. Redactions: {counts}")
            
        elif args.action == 'sanitize_json':
            counts = sanitize_json_file(args.input, args.output)
            logger.info(f"Sanitization complete. Redactions: {counts}")
            
        elif args.action == 'sanitize_logs':
            counts = sanitize_interaction_logs(args.input, args.output)
            logger.info(f"Sanitization complete. Redactions: {counts}")
            
        elif args.action == 'scan':
            results = scan_directory_for_sensitive_data(args.input, args.output)
            logger.info(f"Scan complete. Files with sensitive data: {results['files_with_sensitive_data']}")
            
        elif args.action == 'protect':
            actions = enforce_data_protection_policy(
                args.input, args.output, 
                consent_dir=args.consent_dir
            )
            logger.info(f"Protection complete. Files processed: {actions['files_processed']}")
            
    except Exception as e:
        logger.error(f"Security hardening failed: {e}")
        raise

if __name__ == '__main__':
    main()
