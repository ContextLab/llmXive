import logging
from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.genmod.generalized_estimating_equations import GEE
from statsmodels.discrete.discrete_model import Logit
from statsmodels.base.model import GenericLikelihoodModel
import json
from pathlib import Path

# Import existing utilities from other modules
from config import get_project_paths
from logging_config import get_project_logger

logger = get_project_logger("analysis")

def detect_outcome_type(df: pd.DataFrame, column: str = "prosocial_amount") -> str:
    """
    Detects if the outcome column is binary (0/1) or continuous.
    Returns 'binary' or 'continuous'.
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in dataframe")
    
    unique_vals = df[column].dropna().unique()
    if len(unique_vals) == 2 and set(unique_vals) == {0, 1}:
        return "binary"
    return "continuous"

def get_model_config(outcome_type: str) -> Dict[str, Any]:
    """
    Returns model configuration based on outcome type.
    """
    if outcome_type == "binary":
        return {
            "model_type": "logistic",
            "family": "binomial",
            "link": "logit"
        }
    else:
        return {
            "model_type": "zig",
            "zero_inflation": True,
            "distribution": "gamma"
        }

def fit_zig_model(df: pd.DataFrame, outcome: str = "prosocial_amount", 
                  predictor: str = "condition", 
                  covariates: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Fits a Zero-Inflated Gamma model.
    Since statsmodels doesn't have a native ZIG with Gamma, we implement
    a two-stage approach or use a custom likelihood if necessary.
    For this implementation, we approximate with a Hurdle-like approach
    or use a GLM with a zero-inflation offset if available, otherwise
    we fit two separate models: one for zero vs non-zero (Logit) and
    one for positive values (Gamma GLM).
    
    Returns a dictionary with coefficients for both components.
    """
    if covariates is None:
        covariates = []
    
    # Separate data
    zeros = df[df[outcome] == 0]
    positives = df[df[outcome] > 0]
    
    result = {
        "zero_inflation": {},
        "positive_outcome": {},
        "sample_sizes": {
            "total": len(df),
            "zeros": len(zeros),
            "positives": len(positives)
        }
    }
    
    # 1. Zero Inflation Component (Logistic Regression)
    # Binary target: 1 if zero, 0 if positive
    df_zi = df.copy()
    df_zi['is_zero'] = (df_zi[outcome] == 0).astype(int)
    
    formula_zi = f"is_zero ~ {predictor}"
    if covariates:
        formula_zi += f" + {' + '.join(covariates)}"
    
    try:
        zi_model = Logit.from_formula(formula_zi, data=df_zi).fit(disp=False)
        result["zero_inflation"] = {
            "coefficients": zi_model.params.to_dict(),
            "pvalues": zi_model.pvalues.to_dict(),
            "converged": zi_model.converged
        }
    except Exception as e:
        logger.warning(f"Zero inflation model failed: {e}")
        result["zero_inflation"] = {"error": str(e)}

    # 2. Positive Outcome Component (Gamma GLM)
    if len(positives) > 0:
        formula_pos = f"{outcome} ~ {predictor}"
        if covariates:
            formula_pos += f" + {' + '.join(covariates)}"
        
        try:
            # Gamma family with log link
            pos_model = GLM.from_formula(
                formula_pos, 
                data=positives, 
                family=statsmodels.genmod.families.Gamma(link=statsmodels.genmod.families.links.log())
            ).fit()
            result["positive_outcome"] = {
                "coefficients": pos_model.params.to_dict(),
                "pvalues": pos_model.pvalues.to_dict(),
                "converged": pos_model.converged
            }
        except Exception as e:
            logger.warning(f"Positive outcome model failed: {e}")
            result["positive_outcome"] = {"error": str(e)}
    else:
        result["positive_outcome"] = {"error": "No positive values to model"}

    return result

