import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np

from config import get_config, get_paths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/correlation_significance.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_pearson_results(input_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load Pearson correlation results from the output of T033a.
    
    Args:
        input_path: Path to the correlation_pearson.json file. If None, uses config default.
        
    Returns:
        List of dictionaries containing correlation results.
    """
    if input_path is None:
        paths = get_paths()
        input_path = str(paths["processed_model_outputs"] / "correlation_pearson.json")
    
    path_obj = Path(input_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Pearson results file not found: {input_path}")
    
    logger.info(f"Loading Pearson results from {input_path}")
    with open(path_obj, 'r') as f:
        data = json.load(f)
    
    # Ensure we return a list of results (handle single result or list)
    if isinstance(data, dict):
        return [data]
    return data

def apply_bonferroni_correction(results: List[Dict[str, Any]], alpha: float = 0.05) -> List[Dict[str, Any]]:
    """
    Apply Bonferroni correction to p-values.
    
    The Bonferroni correction adjusts the significance threshold by dividing
    the desired alpha level by the number of tests performed.
    
    Args:
        results: List of correlation result dictionaries with 'p_value' and 'n_features' (or similar).
        alpha: Desired significance level (default 0.05).
        
    Returns:
        List of results with corrected p-values and significance flags.
    """
    logger.info(f"Applying Bonferroni correction with alpha={alpha}")
    
    corrected_results = []
    for result in results:
        p_value = result.get('p_value')
        if p_value is None:
            logger.warning("Skipping result without p_value")
            corrected_results.append(result)
            continue
        
        # Determine number of tests (n_features tested)
        # This assumes the Pearson analysis was done per feature
        n_tests = result.get('n_features', result.get('n_samples', 1))
        
        # Bonferroni correction: adjusted_p = p * n_tests
        adjusted_p = min(p_value * n_tests, 1.0)
        
        # Significance at original alpha level
        is_significant = adjusted_p < alpha
        
        # Interpretation
        interpretation = "Significant" if is_significant else "Not Significant"
        if not is_significant and p_value < alpha:
            interpretation = "Significant before correction, Not Significant after correction"
        
        corrected_entry = {
            **result,
            'adjusted_p_value': adjusted_p,
            'bonferroni_threshold': alpha / n_tests,
            'is_significant_after_correction': is_significant,
            'interpretation': interpretation,
            'correction_method': 'Bonferroni',
            'n_tests': n_tests,
            'alpha': alpha
        }
        corrected_results.append(corrected_entry)
    
    return corrected_results

def generate_summary(corrected_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a summary of the corrected correlation results.
    
    Args:
        corrected_results: List of results after Bonferroni correction.
        
    Returns:
        Summary dictionary with aggregate statistics.
    """
    logger.info("Generating summary of corrected results")
    
    total_tests = len(corrected_results)
    significant_count = sum(1 for r in corrected_results if r.get('is_significant_after_correction', False))
    
    significant_features = [
        r.get('feature_name', f'feature_{i}') 
        for i, r in enumerate(corrected_results) 
        if r.get('is_significant_after_correction', False)
    ]
    
    summary = {
        'total_correlations_tested': total_tests,
        'significant_after_bonferroni': significant_count,
        'non_significant_after_bonferroni': total_tests - significant_count,
        'correction_method': 'Bonferroni',
        'alpha_level': corrected_results[0].get('alpha', 0.05) if corrected_results else 0.05,
        'significant_features': significant_features,
        'summary_interpretation': (
            f"Found {significant_count} out of {total_tests} features with statistically significant "
            f"correlation after Bonferroni correction (alpha={summary['alpha_level']})."
        )
    }
    
    return summary

def save_corrected_results(
    corrected_results: List[Dict[str, Any]], 
    summary: Dict[str, Any],
    output_path: Optional[str] = None
) -> Path:
    """
    Save the corrected correlation results and summary to JSON.
    
    Args:
        corrected_results: List of results with Bonferroni correction applied.
        summary: Summary dictionary.
        output_path: Path for output file. If None, uses config default.
        
    Returns:
        Path to the saved file.
    """
    if output_path is None:
        paths = get_paths()
        output_path = str(paths["processed_model_outputs"] / "correlation_pearson_corrected.json")
    
    path_obj = Path(output_path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        'corrected_results': corrected_results,
        'summary': summary,
        'metadata': {
            'generated_by': 'T034_Bonferroni_Correction',
            'source_file': 'correlation_pearson.json'
        }
    }
    
    logger.info(f"Saving corrected results to {output_path}")
    with open(path_obj, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    return path_obj

def main():
    """
    Main entry point for T034: Pearson correlation significance testing with Bonferroni correction.
    """
    logger.info("Starting T034: Pearson correlation significance testing with Bonferroni correction")
    
    try:
        # Load input
        results = load_pearson_results()
        if not results:
            raise ValueError("No correlation results found to correct")
        
        # Apply Bonferroni correction
        corrected_results = apply_bonferroni_correction(results)
        
        # Generate summary
        summary = generate_summary(corrected_results)
        
        # Save output
        output_path = save_corrected_results(corrected_results, summary)
        
        logger.info(f"T034 completed successfully. Output saved to {output_path}")
        print(f"Bonferroni correction complete. {summary['significant_after_bonferroni']} of {summary['total_correlations_tested']} features are significant.")
        
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during Bonferroni correction: {e}", exc_info=True)
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()