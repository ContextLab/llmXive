import os
import sys
import json
import logging
import warnings
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.formula.api import mixedlm

# Import from existing API surface
from config import get_paths, load_config
from utils.logging import get_logger

logger = get_logger(__name__)

def load_lmm_results(results_path: Path) -> Dict[str, Any]:
    """
    Load the results from the LMM fitting stage (T032).
    Expects a JSON file containing the fixed effects and statistics for Model A and Model B.
    """
    if not results_path.exists():
        raise FileNotFoundError(f"LMM results file not found: {results_path}")
    
    with open(results_path, 'r') as f:
        return json.load(f)

def compare_model_significance(
    model_a_results: Dict[str, Any],
    model_b_results: Dict[str, Any],
    predictor: str = "salience_score"
) -> Dict[str, Any]:
    """
    Compare the statistical significance of the predictor (salience) between Model A and Model B.
    
    Model A: Random intercepts only.
    Model B: Random intercepts + random slopes for salience.
    
    Returns a dictionary with the comparison metrics.
    """
    # Extract fixed effects for the predictor from both models
    # The structure depends on how T032 writes the results, assuming a standard format:
    # { "model_a": { "fixed_effects": { "salience_score": { "coef": ..., "pvalue": ... } } }, ... }
    
    def get_pvalue(model_data: Dict[str, Any], pred: str) -> Optional[float]:
        try:
            effects = model_data.get("fixed_effects", {})
            if pred in effects:
                return effects[pred].get("pvalue")
            # Fallback for flat structure if T032 output differs
            if f"{pred}_pvalue" in model_data:
                return model_data[f"{pred}_pvalue"]
        except (KeyError, TypeError):
            pass
        return None

    p_a = get_pvalue(model_a_results, predictor)
    p_b = get_pvalue(model_b_results, predictor)

    if p_a is None or p_b is None:
        logger.warning(f"Could not extract p-values for {predictor} from both models. Skipping comparison.")
        return {
            "status": "incomplete",
            "reason": "Missing p-values in LMM results"
        }

    # Determine significance at alpha=0.05
    sig_a = p_a < 0.05
    sig_b = p_b < 0.05

    # Check for change in significance (Robustness check)
    # If it's significant in A but not B, the effect is not robust to random slopes.
    # If it's significant in both, it's robust.
    # If not significant in A, we don't usually claim robustness in B for this specific predictor context.
    
    robust = False
    change_status = "unchanged"
    
    if sig_a and sig_b:
        robust = True
        change_status = "both_significant"
    elif sig_a and not sig_b:
        robust = False
        change_status = "lost_significance_in_B"
    elif not sig_a and sig_b:
        robust = False # Unlikely but handled
        change_status = "gained_significance_in_B"
    else:
        robust = False
        change_status = "neither_significant"

    return {
        "predictor": predictor,
        "model_a_pvalue": p_a,
        "model_b_pvalue": p_b,
        "model_a_significant": sig_a,
        "model_b_significant": sig_b,
        "robust": robust,
        "change_status": change_status
    }

def run_sensitivity_analysis(
    results_path: Path,
    output_path: Path
) -> Dict[str, Any]:
    """
    Main function to perform the sensitivity analysis.
    Compares Model A vs Model B significance for the salience predictor.
    Writes the result to the specified output path.
    """
    logger.info(f"Loading LMM results from {results_path}")
    try:
        full_results = load_lmm_results(results_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        raise

    # T032 likely structures results with keys 'model_a' and 'model_b'
    model_a_data = full_results.get("model_a", {})
    model_b_data = full_results.get("model_b", {})

    comparison = compare_model_significance(model_a_data, model_b_data)
    
    # Add metadata
    comparison["analysis_type"] = "sensitivity_analysis"
    comparison["model_comparison"] = "Model A (Intercept) vs Model B (Intercept + Slope)"
    comparison["timestamp"] = str(pd.Timestamp.now())
    
    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(comparison, f, indent=2)
    
    logger.info(f"Sensitivity analysis complete. Results written to {output_path}")
    logger.info(f"Robustness status: {comparison['robust']} ({comparison['change_status']})")
    
    return comparison

def main():
    """Entry point for the sensitivity analysis script."""
    config = load_config()
    paths = get_paths()
    
    # Paths based on T032 output and T033 requirement
    # Assuming T032 writes to data/processed/results.json or similar
    # The task description says T036 writes final results, but T033 needs LMM results.
    # T032 writes "final AnalysisResult JSON/CSV" -> usually data/processed/results.json
    # However, T033 needs the raw LMM stats to compare. 
    # Let's assume the LMM fit output is at data/interim/lmm_results.json or data/processed/results.json
    # Based on T032 description: "Write final AnalysisResult JSON/CSV to data/processed/results.json"
    # We will look there. If T032 output is intermediate, we might need to adjust, 
    # but the prompt implies T032 is the source of truth for the models.
    
    input_path = paths["data_processed"] / "results.json"
    output_path = paths["data_interim"] / "sensitivity_analysis.json"
    
    # Fallback if results.json isn't ready (e.g. running in dev)
    if not input_path.exists():
        # Check common interim location if T032 wrote there temporarily
        interim_path = paths["data_interim"] / "results.json"
        if interim_path.exists():
            input_path = interim_path
        else:
            logger.error(f"LMM results not found at {input_path} or {interim_path}. Cannot run sensitivity analysis.")
            sys.exit(1)

    try:
        result = run_sensitivity_analysis(input_path, output_path)
        
        # Log specific outcome for the "theories of attentional control hierarchy" (Constitution Principle VII)
        if result.get("robust"):
            logger.info("Sensitivity Analysis: Salience effect is ROBUST across model specifications.")
        else:
            logger.warning("Sensitivity Analysis: Salience effect is NOT robust. Significance depends on random slope specification.")
            
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
