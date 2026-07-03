"""
Task T034: Implement Pearson correlation significance testing with Bonferroni correction.

Reads the raw Pearson correlation results from T033a (correlation_pearson.json),
applies Bonferroni correction to the p-values based on the number of tests (features),
and outputs the corrected results to correlation_pearson_corrected.json.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import get_config, get_paths

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_pearson_results(input_path: Path) -> List[Dict[str, Any]]:
    """Load the raw Pearson correlation results from T033a."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    # The structure from T033a is expected to be a list of results per feature
    # or a dict containing a 'results' key. We handle both.
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'results' in data:
        return data['results']
    else:
        # Fallback: treat the whole dict as a single result if it looks like one
        return [data]

def apply_bonferroni_correction(results: List[Dict[str, Any]], num_tests: int) -> List[Dict[str, Any]]:
    """
    Apply Bonferroni correction to p-values.
    
    Corrected p-value = min(raw_p * num_tests, 1.0)
    Significance threshold is adjusted: alpha_corrected = alpha / num_tests
    """
    corrected_results = []
    
    # Default alpha for significance
    alpha = 0.05
    alpha_corrected = alpha / num_tests if num_tests > 0 else alpha
    
    logger.info(f"Applying Bonferroni correction: {num_tests} tests, alpha_corrected = {alpha_corrected:.6f}")
    
    for result in results:
        raw_p = result.get('p_value', 1.0)
        r_value = result.get('r', 0.0)
        feature_name = result.get('feature', 'unknown')
        
        # Bonferroni correction
        corrected_p = min(raw_p * num_tests, 1.0)
        
        # Determine significance
        is_significant = corrected_p < alpha_corrected
        
        # Interpretation
        if is_significant:
            if abs(r_value) > 0.7:
                interpretation = "Strong significant correlation"
            elif abs(r_value) > 0.4:
                interpretation = "Moderate significant correlation"
            else:
                interpretation = "Weak significant correlation"
        else:
            interpretation = "Not significant after correction"
        
        corrected_entry = {
            "feature": feature_name,
            "r": r_value,
            "p_value_raw": raw_p,
            "p_value_corrected": corrected_p,
            "alpha_corrected": alpha_corrected,
            "is_significant": is_significant,
            "interpretation": interpretation
        }
        
        corrected_results.append(corrected_entry)
        
    return corrected_results

def generate_summary(corrected_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate a summary of the corrected analysis."""
    significant_count = sum(1 for r in corrected_results if r['is_significant'])
    total_count = len(corrected_results)
    
    summary = {
        "total_tests": total_count,
        "significant_after_correction": significant_count,
        "alpha_corrected": corrected_results[0]['alpha_corrected'] if corrected_results else 0.0,
        "method": "Bonferroni",
        "results": corrected_results
    }
    
    return summary

def save_corrected_results(output_path: Path, summary: Dict[str, Any]) -> None:
    """Save the corrected results to the output file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Saved corrected results to {output_path}")

def main() -> int:
    """Main entry point for T034."""
    try:
        config = get_config()
        paths = get_paths()
        
        # Input path from T033a
        input_file = paths['data_processed_model_outputs'] / "correlation_pearson.json"
        output_file = paths['data_processed_model_outputs'] / "correlation_pearson_corrected.json"
        
        logger.info(f"Loading Pearson results from {input_file}")
        raw_results = load_pearson_results(input_file)
        
        if not raw_results:
            logger.warning("No results found in input file. Creating empty output.")
            summary = {"total_tests": 0, "significant_after_correction": 0, "results": []}
            save_corrected_results(output_file, summary)
            return 0
        
        # Determine number of tests (features)
        num_tests = len(raw_results)
        
        logger.info(f"Applying Bonferroni correction to {num_tests} tests")
        corrected_results = apply_bonferroni_correction(raw_results, num_tests)
        
        summary = generate_summary(corrected_results)
        
        save_corrected_results(output_file, summary)
        
        # Log key findings
        logger.info(f"Significant features after correction: {summary['significant_after_correction']}/{summary['total_tests']}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error in correlation significance testing: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())