def fit_logistic_regression(df: pd.DataFrame, outcome: str = "prosocial_amount", 
                            predictor: str = "condition", 
                            covariates: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Fits a standard Logistic Regression for binary outcomes.
    """
    if covariates is None:
        covariates = []
    
    formula = f"{outcome} ~ {predictor}"
    if covariates:
        formula += f" + {' + '.join(covariates)}"
    
    try:
        model = Logit.from_formula(formula, data=df).fit(disp=False)
        return {
            "coefficients": model.params.to_dict(),
            "pvalues": model.pvalues.to_dict(),
            "converged": model.converged
        }
    except Exception as e:
        logger.error(f"Logistic regression failed: {e}")
        return {"error": str(e)}

def extract_zig_coefficients(model_result: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
    """
    Extracts the primary coefficients from a ZIG model result.
    Returns (zero_inflation_coef, positive_outcome_coef) for the predictor.
    """
    predictor_coef = None
    zero_coef = None
    
    if "zero_inflation" in model_result and "coefficients" in model_result["zero_inflation"]:
        # Assuming 'condition' is the key, or we need to find the predictor
        # This is a simplification; in reality, we'd look for the specific predictor name
        if "condition" in model_result["zero_inflation"]["coefficients"]:
            zero_coef = model_result["zero_inflation"]["coefficients"]["condition"]
    
    if "positive_outcome" in model_result and "coefficients" in model_result["positive_outcome"]:
        if "condition" in model_result["positive_outcome"]["coefficients"]:
            predictor_coef = model_result["positive_outcome"]["coefficients"]["condition"]
    
    return zero_coef, predictor_coef

def extract_logistic_coefficients(model_result: Dict[str, Any]) -> Optional[float]:
    """
    Extracts the primary coefficient from a logistic model result.
    """
    if "coefficients" in model_result and "condition" in model_result["coefficients"]:
        return model_result["coefficients"]["condition"]
    return None

def analyze_pool(df: pd.DataFrame, pool_name: str = "causal") -> Dict[str, Any]:
    """
    Analyzes a single pool of data (causal or associational).
    """
    outcome_type = detect_outcome_type(df)
    config = get_model_config(outcome_type)
    
    results = {
        "pool": pool_name,
        "outcome_type": outcome_type,
        "n_studies": 1, # This would be aggregated later if multiple studies
        "sample_size": len(df),
        "model_results": None
    }
    
    if outcome_type == "binary":
        results["model_results"] = fit_logistic_regression(df)
    else:
        results["model_results"] = fit_zig_model(df)
        
    return results

def run_meta_analysis(pool_results: List[Dict[str, Any]], pool_name: str) -> Dict[str, Any]:
    """
    Performs a random-effects meta-analysis on the results from a pool.
    This is a simplified implementation. In a real scenario, we would extract
    effect sizes (e.g., log-odds ratios) and standard errors from each study.
    Here we assume each item in pool_results is a study result.
    """
    if not pool_results:
        return {"error": "No results to meta-analyze"}
    
    # For this implementation, we will aggregate the coefficients if available.
    # A proper meta-analysis requires effect sizes and SEs from each study.
    # We will simulate the aggregation logic here for the "Insufficient Causal Data" task.
    
    coefficients = []
    for res in pool_results:
        if "model_results" in res:
            if "zero_inflation" in res["model_results"] and "coefficients" in res["model_results"]["zero_inflation"]:
                # Collect condition coefficient from zero inflation
                if "condition" in res["model_results"]["zero_inflation"]["coefficients"]:
                    coefficients.append(res["model_results"]["zero_inflation"]["coefficients"]["condition"])
            if "positive_outcome" in res["model_results"] and "coefficients" in res["model_results"]["positive_outcome"]:
                if "condition" in res["model_results"]["positive_outcome"]["coefficients"]:
                    coefficients.append(res["model_results"]["positive_outcome"]["coefficients"]["condition"])
    
    if not coefficients:
        return {"error": "No coefficients found for meta-analysis"}
    
    # Simple mean as a placeholder for random-effects (requires SEs for true RE)
    mean_effect = np.mean(coefficients)
    se_effect = np.std(coefficients) / np.sqrt(len(coefficients)) if len(coefficients) > 1 else 0
    
    return {
        "pool": pool_name,
        "n_studies": len(coefficients),
        "mean_effect": mean_effect,
        "se_effect": se_effect,
        "coefficients": coefficients
    }

def check_causal_data_sufficiency(causal_results: List[Dict[str, Any]], threshold: int = 3) -> Dict[str, Any]:
    """
    T029 Implementation: Checks if the Causal Pool has sufficient datasets.
    If < 3 datasets, reports status but allows continuation with Associational Pool.
    """
    n_causal = len(causal_results)
    is_sufficient = n_causal >= threshold
    
    status_msg = "Sufficient causal data" if is_sufficient else "Insufficient causal data"
    
    report = {
        "task_id": "T029",
        "check": "Causal Pool Sufficiency",
        "threshold": threshold,
        "n_causal_studies": n_causal,
        "is_sufficient": is_sufficient,
        "status": status_msg,
        "action": "Continue with Associational Pool" if not is_sufficient else "Proceed with Causal Meta-Analysis"
    }
    
    logger.info(f"Causal Data Check: {status_msg} ({n_causal} >= {threshold})")
    
    # Write to a status log file for the pipeline
    paths = get_project_paths()
    status_file = paths["processed"] / "causal_data_sufficiency.json"
    
    try:
        with open(status_file, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Wrote causal data sufficiency report to {status_file}")
    except Exception as e:
        logger.error(f"Failed to write status file: {e}")
    
    return report

# The rest of the file (if any) would continue here...
# Note: The function names above match the API surface provided in the prompt.
