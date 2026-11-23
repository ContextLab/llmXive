import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

def init_log_file(log_path: Path) -> None:
    """Initialize a JSONL log file."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if not log_path.exists():
        log_path.touch()

def write_log_entry(log_path: Path, entry: Dict[str, Any]) -> None:
    """Append a single log entry to the JSONL file."""
    with open(log_path, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def write_log_entries(log_path: Path, entries: List[Dict[str, Any]]) -> None:
    """Append multiple log entries to the JSONL file."""
    with open(log_path, 'a') as f:
        for entry in entries:
            f.write(json.dumps(entry) + '\n')

def read_log_entries(log_path: Path) -> List[Dict[str, Any]]:
    """Read all entries from a JSONL log file."""
    entries = []
    if log_path.exists():
        with open(log_path, 'r') as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
    return entries

def get_log_stats(log_path: Path) -> Dict[str, Any]:
    """Get statistics about a log file."""
    entries = read_log_entries(log_path)
    return {
        'total_entries': len(entries),
        'timestamp': datetime.now().isoformat()
    }
