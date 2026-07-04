import argparse
import csv
import json
import sys
import statistics
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Import from existing project utilities
from utils.metrics import compute_cohen_d

def load_style_scores(filepath: str) -> List[Dict[str, Any]]:
    """Load style scores from a CSV file."""
    data = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric strings to floats
            row['composite_score'] = float(row['composite_score'])
            data.append(row)
    return data

def assign_group(score: float, low_thresh: float, high_thresh: float) -> str:
    """Assign group based on thresholds."""
    if score < low_thresh:
        return 'Low'
    elif score > high_thresh:
        return 'High'
    else:
        return 'Medium'

def stratify_data(data: List[Dict[str, Any]], low_thresh: float, high_thresh: float) -> Dict[str, List[Dict[str, Any]]]:
    """Stratify data into groups based on thresholds."""
    groups = {'Low': [], 'Medium': [], 'High': []}
    for row in data:
        group = assign_group(row['composite_score'], low_thresh, high_thresh)
        groups[group].append(row)
    return groups

def calculate_group_stability(groups: Dict[str, List[Dict[str, Any]]]) -> Dict[str, float]:
    """Calculate stability metrics for a given stratification.
    
    Returns a dict with:
    - 'variance_of_means': Variance of the mean composite scores across groups
    - 'cohen_d_high_low': Cohen's d between High and Low groups
    - 'group_counts': Number of items in each group
    """
    means = {}
    group_sizes = {}
    
    for group_name, items in groups.items():
        if not items:
            means[group_name] = 0.0
            group_sizes[group_name] = 0
        else:
            scores = [item['composite_score'] for item in items]
            means[group_name] = statistics.mean(scores)
            group_sizes[group_name] = len(items)

    # Variance of group means
    if len(means) < 2:
        variance_of_means = 0.0
    else:
        mean_values = list(means.values())
        variance_of_means = statistics.variance(mean_values) if len(mean_values) > 1 else 0.0

    # Cohen's d between High and Low
    high_scores = [item['composite_score'] for item in groups['High']]
    low_scores = [item['composite_score'] for item in groups['Low']]
    
    cohen_d = 0.0
    if high_scores and low_scores:
        try:
            cohen_d = compute_cohen_d(high_scores, low_scores)
        except Exception:
            cohen_d = 0.0

    return {
        'variance_of_means': variance_of_means,
        'cohen_d_high_low': cohen_d,
        'group_counts': group_sizes
    }

def run_sensitivity_analysis(input_file: str, threshold_sets: List[Tuple[float, float]]) -> Dict[str, Any]:
    """Run sensitivity analysis with multiple threshold sets."""
    if not Path(input_file).exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    data = load_style_scores(input_file)
    
    if not data:
        raise ValueError("Input file contains no data.")

    results = []
    
    for low, high in threshold_sets:
        groups = stratify_data(data, low, high)
        stability = calculate_group_stability(groups)
        
        result_entry = {
            'low_threshold': low,
            'high_threshold': high,
            'variance_of_means': stability['variance_of_means'],
            'cohen_d_high_low': stability['cohen_d_high_low'],
            'group_counts': stability['group_counts']
        }
        results.append(result_entry)

    # Identify optimal threshold set
    # Criterion: Maximize variance of means (good separation) AND maximize Cohen's d
    # We'll use a simple score: variance * abs(cohen_d)
    best_result = None
    best_score = -1.0
    
    for res in results:
        score = res['variance_of_means'] * abs(res['cohen_d_high_low'])
        if score > best_score:
            best_score = score
            best_result = res

    optimal_set = {
        'low_threshold': best_result['low_threshold'],
        'high_threshold': best_result['high_threshold'],
        'score': best_score
    }

    return {
        'threshold_sets_analyzed': len(threshold_sets),
        'total_samples': len(data),
        'results': results,
        'optimal_threshold_set': optimal_set
    }

def main():
    parser = argparse.ArgumentParser(
        description='Run sensitivity analysis on style score thresholds.'
    )
    parser.add_argument(
        '--input', 
        type=str, 
        default='data/metadata/style_scores_raw.csv',
        help='Path to input style scores CSV (default: data/metadata/style_scores_raw.csv)'
    )
    parser.add_argument(
        '--output', 
        type=str, 
        default='data/processed/sensitivity_report.json',
        help='Path to output JSON report (default: data/processed/sensitivity_report.json)'
    )
    
    args = parser.parse_args()

    # Define threshold sets as per task description
    threshold_sets = [
        (0.15, 0.85),
        (0.25, 0.75),
        (0.30, 0.70)
    ]

    try:
        report = run_sensitivity_analysis(args.input, threshold_sets)
        
        # Ensure output directory exists
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        print(f"Sensitivity analysis complete. Report saved to {args.output}")
        print(f"Optimal thresholds: Low={report['optimal_threshold_set']['low_threshold']}, High={report['optimal_threshold_set']['high_threshold']}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()