import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from config import OUTPUTS_LOGS_DIR, LOG_LEVEL

def log_training_metrics(metrics: Dict[str, Any]) -> None:
    """Log training metrics to file."""
    log_file = OUTPUTS_LOGS_DIR / "training_metrics.json"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logs = []
    if log_file.exists():
        with open(log_file, 'r') as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []

    logs.append({
        'timestamp': str(pd.Timestamp.now()),
        'metrics': metrics
    })

    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=2)
