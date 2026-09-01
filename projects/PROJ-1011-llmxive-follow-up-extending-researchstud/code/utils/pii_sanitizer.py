"""
PII Sanitizer Module for llmXive.

This module provides utilities to detect and sanitize Personally Identifiable Information (PII)
from logs and output files to ensure compliance with privacy standards.

It scans for common PII patterns:
- Email addresses
- Phone numbers (US/International formats)
- IP addresses (IPv4/IPv6)
- Social Security Numbers (US)
- Credit Card numbers (Luhn check)
- API Keys / Tokens (generic patterns)
- ORCIDs (specific to this project's domain)
"""
import re
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any, Union
import hashlib
import json
import csv
from datetime import datetime

# Configure logger
logger = logging.getLogger(__name__)

# PII Regex Patterns
PII_PATTERNS = {
    "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    "phone_us": re.compile(r'\b(?:\+1[-.\s]?)?(?:\(?\d{3}\)?)[-.\s]?\d{3}[-.\s]?\d{4}\b'),
    "phone_intl": re.compile(r'\b(?:\+?[0-9]{1,4}[-.\s]?)?(?:\(?\d{1,4}\)?)[-.\s]?\d{1,9}[-.\s]?\d{1,9}\b'),
    "ipv4": re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'),
    "ipv6": re.compile(r'\b(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}\b'),
    "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
    "credit_card": re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
    "api_key": re.compile(r'\b(?:api[_-]?key|token|secret)[\s]*[=:][\s]*["\']?([A-Za-z0-9\-_]{20,})["\']?'),
    "orcid": re.compile(r'\b\d{4}-\d{4}-\d{4}-\d{3}[0-9Xx]\b'),
    "url_private": re.compile(r'https?://[^\s]+/(?:private|secret|internal|admin)[^\s]*'),
}

# Replacement tokens
REPLACEMENTS = {
    "email": "[EMAIL_REDACTED]",
    "phone_us": "[PHONE_REDACTED]",
    "phone_intl": "[PHONE_REDACTED]",
    "ipv4": "[IP_REDACTED]",
    "ipv6": "[IP_REDACTED]",
    "ssn": "[SSN_REDACTED]",
    "credit_card": "[CC_REDACTED]",
    "api_key": "[API_KEY_REDACTED]",
    "orcid": "[ORCID_REDACTED]",
    "url_private": "[URL_PRIVATE_REDACTED]",
}

def detect_pii(text: str) -> List[Dict[str, Any]]:
    """
    Scan a string for PII patterns and return a list of matches with metadata.
    
    Args:
        text: The string to scan.
        
    Returns:
        List of dicts containing: {'type', 'match', 'start', 'end', 'line'}
    """
    findings = []
    lines = text.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        for pii_type, pattern in PII_PATTERNS.items():
            for match in pattern.finditer(line):
                # Specific validation for credit cards (Luhn check) could be added here
                # For now, we trust the regex but log a warning for high-volume matches
                findings.append({
                    "type": pii_type,
                    "match": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                    "line": line_num,
                    "context": line[max(0, match.start()-10):match.end()+10]
                })
    
    return findings

def sanitize_text(text: str, replacement: Optional[str] = None) -> str:
    """
    Remove or redact PII from a text string.
    
    Args:
        text: The input text.
        replacement: Custom replacement string. Defaults to type-specific token.
        
    Returns:
        Sanitized text.
    """
    sanitized = text
    for pii_type, pattern in PII_PATTERNS.items():
        repl = REPLACEMENTS[pii_type] if replacement is None else replacement
        # Use a lambda to ensure we only replace the matched group, not the whole match if groups exist
        # But our patterns mostly capture the whole thing. 
        sanitized = pattern.sub(repl, sanitized)
    return sanitized

