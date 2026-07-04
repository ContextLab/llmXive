import os
import sys
import json
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models.data_models import Dependency
from src.utils.metrics_calculator import calculate_missing_release_proportion, write_metrics_to_file

def main():
    """
    Calculates metrics (T017a) based on collected data.
    """
    data_path = project_root / "data" / "processed" / "dependencies_raw.json"
    if not data_path.exists():
        print("Error: No data found. Run collect_data.py first.")
        return

    with open(data_path, 'r') as f:
        data = json.load(f)

    proportion = calculate_missing_release_proportion(data)
    metrics_path = project_root / "data" / "processed" / "metrics.json"
    write_metrics_to_file(metrics_path, proportion)
    print(f"Metrics written to {metrics_path}")

if __name__ == "__main__":
    main()