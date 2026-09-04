import json
import os
import sys
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import the analysis module to access processed data
# We assume the analysis module has already run and produced data in data/processed/
# or data/results/ that we need to aggregate.

# Since T029 (tradeoff_model.py) is implemented, we should leverage it if possible.
# However, T032 specifically asks for a script to generate the CSV.
# We will load the processed execution logs and compute the necessary regression points.

def load_processed_logs(processed_dir: Path) -> List[Dict[str, Any]]:
    """Load all processed execution logs from the directory."""
    logs = []
    if not processed_dir.exists():
        raise FileNotFoundError(f"Processed directory not found: {processed_dir}")
    
    for file_path in processed_dir.glob("*.json"):
        with open(file_path, 'r') as f:
            try:
                data = json.load(f)
                logs.append(data)
            except json.JSONDecodeError:
                print(f"Warning: Could not decode {file_path}, skipping.")
    return logs

def save_regression_data_to_csv(logs: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Generate the tradeoff curve CSV.
    
    The CSV should contain aggregated data points suitable for regression analysis.
    We group by compression level (or token reduction %) and calculate:
    - Mean error rate
    - Mean token reduction
    - Count of samples
    
    This matches the requirement for 'raw regression data for the paper'.
    """
    if not logs:
        raise ValueError("No processed logs found to generate regression data.")

    # Prepare data structure for aggregation
    # Key: compression_level (or a binned token_reduction_pct)
    # We'll use the 'compression_level' or 'depth' if available, otherwise bin by token reduction.
    
    aggregated_data = {}

    for log in logs:
        # Extract relevant fields based on expected schema from T005/T006
        # Expected fields: compression_level, token_reduction_pct, has_violation (bool), is_valid (bool)
        
        # Skip invalid workflows
        if log.get('is_valid') is False:
            continue

        # Determine the grouping key
        # Prefer explicit compression_level if available, otherwise use token_reduction_pct binned
        comp_level = log.get('compression_level')
        token_red_pct = log.get('token_reduction_pct', 0.0)
        
        if comp_level is not None:
            key = str(comp_level)
        else:
            # Bin into 5% increments if level is missing
            bin_size = 5.0
            key = f"{int(token_red_pct // bin_size) * bin_size}-{int((token_red_pct // bin_size) + 1) * bin_size}"

        is_violation = log.get('has_violation', False)
        
        if key not in aggregated_data:
            aggregated_data[key] = {
                'count': 0,
                'violations': 0,
                'total_token_reduction': 0.0,
                'token_red_samples': 0
            }

        aggregated_data[key]['count'] += 1
        if is_violation:
            aggregated_data[key]['violations'] += 1
        
        # Accumulate token reduction for averaging
        aggregated_data[key]['total_token_reduction'] += token_red_pct
        aggregated_data[key]['token_red_samples'] += 1

    # Sort keys for consistent output
    sorted_keys = sorted(aggregated_data.keys(), key=lambda x: float(x.split('-')[0]) if '-' in x else int(x))

    # Write to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as csvfile:
        fieldnames = ['compression_level', 'token_reduction_pct_mean', 'error_rate', 'sample_count', 'violation_count']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        
        for key in sorted_keys:
            data = aggregated_data[key]
            if data['count'] == 0:
                continue
            
            mean_token_red = data['total_token_reduction'] / data['token_red_samples']
            error_rate = data['violations'] / data['count']
            
            row = {
                'compression_level': key,
                'token_reduction_pct_mean': round(mean_token_red, 4),
                'error_rate': round(error_rate, 4),
                'sample_count': data['count'],
                'violation_count': data['violations']
            }
            writer.writerow(row)

def main():
    """
    Main entry point for T032.
    Loads processed logs and generates data/results/tradeoff_curve.csv
    """
    # Determine paths relative to project root
    # Assuming this script is run from project root or code/
    project_root = Path(__file__).parent.parent.parent
    processed_dir = project_root / "data" / "processed"
    output_file = project_root / "data" / "results" / "tradeoff_curve.csv"

    print(f"Loading processed logs from: {processed_dir}")
    try:
        logs = load_processed_logs(processed_dir)
        print(f"Loaded {len(logs)} valid logs.")
        
        print(f"Generating regression data to: {output_file}")
        save_regression_data_to_csv(logs, output_file)
        print("Success: tradeoff_curve.csv generated.")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Ensure that T025 (save processed execution logs) has been completed successfully.")
        sys.exit(1)
    except Exception as e:
        print(f"Error generating regression data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
