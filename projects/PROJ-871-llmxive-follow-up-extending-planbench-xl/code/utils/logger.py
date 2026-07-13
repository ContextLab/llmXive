import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

def init_log_file(path: str | Path) -> None:
    """
    Initialize a log file at the specified path.
    Creates the directory if it doesn't exist.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Create empty file
    with open(path, 'w', encoding='utf-8') as f:
        f.write("")

def write_log_entry(path: str | Path, entry: Dict[str, Any]) -> None:
    """
    Write a single log entry (JSONL format) to the file.
    """
    path = Path(path)
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')

def write_log_entries(path: str | Path, entries: List[Dict[str, Any]]) -> None:
    """
    Write multiple log entries to the file.
    """
    for entry in entries:
        write_log_entry(path, entry)

def read_log_entries(path: str | Path) -> List[Dict[str, Any]]:
    """
    Read all log entries from the file.
    """
    path = Path(path)
    entries = []
    if not path.exists():
        return entries
        
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries

def get_log_stats(path: str | Path) -> Dict[str, Any]:
    """
    Calculate basic statistics from the log file.
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
        "exception": exceptions
    }
