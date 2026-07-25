"""
Sensitivity Analysis Engine for Text Message Tone Study.

This module implements the sensitivity analysis engine that:
1. Reads operationalization definitions from data/processed/sensitivity_definitions.json
2. Reads primary results from data/processed/analysis_results.json
3. Dynamically applies each definition to re-calculate 'Cue Intensity'
4. Re-runs the LMM for each definition
5. Calculates stability metrics and generates a report
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np
from statsmodels.formula.api import mixedlm
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.stats.anova import anova_lm

# Import from project config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import get_processed_data_dir, get_raw_data_dir
from logging_config import setup_logging, get_logger

# Setup logging
logger = get_logger(__name__)

def load_sensitivity_definitions() -> Dict[str, Any]:
    """Load sensitivity definitions from JSON file."""
    definitions_path = get_processed_data_dir() / "sensitivity_definitions.json"
    if not definitions_path.exists():
        raise FileNotFoundError(f"Sensitivity definitions file not found: {definitions_path}")
    
    with open(definitions_path, 'r') as f:
        definitions = json.load(f)
    
    logger.info(f"Loaded {len(definitions.get('definitions', []))} sensitivity definitions")
    return definitions

def load_primary_results() -> Dict[str, Any]:
    """Load primary analysis results from JSON file."""
    results_path = get_processed_data_dir() / "analysis_results.json"
    if not results_path.exists():
        raise FileNotFoundError(f"Primary analysis results not found: {results_path}")
    
    with open(results_path, 'r') as f:
        results = json.load(f)
    
    logger.info("Loaded primary analysis results")
    return results

def load_raw_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load stimuli and ratings data."""
    stimuli_path = get_raw_data_dir() / "stimuli.csv"
    ratings_path = get_raw_data_dir() / "ratings.csv"
    
    if not stimuli_path.exists():
        raise FileNotFoundError(f"Stimuli data not found: {stimuli_path}")
    if not ratings_path.exists():
        raise FileNotFoundError(f"Ratings data not found: {ratings_path}")
    
    stimuli = pd.read_csv(stimuli_path)
    ratings = pd.read_csv(ratings_path)
    
    logger.info(f"Loaded {len(stimuli)} stimuli and {len(ratings)} ratings")
    return stimuli, ratings

def apply_cue_definition(df: pd.DataFrame, definition: Dict[str, Any]) -> pd.Series:
    """
    Apply a specific cue intensity definition to calculate cue intensity.
    
    Args:
        df: DataFrame containing stimulus data
        definition: Definition dictionary with 'type' and parameters
        
    Returns:
        Series of calculated cue intensity values
    """
    cue_type = definition.get('type')
    params = definition.get('params', {})
    
    if cue_type == 'conjunctive':
        # High Emoji AND High Punctuation
        emoji_threshold = params.get('emoji_threshold', 1)
        punct_threshold = params.get('punct_threshold', 1)
        
        cue_intensity = (
            (df['emoji_count'] >= emoji_threshold) & 
            (df['punctuation_count'] >= punct_threshold)
        ).astype(int)
        
    elif cue_type == 'disjunctive':
        # High Emoji OR High Punctuation
        emoji_threshold = params.get('emoji_threshold', 1)
        punct_threshold = params.get('punct_threshold', 1)
        
        cue_intensity = (
            (df['emoji_count'] >= emoji_threshold) | 
            (df['punctuation_count'] >= punct_threshold)
        ).astype(int)
        
    elif cue_type == 'threshold':
        # Threshold-based: weighted sum
        emoji_weight = params.get('emoji_weight', 1.0)
        punct_weight = params.get('punct_weight', 1.0)
        total_threshold = params.get('total_threshold', 2)
        
        weighted_sum = (df['emoji_count'] * emoji_weight + 
                      df['punctuation_count'] * punct_weight)
        cue_intensity = (weighted_sum >= total_threshold).astype(int)
        
    elif cue_type == 'ordinal':
        # Ordinal: 0, 1, 2 based on combined score
        emoji_weight = params.get('emoji_weight', 1.0)
        punct_weight = params.get('punct_weight', 1.0)
        
        combined_score = df['emoji_count'] * emoji_weight + df['punctuation_count'] * punct_weight
        
        # Create ordinal categories: 0 (low), 1 (medium), 2 (high)
        cue_intensity = pd.cut(
            combined_score, 
            bins=[-0.1, 1, 2, float('inf')], 
            labels=[0, 1, 2]
        ).astype(int)
        
    else:
        raise ValueError(f"Unknown cue definition type: {cue_type}")
    
    return cue_intensity

