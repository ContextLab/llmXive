import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add project root to path if running directly
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.models.data_models import Dependency

def load_dependencies_from_json(filepath: str) -> List[Dict[str, Any]]:
    """
    Load dependencies from a JSON file.
    Handles both the raw JSON structure and CSV-like JSON structures.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {filepath}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle if the data is a list directly
    if isinstance(data, list):
        return data
    
    # Handle if the data is a dict with a 'dependencies' key
    if isinstance(data, dict) and 'dependencies' in data:
        return data['dependencies']
    
    # Handle if the data is a dict with a 'data' key
    if isinstance(data, dict) and 'data' in data:
        return data['data']
    
    # If it's a dict but not structured as expected, treat the whole dict as one item
    # This is a fallback for unexpected formats
    return [data]

def calculate_missing_release_proportion(dependencies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate the proportion of dependencies with missing release metadata.
    
    Release metadata is considered missing if:
    - 'last_release_date' is None, null, or missing
    - 'last_release_date' is an empty string
    
    Returns a dictionary with:
    - missing_release_metadata_ratio: float (0.0 to 1.0)
    - total_dependencies: int
    - missing_count: int
    """
    if not dependencies:
        return {
            'missing_release_metadata_ratio': 0.0,
            'total_dependencies': 0,
            'missing_count': 0
        }
    
    missing_count = 0
    total_count = len(dependencies)
    
    for dep in dependencies:
        # Check if the dependency is a dict
        if not isinstance(dep, dict):
            continue
        
        # Check for missing release date
        release_date = dep.get('last_release_date')
        
        if release_date is None or release_date == '' or release_date == 'null':
            missing_count += 1
    
    ratio = missing_count / total_count if total_count > 0 else 0.0
    
    return {
        'missing_release_metadata_ratio': ratio,
        'total_dependencies': total_count,
        'missing_count': missing_count
    }

def write_metrics_to_file(metrics: Dict[str, Any], output_path: str) -> None:
    """
    Write the calculated metrics to a JSON file.
    
    Ensures the output directory exists before writing.
    """
    path = Path(output_path)
    output_dir = path.parent
    
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"Metrics written to {output_path}")

def main():
    """
    CLI entry point for calculating missing release metadata metrics.
    
    Usage:
    python -m src.cli.calculate_metrics --input data/processed/dependencies_raw.csv --output data/processed/metrics.json
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Calculate missing release metadata metrics')
    parser.add_argument('--input', type=str, required=True, help='Path to input dependencies file (JSON or CSV)')
    parser.add_argument('--output', type=str, required=True, help='Path to output metrics JSON file')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
    
    try:
        # Load data
        print(f"Loading dependencies from {input_path}...")
        dependencies = load_dependencies_from_json(str(input_path))
        print(f"Loaded {len(dependencies)} dependencies.")
        
        # Calculate metrics
        print("Calculating missing release metadata proportion...")
        metrics = calculate_missing_release_proportion(dependencies)
        
        # Write output
        print(f"Writing metrics to {output_path}...")
        write_metrics_to_file(metrics, str(output_path))
        
        # Print summary
        print("\n--- Summary ---")
        print(f"Total Dependencies: {metrics['total_dependencies']}")
        print(f"Missing Release Metadata: {metrics['missing_count']}")
        print(f"Ratio: {metrics['missing_release_metadata_ratio']:.4f}")
        
    except Exception as e:
        print(f"Error processing data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
