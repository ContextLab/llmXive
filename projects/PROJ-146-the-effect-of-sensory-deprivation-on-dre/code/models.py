import os
import sys
import logging
import json
import warnings
from typing import Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.genmod import families
from statsmodels.robust import robust_linear_model
from statsmodels.robust.robust_linear_model import RLM
from statsmodels.robust.norms import HuberT
from statsmodels.miscmodels.ordinal_model import OrderedModel
import yaml

# Import logging setup from sibling module
from logging_config import setup_logging

logger = logging.getLogger(__name__)

def load_protocol(protocol_path: str = "data/protocols/protocol.yaml") -> Dict[str, Any]:
    """Load simulation parameters from protocol.yaml."""
    if not os.path.exists(protocol_path):
        raise FileNotFoundError(f"Protocol file not found: {protocol_path}")
    with open(protocol_path, 'r') as f:
        return yaml.safe_load(f)

def fit_logistic_mixed(df: pd.DataFrame, condition_col: str = 'condition', 
                       outcome_col: str = 'recall', 
                       random_effects_col: str = 'participant_id',
                       use_fallback: bool = False) -> Dict[str, Any]:
    """
    Fit a logistic regression model for dream recall.
    
    If use_fallback is True or sample size is small, falls back to fixed-effects.
    """
    # T026: Check sample size
    n_samples = len(df)
    if n_samples < 10:
        msg = f"Sample size ({n_samples}) is less than 10. Falling back to fixed-effects logistic regression."
        warnings.warn(msg)
        logger.warning(msg)
        use_fallback = True

    if use_fallback:
        logger.info("Using fixed-effects logistic regression (GLM) as fallback.")
        # Fixed effects logistic regression using GLM
        X = sm.add_constant(df[condition_col].astype('category').codes)
        y = df[outcome_col]
        
        # Use Firth-like penalization if available, otherwise standard GLM
        # statsmodels GLM doesn't have native Firth, but we can use a simple penalized approach
        # or just standard GLM with caution
        model = GLM(y, X, family=families.Binomial())
        try:
            result = model.fit()
        except Exception as e:
            logger.error(f"GLM fit failed: {e}. Using simpler approach.")
            # Fallback to simple logistic regression if GLM fails
            from sklearn.linear_model import LogisticRegression
            clf = LogisticRegression()
            clf.fit(X, y)
            return {
                "model_type": "logistic_fallback_sklearn",
                "coefficients": clf.coef_[0].tolist(),
                "intercept": float(clf.intercept_[0]),
                "warning": "Used sklearn fallback due to statsmodels GLM failure"
            }
        
        return {
            "model_type": "logistic_glm_fallback",
            "coefficients": result.params.tolist(),
            "std_errors": result.bse.tolist(),
            "p_values": result.pvalues.tolist(),
            "n_samples": n_samples,
            "warning": f"Used fixed-effects fallback due to small sample size (N={n_samples})"
        }

    # For true mixed-effects, we would use statsmodels MixedLM, but it doesn't support binomial directly
    # So we use a group-by approach or approximations
    # For now, we'll use a fixed-effects model with cluster-robust standard errors if possible
    # or fall back to the same logic as above
    logger.info("Attempting mixed-effects approximation (fixed-effects with clustering).")
    # This is a simplified approach; a true mixed-effects logistic would require more complex setup
    X = sm.add_constant(df[condition_col].astype('category').codes)
    y = df[outcome_col]
    
    model = GLM(y, X, family=families.Binomial())
    try:
        result = model.fit()
        # In a real scenario, we'd compute cluster-robust SEs here
        return {
            "model_type": "logistic_approx",
            "coefficients": result.params.tolist(),
            "std_errors": result.bse.tolist(),
            "p_values": result.pvalues.tolist(),
            "n_samples": n_samples
        }
    except Exception as e:
        logger.error(f"Mixed-effects approximation failed: {e}")
        return fit_logistic_mixed(df, condition_col, outcome_col, random_effects_col, use_fallback=True)

