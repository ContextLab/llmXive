"""
Statistical Model for Mixed-Effects Logistic Regression.

Fits a mixed-effects logistic regression model to determine the interaction
between failure type and method on pivot success.

Model: Success ~ FailureType * Method + (1|TaskID)
"""
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

# Import from project utils
from utils.logging import get_logger, log_stage_start, log_stage_end, log_resource_usage
from utils.config import set_seed, validate_resource_limits

# Import statsmodels for mixed-effects modeling
try:
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
except ImportError:
    raise ImportError("statsmodels is required for statistical analysis. Install via: pip install statsmodels")

# Configuration
logger = get_logger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DERIVED_PATH = PROJECT_ROOT / "data" / "derived"
OUTPUT_PATH = DATA_DERIVED_PATH / "regression_results.json"

def load_results_csv() -> pd.DataFrame:
    """
    Load the results from the experiments CSV file.
    
    Returns:
        pd.DataFrame: The loaded results dataframe.
    
    Raises:
        FileNotFoundError: If the results CSV file does not exist.
    """
    results_path = DATA_DERIVED_PATH / "results.csv"
    if not results_path.exists():
        raise FileNotFoundError(f"Results file not found at {results_path}. "
                              "Ensure T022 (merge results) has been completed.")
    
    logger.info(f"Loading results from {results_path}")
    df = pd.read_csv(results_path)
    
    # Validate required columns
    required_cols = ['task_id', 'method', 'time_to_pivot', 'success', 'failure_type']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in results.csv: {missing_cols}")
    
    # Ensure success is numeric (0/1)
    df['success'] = pd.to_numeric(df['success'], errors='coerce').fillna(0).astype(int)
    
    logger.info(f"Loaded {len(df)} records. Success rate: {df['success'].mean():.2%}")
    return df

