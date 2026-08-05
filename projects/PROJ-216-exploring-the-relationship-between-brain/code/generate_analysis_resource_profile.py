"""
Generate analysis resource profile for SC-005 verification.

This script reads the existing resource usage logs generated during the
preprocessing (T018) and graph metric computation phases, aggregates the
peak RAM usage and total runtime, and writes the result to
`data/processed/analysis_resource_profile.json`.

It relies on the `ResourceMonitor` class from `code/utils.py` which logs
per-subject resource usage to `data/processed/resource_profile.json`.
"""
import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils import ResourceMonitor

OUTPUT_PATH = project_root / "data" / "processed" / "analysis_resource_profile.json"
INPUT_PATH = project_root / "data" / "processed" / "resource_profile.json"

def load_resource_profile(path: Path) -> Optional[Dict[str, Any]]:
    """Load the resource profile JSON if it exists."""
    if not path.exists():
        return None
    with open(path, "r") as f:
        return json.load(f)

def aggregate_analysis_resources(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aggregate peak RAM and total runtime from the resource profile.
    
    Expected profile structure (from ResourceMonitor):
    {
        "subjects": [
            {"id": "sub-01", "peak_ram_mb": 123.4, "runtime_seconds": 5.6},
            ...
        ],
        "total_runtime_seconds": 100.0,
        "max_peak_ram_mb": 200.0
    }
    """
    subjects = profile.get("subjects", [])
    
    if not subjects:
        return {
            "peak_ram_mb": 0.0,
            "total_runtime_seconds": 0.0,
            "subject_count": 0,
            "note": "No subjects found in resource profile."
        }
    
    # Calculate aggregate peak RAM (max of individual peaks)
    # The ResourceMonitor already tracks this, but we re-aggregate for clarity
    peak_rams = [s.get("peak_ram_mb", 0) for s in subjects]
    max_peak_ram = max(peak_rams) if peak_rams else 0.0
    
    # Total runtime is the sum of individual runtimes or the recorded total
    # We use the recorded total if available, otherwise sum individual runtimes
    total_runtime = profile.get("total_runtime_seconds", 0.0)
    if total_runtime == 0.0:
        total_runtime = sum(s.get("runtime_seconds", 0) for s in subjects)
    
    return {
        "peak_ram_mb": round(max_peak_ram, 2),
        "total_runtime_seconds": round(total_runtime, 2),
        "subject_count": len(subjects),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_file": str(INPUT_PATH),
        "verification_target": "SC-005"
    }

def main():
    """Main entry point for generating the analysis resource profile."""
    print(f"Loading resource profile from: {INPUT_PATH}")
    
    profile = load_resource_profile(INPUT_PATH)
    
    if profile is None:
        print(f"Warning: Resource profile not found at {INPUT_PATH}.")
        print("Creating an empty profile with zero metrics.")
        aggregated = {
            "peak_ram_mb": 0.0,
            "total_runtime_seconds": 0.0,
            "subject_count": 0,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "source_file": str(INPUT_PATH),
            "verification_target": "SC-005",
            "note": "No resource profile found. Ensure preprocessing and graph metric steps have run."
        }
    else:
        print(f"Processing resource profile with {len(profile.get('subjects', []))} subjects.")
        aggregated = aggregate_analysis_resources(profile)
    
    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Write the aggregated profile
    with open(OUTPUT_PATH, "w") as f:
        json.dump(aggregated, f, indent=2)
    
    print(f"Analysis resource profile written to: {OUTPUT_PATH}")
    print(f"  Peak RAM: {aggregated['peak_ram_mb']} MB")
    print(f"  Total Runtime: {aggregated['total_runtime_seconds']} seconds")
    print(f"  Subjects processed: {aggregated['subject_count']}")

if __name__ == "__main__":
    main()