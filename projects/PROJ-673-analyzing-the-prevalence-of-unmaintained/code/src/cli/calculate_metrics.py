import os
import sys
import json
from pathlib import Path
from datetime import datetime
from src.models.data_models import Dependency

def calculate_missing_release_proportion(dependencies_list):
    """
    Calculate the proportion of dependencies with missing release metadata.
    
    Args:
        dependencies_list: List of dictionaries representing dependencies
        
    Returns:
        dict: Contains total count, missing count, and proportion
    """
    if not dependencies_list:
        return {
            "total_dependencies": 0,
            "missing_release_metadata": 0,
            "proportion": 0.0,
            "timestamp": datetime.now().isoformat()
        }
    
    missing_count = 0
    for dep in dependencies_list:
        # Check if release_date is missing (None, null, or empty string)
        release_date = dep.get("release_date")
        if release_date is None or release_date == "":
            missing_count += 1
    
    proportion = missing_count / len(dependencies_list)
    
    return {
        "total_dependencies": len(dependencies_list),
        "missing_release_metadata": missing_count,
        "proportion": proportion,
        "timestamp": datetime.now().isoformat()
    }

def load_dependencies_from_json(json_path):
    """Load dependencies from a JSON file."""
    with open(json_path, 'r') as f:
        data = json.load(f)
    return data.get("dependencies", [])

def write_metrics_to_file(metrics, output_path):
    """Write metrics to a JSON file."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(metrics, f, indent=2)

def main():
    """Main entry point for calculating metrics."""
    # Define paths
    input_path = Path("data/processed/dependencies_raw.json")
    output_path = Path("data/processed/metrics.json")
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
    
    # Load dependencies
    dependencies = load_dependencies_from_json(input_path)
    
    # Calculate metrics
    metrics = calculate_missing_release_proportion(dependencies)
    
    # Write to output file
    write_metrics_to_file(metrics, output_path)
    
    print(f"Metrics calculated and written to {output_path}")
    print(f"Total dependencies: {metrics['total_dependencies']}")
    print(f"Missing release metadata: {metrics['missing_release_metadata']}")
    print(f"Proportion: {metrics['proportion']:.4f}")

if __name__ == "__main__":
    main()
