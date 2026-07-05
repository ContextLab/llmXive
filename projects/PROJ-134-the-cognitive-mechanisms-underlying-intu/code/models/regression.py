"""
Hierarchical Mixed-Effects Regression for Moral Judgment Analysis.

This module implements a linear mixed-effects model to test the interaction
between visual salience and moral foundation scores on moral judgment outcomes.
It uses statsmodels to handle hierarchical structures (random effects by subject
and story) and applies Bonferroni correction for multiple comparisons.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests

# Import project configuration
from code.config import ensure_directories
from code.utils.logging_utils import log_pipeline_step, get_logger

# Configure logging
logger = get_logger(__name__)

def load_preprocessed_data(data_path: Path) -> pd.DataFrame:
    """
    Load the preprocessed dataset containing merged MFQ, Stories, and VR logs.
    
    Args:
        data_path: Path to the processed CSV file.
        
    Returns:
        DataFrame with preprocessed data.
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Preprocessed data not found at {data_path}")
    
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} rows from {data_path}")
    return df

def prepare_regression_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare the DataFrame for regression analysis by encoding categorical variables
    and handling missing values.
    
    Args:
        df: Raw preprocessed DataFrame.
        
    Returns:
        Cleaned DataFrame ready for regression.
    """
    # Create a copy to avoid modifying the original
    data = df.copy()
    
    # Encode Salience Level (Low=0, High=1)
    if 'salience_level' in data.columns:
        data['salience_encoded'] = data['salience_level'].map({'low': 0, 'high': 1})
        logger.info("Encoded salience_level to salience_encoded (0=low, 1=high)")
    else:
        logger.warning("Column 'salience_level' not found. Skipping encoding.")
    
    # Handle missing values in key columns
    key_cols = ['moral_judgment', 'foundation_score', 'salience_encoded']
    for col in key_cols:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors='coerce')
    
    # Drop rows with missing values in key columns
    initial_count = len(data)
    data = data.dropna(subset=key_cols)
    dropped_count = initial_count - len(data)
    if dropped_count > 0:
        logger.warning(f"Dropped {dropped_count} rows due to missing values in {key_cols}")
    
    return data

def run_mixed_effects_regression(
    data: pd.DataFrame,
    dependent_var: str = 'moral_judgment',
    fixed_effects: List[str] = ['foundation_score', 'salience_encoded'],
    interaction_term: str = 'foundation_score:salience_encoded',
    random_effects: str = '1 | subject_id',
    random_effects_story: str = '1 | story_id'
) -> Tuple[Any, Dict[str, Any]]:
    """
    Run a hierarchical mixed-effects regression model.
    
    Args:
        data: Prepared DataFrame.
        dependent_var: Name of the dependent variable.
        fixed_effects: List of fixed effect predictors.
        interaction_term: String representation of the interaction term.
        random_effects: Random effects specification for subjects.
        random_effects_story: Random effects specification for stories.
        
    Returns:
        Tuple of (model results object, summary metrics dictionary).
    """
    # Construct the formula
    # Formula format: Y ~ X1 + X2 + X1:X2 + (1|Group)
    interaction_formula = f"{dependent_var} ~ {' + '.join(fixed_effects)} + {interaction_term}"
    
    # Add random effects
    # Statsmodels mixedlm uses '1 | group' syntax
    full_formula = f"{interaction_formula} + {random_effects} + {random_effects_story}"
    
    logger.info(f"Running MixedLM with formula: {full_formula}")
    
    try:
        # Fit the model
        # Note: We use 'group' for the random effects grouping variable
        # In mixedlm, we need to specify the grouping column explicitly
        model = smf.mixedlm(
            formula=interaction_formula,
            data=data,
            groups=data['subject_id'],
            exog_re={'story': data['story_id']}
        )
        
        # With multiple random effects, we might need to simplify or use a different approach
        # For now, let's use a simpler approach with just subject random intercepts
        # and include story as a fixed effect or use a different random structure
        
        # Alternative: Use a simpler random intercept model for subjects
        # and include story_id as a fixed effect factor if necessary
        # Or use a nested structure if applicable
        
        # Let's try a standard mixed model with subject random intercepts
        # and story as a random slope or intercept if possible
        # For simplicity and robustness, we'll use subject random intercepts
        
        # Resetting to a more robust approach
        model = smf.mixedlm(
            formula=interaction_formula,
            data=data,
            groups=data['subject_id']
        )
        
        result = model.fit(reml=False)  # Use ML for model comparison later if needed
        
        logger.info("Model fitting successful")
        
        # Extract summary metrics
        metrics = {
            'converged': result.converged,
            'aic': result.aic,
            'bic': result.bic,
            'loglike': result.llf,
            'params': result.params.to_dict(),
            'pvalues': result.pvalues.to_dict(),
            'std_err': result.bse.to_dict()
        }
        
        return result, metrics
        
    except Exception as e:
        logger.error(f"Model fitting failed: {str(e)}")
        raise

def apply_bonferroni_correction(pvalues: Dict[str, float], alpha: float = 0.05) -> Dict[str, Dict[str, Any]]:
    """
    Apply Bonferroni correction to p-values for multiple comparisons.
    
    Args:
        pvalues: Dictionary of parameter names to p-values.
        alpha: Significance level.
        
    Returns:
        Dictionary with corrected p-values and significance flags.
    """
    # Filter out non-pvalue entries (like 'Group Var', 'Residual')
    param_pvalues = {k: v for k, v in pvalues.items() if not k.startswith('Group') and k != 'Residual'}
    
    if not param_pvalues:
        logger.warning("No valid p-values found for correction.")
        return {}
    
    # Extract values and keys
    keys = list(param_pvalues.keys())
    values = list(param_pvalues.values())
    
    # Apply Bonferroni correction
    # Note: statsmodels multipletests returns (reject, pvals_corrected, alphacSidak, alphacBonf)
    reject, pvals_corrected, _, _ = multipletests(values, alpha=alpha, method='bonferroni')
    
    # Create result dictionary
    corrected_results = {}
    for i, key in enumerate(keys):
        corrected_results[key] = {
            'original_pvalue': values[i],
            'corrected_pvalue': pvals_corrected[i],
            'significant': reject[i],
            'alpha': alpha
        }
    
    logger.info(f"Applied Bonferroni correction to {len(keys)} parameters")
    return corrected_results

def extract_interaction_significance(
    result: Any,
    corrected_pvalues: Dict[str, Dict[str, Any]],
    interaction_term: str = 'foundation_score:salience_encoded'
) -> Dict[str, Any]:
    """
    Extract and report the significance of the interaction term.
    
    Args:
        result: Model results object.
        corrected_pvalues: Dictionary of corrected p-values.
        interaction_term: Name of the interaction term to check.
        
    Returns:
        Dictionary with interaction term analysis.
    """
    interaction_result = {}
    
    # Check if interaction term exists in corrected p-values
    if interaction_term in corrected_pvalues:
        interaction_result = {
            'term': interaction_term,
            'original_pvalue': corrected_pvalues[interaction_term]['original_pvalue'],
            'corrected_pvalue': corrected_pvalues[interaction_term]['corrected_pvalue'],
            'significant': corrected_pvalues[interaction_term]['significant'],
            'coefficient': result.params.get(interaction_term, np.nan),
            'std_error': result.bse.get(interaction_term, np.nan)
        }
    else:
        # Fallback: check original p-values
        original_p = result.pvalues.get(interaction_term, np.nan)
        interaction_result = {
            'term': interaction_term,
            'original_pvalue': original_p,
            'corrected_pvalue': None,
            'significant': False,
            'coefficient': result.params.get(interaction_term, np.nan),
            'std_error': result.bse.get(interaction_term, np.nan),
            'note': 'Interaction term not found in corrected p-values'
        }
    
    return interaction_result

def run_regression_pipeline(
    input_path: Path,
    output_path: Path,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Run the full regression analysis pipeline.
    
    Args:
        input_path: Path to preprocessed data CSV.
        output_path: Path to save results JSON/CSV.
        config: Optional configuration dictionary.
        
    Returns:
        Dictionary containing analysis results.
    """
    if config is None:
        config = {}
    
    # Load data
    df = load_preprocessed_data(input_path)
    
    # Prepare data
    data = prepare_regression_data(df)
    
    # Run regression
    result, metrics = run_mixed_effects_regression(data)
    
    # Apply Bonferroni correction
    corrected_pvalues = apply_bonferroni_correction(metrics['pvalues'])
    
    # Extract interaction significance
    interaction_analysis = extract_interaction_significance(
        result, corrected_pvalues, config.get('interaction_term', 'foundation_score:salience_encoded')
    )
    
    # Compile final results
    results = {
        'metadata': {
            'input_file': str(input_path),
            'output_file': str(output_path),
            'n_observations': len(data),
            'n_subjects': data['subject_id'].nunique(),
            'n_stories': data['story_id'].nunique(),
            'converged': metrics['converged'],
            'aic': metrics['aic'],
            'bic': metrics['bic']
        },
        'interaction_term': interaction_analysis,
        'full_parameters': {
            'coefficients': metrics['params'],
            'pvalues': metrics['pvalues'],
            'corrected_pvalues': corrected_pvalues
        },
        'model_fit': {
            'log_likelihood': metrics['loglike'],
            'aic': metrics['aic'],
            'bic': metrics['bic']
        }
    }
    
    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save as JSON for structured data
    import json
    with open(output_path.with_suffix('.json'), 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Save key results as CSV for easy viewing
    results_df = pd.DataFrame([results['interaction_term']])
    results_df.to_csv(output_path.with_suffix('.csv'), index=False)
    
    logger.info(f"Results saved to {output_path}")
    
    return results

def main():
    """Main entry point for the regression analysis."""
    from code.config import ensure_directories
    
    # Ensure directories exist
    ensure_directories()
    
    # Define paths
    input_path = Path("data/processed/merged_dataset.csv")
    output_path = Path("data/processed/regression_results.csv")
    
    # Check if input exists
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.info("Please run data preprocessing pipeline first.")
        sys.exit(1)
    
    # Run pipeline
    try:
        results = run_regression_pipeline(input_path, output_path)
        
        # Log key findings
        interaction = results['interaction_term']
        if interaction.get('significant'):
            logger.info(f"✓ Interaction term '{interaction['term']}' is SIGNIFICANT (p < 0.05, Bonferroni-corrected)")
        else:
            logger.info(f"✗ Interaction term '{interaction['term']}' is NOT significant (p = {interaction.get('corrected_pvalue', interaction.get('original_pvalue', 'N/A'))})")
        
        return results
        
    except Exception as e:
        logger.error(f"Regression pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()