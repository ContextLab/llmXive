import os
import sys
import json
from pathlib import Path
from src.utils import capture_metrics

def main():
    """
    Main entry point for the resource monitoring script.
    Invokes capture_metrics() and ensures the output is written to disk.
    """
    output_path = "data/processed/resource_metrics.json"
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Capturing resource metrics to {output_path}...")
    metrics = capture_metrics(output_path)
    
    print("Resource metrics captured successfully:")
    print(json.dumps(metrics, indent=2))
    
    # Verify file was written
    if os.path.exists(output_path):
        print(f"Verification: {output_path} exists.")
        with open(output_path, 'r') as f:
            saved_metrics = json.load(f)
        print(f"Saved content: {saved_metrics}")
    else:
        print(f"ERROR: {output_path} was not created.")
        sys.exit(1)

if __name__ == "__main__":
    main()