import json
import csv
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import sys

# Import from existing API surface
from code.config.env_config import get_path

# Constants for validation
VALID_STIMULUS_TYPES = ['target', 'non-target']
MAX_RESPONSE_TIME_MS = 10000  # 10 seconds max
MIN_RESPONSE_TIME_MS = 100    # 100ms min
MAX_MINUTES_PER_DAY = 1440    # 24 hours

def parse_json_logs(input_path: str) -> List[Dict[str, Any]]:
    """
    Parse compliance logs from a JSON file.
    
    This function implements the "Fail Loudly" principle: if the file does not exist
    or is malformed, it raises an exception immediately rather than falling back to
    synthetic data.
    
    Args:
        input_path: Path to the JSON log file
        
    Returns:
        List of parsed log records
        
    Raises:
        FileNotFoundError: If the input file does not exist
        json.JSONDecodeError: If the file is not valid JSON
        ValueError: If the file is empty or malformed
    """
    path = Path(input_path)
    
    # CRITICAL: Fail loudly if file does not exist - NO fallback to synthetic
    if not path.exists():
        raise FileNotFoundError(
            f"Log file not found: {input_path}. "
            "The pipeline requires real compliance log data. Do not use synthetic fallbacks."
        )
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                raise ValueError(f"Log file is empty: {input_path}")
            
            data = json.loads(content)
            
            # Handle both list and dict with 'logs' key
            if isinstance(data, dict):
                if 'logs' not in data:
                    raise ValueError(
                        f"JSON file must contain a 'logs' key or be a list. "
                        f"Found keys: {list(data.keys())}"
                    )
                logs = data['logs']
            elif isinstance(data, list):
                logs = data
            else:
                raise ValueError(f"JSON file must contain a list or dict with 'logs' key")
            
            if not isinstance(logs, list):
                raise ValueError("'logs' must be a list of log entries")
            
            if len(logs) == 0:
                raise ValueError(f"Log file contains no data entries: {input_path}")
            
            return logs
            
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Failed to parse JSON file {input_path}: {e.msg}", e.doc, e.pos
        )

