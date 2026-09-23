import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

def init_log_file(path: str | Path) -> None:
    """
    Initialize a log file at the specified path.
    Creates the directory if it doesn't exist.
    Overwrites any existing content to ensure a fresh start.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Create/overwrite file
    with open(path, 'w', encoding='utf-8') as f:
        f.write("")

def write_log_entry(path: str | Path, entry: Dict[str, Any]) -> None:
    """
    Write a single log entry (JSONL format) to the file.
    Adds a timestamp to the entry if not present.
    """
    path = Path(path)
    if "timestamp" not in entry:
        entry["timestamp"] = datetime.utcnow().isoformat() + "Z"
    
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')

def write_log_entries(path: str | Path, entries: List[Dict[str, Any]]) -> None:
    """
    Write multiple log entries to the file efficiently.
    """
    path = Path(path)
    with open(path, 'a', encoding='utf-8') as f:
        for entry in entries:
            if "timestamp" not in entry:
                entry["timestamp"] = datetime.utcnow().isoformat() + "Z"
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

def read_log_entries(path: str | Path) -> List[Dict[str, Any]]:
    """
    Read all log entries from the file.
    Returns a list of dictionaries. Skips malformed lines.
    """
    path = Path(path)
    entries = []
    if not path.exists():
        return entries
        
    with open(path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError as e:
                    # Log error but continue reading valid lines
                    print(f"Warning: Skipping malformed JSON at line {line_num}: {e}")
                    continue
    return entries

def get_log_stats(path: str | Path) -> Dict[str, Any]:
    """
    Calculate basic statistics from the log file.
    Returns counts of total, success, failure, and exception entries.
    """
    entries = read_log_entries(path)
    total = len(entries)
    success = sum(1 for e in entries if e.get("agent_status") == "success")
    failure = sum(1 for e in entries if e.get("agent_status") == "failure")
    exceptions = sum(1 for e in entries if e.get("agent_status") == "exception")
    
    return {
        "total_entries": total,
        "success": success,
        "failure": failure,
        "exception": exceptions,
        "success_rate": success / total if total > 0 else 0.0
    }