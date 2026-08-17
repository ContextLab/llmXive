import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from config.env_config import get_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_p_values_from_json(filepath: Path) -> List[Dict[str, Any]]:
    """
    Load p-values and effect sizes from the effect sizes JSON file.
    
    Args:
        filepath: Path to the JSON file containing effect size results.
        
    Returns:
        List of dictionaries containing metric name, raw p-value, and Cohen's d.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Effect sizes file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    results = []
    for item in data:
        results.append({
            'metric': item.get('metric'),
            'p_value': item.get('p_value'),
            'cohens_d': item.get('cohens_d'),
            'ci_lower': item.get('ci_lower'),
            'ci_upper': item.get('ci_upper'),
            'direction': item.get('direction')
        })
    
    return results

def aggregate_results(effect_size_results: List[Dict[str, Any]], 
                    holm_results: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Aggregate effect sizes and corrected p-values into a statistical summary.
    
    Args:
        effect_size_results: List of dictionaries with metric, p-value, and effect size.
        holm_results: Optional list of dictionaries with Holm-Bonferroni corrected p-values.
        
    Returns:
        Dictionary containing the aggregated statistical summary.
    """
    summary = {
        'generated_at': None,  # Will be set in main
        'metrics': []
    }
    
    # Create a mapping of metric names to Holm-corrected p-values if available
    holm_mapping = {}
    if holm_results:
        for item in holm_results:
            metric = item.get('metric')
            corrected_p = item.get('corrected_p_value')
            is_significant = item.get('is_significant')
            holm_mapping[metric] = {
                'corrected_p': corrected_p,
                'is_significant': is_significant
            }
    
    # Process each effect size result
    for item in effect_size_results:
        metric_name = item.get('metric')
        raw_p = item.get('p_value')
        cohens_d = item.get('cohens_d')
        ci_lower = item.get('ci_lower')
        ci_upper = item.get('ci_upper')
        direction = item.get('direction')
        
        # Get Holm-corrected p-value if available
        corrected_p = None
        is_significant = None
        if holm_mapping and metric_name in holm_mapping:
            corrected_p = holm_mapping[metric_name]['corrected_p']
            is_significant = holm_mapping[metric_name]['is_significant']
        
        metric_summary = {
            'metric': metric_name,
            'mean_change': None,  # Will be populated from change scores if needed
            'cohens_d': cohens_d,
            'd_ci': {
                'lower': ci_lower,
                'upper': ci_upper
            },
            'raw_p_value': raw_p,
            'corrected_p_value': corrected_p,
            'is_significant': is_significant,
            'direction': direction,
            'success_criteria': {
                'sc_001': corrected_p is not None and corrected_p < 0.05 if corrected_p is not None else False,
                'sc_002': abs(cohens_d) >= 0.2 if cohens_d is not None else False,
                'sc_003': direction in ['increase', 'decrease'],
                'sc_004': ci_lower is not None and ci_upper is not None,
                'sc_005': corrected_p is not None and corrected_p < 0.05 and abs(cohens_d) >= 0.2
                    if corrected_p is not None and cohens_d is not None else False
            }
        }
        
        summary['metrics'].append(metric_summary)
    
    # Add summary statistics
    significant_count = sum(1 for m in summary['metrics'] if m.get('is_significant'))
    total_count = len(summary['metrics'])
    
    summary['summary_statistics'] = {
        'total_metrics': total_count,
        'significant_metrics': significant_count,
        'significance_rate': significant_count / total_count if total_count > 0 else 0
    }
    
    return summary

def write_summary(summary: Dict[str, Any], output_path: Path) -> None:
    """
    Write the statistical summary to a JSON file.
    
    Args:
        summary: Dictionary containing the statistical summary.
        output_path: Path to write the JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Statistical summary written to {output_path}")

def main():
    """
    Main function to generate the statistical summary.
    
    This function:
    1. Loads effect size results from code/analysis/effect_sizes.json
    2. Loads Holm-Bonferroni corrected p-values from code/analysis/holm_bonferroni_results.json
    3. Aggregates the results into a statistical summary
    4. Writes the summary to results/statistical_summary.json
    """
    try:
        # Get paths from config
        effect_sizes_path = get_path('effect_sizes_json')
        holm_results_path = get_path('holm_results_json')
        output_path = get_path('statistical_summary_json')
        
        logger.info(f"Loading effect sizes from {effect_sizes_path}")
        effect_size_results = load_p_values_from_json(effect_sizes_path)
        
        logger.info(f"Loading Holm-Bonferroni results from {holm_results_path}")
        holm_results = load_p_values_from_json(holm_results_path)
        
        logger.info("Aggregating results")
        summary = aggregate_results(effect_size_results, holm_results)
        
        # Set generation timestamp
        from datetime import datetime
        summary['generated_at'] = datetime.now().isoformat()
        
        logger.info(f"Writing summary to {output_path}")
        write_summary(summary, output_path)
        
        logger.info("Statistical summary generation completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error generating statistical summary: {str(e)}")
        raise

if __name__ == "__main__":
    main()