import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from config import get_path, ensure_directories

def validate_log(log_entry: Dict) -> bool:
    """Validate that a log entry has required fields."""
    required = ['repo_id', 'context_precision', 'total_tokens', 'wall_clock_latency']
    return all(k in log_entry for k in required)

def log_metrics(log_entry: Dict, output_path: str) -> None:
    """Append a log entry to a JSONL file."""
    ensure_directories([Path(output_path).parent])
    with open(output_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry) + '\n')

def create_log_entry(
    repo_id: str,
    context_precision: float,
    total_tokens: int,
    wall_clock_latency: float,
    regularity_score: Optional[float] = None,
    set_type: Optional[str] = None,
    **extra: Any
) -> Dict:
    """Create a structured log entry."""
    entry = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'repo_id': repo_id,
        'context_precision': context_precision,
        'total_tokens': total_tokens,
        'wall_clock_latency': wall_clock_latency,
        'regularity_score': regularity_score,
        'set_type': set_type
    }
    entry.update(extra)
    return entry

def main():
    # Demo
    entry = create_log_entry(
        repo_id="test-repo",
        context_precision=0.85,
        total_tokens=100,
        wall_clock_latency=0.5
    )
    path = get_path('results', 'demo_logs.jsonl')
    log_metrics(entry, path)
    print(f"Logged to {path}")

if __name__ == '__main__':
    main()
