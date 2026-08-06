import os
import csv
import logging
from typing import List, Dict, Tuple, Optional
from config import RESULTS_DIR

logger = logging.getLogger(__name__)

def load_corrected_p_values(filepath: str) -> List[Dict[str, Any]]:
    """
    Load corrected p-values from a CSV file.
    
    Args:
        filepath: Path to the corrected p-values CSV file.
        
    Returns:
        List of dictionaries containing query_id, metric, raw_p, corrected_p, is_significant.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Corrected p-values file not found: {filepath}")
    
    results = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                'query_id': int(row['query_id']),
                'metric': row['metric'],
                'raw_p': float(row['raw_p']),
                'corrected_p': float(row['corrected_p']),
                'is_significant': row['is_significant'].lower() == 'true'
            })
    return results

def determine_significance(corrected_p: float, alpha: float) -> bool:
    """
    Determine if a result is significant at the given alpha level.
    
    Args:
        corrected_p: The corrected p-value.
        alpha: The significance threshold.
        
    Returns:
        True if the result is significant, False otherwise.
    """
    return corrected_p <= alpha

def run_sensitivity_analysis(alpha_values: Optional[List[float]] = None,
                             input_file: Optional[str] = None,
                             output_file: Optional[str] = None) -> Dict[str, int]:
    """
    Run sensitivity analysis by iterating over alpha values and counting significant queries.
    
    This function reads corrected p-values, determines significance at each alpha level,
    and counts how many query-metric pairs are significant at each threshold.
    
    Args:
        alpha_values: List of alpha values to test. Defaults to [0.01, 0.05, 0.10].
        input_file: Path to corrected p-values CSV. Defaults to results/p_values/corrected_p_values.csv.
        output_file: Path to output sensitivity analysis CSV. Defaults to results/sensitivity/alpha_sweep.csv.
        
    Returns:
        Dictionary mapping alpha values to significant counts.
    """
    if alpha_values is None:
        alpha_values = [0.01, 0.05, 0.10]
    
    if input_file is None:
        input_file = os.path.join(RESULTS_DIR, 'p_values', 'corrected_p_values.csv')
    
    if output_file is None:
        output_dir = os.path.join(RESULTS_DIR, 'sensitivity')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'alpha_sweep.csv')
    
    # Load corrected p-values
    logger.info(f"Loading corrected p-values from {input_file}")
    try:
        p_values_data = load_corrected_p_values(input_file)
    except FileNotFoundError as e:
        logger.error(f"Failed to load corrected p-values: {e}")
        raise
    
    if not p_values_data:
        logger.warning("No corrected p-values found in the input file.")
        # Write empty result with headers
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['alpha', 'significant_count'])
        return {alpha: 0 for alpha in alpha_values}
    
    logger.info(f"Loaded {len(p_values_data)} corrected p-value records.")
    
    # Perform sensitivity analysis
    results = {}
    for alpha in alpha_values:
        significant_count = sum(
            1 for record in p_values_data 
            if determine_significance(record['corrected_p'], alpha)
        )
        results[alpha] = significant_count
        logger.info(f"Alpha={alpha}: {significant_count} significant queries/metrics")
    
    # Write results to CSV
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['alpha', 'significant_count'])
        for alpha in alpha_values:
            writer.writerow([alpha, results[alpha]])
    
    logger.info(f"Sensitivity analysis results written to {output_file}")
    return results

def main():
    """Main entry point for sensitivity analysis."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        results = run_sensitivity_analysis()
        logger.info("Sensitivity analysis completed successfully.")
        return results
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
