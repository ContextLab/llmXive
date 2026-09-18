import logging
import warnings
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import numpy as np
from statsmodels.regression.mixed_linear_model import MixedLM
from code.config import Config
from pathlib import Path

logger = logging.getLogger(__name__)

# FR-003 Compliance: Associational Analysis Warning
ASSOCIATIONAL_CAUTION = "Associational analysis only; not causal"

def aggregate_to_stimulus_level(data: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate data to the Stimulus level (mean response time per stimulus per participant).
    Ensures within-stimulus variance is preserved for modeling.
    """
    logger.info("Aggregating data to stimulus level...")
    # Ensure necessary columns exist
    required_cols = ['response_time', 'stimulus_id', 'participant_id', 'prime_valence', 'stimulus_ambiguity']
    missing = [c for c in required_cols if c not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns for aggregation: {missing}")

    # Group by stimulus and participant to calculate mean RT
    # We also need to preserve the prime_valence and ambiguity which should be constant per stimulus
    agg_data = data.groupby(['stimulus_id', 'participant_id']).agg({
        'response_time': 'mean',
        'prime_valence': 'first',
        'stimulus_ambiguity': 'first'
    }).reset_index()

    logger.info(f"Aggregated data shape: {agg_data.shape}")
    return agg_data

def fit_lmm_with_retry(data: pd.DataFrame) -> Tuple[Optional[MixedLM], Dict[str, Any]]:
    """
    Fit Linear Mixed-Effects Model with retry logic for different optimizers.
    Formula: mean_response_time ~ prime_valence * stimulus_ambiguity + (1 | participant_id)
    
    Returns:
        Tuple of (fitted_model, result_dict)
        result_dict includes 'caution_note' per FR-003.
    """
    logger.info("Fitting Linear Mixed-Effects Model...")
    
    # Prepare formula
    # Note: Assuming prime_valence and stimulus_ambiguity are numeric or appropriately encoded
    formula = "response_time ~ prime_valence * stimulus_ambiguity"
    groups = "participant_id"
    
    # Ensure numeric types for fixed effects if they are categorical
    # For simplicity in this implementation, we assume they are already numeric or dummy-encoded.
    # If they are strings, statsmodels might handle them, but explicit conversion is safer.
    for col in ['prime_valence', 'stimulus_ambiguity']:
        if data[col].dtype == 'object':
            data[col] = pd.Categorical(data[col]).codes
    
    # Prepare data for statsmodels (dropna)
    model_data = data.dropna(subset=['response_time', 'prime_valence', 'stimulus_ambiguity', 'participant_id'])
    
    if len(model_data) == 0:
        raise ValueError("No valid data remaining after dropping NaNs for LMM fitting.")

    optimizers = ['bfgs', 'lbfgs', 'cg', 'ncg']
    model = None
    result = None
    last_error = None
    
    for opt in optimizers:
        try:
            logger.info(f"Attempting LMM fit with optimizer: {opt}")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model = MixedLM.from_formula(formula, groups=model_data[groups], re_formula="1", data=model_data)
                result = model.fit(method=opt)
            
            if result.converged:
                logger.info(f"Model converged successfully with optimizer: {opt}")
                break
            else:
                logger.warning(f"Model did not converge with optimizer: {opt}, trying next.")
                result = None
        except Exception as e:
            last_error = e
            logger.warning(f"Fit failed with optimizer {opt}: {e}")
            continue

    if result is None:
        logger.error("LMM failed to converge with any available optimizer.")
        if last_error:
            raise RuntimeError(f"LMM convergence failed after all retries. Last error: {last_error}")
        else:
            raise RuntimeError("LMM convergence failed after all retries.")

    # Prepare result dictionary
    # FR-003: Ensure findings are framed as associational
    result_dict = {
        "model": result,
        "summary": result.summary().as_text(),
        "params": result.params.to_dict(),
        "converged": result.converged,
        "caution_note": ASSOCIATIONAL_CAUTION
    }
    
    # Log the caution note explicitly
    logger.info(f"Model fitting complete. {ASSOCIATIONAL_CAUTION}")
    
    return model, result_dict

def run_lmm_analysis(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Main entry point for running LMM analysis on processed data.
    
    Args:
        input_path: Path to the aggregated data CSV (e.g., from T024 output).
        output_path: Path to save the results JSON.
        
    Returns:
        Dictionary containing model results and the associational caution note.
    """
    logger.info(f"Starting LMM analysis pipeline. Input: {input_path}, Output: {output_path}")
    
    # Load data
    df = pd.read_csv(input_path)
    
    # Aggregate if not already done (T024 logic can be embedded here or called separately)
    # Assuming input is already aggregated as per T024 description
    if 'response_time' not in df.columns:
        logger.warning("Response time column not found, checking for raw data...")
        df = aggregate_to_stimulus_level(df)
    
    # Fit model
    _, result_dict = fit_lmm_with_retry(df)
    
    # Save results
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert numpy types to python native for JSON serialization
    serializable_params = {}
    for k, v in result_dict['params'].items():
        serializable_params[k] = float(v)
    
    result_dict['params'] = serializable_params
    
    import json
    with open(output_file, 'w') as f:
        json.dump(result_dict, f, indent=2)
        
    logger.info(f"LMM analysis complete. Results saved to {output_path}")
    logger.info(f"Caution: {result_dict['caution_note']}")
    
    return result_dict

def main():
    """CLI entry point for LMM analysis."""
    logging.basicConfig(level=logging.INFO)
    
    # Default paths based on project structure
    input_file = str(Path(Config.DATA_PROCESSED) / "aggregated_trials.csv")
    output_file = str(Path(Config.DATA_PROCESSED) / "lmm_results.json")
    
    # Check if input exists
    if not Path(input_file).exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please run T024 (aggregation) first.")
        return 1
    
    try:
        run_lmm_analysis(input_file, output_file)
        return 0
    except Exception as e:
        logger.error(f"LMM analysis failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
