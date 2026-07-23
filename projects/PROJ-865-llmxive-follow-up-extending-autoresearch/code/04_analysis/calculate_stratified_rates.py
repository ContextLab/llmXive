import json
import csv
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import defaultdict

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def load_results_csv(filepath: Path) -> List[Dict[str, Any]]:
    """Load the merged results CSV file."""
    if not filepath.exists():
        raise FileNotFoundError(f"Results file not found: {filepath}")
    
    results = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Ensure types are correct
            row['time_to_pivot'] = float(row['time_to_pivot'])
            row['success'] = row['success'].lower() == 'true'
            results.append(row)
    return results

def calculate_stratified_rates(results: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Calculate success rates and time-to-pivot metrics stratified by failure type.
    
    Returns a dictionary keyed by failure_type containing:
      - count: total number of cases
      - success_count: number of successful pivots
      - success_rate: float (0.0 to 1.0)
      - avg_time_to_pivot: float
    """
    stratified_data = defaultdict(lambda: {
        'count': 0,
        'success_count': 0,
        'total_time': 0.0
    })

    for row in results:
        failure_type = row.get('failure_type', 'Unknown')
        stratified_data[failure_type]['count'] += 1
        
        if row['success']:
            stratified_data[failure_type]['success_count'] += 1
        
        stratified_data[failure_type]['total_time'] += row['time_to_pivot']

    output = {}
    for failure_type, data in stratified_data.items():
        count = data['count']
        output[failure_type] = {
            'count': count,
            'success_count': data['success_count'],
            'success_rate': data['success_count'] / count if count > 0 else 0.0,
            'avg_time_to_pivot': data['total_time'] / count if count > 0 else 0.0
        }
    
    return output

def write_stratified_rates_csv(data: Dict[str, Dict[str, Any]], output_path: Path) -> None:
    """
    Write the stratified rates to a CSV file.
    Columns: failure_type, count, success_count, success_rate, avg_time_to_pivot
    """
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ['failure_type', 'count', 'success_count', 'success_rate', 'avg_time_to_pivot']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        # Sort by failure type for consistent output
        for failure_type in sorted(data.keys()):
            row = data[failure_type]
            writer.writerow({
                'failure_type': failure_type,
                'count': row['count'],
                'success_count': row['success_count'],
                'success_rate': f"{row['success_rate']:.4f}",
                'avg_time_to_pivot': f"{row['avg_time_to_pivot']:.4f}"
            })

def save_stratified_rates_json(data: Dict[str, Dict[str, Any]], output_path: Path) -> None:
    """Save the full metrics dictionary to a JSON file for programmatic access."""
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def main():
    """
    Main entry point to calculate stratified success rates.
    Reads from data/derived/results.csv and writes to:
      - data/derived/stratified_success_rates.csv
      - data/derived/stratified_success_rates.json
    """
    project_root = Path(__file__).parent.parent.parent
    results_path = project_root / 'data' / 'derived' / 'results.csv'
    csv_output_path = project_root / 'data' / 'derived' / 'stratified_success_rates.csv'
    json_output_path = project_root / 'data' / 'derived' / 'stratified_success_rates.json'

    print(f"Loading results from {results_path}...")
    try:
        results = load_results_csv(results_path)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    if not results:
        print("WARNING: Results file is empty. No data to process.")
        # Still create empty output files to satisfy pipeline expectations
        write_stratified_rates_csv({}, csv_output_path)
        save_stratified_rates_json({}, json_output_path)
        return

    print(f"Processing {len(results)} records...")
    stratified_metrics = calculate_stratified_rates(results)

    print(f"Writing CSV output to {csv_output_path}...")
    write_stratified_rates_csv(stratified_metrics, csv_output_path)

    print(f"Writing JSON output to {json_output_path}...")
    save_stratified_rates_json(stratified_metrics, json_output_path)

    print("Stratification complete.")
    print("Summary:")
    for ft, metrics in sorted(stratified_metrics.items()):
        print(f"  {ft}: {metrics['count']} cases, {metrics['success_rate']:.2%} success rate")

if __name__ == "__main__":
    main()