import logging
import warnings
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import numpy as np
from statsmodels.regression.mixed_linear_model import MixedLM
from config import get_path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def aggregate_to_stimulus_level(data: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate data to Stimulus level (mean response time per stimulus per participant).
    
    Args:
        data: DataFrame with trial-level data including participant_id, stimulus_id, response_time
        
    Returns:
        DataFrame with aggregated mean response time per stimulus per participant
    """
    if data.empty:
        logger.warning("Input data is empty for aggregation")
        return data
        
    # Ensure required columns exist
    required_cols = ['participant_id', 'stimulus_id', 'response_time']
    missing_cols = [col for col in required_cols if col not in data.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for aggregation: {missing_cols}")
        
    # Aggregate to stimulus level per participant
    aggregated = data.groupby(['participant_id', 'stimulus_id']).agg({
        'response_time': 'mean',
        # Keep other relevant columns if needed (e.g., prime_valence, stimulus_ambiguity)
        'prime_condition': 'first',
        'prime_valence': 'first',
        'stimulus_ambiguity': 'first'
    }).reset_index()
    
    logger.info(f"Aggregated {len(data)} trials to {len(aggregated)} stimulus-participant combinations")
    return aggregated

def fit_lmm_with_retry(
    data: pd.DataFrame,
    formula: str,
    random_effect: str,
    max_retries: int = 3
) -> Tuple[Optional[MixedLM], Dict[str, Any]]:
    """
    Fit Linear Mixed-Effects Model with retry logic for convergence issues.
    
    Args:
        data: Aggregated DataFrame
        formula: Model formula (e.g., 'mean_response_time ~ prime_valence * stimulus_ambiguity')
        random_effect: Random effect specification (e.g., 'participant_id')
        max_retries: Maximum number of optimizer attempts
        
    Returns:
        Tuple of (model results or None, metadata dict with convergence info)
    """
    if data.empty:
        logger.error("Cannot fit LMM on empty data")
        return None, {'status': 'failed', 'reason': 'empty_data'}
        
    # Ensure numeric columns are numeric
    for col in data.columns:
        if col not in ['participant_id', 'stimulus_id']:
            try:
                data[col] = pd.to_numeric(data[col], errors='coerce')
            except Exception:
                pass
                
    # Drop rows with missing values in required columns
    initial_rows = len(data)
    data_clean = data.dropna(subset=formula.split('~')[0].split() + [formula.split('~')[1].split()[0]])
    if len(data_clean) < initial_rows:
        logger.warning(f"Dropped {initial_rows - len(data_clean)} rows with missing values")
        
    if len(data_clean) == 0:
        return None, {'status': 'failed', 'reason': 'no_valid_data_after_cleaning'}
        
    # Prepare endog and exog
    try:
        # Use statsmodels formula API
        from statsmodels.formula.api import mixedlm
        
        result = None
        last_error = None
        convergence_status = 'failed'
        
        # Try different optimizers
        optimizers = ['lbfgs', 'bfgs', 'newton', 'cg']
        
        for i, method in enumerate(optimizers[:max_retries]):
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    result = mixedlm(formula, data_clean, groups=data_clean[random_effect], method=method).fit()
                    
                if result.converged:
                    convergence_status = 'converged'
                    logger.info(f"LMM converged on attempt {i+1} with method: {method}")
                    break
                else:
                    logger.warning(f"LMM did not converge on attempt {i+1} with method: {method}")
                    
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {i+1} failed with method {method}: {str(e)}")
                continue
                
        if result is None:
            logger.error("LMM failed to converge after all retry attempts")
            return None, {'status': 'failed', 'reason': 'no_convergence', 'last_error': str(last_error)}
            
        # Extract key results
        results_dict = {
            'status': 'success',
            'converged': result.converged,
            'method': result.method,
            'iterations': result.ncov_params,
            'aic': result.aic,
            'bic': result.bic,
            'params': result.params.to_dict(),
            'pvalues': result.pvalues.to_dict(),
            'rsquared': getattr(result, 'rsquared', None)
        }
        
        return result, results_dict
        
    except Exception as e:
        logger.error(f"Error fitting LMM: {str(e)}")
        return None, {'status': 'failed', 'reason': str(e)}

def run_lmm_analysis(
    data: pd.DataFrame,
    formula: str = "response_time ~ prime_valence * stimulus_ambiguity",
    random_effect: str = "participant_id"
) -> Dict[str, Any]:
    """
    Run complete LMM analysis pipeline with associational framing.
    
    This function fits the model, extracts results, and ensures all outputs
    are framed as "associational" rather than causal per FR-003.
    
    Args:
        data: Preprocessed and aggregated data
        formula: Model formula
        random_effect: Random effect grouping variable
        
    Returns:
        Dictionary containing model results and metadata
    """
    logger.info("Starting LMM analysis with associational framing")
    
    # Fit model
    model_result, metadata = fit_lmm_with_retry(data, formula, random_effect)
    
    if model_result is None:
        logger.error("LMM analysis failed: could not fit model")
        return {
            'status': 'failed',
            'reason': metadata.get('reason', 'unknown'),
            'framing_note': 'Analysis aborted due to model fitting failure'
        }
    
    # Extract fixed effects with associational language
    params = model_result.params
    pvalues = model_result.pvalues
    
    # Build results with explicit associational framing
    results = {
        'status': 'success',
        'framing_note': 'Results represent statistical associations, not causal effects. Per FR-003, findings are observational in nature.',
        'model_info': {
            'formula': formula,
            'random_effect': random_effect,
            'converged': metadata['converged'],
            'method': metadata['method'],
            'aic': metadata['aic'],
            'bic': metadata['bic']
        },
        'fixed_effects': [],
        'associational_interpretation': {
            'prime_valence': f"Association between prime valence and response time (b={params.get('prime_valence', 0):.4f}, p={pvalues.get('prime_valence', 1):.4f})",
            'stimulus_ambiguity': f"Association between stimulus ambiguity and response time (b={params.get('stimulus_ambiguity', 0):.4f}, p={pvalues.get('stimulus_ambiguity', 1):.4f})",
            'interaction': f"Association of interaction term (b={params.get('prime_valence:stimulus_ambiguity', 0):.4f}, p={pvalues.get('prime_valence:stimulus_ambiguity', 1):.4f})"
        }
    }
    
    # Format fixed effects
    for param_name, param_value in params.items():
        if param_name != 'Intercept':
            p_val = pvalues.get(param_name, 1.0)
            results['fixed_effects'].append({
                'term': param_name,
                'coefficient': float(param_value),
                'p_value': float(p_val),
                'interpretation': f"Observed association for {param_name}"
            })
    
    logger.info(f"LMM analysis completed. Framing: Associational (not causal)")
    return results

def main():
    """Main entry point for LMM analysis."""
    logger.info("Running LMM analysis main pipeline")
    
    # Load data from processed linked trials
    processed_path = get_path('data/processed/linked_trials.csv')
    if not processed_path.exists():
        logger.error(f"Data file not found: {processed_path}")
        print("Error: linked_trials.csv not found. Run data ingestion first.")
        return
        
    try:
        data = pd.read_csv(processed_path)
        logger.info(f"Loaded {len(data)} trials from {processed_path}")
        
        # Aggregate to stimulus level
        aggregated_data = aggregate_to_stimulus_level(data)
        
        # Run LMM analysis
        results = run_lmm_analysis(
            aggregated_data,
            formula="response_time ~ prime_valence * stimulus_ambiguity",
            random_effect="participant_id"
        )
        
        # Save results
        output_path = get_path('data/processed/lmm_results.json')
        import json
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"LMM results saved to {output_path}")
        print(f"\nLMM Analysis Complete")
        print(f"Framing: {results.get('framing_note', 'Associational (not causal)')}")
        print(f"Status: {results['status']}")
        
    except Exception as e:
        logger.error(f"Error in LMM analysis: {str(e)}")
        raise

if __name__ == "__main__":
    main()