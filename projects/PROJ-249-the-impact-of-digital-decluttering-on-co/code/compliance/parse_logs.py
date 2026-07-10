"""
Daily log parser for digital decluttering compliance study.

Parses raw daily compliance logs (JSON or CSV) into a standardized format
suitable for downstream validation and rule enforcement.

Input formats supported:
- JSON: Array of log objects or newline-delimited JSON (NDJSON)
- CSV: Standard CSV with headers matching expected schema

Output:
- Normalized DataFrame-like list of dicts ready for validation (T025)
  and rule engine (T026).
"""
import json
import csv
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

# Expected schema for a single daily log entry
# Matches data-model.md and contracts/dataset.schema.yaml (T007)
EXPECTED_FIELDS = {
    "participant_id": str,
    "date": str,  # ISO format YYYY-MM-DD
    "social_media_minutes": (int, float),
    "news_minutes": (int, float),
    "notifications_disabled": bool,
    "device_used": str,
    "notes": Optional[str],
}

REQUIRED_FIELDS = ["participant_id", "date", "social_media_minutes", "news_minutes", "notifications_disabled"]


def parse_json_logs(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Parse JSON or NDJSON log file into a list of dictionaries.
    
    Args:
        file_path: Path to the JSON file.
        
    Returns:
        List of parsed log dictionaries.
        
    Raises:
        FileNotFoundError: If file does not exist.
        json.JSONDecodeError: If JSON is malformed.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Log file not found: {path}")

    logs = []
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        
        # Check if NDJSON (multiple JSON objects, one per line)
        if '\n' in content:
            for line in content.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    logs.append(json.loads(line))
                except json.JSONDecodeError as e:
                    raise json.JSONDecodeError(f"Error parsing line: {line}", e.doc, e.pos)
        else:
            # Single JSON object or array
            data = json.loads(content)
            if isinstance(data, list):
                logs.extend(data)
            elif isinstance(data, dict):
                logs.append(data)
            else:
                raise ValueError(f"Unexpected JSON root type: {type(data)}")
                
    return logs


def parse_csv_logs(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Parse CSV log file into a list of dictionaries.
    
    Args:
        file_path: Path to the CSV file.
        
    Returns:
        List of parsed log dictionaries.
        
    Raises:
        FileNotFoundError: If file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Log file not found: {path}")

    logs = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric strings to appropriate types
            if 'social_media_minutes' in row:
                try:
                    row['social_media_minutes'] = float(row['social_media_minutes'])
                except ValueError:
                    row['social_media_minutes'] = 0.0
                    
            if 'news_minutes' in row:
                try:
                    row['news_minutes'] = float(row['news_minutes'])
                except ValueError:
                    row['news_minutes'] = 0.0
                    
            if 'notifications_disabled' in row:
                val = str(row['notifications_disabled']).lower().strip()
                row['notifications_disabled'] = val in ('true', '1', 'yes')
                
            logs.append(row)
            
    return logs


def validate_and_normalize(logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validate required fields and normalize data types.
    
    This function ensures that every log entry has the required fields
    and attempts to coerce values to the expected types.
    
    Args:
        logs: List of raw log dictionaries.
        
    Returns:
        List of normalized log dictionaries.
        
    Raises:
        ValueError: If required fields are missing or cannot be coerced.
    """
    normalized = []
    for i, log in enumerate(logs):
        # Check required fields
        missing = [f for f in REQUIRED_FIELDS if f not in log]
        if missing:
            raise ValueError(f"Log entry {i} missing required fields: {missing}")
        
        # Normalize participant_id
        pid = str(log['participant_id']).strip()
        if not pid:
            raise ValueError(f"Log entry {i} has empty participant_id")
        
        # Normalize date
        date_str = str(log['date']).strip()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Log entry {i} has invalid date format: {date_str}. Expected YYYY-MM-DD.")
        
        # Normalize numeric fields
        try:
            social_media = float(log['social_media_minutes'])
        except (ValueError, TypeError):
            raise ValueError(f"Log entry {i} has invalid social_media_minutes: {log['social_media_minutes']}")
        
        try:
            news = float(log['news_minutes'])
        except (ValueError, TypeError):
            raise ValueError(f"Log entry {i} has invalid news_minutes: {log['news_minutes']}")
        
        # Normalize boolean
        notif = log['notifications_disabled']
        if isinstance(notif, bool):
            notif_bool = notif
        elif isinstance(notif, str):
            notif_bool = notif.lower().strip() in ('true', '1', 'yes')
        else:
            notif_bool = bool(notif)
        
        normalized_entry = {
            "participant_id": pid,
            "date": date_str,
            "social_media_minutes": social_media,
            "news_minutes": news,
            "notifications_disabled": notif_bool,
            "device_used": str(log.get("device_used", "unknown")),
            "notes": log.get("notes", ""),
        }
        normalized.append(normalized_entry)
        
    return normalized


def parse_logs(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Main entry point for parsing daily compliance logs.
    
    Automatically detects file format based on extension and parses accordingly.
    Validates and normalizes the output.
    
    Args:
        file_path: Path to the log file (JSON, NDJSON, or CSV).
        
    Returns:
        List of normalized log dictionaries ready for validation (T025)
        and rule engine (T026).
        
    Raises:
        FileNotFoundError: If file does not exist.
        ValueError: If file format is unsupported or data is invalid.
        json.JSONDecodeError: If JSON is malformed.
    """
    path = Path(file_path)
    suffix = path.suffix.lower()
    
    if suffix == '.json':
        raw_logs = parse_json_logs(path)
    elif suffix == '.csv':
        raw_logs = parse_csv_logs(path)
    else:
        raise ValueError(f"Unsupported file format: {suffix}. Use .json or .csv")
        
    if not raw_logs:
        return []
        
    return validate_and_normalize(raw_logs)


def main():
    """
    Command-line interface for testing the parser.
    
    Usage:
        python -m code.compliance.parse_logs <path_to_log_file>
        
    Reads the specified file, parses it, and prints the normalized results.
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m code.compliance.parse_logs <path_to_log_file>")
        sys.exit(1)
        
    log_file = sys.argv[1]
    
    try:
        logs = parse_logs(log_file)
        print(f"Successfully parsed {len(logs)} log entries:")
        for log in logs:
            print(json.dumps(log, indent=2))
    except Exception as e:
        print(f"Error parsing logs: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()