import os
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import capture_metrics


def main():
    """
    Run resource monitoring and save metrics to data/processed/resource_metrics.json.
    This script is invoked by the run-book to satisfy SC-005.
    """
    output_path = "data/processed/resource_metrics.json"
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    print(f"Capturing resource metrics to {output_path}...")
    metrics = capture_metrics(output_path)
    
    print("Resource metrics captured:")
    print(json.dumps(metrics, indent=2))
    
    # Verify file was written
    if os.path.exists(output_path):
        print(f"SUCCESS: Metrics file written to {output_path}")
    else:
        print(f"ERROR: Failed to write metrics file to {output_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()