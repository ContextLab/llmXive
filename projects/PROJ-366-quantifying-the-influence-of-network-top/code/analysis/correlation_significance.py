"""
Pearson correlation significance testing with Bonferroni correction.

Implements FR-006 and SC-001:
- Load Pearson correlation results from T033a
- Apply Bonferroni correction for multiple hypothesis testing
- Output corrected p-values and interpretations
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_pearson_results(input_path: str) -> Dict[str, Any]:
    """
    Load Pearson correlation results from T033a.
    
    Args:
        input_path: Path to correlation_pearson.json
        
    Returns:
        Dictionary containing correlation results
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Pearson results file not found: {input_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    logger.info(f"Loaded Pearson results from {input_path}")
    return data

def apply_bonferroni_correction(results: Dict[str, Any], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Bonferroni correction to p-values for multiple hypothesis testing.
    
    The Bonferroni correction adjusts the significance threshold by dividing
    alpha by the number of tests (m), or equivalently multiplies each p-value
    by m (capped at 1.0).
    
    Args:
        results: Dictionary containing correlation results with 'correlations' list
        alpha: Significance level (default 0.05)
        
    Returns:
        Dictionary with corrected p-values and significance flags
    """
    correlations = results.get('correlations', [])
    m = len(correlations)
    
    if m == 0:
        logger.warning("No correlations found to correct")
        return {
            'corrections': [],
            'alpha': alpha,
            'num_tests': 0,
            'method': 'bonferroni',
            'interpretation': 'No tests performed'
        }
    
    corrected_correlations = []
    adjusted_alpha = alpha / m
    
    for corr in correlations:
        feature_name = corr.get('feature', 'unknown')
        r_value = corr.get('r', 0.0)
        p_value = corr.get('p_value', 1.0)
        
        # Bonferroni correction: multiply p-value by number of tests
        corrected_p = min(p_value * m, 1.0)
        is_significant = corrected_p < alpha
        
        # Determine interpretation
        if is_significant:
            interpretation = f"Significant correlation (p < {alpha}) after Bonferroni correction"
        else:
            interpretation = f"Not significant (p >= {alpha}) after Bonferroni correction"
        
        corrected_correlations.append({
            'feature': feature_name,
            'r': r_value,
            'p_value': p_value,
            'corrected_p_value': corrected_p,
            'alpha': alpha,
            'adjusted_alpha': adjusted_alpha,
            'is_significant': is_significant,
            'interpretation': interpretation
        })
    
    summary = {
        'corrections': corrected_correlations,
        'alpha': alpha,
        'num_tests': m,
        'method': 'bonferroni',
        'interpretation': (
            f"Applied Bonferroni correction for {m} tests. "
            f"Significance threshold adjusted from {alpha} to {adjusted_alpha:.6f}. "
            f"Significant features: {sum(1 for c in corrected_correlations if c['is_significant'])}/{m}"
        )
    }
    
    logger.info(f"Bonferroni correction applied to {m} correlations")
    logger.info(f"Significant features: {summary['interpretation']}")
    
    return summary

def generate_summary(corrected_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a human-readable summary of the corrected results.
    
    Args:
        corrected_results: Dictionary containing corrected correlation data
        
    Returns:
        Dictionary with summary statistics and interpretation
    """
    corrections = corrected_results.get('corrections', [])
    num_tests = corrected_results.get('num_tests', 0)
    alpha = corrected_results.get('alpha', 0.05)
    
    if num_tests == 0:
        return {
            'summary': 'No correlations to analyze',
            'significant_count': 0,
            'total_count': 0,
            'recommendation': 'No analysis performed'
        }
    
    significant_features = [c for c in corrections if c['is_significant']]
    non_significant = [c for c in corrections if not c['is_significant']]
    
    # Build detailed interpretation
    interpretation_parts = []
    
    if significant_features:
        sig_names = [f['feature'] for f in significant_features]
        interpretation_parts.append(
            f"Found {len(sig_names)} feature(s) with significant correlation: {', '.join(sig_names)}"
        )
    
    if non_significant:
        interpretation_parts.append(
            f"Found {len(non_significant)} feature(s) without significant correlation after correction"
        )
    
    # Overall conclusion
    if len(significant_features) == num_tests:
        conclusion = "All tested features show significant correlation with thermal conductivity."
    elif len(significant_features) == 0:
        conclusion = "No features show significant correlation after Bonferroni correction."
    else:
        conclusion = f"Mixed results: some features significant, others not."
    
    return {
        'summary': ' '.join(interpretation_parts),
        'significant_count': len(significant_features),
        'non_significant_count': len(non_significant),
        'total_count': num_tests,
        'significance_threshold': alpha,
        'adjusted_threshold': alpha / num_tests if num_tests > 0 else alpha,
        'recommendation': (
            "Features with significant corrected p-values are candidates for further investigation "
            "as topological drivers of thermal conductivity."
        ),
        'conclusion': conclusion
    }

def save_corrected_results(
    corrected_data: Dict[str, Any], 
    summary: Dict[str, Any],
    output_path: str
) -> None:
    """
    Save corrected results and summary to JSON file.
    
    Args:
        corrected_data: Dictionary with corrected p-values
        summary: Dictionary with summary statistics
        output_path: Path to output JSON file
    """
    output = {
        'corrections': corrected_data['corrections'],
        'alpha': corrected_data['alpha'],
        'num_tests': corrected_data['num_tests'],
        'method': corrected_data['method'],
        'interpretation': corrected_data['interpretation'],
        'summary': summary,
        'metadata': {
            'analysis_task': 'T034',
            'description': 'Pearson correlation significance testing with Bonferroni correction',
            'references': ['FR-006', 'SC-001']
        }
    }
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(output, f, indent=2)
    
    logger.info(f"Saved corrected results to {output_path}")

def main():
    """Main entry point for the significance testing pipeline."""
    logger.info("Starting Pearson correlation significance testing with Bonferroni correction")
    
    # Define paths
    config_path = Path(__file__).parent.parent / 'config.py'
    if config_path.exists():
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from config import get_config, get_paths
        config = get_config()
        paths = get_paths()
        
        input_path = paths.get('pearson_correlation', 'data/processed/model_outputs/correlation_pearson.json')
        output_path = paths.get('pearson_corrected', 'data/processed/model_outputs/correlation_pearson_corrected.json')
        alpha = config.get('analysis', {}).get('significance_level', 0.05)
    else:
        # Fallback to defaults if config not available
        input_path = 'data/processed/model_outputs/correlation_pearson.json'
        output_path = 'data/processed/model_outputs/correlation_pearson_corrected.json'
        alpha = 0.05
    
    try:
        # Step 1: Load Pearson results
        logger.info(f"Loading Pearson results from {input_path}")
        results = load_pearson_results(input_path)
        
        # Step 2: Apply Bonferroni correction
        logger.info(f"Applying Bonferroni correction with alpha={alpha}")
        corrected_data = apply_bonferroni_correction(results, alpha)
        
        # Step 3: Generate summary
        logger.info("Generating summary of corrected results")
        summary = generate_summary(corrected_data)
        
        # Step 4: Save results
        logger.info(f"Saving corrected results to {output_path}")
        save_corrected_results(corrected_data, summary, output_path)
        
        # Print summary to console
        print("\n" + "="*60)
        print("PEARSON CORRELATION SIGNIFICANCE TESTING RESULTS")
        print("="*60)
        print(f"Total tests: {corrected_data['num_tests']}")
        print(f"Significance level: {alpha}")
        print(f"Adjusted threshold: {corrected_data['adjusted_alpha']:.6f}")
        print(f"\nSignificant features: {summary['significant_count']}")
        print(f"Non-significant features: {summary['non_significant_count']}")
        print(f"\nConclusion: {summary['conclusion']}")
        print("="*60 + "\n")
        
        logger.info("Significance testing completed successfully")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        print(f"ERROR: {e}")
        print("Ensure T033a has been run and correlation_pearson.json exists.")
        return 1
    except Exception as e:
        logger.error(f"Error during significance testing: {e}", exc_info=True)
        print(f"ERROR: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())