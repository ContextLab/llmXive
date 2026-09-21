import logging
import warnings
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import numpy as np
from statsmodels.regression.mixed_linear_model import MixedLM
from code.config import Config, set_seed

logger = logging.getLogger(__name__)

def aggregate_to_stimulus_level(data: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate data to Stimulus level (mean response time per stimulus per participant).
    
    Args:
        data: DataFrame with columns including 'stimulus_id', 'participant_id', 'response_time'
    
    Returns:
        DataFrame with aggregated mean response times
    """
    logger.info("Aggregating data to stimulus level...")
    aggregated = data.groupby(['stimulus_id', 'participant_id']).agg({
        'response_time': 'mean'
    }).reset_index()
    aggregated.rename(columns={'response_time': 'mean_response_time'}, inplace=True)
    return aggregated

def fit_lmm_with_retry(data: pd.DataFrame, max_retries: int = 3) -> Dict[str, Any]:
    """
    Fit Linear Mixed-Effects Model with retry logic for convergence failures.
    
    Formula: mean_response_time ~ prime_valence * stimulus_ambiguity + (1 | participant_id)
    
    Args:
        data: DataFrame with required columns
        max_retries: Maximum number of optimizer attempts
    
    Returns:
        Dictionary containing model results, convergence status, and caution notes.
    """
    set_seed(Config.SEED)
    
    required_cols = ['mean_response_time', 'prime_valence', 'stimulus_ambiguity', 'participant_id']
    if not all(col in data.columns for col in required_cols):
        raise ValueError(f"Missing required columns for LMM. Expected: {required_cols}, Found: {list(data.columns)}")
    
    # Prepare formula
    formula = "mean_response_time ~ prime_valence * stimulus_ambiguity"
    groups = data['participant_id']
    
    model_result = None
    convergence_status = "failed"
    attempts = 0
    optimizer_used = None
    
    optimizers = ['bfgs', 'lbfgs', 'newton', 'cg', 'ncg']
    
    logger.info(f"Attempting LMM fit with formula: {formula}")
    
    for i in range(max_retries):
        attempts += 1
        current_optimizer = optimizers[i % len(optimizers)]
        
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model = MixedLM.from_formula(
                    formula, 
                    groups=groups, 
                    data=data
                )
                result = model.fit(method=current_optimizer, maxiter=1000)
                
                if result.converged:
                    model_result = result
                    convergence_status = "converged"
                    optimizer_used = current_optimizer
                    logger.info(f"Model converged on attempt {attempts} using {current_optimizer}")
                    break
                else:
                    logger.warning(f"Attempt {attempts} with {current_optimizer} did not converge.")
                    
        except Exception as e:
            logger.warning(f"Attempt {attempts} with {current_optimizer} failed: {str(e)}")
            continue
    
    # If still not converged after retries, log final status
    if convergence_status == "failed":
        logger.error("Model failed to converge after all retry attempts.")
        # Return a minimal result structure even on failure to allow pipeline to continue with caution
        model_result = None
    
    # Construct result dictionary with explicit associational framing
    result_dict = {
        "convergence_status": convergence_status,
        "optimizer_used": optimizer_used,
        "attempts": attempts,
        "fixed_effects": None,
        "random_effects": None,
        "caution_note": "Associational analysis only; not causal",
        "limitation_note": "Limitation: Derived prime valence scores used"
    }
    
    if model_result is not None:
        result_dict["fixed_effects"] = model_result.params.to_dict()
        result_dict["random_effects"] = model_result.random_effects
        result_dict["covariance_matrix"] = model_result.cov_params().to_dict()
        result_dict["log_likelihood"] = model_result.llf
        logger.info(f"LMM fit successful. Log-likelihood: {model_result.llf}")
    else:
        logger.warning("No valid model results to report.")
    
    # Log the caution notes explicitly
    logger.warning(f"CAUTION: {result_dict['caution_note']}")
    logger.warning(f"LIMITATION: {result_dict['limitation_note']}")
    
    return result_dict

def run_lmm_analysis(input_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Run full LMM analysis pipeline on aggregated data.
    
    Args:
        input_path: Path to aggregated data CSV
        output_path: Optional path to save results JSON (not implemented in this snippet, handled by caller)
    
    Returns:
        Dictionary with analysis results and associational framing notes.
    """
    logger.info(f"Loading aggregated data from {input_path}")
    try:
        data = pd.read_csv(input_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Aggregated data file not found at {input_path}. Ensure T024 has run.")
    
    logger.info(f"Loaded {len(data)} rows of aggregated data.")
    
    if data.empty:
        raise ValueError("Aggregated data is empty. Cannot run LMM.")
    
    # Run the model fitting
    results = fit_lmm_with_retry(data)
    
    logger.info("LMM analysis complete.")
    logger.info(f"Result keys: {list(results.keys())}")
    
    return results

def main():
    """Main entry point for LMM analysis script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(Config.LOG_PATH / 'lmm_analysis.log')
        ]
    )
    
    # Default paths based on Config
    input_file = Config.DATA_PROCESSED / "aggregated_trials.csv"
    
    if not input_file.exists():
        logger.error(f"Input file {input_file} does not exist. Run T024 first.")
        return
    
    try:
        results = run_lmm_analysis(str(input_file))
        logger.info("LMM Analysis completed successfully.")
        logger.info(f"Convergence Status: {results['convergence_status']}")
        logger.info(f"Caution: {results['caution_note']}")
        logger.info(f"Limitation: {results['limitation_note']}")
        
        # Note: In a full pipeline, results would be saved to JSON here
        # but T029 specifically focuses on the content of the notes in the dict.
        
    except Exception as e:
        logger.error(f"LMM Analysis failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