def parse_csv_logs(input_path: str) -> List[Dict[str, Any]]:
    """
    Parse compliance logs from a CSV file.
    
    This function implements the "Fail Loudly" principle: if the file does not exist
    or is malformed, it raises an exception immediately rather than falling back to
    synthetic data.
    
    Args:
        input_path: Path to the CSV log file
        
    Returns:
        List of parsed log records
        
    Raises:
        FileNotFoundError: If the input file does not exist
        ValueError: If the file is malformed or missing required columns
    """
    path = Path(input_path)
    
    # CRITICAL: Fail loudly if file does not exist - NO fallback to synthetic
    if not path.exists():
        raise FileNotFoundError(
            f"Log file not found: {input_path}. "
            "The pipeline requires real compliance log data. Do not use synthetic fallbacks."
        )
    
    records = []
    required_columns = {'participant_id', 'date', 'minutes', 'activity_type'}
    
    try:
        with open(path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            if reader.fieldnames is None:
                raise ValueError(f"CSV file is empty or has no headers: {input_path}")
            
            header_set = set(reader.fieldnames)
            missing = required_columns - header_set
            if missing:
                raise ValueError(
                    f"CSV file missing required columns: {missing}. "
                    f"Found: {header_set}"
                )
            
            for row_num, row in enumerate(reader, start=2):
                records.append(row)
                
    except csv.Error as e:
        raise ValueError(f"Failed to parse CSV file {input_path}: {e}") from e
    
    if not records:
        raise ValueError(f"CSV file {input_path} contains no data rows")
    
    return records

def validate_and_normalize(logs: List[Dict[str, Any]], log_format: str = 'json') -> List[Dict[str, Any]]:
    """
    Validate and normalize log entries.
    
    This function:
    1. Validates required fields are present
    2. Normalizes field names and types
    3. Validates data ranges (fail loudly on invalid data)
    
    Args:
        logs: List of raw log entries
        log_format: 'json' or 'csv' indicating source format
        
    Returns:
        List of normalized log records
        
    Raises:
        ValueError: If any log entry is invalid
    """
    normalized = []
    
    for idx, log in enumerate(logs):
        try:
            # Determine source fields based on format
            if log_format == 'json':
                # JSON format: participant_id, date, minutes, activity_type, etc.
                participant_id = log.get('participant_id')
                date_str = log.get('date')
                minutes = log.get('minutes')
                activity_type = log.get('activity_type')
            else:
                # CSV format
                participant_id = log.get('participant_id')
                date_str = log.get('date')
                minutes = log.get('minutes')
                activity_type = log.get('activity_type')
            
            # Validate required fields
            if not participant_id:
                raise ValueError(f"Entry {idx}: Missing participant_id")
            if not date_str:
                raise ValueError(f"Entry {idx}: Missing date")
            if minutes is None:
                raise ValueError(f"Entry {idx}: Missing minutes")
            if not activity_type:
                raise ValueError(f"Entry {idx}: Missing activity_type")
            
            # Normalize types
            try:
                minutes_float = float(minutes)
            except (ValueError, TypeError):
                raise ValueError(f"Entry {idx}: minutes must be numeric, got {minutes}")
            
            # Validate ranges - FAIL LOUDLY
            if minutes_float < 0:
                raise ValueError(f"Entry {idx}: minutes cannot be negative, got {minutes_float}")
            if minutes_float > MAX_MINUTES_PER_DAY:
                raise ValueError(
                    f"Entry {idx}: minutes exceeds maximum ({MAX_MINUTES_PER_DAY}), got {minutes_float}"
                )
            
            # Normalize date
            try:
                parsed_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                normalized_date = parsed_date.strftime('%Y-%m-%d')
            except (ValueError, AttributeError):
                raise ValueError(f"Entry {idx}: Invalid date format '{date_str}'")
            
            normalized_record = {
                'participant_id': str(participant_id).strip(),
                'date': normalized_date,
                'minutes': minutes_float,
                'activity_type': str(activity_type).strip().lower(),
                'raw_entry': log
            }
            
            normalized.append(normalized_record)
            
        except ValueError as e:
            raise ValueError(f"Validation failed for entry {idx}: {e}") from e
    
    return normalized

def parse_logs(input_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Main entry point for parsing compliance logs.
    
    This function:
    1. Detects file format (JSON or CSV)
    2. Parses the logs (fail loudly on errors)
    3. Validates and normalizes entries
    4. Writes output to CSV
    
    Args:
        input_path: Path to the input log file
        output_path: Path for output CSV (optional)
        
    Returns:
        Dictionary with parsing results
        
    Raises:
        FileNotFoundError: If input file does not exist
        ValueError: If file is malformed or data is invalid
    """
    path = Path(input_path)
    
    if not path.exists():
        raise FileNotFoundError(
            f"Log file not found: {input_path}. "
            "The pipeline requires real compliance log data. Do not use synthetic fallbacks."
        )
    
    # Detect format
    suffix = path.suffix.lower()
    if suffix == '.json':
        log_format = 'json'
        raw_logs = parse_json_logs(input_path)
    elif suffix == '.csv':
        log_format = 'csv'
        raw_logs = parse_csv_logs(input_path)
    else:
        raise ValueError(f"Unsupported file format: {suffix}. Use .json or .csv")
    
    print(f"Parsed {len(raw_logs)} raw log entries from {input_path}")
    
    # Validate and normalize
    normalized_logs = validate_and_normalize(raw_logs, log_format)
    print(f"Validated and normalized {len(normalized_logs)} entries")
    
    # Write output
    if output_path is None:
        output_path = get_path('data/processed/parsed_compliance_logs.csv')
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['participant_id', 'date', 'minutes', 'activity_type']
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for log in normalized_logs:
            writer.writerow({k: log[k] for k in fieldnames})
    
    print(f"Written {len(normalized_logs)} entries to {output_path}")
    
    return {
        'input_path': input_path,
        'output_path': str(output_path),
        'format': log_format,
        'total_entries': len(normalized_logs),
        'status': 'success'
    }

def main():
    """
    Main entry point for the parse_logs script.
    
    Usage:
        python code/compliance/parse_logs.py --input <logs.json> --output <parsed.csv>
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Parse and validate compliance logs from JSON or CSV'
    )
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Path to input log file (JSON or CSV)'
    )
    parser.add_argument(
        '--output', '-o',
        default=None,
        help='Path to output CSV file (default: data/processed/parsed_compliance_logs.csv)'
    )
    
    args = parser.parse_args()
    
    try:
        result = parse_logs(args.input, args.output)
        print("\n=== Log Parsing Complete ===")
        print(f"Total entries processed: {result['total_entries']}")
        print(f"Output file: {result['output_path']}")
        return 0
    except FileNotFoundError as e:
        print(f"\n[ERROR] File not found: {e}", file=sys.stderr)
        print("The pipeline requires real compliance log data. Please ensure the input file exists.", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"\n[ERROR] Validation failed: {e}", file=sys.stderr)
        print("The input data is invalid. Please check the log file.", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"\n[ERROR] JSON parsing failed: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())