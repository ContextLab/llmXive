import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path to allow imports from sibling modules
# Assumes this script is run from the project root or code directory
def get_project_root() -> Path:
    """Determine the project root directory."""
    current = Path(__file__).resolve()
    # Traverse up to find the directory containing 'code', 'data', 'state'
    for parent in current.parents:
        if (parent / "state").exists() and (parent / "data").exists():
            return parent
    # Fallback: assume project root is parent of 'code'
    return current.parent.parent

def get_paths(project_root: Path) -> Dict[str, Path]:
    """Get standard paths for state artifacts."""
    return {
        "state_dir": project_root / "state",
        "runtime_metrics_path": project_root / "state" / "runtime_metrics.json",
        "start_timestamp_path": project_root / "state" / "pipeline_start_timestamp.txt",
        "end_timestamp_path": project_root / "state" / "pipeline_end_timestamp.txt",
    }

def load_timestamp(path: Path, label: str) -> float:
    """Load a timestamp from a file. Raises FileNotFoundError if missing."""
    if not path.exists():
        raise FileNotFoundError(
            f"Required timestamp file missing for {label}: {path}. "
            "Ensure the pipeline writes start/end timestamps before running this script."
        )
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()
    try:
        return float(content)
    except ValueError:
        raise ValueError(f"Invalid timestamp format in {path}: '{content}'")

def measure_runtime() -> Dict[str, Any]:
    """
    Calculate total runtime in minutes and compare against the 300-minute limit.
    
    Reads start and end timestamps from state files written by the pipeline.
    
    Returns:
        Dict with keys:
            - total_runtime_minutes (float)
            - limit_minutes (int)
            - status (str: "pass" or "fail")
    """
    project_root = get_project_root()
    paths = get_paths(project_root)
    
    # Ensure state directory exists
    paths["state_dir"].mkdir(parents=True, exist_ok=True)
    
    # Load timestamps
    start_time = load_timestamp(paths["start_timestamp_path"], "start")
    end_time = load_timestamp(paths["end_timestamp_path"], "end")
    
    # Calculate duration
    duration_seconds = end_time - start_time
    if duration_seconds < 0:
        raise ValueError(
            f"End timestamp ({end_time}) is before start timestamp ({start_time}). "
            "Pipeline timing logic is incorrect."
        )
    
    total_runtime_minutes = duration_seconds / 60.0
    limit_minutes = 300
    
    status = "pass" if total_runtime_minutes <= limit_minutes else "fail"
    
    return {
        "total_runtime_minutes": round(total_runtime_minutes, 4),
        "limit_minutes": limit_minutes,
        "status": status,
        "start_timestamp": start_time,
        "end_timestamp": end_time,
        "duration_seconds": duration_seconds
    }

def save_metrics(metrics: Dict[str, Any], output_path: Path) -> None:
    """Save runtime metrics to a JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

def main() -> None:
    """Main entry point for runtime measurement."""
    project_root = get_project_root()
    paths = get_paths(project_root)
    
    try:
        metrics = measure_runtime()
        save_metrics(metrics, paths["runtime_metrics_path"])
        
        status_icon = "✅" if metrics["status"] == "pass" else "⚠️"
        print(f"{status_icon} Runtime Check: {metrics['total_runtime_minutes']:.2f} minutes "
              f"(Limit: {metrics['limit_minutes']} minutes) -> {metrics['status'].upper()}")
        print(f"Metrics saved to: {paths['runtime_metrics_path']}")
        
        # Exit with error code if limit exceeded
        if metrics["status"] == "fail":
            sys.exit(1)
            
    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()