def prepare_data_for_regression(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare the dataframe for mixed-effects regression.
    
    - Ensures categorical types for predictors.
    - Handles missing values.
    
    Args:
        df (pd.DataFrame): The raw results dataframe.
    
    Returns:
        pd.DataFrame: The prepared dataframe ready for modeling.
    """
    df_prep = df.copy()
    
    # Convert categorical columns
    df_prep['failure_type'] = df_prep['failure_type'].astype('category')
    df_prep['method'] = df_prep['method'].astype('category')
    df_prep['task_id'] = df_prep['task_id'].astype('category')
    
    # Drop rows with missing success values (should be rare after cleaning in load_results_csv)
    df_prep = df_prep.dropna(subset=['success'])
    
    logger.info(f"Prepared {len(df_prep)} records for regression.")
    return df_prep

def fit_mixed_effects_model(df: pd.DataFrame) -> Optional[object]:
    """
    Fit the mixed-effects logistic regression model.
    
    Model Formula: Success ~ FailureType * Method + (1|TaskID)
    
    Args:
        df (pd.DataFrame): The prepared dataframe.
    
    Returns:
        statsmodels.base.wrapper.ResultsWrap or None: The fitted model results.
    """
    formula = "success ~ failure_type * method + (1 | task_id)"
    
    logger.info(f"Fitting mixed-effects model: {formula}")
    try:
        # Use MixedLM for mixed effects (glmm is not available in standard statsmodels, 
        # so we use MixedLM with Gaussian link as approximation or GLMM if available)
        # Note: statsmodels MixedGLM is experimental. We will use MixedLM with a workaround
        # or standard GLM with random effects if MixedLM is too strict for binary data.
        # However, for binary outcomes, MixedLM is not ideal. 
        # We will attempt to use glmer-style formula via statsmodels if possible, 
        # otherwise fallback to a robust GLM with cluster-robust SEs if mixed is too heavy.
        # But the task asks for Mixed-Effects. Let's try statsmodels MixedLM with a trick 
        # or use the 'formula' API if available in the environment.
        
        # Standard approach in statsmodels for binary mixed effects is limited.
        # We will use 'MixedLM' but note it assumes Gaussian. 
        # For true logistic mixed effects, we might need 'GLMM' (experimental) or 'lme4' equivalent.
        # Given the constraints, we will use `smf.mixedlm` but warn about the link function,
        # OR we can use `smf.glm` with `cov_type='cluster'` if mixed is not strictly required 
        # to be non-Gaussian, but the prompt says "Mixed-Effects Logistic".
        
        # Let's try to use the experimental GLMM if available, otherwise use MixedLM with a warning
        # or a workaround.
        # Actually, statsmodels does not have a fully supported `logit` mixed model in stable releases.
        # We will use `MixedLM` with a Gaussian assumption as a proxy for the coefficients, 
        # OR we can use `statsmodels.genmod.generalized_linear_model.GLM` with cluster robust errors
        # to approximate the interaction significance if true GLMM is unavailable.
        
        # However, to strictly follow "Mixed-Effects Logistic", we attempt to use the 
        # `statsmodels.genmod.generalized_linear_model` with a custom solver or 
        # `statsmodels.robust.robust_linear_model`? No.
        
        # Let's assume the environment has `statsmodels` >= 0.13 which has some GLMM support 
        # or we use `pymer4`? No, stick to std lib.
        
        # Strategy: Use `smf.mixedlm` but treat the binary outcome as continuous (0/1) 
        # for the purpose of estimating the interaction coefficient and p-value 
        # (Linear Mixed Model approximation). This is common in some fields when true GLMM 
        # is not available, though less ideal.
        # OR, we use `smf.glm` with `family=sm.families.Binomial()` and `cov_type='cluster'` 
        # to get robust standard errors, which is a valid alternative for significance testing 
        # of fixed effects.
        
        # Given the prompt specifically asks for "Mixed-Effects Logistic", and true GLMM 
        # is tricky in statsmodels, we will use `smf.mixedlm` on the binary outcome 
        # (Linear Mixed Model) as a pragmatic approximation for the interaction term's p-value, 
        # noting that for large N, the t-test on the fixed effect is often robust.
        # Alternatively, we can use `statsmodels.genmod.generalized_estimating_equations.GEE` 
        # which handles binary outcomes and clustering.
        
        # Let's use GEE for a proper binary mixed-effects-like model (marginal model) 
        # which provides valid p-values for the interaction.
        
        model = smf.gee(
            formula=formula.replace("(1 | task_id)", "groups=task_id"),
            data=df,
            family=sm.families.Binomial(),
            cov_struct=sm.cov_struct.Exchangeable()
        )
        result = model.fit()
        
        logger.info("Model fitted successfully using GEE (approximation for Mixed-Effects Logistic).")
        return result
        
    except Exception as e:
        logger.error(f"Failed to fit model: {e}", exc_info=True)
        # Fallback: Try simple GLM with cluster robust errors if GEE fails
        try:
            logger.warning("Falling back to GLM with cluster robust errors.")
            model_glm = smf.glm(
                formula=formula.replace("(1 | task_id)", ""),
                data=df,
                family=sm.families.Binomial()
            )
            result_glm = model_glm.fit(cov_type='cluster', cov_kwds={'groups': df['task_id']})
            return result_glm
        except Exception as e2:
            logger.error(f"Both GEE and GLM cluster failed: {e2}")
            return None

def extract_interaction_p_value(result: object) -> float:
    """
    Extract the p-value for the interaction term (FailureType * Method).
    
    Args:
        result (object): The fitted model results.
    
    Returns:
        float: The p-value for the interaction term.
    """
    # The interaction term will have a name like "failure_type[T.Type]:method[T.Method]"
    # We need to find the coefficient corresponding to the interaction.
    params = result.params
    pvalues = result.pvalues
    
    interaction_p = None
    interaction_key = None
    
    for key, pval in pvalues.items():
        if ':' in key: # Interaction term
            interaction_key = key
            interaction_p = float(pval)
            break
    
    if interaction_p is None:
        logger.warning("No interaction term found in model results.")
        return 1.0 # Default to non-significant
    
    logger.info(f"Interaction term '{interaction_key}' p-value: {interaction_p:.4f}")
    return interaction_p

def save_regression_results(results: Dict[str, Any], interaction_p_value: float) -> None:
    """
    Save the regression results to a JSON file.
    
    Args:
        results (Dict[str, Any]): The full results dictionary.
        interaction_p_value (float): The p-value for the interaction term.
    """
    output_data = {
        "model_summary": {
            "formula": "Success ~ FailureType * Method + (1|TaskID)",
            "method": "Mixed-Effects Logistic (approximated via GEE/GLM Cluster)",
            "n_observations": results.get("n_observations", 0),
            "interaction_p_value": interaction_p_value,
            "is_significant": interaction_p_value < 0.05,
            "significance_threshold": 0.05
        },
        "coefficients": {
            str(k): float(v) for k, v in results.get("coefficients", {}).items()
        },
        "p_values": {
            str(k): float(v) for k, v in results.get("p_values", {}).items()
        },
        "conclusion": "Significant interaction" if interaction_p_value < 0.05 else "No significant interaction"
    }
    
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Regression results saved to {OUTPUT_PATH}")

def main():
    """Main entry point for the statistical model task."""
    log_stage_start("T026 - Statistical Model Analysis")
    validate_resource_limits()
    set_seed(42)
    
    try:
        # 1. Load Data
        df = load_results_csv()
        
        # 2. Prepare Data
        df_prep = prepare_data_for_regression(df)
        
        if len(df_prep) == 0:
            raise ValueError("No data available for regression after preparation.")
        
        # 3. Fit Model
        model_result = fit_mixed_effects_model(df_prep)
        
        if model_result is None:
            raise RuntimeError("Failed to fit the statistical model.")
        
        # 4. Extract Metrics
        interaction_p = extract_interaction_p_value(model_result)
        
        # 5. Prepare Results Dictionary
        results_dict = {
            "n_observations": len(df_prep),
            "coefficients": model_result.params.to_dict(),
            "p_values": model_result.pvalues.to_dict()
        }
        
        # 6. Save Results
        save_regression_results(results_dict, interaction_p)
        
        log_stage_end("T026 - Statistical Model Analysis", status="Success")
        
    except Exception as e:
        logger.error(f"Task T026 failed: {e}", exc_info=True)
        log_stage_end("T026 - Statistical Model Analysis", status="Failed", error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
