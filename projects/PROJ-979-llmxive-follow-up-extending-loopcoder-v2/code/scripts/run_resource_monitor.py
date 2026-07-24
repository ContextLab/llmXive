"""
Script to execute resource metric capture for T005e.
This script ensures the data/processed directory exists and runs capture_metrics().
"""
import os
import sys
import json
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from utils import capture_metrics

def main():
    """
    Execute resource monitoring and save to data/processed/resource_metrics.json.
    """
    print("Starting resource metric capture (Task T005e)...")
    
    # Ensure the output directory exists
    output_path = Path("data/processed/resource_metrics.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Capture metrics
    metrics = capture_metrics(output_path=str(output_path))
    
    # Verify file was written
    if output_path.exists():
        print(f"SUCCESS: Resource metrics saved to {output_path}")
        with open(output_path, 'r') as f:
            data = json.load(f)
            print(f"Captured memory: {data.get('memory', {}).get('used_gb', 'N/A')} GB used")
            print(f"Captured GPU status: {data.get('gpu', {}).get('available', 'N/A')}")
        return 0
    else:
        print("ERROR: Failed to write metrics file.")
        return 1

if __name__ == "__main__":
    sys.exit(main())