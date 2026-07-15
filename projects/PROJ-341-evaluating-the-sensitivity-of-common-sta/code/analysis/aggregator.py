import os
import csv
import json
from typing import List, Dict, Any, Optional
from code.simulation.output_writer import load_p_values_raw

def calculate_error_rates(p_values: List[Dict[str, Any]], alpha: float = 0.05) -> List[Dict[str, Any]]:
    """
    Calculate empirical Type I and Type II error rates from raw p-values.
    
    Type I Error: Rejecting null when it is true (p < alpha when hypothesis='null')
    Type II Error: Failing to reject null when it is false (p > alpha when hypothesis='alternative')
    
    Args:
        p_values: List of dicts with keys: sample_size, effect_size, test_type, p_value, hypothesis
        alpha: Significance threshold (default 0.05)
    
    Returns:
        List of aggregated error rate records per condition.
    """
    if not p_values:
        return []
    
    # Group by condition
    conditions = {}
    for row in p_values:
        key = (row['sample_size'], row['effect_size'], row['test_type'])
        if key not in conditions:
            conditions[key] = {'null': [], 'alternative': []}
        
        hypothesis_type = row.get('hypothesis', 'null').lower()
        if hypothesis_type == 'null':
            conditions[key]['null'].append(float(row['p_value']))
        else:
            conditions[key]['alternative'].append(float(row['p_value']))
    
    results = []
    for (n, effect, test_type), data in conditions.items():
        null_pvals = data['null']
        alt_pvals = data['alternative']
        
        # Calculate Type I error rate (proportion of null p-values < alpha)
        type_1_errors = sum(1 for p in null_pvals if p < alpha)
        type_1_rate = type_1_errors / len(null_pvals) if null_pvals else 0.0
        
        # Calculate Type II error rate (proportion of alt p-values > alpha)
        # Note: Power = 1 - Type II error rate
        type_2_errors = sum(1 for p in alt_pvals if p >= alpha)
        type_2_rate = type_2_errors / len(alt_pvals) if alt_pvals else 0.0
        
        power = 1.0 - type_2_rate if alt_pvals else 0.0
        
        results.append({
            'sample_size': int(n),
            'effect_size': float(effect),
            'test_type': test_type,
            'type_1_error_rate': type_1_rate,
            'type_2_error_rate': type_2_rate,
            'power': power,
            'n_null_simulations': len(null_pvals),
            'n_alt_simulations': len(alt_pvals)
        })
    
    return results

def save_aggregated_results(error_rates: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save aggregated error rates to a CSV file.
    
    Args:
        error_rates: List of error rate dictionaries from calculate_error_rates
        output_path: Path to save the CSV file
    """
    if not error_rates:
        # Write empty file with headers if no data
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'sample_size', 'effect_size', 'test_type', 
                'type_1_error_rate', 'type_2_error_rate', 'power',
                'n_null_simulations', 'n_alt_simulations'
            ])
            writer.writeheader()
        return
    
    fieldnames = [
        'sample_size', 'effect_size', 'test_type', 
        'type_1_error_rate', 'type_2_error_rate', 'power',
        'n_null_simulations', 'n_alt_simulations'
    ]
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in error_rates:
            writer.writerow(row)

def main(alpha: float = 0.05, input_path: Optional[str] = None, output_path: Optional[str] = None) -> None:
    """
    Main entry point for the aggregation process.
    
    Reads raw p-values, calculates error rates, and saves the summary.
    """
    if input_path is None:
        input_path = 'data/simulation/p_values_raw.csv'
    if output_path is None:
        output_path = 'data/simulation/error_rates_summary.csv'
    
    print(f"Loading raw p-values from {input_path}...")
    p_values = load_p_values_raw(input_path)
    
    if not p_values:
        print("Warning: No p-values found in input file. Creating empty summary.")
        save_aggregated_results([], output_path)
        print(f"Empty summary saved to {output_path}")
        return
    
    print(f"Calculating error rates for {len(p_values)} records (alpha={alpha})...")
    error_rates = calculate_error_rates(p_values, alpha)
    
    print(f"Saving aggregated results to {output_path}...")
    save_aggregated_results(error_rates, output_path)
    
    print(f"Aggregation complete. {len(error_rates)} unique conditions processed.")
    print(f"Output written to: {output_path}")

if __name__ == '__main__':
    main()