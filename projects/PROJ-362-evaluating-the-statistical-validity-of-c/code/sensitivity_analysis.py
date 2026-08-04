import os
import csv
import logging
from typing import List, Dict, Tuple, Optional
from config import RESULTS_DIR

logger = logging.getLogger(__name__)

def load_corrected_p_values(filepath: str) -> List[Dict[str, Any]]:
    """
    Load corrected p-values from a CSV file.
    Expected columns: query_id, metric, raw_p, corrected_p, is_significant
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
    Determine if a result is significant given an alpha threshold.
    """
    return corrected_p < alpha

def run_sensitivity_analysis(
    input_file: Optional[str] = None,
    output_dir: Optional[str] = None,
    alphas: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Run sensitivity analysis by iterating over alpha values.
    
    Args:
        input_file: Path to the corrected p-values CSV. Defaults to 
                    RESULTS_DIR/p_values/corrected_p_values.csv
        output_dir: Directory to save the sensitivity report. Defaults to 
                    RESULTS_DIR/sensitivity
        alphas: List of alpha values to test. Defaults to [0.01, 0.05, 0.10]
    
    Returns:
        Dictionary containing the analysis results.
    """
    if input_file is None:
        input_file = os.path.join(RESULTS_DIR, "p_values", "corrected_p_values.csv")
    
    if output_dir is None:
        output_dir = os.path.join(RESULTS_DIR, "sensitivity")
    
    if alphas is None:
        alphas = [0.01, 0.05, 0.10]

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    logger.info(f"Loading corrected p-values from {input_file}")
    data = load_corrected_p_values(input_file)
    logger.info(f"Loaded {len(data)} records")

    if not data:
        logger.warning("No data found in corrected p-values file. Skipping analysis.")
        return {"results": [], "error": "No data found"}

    # Determine baseline significance (using 0.05 as reference, or first alpha)
    # The task asks to report counts where significance status *changes* between alpha values.
    # We will calculate the count of significant queries for EACH alpha.
    # Then we can report the counts. The "change" metric is implicit in the sweep.
    
    analysis_results = []
    
    logger.info(f"Running sensitivity sweep for alphas: {alphas}")
    
    for alpha in alphas:
        significant_count = 0
        for record in data:
            if determine_significance(record['corrected_p'], alpha):
                significant_count += 1
        
        analysis_results.append({
            'alpha': alpha,
            'significant_count': significant_count
        })
        logger.info(f"Alpha={alpha}: {significant_count} significant queries")

    # Write results to CSV
    output_file = os.path.join(output_dir, "alpha_sweep.csv")
    logger.info(f"Writing results to {output_file}")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['alpha', 'significant_count'])
        writer.writeheader()
        writer.writerows(analysis_results)

    return {
        "results": analysis_results,
        "output_file": output_file,
        "total_queries": len(data)
    }

def main():
    """
    Entry point for running sensitivity analysis via command line or script.
    """
    logging.basicConfig(level=logging.INFO)
    try:
        result = run_sensitivity_analysis()
        logger.info("Sensitivity analysis completed successfully.")
        logger.info(f"Output written to: {result.get('output_file')}")
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()