"""
Linear Mixed-Effects Model (LMM) implementation for associative analysis.

This module fits LMMs to study the association between prime valence, 
stimulus ambiguity, and response times. All outputs explicitly frame 
findings as "associational" per FR-003, avoiding causal language.
"""
import logging
import warnings
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import numpy as np
from statsmodels.regression.mixed_linear_model import MixedLM
from config import get_path, get_seed, set_seed
import json
from pathlib import Path
import os

logger = logging.getLogger(__name__)

def aggregate_to_stimulus_level(data: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate data to stimulus level (mean response time per stimulus per participant).
    
    This ensures within-stimulus variance is preserved for the LMM.
    
    Args:
        data: DataFrame with trial-level data including response_time, stimulus_id, participant_id.
    
    Returns:
        DataFrame aggregated to stimulus level.
    """
    if data.empty:
        raise ValueError("Input data is empty; cannot aggregate.")
    
    required_cols = ['response_time', 'stimulus_id', 'participant_id']
    missing = [col for col in required_cols if col not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns for aggregation: {missing}")
    
    # Aggregate mean response time per stimulus per participant
    aggregated = data.groupby(['stimulus_id', 'participant_id']).agg({
        'response_time': 'mean',
        'prime_valence': 'first',  # Assuming constant per stimulus
        'stimulus_ambiguity': 'first'
    }).reset_index()
    
    logger.info(f"Aggregated {len(data)} trials to {len(aggregated)} stimulus-participant pairs.")
    return aggregated

def fit_lmm_with_retry(
    data: pd.DataFrame,
    formula: str = "response_time ~ prime_valence * stimulus_ambiguity",
    re_formula: str = "1",
    max_retries: int = 3
) -> Tuple[Optional[MixedLM], Dict[str, Any]]:
    """
    Fit LMM with optimizer retry logic on convergence failure.
    
    All results are framed as associational.
    
    Args:
        data: Aggregated DataFrame.
        formula: Fixed effects formula.
        re_formula: Random effects formula.
        max_retries: Number of optimizer attempts.
    
    Returns:
        Tuple of (fitted model, metadata dict with convergence info).
    """
    if data.empty:
        raise ValueError("Data is empty; cannot fit LMM.")
    
    set_seed(get_seed())
    metadata = {
        "formula": formula,
        "re_formula": re_formula,
        "converged": False,
        "attempts": 0,
        "final_optimizer": None,
        "message": ""
    }
    
    # Define optimizers to try
    optimizers = ['lbfgs', 'bfgs', 'cg', 'newton']
    
    for attempt, optimizer in enumerate(optimizers[:max_retries]):
        metadata["attempts"] = attempt + 1
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                
                # Fit the model
                model = MixedLM.from_formula(
                    formula,
                    data=data,
                    groups="participant_id",
                    re_formula=re_formula
                )
                
                result = model.fit(method=optimizer)
                
                if result.converged:
                    metadata["converged"] = True
                    metadata["final_optimizer"] = optimizer
                    metadata["message"] = "Model converged successfully."
                    logger.info(f"LMM converged on attempt {attempt + 1} with optimizer '{optimizer}'.")
                    return result, metadata
                else:
                    logger.warning(f"LMM attempt {attempt + 1} with '{optimizer}' did not converge.")
                    
        except Exception as e:
            logger.warning(f"LMM attempt {attempt + 1} with '{optimizer}' failed: {str(e)}")
            continue
    
    metadata["message"] = "Model failed to converge after all optimizer attempts."
    logger.error("LMM failed to converge after all optimizer attempts.")
    return None, metadata

def _format_associational_summary(result: MixedLM) -> Dict[str, Any]:
    """
    Format model results with explicit associational language.
    
    Args:
        result: Fitted MixedLM result.
    
    Returns:
        Dictionary of formatted results with associational framing.
    """
    params = result.params
    conf_int = result.conf_int()
    
    formatted = {
        "interpretation_note": "These results describe associations between variables and should not be interpreted as causal effects.",
        "fixed_effects": {}
    }
    
    for param_name, coef in params.items():
        if param_name.startswith("Intercept"):
            continue
        
        # Format associational language
        direction = "positive" if coef > 0 else "negative"
        formatted["fixed_effects"][param_name] = {
            "coefficient": float(coef),
            "std_error": float(conf_int.loc[param_name, 1] - conf_int.loc[param_name, 0]) / 2,
            "direction": direction,
            "interpretation": f"A {direction} association was observed between '{param_name}' and response time.",
            "causal_warning": "This finding is associational; no causal claims are made per FR-003."
        }
    
    return formatted

def run_lmm_analysis(
    input_path: str,
    output_path: str,
    formula: str = "response_time ~ prime_valence * stimulus_ambiguity"
) -> Dict[str, Any]:
    """
    Run full LMM analysis pipeline.
    
    Outputs are explicitly framed as associational.
    
    Args:
        input_path: Path to aggregated data CSV.
        output_path: Path to save results JSON.
        formula: Fixed effects formula.
    
    Returns:
        Analysis results dictionary.
    """
    logger.info(f"Loading data from {input_path}")
    data = pd.read_csv(input_path)
    
    logger.info("Aggregating to stimulus level")
    aggregated = aggregate_to_stimulus_level(data)
    
    logger.info("Fitting LMM with retry logic")
    result, metadata = fit_lmm_with_retry(aggregated, formula=formula)
    
    analysis_results = {
        "status": "success" if result else "failed",
        "metadata": metadata,
        "associational_framing": True,
        "causal_claims": False,
        "formula": formula,
        "interpretation": "All reported effects are associational in nature. No causal inference is implied."
    }
    
    if result:
        analysis_results["results"] = _format_associational_summary(result)
        analysis_results["summary"] = (
            f"The analysis identified {len(result.params) - 1} fixed effects. "
            "These results describe statistical associations between prime valence, stimulus ambiguity, "
            "and response times. Per FR-003, these findings are strictly associational and do not imply causation."
        )
    else:
        analysis_results["error"] = metadata["message"]
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving results to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(analysis_results, f, indent=2)
    
    return analysis_results

def main():
    """Main entry point for LMM analysis."""
    logging.basicConfig(level=logging.INFO)
    
    input_file = get_path("data/processed/linked_trials.csv")
    output_file = get_path("state/lmm_results.json")
    
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        return 1
    
    try:
        results = run_lmm_analysis(input_file, output_file)
        logger.info("LMM analysis completed successfully.")
        logger.info(results["summary"])
        return 0
    except Exception as e:
        logger.error(f"LMM analysis failed: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())
