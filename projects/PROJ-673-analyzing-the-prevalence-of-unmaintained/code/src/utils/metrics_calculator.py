import json
from pathlib import Path
from typing import List, Dict, Any

def calculate_missing_release_proportion(data: List[Dict[str, Any]]) -> float:
    """
    Calculates the proportion of dependencies with missing release metadata.
    """
    if not data:
        return 0.0
    
    missing_count = sum(1 for d in data if not d.get('last_release_date'))
    return missing_count / len(data)

def write_metrics_to_file(metrics_path: Path, proportion: float) -> None:
    """
    Writes the metrics to a JSON file.
    """
    metrics = {
        "missing_release_proportion": proportion,
        "timestamp": "2023-10-27T12:00:00Z" # Placeholder for real timestamp
    }
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
