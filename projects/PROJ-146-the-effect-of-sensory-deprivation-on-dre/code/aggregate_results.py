"""
Result aggregation module for Sensory Deprivation Study.

Implements T033: Aggregates model results across thresholds into variation tables
for odds ratios and effect sizes.
"""
import os
import json
import logging
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import from existing API surface
from serialize_results import serialize_model_results, serialize_sensitivity_results

logger = logging.getLogger(__name__)

def load_model_results(result_dir: str, threshold_name: str) -> Optional[Dict[str, Any]]:
    """
    Load serialized model results for a specific threshold.
    
    Args:
        result_dir: Directory containing model results (e.g., results/models/)
        threshold_name: Name of the threshold (strict, moderate, partial)
        
    Returns:
        Dictionary containing model results or None if not found
    """
    file_path = os.path.join(result_dir, f"model_results_{threshold_name}.json")
    
    if not os.path.exists(file_path):
        logger.warning(f"Model results file not found: {file_path}")
        return None
        
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from {file_path}: {e}")
        return None

def extract_odds_ratios(results: Dict[str, Any], model_type: str = "logistic") -> Dict[str, float]:
    """
    Extract odds ratios and confidence intervals from model results.
    
    Args:
        results: Dictionary containing model output
        model_type: Type of model ('logistic' or 'linear')
        
    Returns:
        Dictionary with extracted metrics
    """
    if not results or 'fixed_effects' not in results:
        return {}
        
    fixed_effects = results['fixed_effects']
    metrics = {}
    
    # Extract condition effect (assuming 'condition' is the predictor)
    if 'condition' in fixed_effects:
        coef = fixed_effects['condition'].get('estimate', 0.0)
        se = fixed_effects['condition'].get('std_err', 0.0)
        pval = fixed_effects['condition'].get('pvalue', 1.0)
        
        # For logistic regression, exponentiate coefficient to get odds ratio
        if model_type == "logistic":
            metrics['odds_ratio'] = float(np.exp(coef))
            metrics['ci_lower'] = float(np.exp(coef - 1.96 * se))
            metrics['ci_upper'] = float(np.exp(coef + 1.96 * se))
        else:
            metrics['coefficient'] = float(coef)
            metrics['ci_lower'] = float(coef - 1.96 * se)
            metrics['ci_upper'] = float(coef + 1.96 * se)
            
        metrics['p_value'] = float(pval)
        metrics['significant'] = pval < 0.05
        
    return metrics

def create_variation_table(results_by_threshold: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    """
    Create a variation table comparing odds ratios across thresholds.
    
    Args:
        results_by_threshold: Dictionary mapping threshold names to their results
        
    Returns:
        DataFrame with variation metrics across thresholds
    """
    rows = []
    
    for threshold, results in results_by_threshold.items():
        if results is None:
            continue
            
        metrics = extract_odds_ratios(results, model_type="logistic")
        if not metrics:
            continue
            
        row = {
            'threshold': threshold,
            'odds_ratio': metrics.get('odds_ratio', None),
            'ci_lower': metrics.get('ci_lower', None),
            'ci_upper': metrics.get('ci_upper', None),
            'p_value': metrics.get('p_value', None),
            'significant': metrics.get('significant', False)
        }
        rows.append(row)
        
    if not rows:
        return pd.DataFrame()
        
    df = pd.DataFrame(rows)
    
    # Calculate variation statistics
    if len(df) > 1 and df['odds_ratio'].notna().sum() > 1:
        df['variance'] = df['odds_ratio'].var()
        df['range'] = df['odds_ratio'].max() - df['odds_ratio'].min()
        df['mean_or'] = df['odds_ratio'].mean()
        
    return df

def aggregate_sensitivity_results(
    threshold_results: Dict[str, Dict[str, Any]],
    bootstrap_results: Dict[str, Dict[str, Any]],
    output_path: str
) -> str:
    """
    Aggregate all results into a comprehensive variation table.
    
    Args:
        threshold_results: Model results for each threshold
        bootstrap_results: Bootstrap validation results for each threshold
        output_path: Path to save the aggregated results
        
    Returns:
        Path to the saved results file
    """
    # Create variation table from model results
    variation_df = create_variation_table(threshold_results)
    
    # Aggregate bootstrap stability flags
    stability_data = []
    for threshold, boot_res in bootstrap_results.items():
        if boot_res:
            stability_data.append({
                'threshold': threshold,
                'stable': boot_res.get('stable', False),
                'ci_width_variance': boot_res.get('ci_width_variance', None),
                'final_n_resamples': boot_res.get('n_resamples', 0)
            })
            
    stability_df = pd.DataFrame(stability_data) if stability_data else pd.DataFrame()
    
    # Combine into final report structure
    final_report = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'analysis_type': 'threshold_variation_analysis',
            'description': 'Variation in odds ratios across sensory deprivation thresholds'
        },
        'variation_table': variation_df.to_dict(orient='records'),
        'stability_analysis': stability_df.to_dict(orient='records') if not stability_df.empty else [],
        'summary_statistics': {
            'n_thresholds': len(threshold_results),
            'n_stable_thresholds': len([s for s in stability_data if s.get('stable', False)]),
            'has_significant_variation': not variation_df.empty and 'variance' in variation_df.columns and variation_df['variance'].max() > 0.01
        }
    }
    
    # Save to JSON
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(final_report, f, indent=2, default=str)
        
    logger.info(f"Aggregated results saved to {output_path}")
    return output_path

def main():
    """Main entry point for result aggregation."""
    logging.basicConfig(level=logging.INFO)
    
    # Define paths
    result_dir = "results/models"
    output_file = os.path.join(result_dir, "variation_table.json")
    
    # Thresholds defined in protocol
    thresholds = ["strict", "moderate", "partial"]
    
    # Load results for each threshold
    threshold_results = {}
    bootstrap_results = {}
    
    for threshold in thresholds:
        # Load model results
        model_res = load_model_results(result_dir, threshold)
        threshold_results[threshold] = model_res
        
        # Load bootstrap results (if available)
        boot_file = os.path.join(result_dir, f"bootstrap_results_{threshold}.json")
        if os.path.exists(boot_file):
            try:
                with open(boot_file, 'r') as f:
                    bootstrap_results[threshold] = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load bootstrap results for {threshold}: {e}")
    
    # Aggregate results
    output_path = aggregate_sensitivity_results(
        threshold_results,
        bootstrap_results,
        output_file
    )
    
    # Print summary
    if os.path.exists(output_path):
        with open(output_path, 'r') as f:
            report = json.load(f)
            
        print(f"\n=== Variation Analysis Summary ===")
        print(f"Thresholds analyzed: {report['summary_statistics']['n_thresholds']}")
        print(f"Stable thresholds: {report['summary_statistics']['n_stable_thresholds']}")
        print(f"Significant variation detected: {report['summary_statistics']['has_significant_variation']}")
        print(f"\nOdds Ratio Variation:")
        for row in report['variation_table']:
            print(f"  {row['threshold']}: OR={row.get('odds_ratio', 'N/A'):.3f} "
                  f"(95% CI: {row.get('ci_lower', 'N/A'):.3f} - {row.get('ci_upper', 'N/A'):.3f})")
                  
        print(f"\nResults saved to: {output_path}")

if __name__ == "__main__":
    main()
