"""
Metrics calculator for calculating proportions of dependencies with missing release metadata.
Satisfies SC-002.
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure we can import from src if run as script, though usually imported as module
try:
    from src.models.data_models import Dependency
except ImportError:
    # Fallback for direct execution if path isn't set up correctly
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.models.data_models import Dependency


def calculate_missing_release_proportion(dependencies: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate the proportion of dependencies with missing release metadata.
    
    Args:
        dependencies: List of dependency dictionaries containing metadata.
                      Expected keys: 'name', 'last_release_date', 'last_commit_date', etc.
    
    Returns:
        Dictionary with:
            - total_count: Total number of dependencies
            - missing_release_count: Number of dependencies with null/missing last_release_date
            - missing_release_proportion: Ratio of missing release metadata (0.0 to 1.0)
    """
    if not dependencies:
        return {
            "total_count": 0,
            "missing_release_count": 0,
            "missing_release_proportion": 0.0
        }
    
    total_count = len(dependencies)
    missing_release_count = 0
    
    for dep in dependencies:
        # Check if last_release_date is missing (None, null, or empty string)
        release_date = dep.get('last_release_date')
        if release_date is None or release_date == '':
            missing_release_count += 1
    
    missing_release_proportion = missing_release_count / total_count if total_count > 0 else 0.0
    
    return {
        "total_count": total_count,
        "missing_release_count": missing_release_count,
        "missing_release_proportion": missing_release_proportion
    }


def write_metrics_to_file(metrics: Dict[str, Any], output_path: str) -> None:
    """
    Write calculated metrics to a JSON file.
    
    Args:
        metrics: Dictionary containing calculated metrics
        output_path: Path to the output JSON file
    """
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)


def main():
    """
    Main entry point for calculating and writing metrics.
    Reads dependencies from data/processed/dependencies_raw.csv (if exists),
    calculates the proportion of missing release metadata, and writes to data/processed/metrics.json.
    """
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    input_file = project_root / "data" / "processed" / "dependencies_raw.csv"
    output_file = project_root / "data" / "processed" / "metrics.json"
    
    dependencies = []
    
    if input_file.exists():
        import pandas as pd
        df = pd.read_csv(input_file)
        # Convert dataframe to list of dictionaries
        dependencies = df.to_dict('records')
        print(f"Loaded {len(dependencies)} dependencies from {input_file}")
    else:
        print(f"Warning: Input file {input_file} not found. Using empty dataset.")
    
    # Calculate metrics
    metrics = calculate_missing_release_proportion(dependencies)
    metrics['source_file'] = str(input_file)
    metrics['output_file'] = str(output_file)
    
    # Write to output file
    write_metrics_to_file(metrics, str(output_file))
    print(f"Metrics written to {output_file}")
    print(f"Total dependencies: {metrics['total_count']}")
    print(f"Missing release metadata: {metrics['missing_release_count']} ({metrics['missing_release_proportion']:.2%})")


if __name__ == "__main__":
    main()