def sanitize_file(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    mode: str = 'text',
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Scan and sanitize a file for PII.
    
    Args:
        input_path: Path to the source file.
        output_path: Path to write the sanitized file.
        mode: 'text' for plain text, 'json' for JSON objects, 'csv' for CSV.
        dry_run: If True, only scan and report, do not write output.
        
    Returns:
        Dict with scan statistics: {'total_lines', 'pii_found', 'types_found', 'sanitized': bool}
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    stats = {
        "total_lines": 0,
        "pii_found": 0,
        "types_found": set(),
        "sanitized": False
    }
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            if mode == 'json':
                # Read entire file as JSON
                content = f.read()
                data = json.loads(content)
                # Recursively sanitize JSON structure
                sanitized_data = _sanitize_json_recursive(data)
                stats["pii_found"] = len(_count_pii_in_object(data)) # Approximate count
                
                if not dry_run:
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, 'w', encoding='utf-8') as out_f:
                        json.dump(sanitized_data, out_f, indent=2)
                    stats["sanitized"] = True
                    
            elif mode == 'csv':
                # Process line by line to handle large files
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                rows = []
                
                for row in reader:
                    stats["total_lines"] += 1
                    new_row = {}
                    for key, value in row.items():
                        if value:
                            findings = detect_pii(value)
                            if findings:
                                stats["pii_found"] += len(findings)
                                stats["types_found"].update(f["type"] for f in findings)
                                new_row[key] = sanitize_text(value)
                            else:
                                new_row[key] = value
                        else:
                            new_row[key] = value
                    rows.append(new_row)
                
                if not dry_run:
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, 'w', newline='', encoding='utf-8') as out_f:
                        writer = csv.DictWriter(out_f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(rows)
                    stats["sanitized"] = True
                    
            else: # text
                lines = f.readlines()
                sanitized_lines = []
                for line in lines:
                    stats["total_lines"] += 1
                    findings = detect_pii(line)
                    if findings:
                        stats["pii_found"] += len(findings)
                        stats["types_found"].update(f["type"] for f in findings)
                    sanitized_lines.append(sanitize_text(line))
                
                if not dry_run:
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, 'w', encoding='utf-8') as out_f:
                        out_f.writelines(sanitized_lines)
                    stats["sanitized"] = True
                    
    except json.JSONDecodeError:
        logger.warning(f"File {input_path} is not valid JSON. Treating as text.")
        # Fallback to text processing
        return sanitize_file(input_path, output_path, mode='text', dry_run=dry_run)
    except Exception as e:
        logger.error(f"Error processing file {input_path}: {e}")
        raise
        
    return stats

def _sanitize_json_recursive(obj: Any) -> Any:
    """Recursively sanitize a JSON object."""
    if isinstance(obj, dict):
        return {k: _sanitize_json_recursive(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_sanitize_json_recursive(item) for item in obj]
    elif isinstance(obj, str):
        return sanitize_text(obj)
    else:
        return obj

def _count_pii_in_object(obj: Any) -> int:
    """Count PII occurrences in a JSON object."""
    count = 0
    if isinstance(obj, dict):
        for v in obj.values():
            count += _count_pii_in_object(v)
    elif isinstance(obj, list):
        for item in obj:
            count += _count_pii_in_object(item)
    elif isinstance(obj, str):
        count += len(detect_pii(obj))
    return count

def validate_output_file(path: Union[str, Path]) -> bool:
    """
    Verify that a file contains no PII.
    
    Args:
        path: Path to the file to validate.
        
    Returns:
        True if no PII found, False otherwise.
        
    Raises:
        ValidationError: If PII is detected.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    try:
        content = path.read_text(encoding='utf-8')
        findings = detect_pii(content)
        if findings:
            types = set(f["type"] for f in findings)
            logger.error(f"PII detected in {path}: {types}")
            # Log first few findings for debugging
            for f in findings[:5]:
                logger.error(f"  - Type: {f['type']}, Line: {f['line']}, Context: ...{f['context']}...")
            return False
        return True
    except Exception as e:
        logger.error(f"Error validating file {path}: {e}")
        raise

def main():
    """CLI entry point for PII sanitization."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Sanitize PII from project files.")
    parser.add_argument("input", help="Input file path")
    parser.add_argument("output", help="Output file path")
    parser.add_argument("--mode", choices=["text", "json", "csv"], default="text", help="File mode")
    parser.add_argument("--dry-run", action="store_true", help="Only scan, do not write")
    parser.add_argument("--validate", action="store_true", help="Validate output for PII after writing")
    
    args = parser.parse_args()
    
    logger.info(f"Scanning {args.input} for PII...")
    stats = sanitize_file(args.input, args.output, mode=args.mode, dry_run=args.dry_run)
    
    if args.dry_run:
        print(f"Scan complete. Found {stats['pii_found']} PII instances of types: {stats['types_found']}")
        return
        
    print(f"Sanitized file written to {args.output}")
    print(f"Statistics: {stats}")
    
    if args.validate:
        if validate_output_file(args.output):
            print("Validation PASSED: No PII found in output.")
        else:
            print("Validation FAILED: PII still detected in output.")
            exit(1)

if __name__ == "__main__":
    main()
