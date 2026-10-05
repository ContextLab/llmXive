import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

from utils import ResourceMonitor

def load_subject_logs(log_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all subject log files from the preprocessing log directory.
    Expected log format per file:
    {
      "subject_id": "subj_XXX",
      "status": "success" | "failed",
      "error_message": "..." (optional),
      "ram_gb": float,
      "runtime_hours": float
    }
    """
    logs = []
    if not log_dir.exists():
        return logs
    for log_file in log_dir.glob("*.json"):
        try:
            with open(log_file, 'r') as f:
                data = json.load(f)
                # Validate required fields
                if "subject_id" in data and "status" in data:
                    logs.append(data)
        except (json.JSONDecodeError, IOError):
            continue
    return logs

def calculate_stats(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate preprocessing statistics from the list of subject logs.
    Returns a dictionary with:
    - total_subjects: int
    - successful_subjects: int
    - failed_subjects: int
    - success_rate: float
    - peak_ram_gb: float (max across all subjects)
    - total_runtime_hours: float (sum across all subjects)
    - failed_subject_ids: list of subject IDs that failed
    """
    total = len(logs)
    if total == 0:
        return {
            "total_subjects": 0,
            "successful_subjects": 0,
            "failed_subjects": 0,
            "success_rate": 0.0,
            "peak_ram_gb": 0.0,
            "total_runtime_hours": 0.0,
            "failed_subject_ids": []
        }

    successful = [l for l in logs if l.get("status") == "success"]
    failed = [l for l in logs if l.get("status") == "failed"]

    success_rate = len(successful) / total if total > 0 else 0.0

    peak_ram = max((l.get("ram_gb", 0.0) for l in logs), default=0.0)
    total_runtime = sum(l.get("runtime_hours", 0.0) for l in logs)

    failed_ids = [l["subject_id"] for l in failed]

    return {
        "total_subjects": total,
        "successful_subjects": len(successful),
        "failed_subjects": len(failed),
        "success_rate": success_rate,
        "peak_ram_gb": peak_ram,
        "total_runtime_hours": total_runtime,
        "failed_subject_ids": failed_ids
    }

def main():
    """
    Main entry point to generate preprocessing statistics.
    Reads logs from data/processed/logs/ and writes stats to data/processed/preprocessing_stats.json.
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    log_dir = project_root / "data" / "processed" / "logs"
    output_path = project_root / "data" / "processed" / "preprocessing_stats.json"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load logs
    logs = load_subject_logs(log_dir)

    # Calculate statistics
    stats = calculate_stats(logs)

    # Write output
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)

    print(f"Preprocessing statistics written to {output_path}")
    print(f"Total subjects: {stats['total_subjects']}")
    print(f"Success rate: {stats['success_rate']:.2%}")

    return stats

if __name__ == "__main__":
    main()