def run_lmm_for_definition(data: pd.DataFrame, definition_name: str) -> Dict[str, Any]:
    """
    Run LMM analysis for a specific cue intensity definition.
    
    Args:
        data: DataFrame with ratings and calculated cue intensity
        definition_name: Name of the definition being tested
        
    Returns:
        Dictionary with model results
    """
    try:
        # Prepare formula: rating ~ relationship * cue_intensity + (1|participant_id) + (1|stimulus_id)
        formula = "rating ~ relationship * cue_intensity + (1|participant_id) + (1|stimulus_id)"
        
        # Fit model
        model = mixedlm.from_formula(
            formula, 
            data=data, 
            groups=data['participant_id'],
            exog_re=data[['stimulus_id']]
        )
        
        result = model.fit()
        
        # Extract key statistics
        fixed_effects = result.params
        f_statistic = result.f_pvalue if hasattr(result, 'f_pvalue') else None
        
        # Get interaction p-value
        interaction_term = "relationship[T.acquaintance]:cue_intensity"
        interaction_p = fixed_effects.get(interaction_term, np.nan)
        
        # Run Tukey post-hoc if interaction is significant
        tukey_results = None
        if not np.isnan(interaction_p) and interaction_p < 0.05:
            try:
                tukey = pairwise_tukeyhsd(
                    endog=data['rating'],
                    groups=data['relationship'],
                    alpha=0.05
                )
                tukey_results = {
                    'reject': bool(tukey.reject.any()),
                    'mean_diff': tukey.meandiffs.tolist() if hasattr(tukey, 'meandiffs') else []
                }
            except Exception as e:
                logger.warning(f"Tukey post-hoc failed: {e}")
        
        return {
            'definition_name': definition_name,
            'f_statistic': float(f_statistic) if f_statistic is not None else None,
            'interaction_p_value': float(interaction_p) if not np.isnan(interaction_p) else None,
            'fixed_effects': {k: float(v) for k, v in fixed_effects.items()},
            'tukey_results': tukey_results,
            'converged': result.converged if hasattr(result, 'converged') else True
        }
        
    except Exception as e:
        logger.error(f"LMM failed for definition {definition_name}: {e}")
        return {
            'definition_name': definition_name,
            'error': str(e),
            'f_statistic': None,
            'interaction_p_value': None,
            'converged': False
        }

def calculate_stability_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate stability metrics across different definitions.
    
    Args:
        results: List of LMM results for each definition
        
    Returns:
        Dictionary with stability metrics
    """
    # Filter out failed results
    valid_results = [r for r in results if r.get('interaction_p_value') is not None]
    
    if len(valid_results) < 2:
        return {
            'num_valid_definitions': len(valid_results),
            'stability_note': 'Insufficient valid results for stability analysis'
        }
    
    # Extract p-values and F-statistics
    p_values = [r['interaction_p_value'] for r in valid_results]
    f_stats = [r['f_statistic'] for r in valid_results if r.get('f_statistic') is not None]
    
    # Calculate variance and coefficient of variation
    p_var = np.var(p_values)
    p_cv = np.std(p_values) / np.mean(p_values) if np.mean(p_values) != 0 else float('inf')
    
    f_var = np.var(f_stats) if f_stats else None
    f_cv = np.std(f_stats) / np.mean(f_stats) if f_stats and np.mean(f_stats) != 0 else float('inf')
    
    # Check if all definitions agree on significance
    significant = [p < 0.05 for p in p_values]
    agreement_rate = sum(significant) / len(significant)
    
    return {
        'num_valid_definitions': len(valid_results),
        'p_value_variance': float(p_var),
        'p_value_cv': float(p_cv),
        'f_statistic_variance': float(f_var) if f_var is not None else None,
        'f_statistic_cv': float(f_cv) if f_cv is not None else None,
        'significance_agreement_rate': float(agreement_rate),
        'stable': agreement_rate > 0.8 and p_var < 0.01
    }

def generate_sensitivity_report(
    results: List[Dict[str, Any]], 
    stability_metrics: Dict[str, Any]
) -> pd.DataFrame:
    """
    Generate a CSV report of sensitivity analysis results.
    
    Args:
        results: List of LMM results for each definition
        stability_metrics: Stability metrics across definitions
        
    Returns:
        DataFrame with the sensitivity report
    """
    report_data = []
    
    for result in results:
        row = {
            'definition_name': result.get('definition_name', 'unknown'),
            'f_statistic': result.get('f_statistic'),
            'interaction_p_value': result.get('interaction_p_value'),
            'converged': result.get('converged', False),
            'has_error': 'error' in result
        }
        
        if result.get('tukey_results'):
            row['tukey_rejected'] = result['tukey_results'].get('reject', False)
        
        report_data.append(row)
    
    report_df = pd.DataFrame(report_data)
    return report_df

def main():
    """Main entry point for sensitivity analysis."""
    setup_logging()
    logger.info("Starting sensitivity analysis")
    
    try:
        # Load inputs
        definitions = load_sensitivity_definitions()
        primary_results = load_primary_results()
        stimuli, ratings = load_raw_data()
        
        # Merge data
        data = ratings.merge(stimuli, on='stimulus_id', how='left')
        
        # Run analysis for each definition
        all_results = []
        definitions_list = definitions.get('definitions', [])
        
        for definition in definitions_list:
            def_name = definition.get('name', 'unknown')
            logger.info(f"Processing definition: {def_name}")
            
            # Apply definition to calculate cue intensity
            data['cue_intensity'] = apply_cue_definition(data, definition)
            
            # Run LMM
            result = run_lmm_for_definition(data, def_name)
            all_results.append(result)
            
            logger.info(f"  F-statistic: {result.get('f_statistic')}, "
                        f"Interaction p-value: {result.get('interaction_p_value')}")
        
        # Calculate stability metrics
        stability_metrics = calculate_stability_metrics(all_results)
        logger.info(f"Stability analysis complete: {stability_metrics}")
        
        # Generate report
        report_df = generate_sensitivity_report(all_results, stability_metrics)
        
        # Save results
        output_dir = get_processed_data_dir()
        
        # Save detailed results JSON
        detailed_results = {
            'primary_results': primary_results,
            'sensitivity_results': all_results,
            'stability_metrics': stability_metrics
        }
        
        with open(output_dir / 'sensitivity_analysis_results.json', 'w') as f:
            json.dump(detailed_results, f, indent=2, default=str)
        
        # Save CSV report
        report_df.to_csv(output_dir / 'sensitivity_report.csv', index=False)
        
        logger.info(f"Sensitivity analysis complete. Results saved to {output_dir}")
        return 0
        
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())