def fit_linear_mixed(df: pd.DataFrame, condition_col: str = 'condition',
                     outcome_col: str = 'bizarreness',
                     random_effects_col: str = 'participant_id',
                     use_fallback: bool = False) -> Dict[str, Any]:
    """
    Fit a linear mixed model for dream bizarreness.
    
    Uses RLM with HuberT as a robust approximation if mixed-effects is not feasible.
    """
    n_samples = len(df)
    if n_samples < 10:
        msg = f"Sample size ({n_samples}) is less than 10. Falling back to robust linear model."
        warnings.warn(msg)
        logger.warning(msg)
        use_fallback = True

    if use_fallback:
        logger.info("Using robust linear model (RLM) as fallback.")
        X = sm.add_constant(df[condition_col].astype('category').codes)
        y = df[outcome_col]
        
        rlm = RLM(y, X, M=HuberT())
        try:
            result = rlm.fit()
            return {
                "model_type": "linear_robust_fallback",
                "coefficients": result.params.tolist(),
                "std_errors": result.bse.tolist(),
                "p_values": None, # RLM doesn't provide p-values directly
                "n_samples": n_samples,
                "warning": f"Used robust linear model fallback due to small sample size (N={n_samples})"
            }
        except Exception as e:
            logger.error(f"RLM fit failed: {e}")
            # Fallback to OLS
            from statsmodels.regression.linear_model import OLS
            ols_model = OLS(y, X)
            ols_result = ols_model.fit()
            return {
                "model_type": "linear_ols_fallback",
                "coefficients": ols_result.params.tolist(),
                "std_errors": ols_result.bse.tolist(),
                "p_values": ols_result.pvalues.tolist(),
                "n_samples": n_samples,
                "warning": "Used OLS fallback due to RLM failure"
            }

    # Attempt mixed-effects linear model
    # statsmodels MixedLM requires specific setup
    try:
        from statsmodels.regression.mixed_linear_model import MixedLM
        groups = df[random_effects_col]
        X = sm.add_constant(df[condition_col].astype('category').codes)
        y = df[outcome_col]
        
        # Fit mixed model
        mixed_model = MixedLM(y, X, groups=groups)
        mixed_result = mixed_model.fit()
        
        return {
            "model_type": "linear_mixed",
            "coefficients": mixed_result.params.tolist(),
            "std_errors": mixed_result.bse.tolist(),
            "p_values": mixed_result.pvalues.tolist(),
            "n_samples": n_samples
        }
    except Exception as e:
        logger.warning(f"Mixed-effects linear model failed: {e}. Using fallback.")
        return fit_linear_mixed(df, condition_col, outcome_col, random_effects_col, use_fallback=True)

def fit_ordinal_approx(df: pd.DataFrame, condition_col: str = 'condition',
                       outcome_col: str = 'bizarreness',
                       use_fallback: bool = False) -> Dict[str, Any]:
    """
    Fit an ordered model as a fixed-effects approximation.
    """
    n_samples = len(df)
    if n_samples < 10:
        msg = f"Sample size ({n_samples}) is less than 10. Falling back to ordered model with caution."
        warnings.warn(msg)
        logger.warning(msg)

    X = sm.add_constant(df[condition_col].astype('category').codes)
    y = df[outcome_col]

    try:
        ordinal_model = OrderedModel(y, X, dist='logit')
        result = ordinal_model.fit(method='bfgs')
        
        return {
            "model_type": "ordinal_fixed_effects",
            "coefficients": result.params.tolist(),
            "std_errors": result.bse.tolist(),
            "p_values": result.pvalues.tolist(),
            "n_samples": n_samples,
            "warning": "Fixed-effects approximation (not mixed-effects)" if n_samples < 30 else None
        }
    except Exception as e:
        logger.error(f"Ordinal model fit failed: {e}")
        return {
            "model_type": "ordinal_failed",
            "error": str(e),
            "n_samples": n_samples
        }

def validate_ordinal_approx(df: pd.DataFrame, true_effect: float) -> Dict[str, Any]:
    """
    Validate the ordinal approximation against known ground truth.
    """
    result = fit_ordinal_approx(df)
    if result["model_type"] == "ordinal_failed":
        return {"valid": False, "error": result["error"]}
    
    estimated_effect = result["coefficients"][1] if len(result["coefficients"]) > 1 else 0
    error = abs(estimated_effect - true_effect)
    
    return {
        "valid": error < 0.5, # Arbitrary threshold for validation
        "estimated_effect": estimated_effect,
        "true_effect": true_effect,
        "absolute_error": error
    }

def run_analysis_pipeline(df: pd.DataFrame, protocol: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the full analysis pipeline: logistic, linear, and ordinal models.
    """
    results = {}
    
    # Logistic model for recall
    results["recall_model"] = fit_logistic_mixed(
        df, 
        condition_col='condition', 
        outcome_col='recall',
        random_effects_col='participant_id'
    )
    
    # Linear model for bizarreness
    results["bizarreness_model"] = fit_linear_mixed(
        df,
        condition_col='condition',
        outcome_col='bizarreness',
        random_effects_col='participant_id'
    )
    
    # Ordinal approximation for bizarreness
    results["ordinal_model"] = fit_ordinal_approx(
        df,
        condition_col='condition',
        outcome_col='bizarreness'
    )
    
    return results

def main():
    """
    Main entry point for running the analysis on processed data.
    """
    setup_logging()
    logger.info("Starting model analysis pipeline.")
    
    # Load protocol
    protocol = load_protocol()
    
    # Determine input file based on threshold
    # This would be called by a script that passes the specific data file
    data_file = os.environ.get("INPUT_DATA_FILE", "data/processed/data_threshold_strict.csv")
    
    if not os.path.exists(data_file):
        logger.error(f"Data file not found: {data_file}")
        sys.exit(1)
    
    df = pd.read_csv(data_file)
    logger.info(f"Loaded data from {data_file} with {len(df)} rows.")
    
    # Run analysis
    results = run_analysis_pipeline(df, protocol)
    
    # Serialize results
    output_dir = "results/models"
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, f"results_{os.path.basename(data_file).replace('.csv', '')}.json")
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Results saved to {output_file}")
    print(json.dumps(results, indent=2, default=str))

if __name__ == "__main__":
    main()