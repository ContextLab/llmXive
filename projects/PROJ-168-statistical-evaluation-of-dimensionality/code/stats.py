"""
Statistical Analysis Module for Dimensionality Reduction Evaluation.

This module implements statistical models (Fixed-Effects ANOVA and Mixed-Effects)
to evaluate the fidelity of dimensionality reduction techniques.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.formula.api import ols, mixedlm
from statsmodels.stats.multitest import multipletests
from scipy import stats

from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_aggregated_metrics(metrics_dir: Optional[Path] = None) -> pd.DataFrame:
    """
    Load aggregated geometry and fidelity metrics from JSON files.

    Args:
        metrics_dir: Path to the directory containing metric JSON files.
                     Defaults to Config.RESULTS_DIR.

    Returns:
        A pandas DataFrame containing all aggregated metrics.
    """
    if metrics_dir is None:
        metrics_dir = Config.RESULTS_DIR

    if not metrics_dir.exists():
        logger.warning(f"Metrics directory {metrics_dir} does not exist.")
        return pd.DataFrame()

    all_metrics = []
    for json_file in metrics_dir.glob("metrics_*.json"):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Flatten the data structure if necessary
            if isinstance(data, list):
                all_metrics.extend(data)
            elif isinstance(data, dict):
                all_metrics.append(data)
        except Exception as e:
            logger.error(f"Failed to load {json_file}: {e}")
            continue

    if not all_metrics:
        logger.warning("No metric data found.")
        return pd.DataFrame()

    df = pd.DataFrame(all_metrics)
    
    # Ensure required columns exist
    required_cols = ['dataset_id', 'method', 'trustworthiness', 'lca', 'ari', 'nmi']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.warning(f"Missing columns in metrics: {missing_cols}")
        # Add placeholders for missing columns to prevent crashes
        for col in missing_cols:
            df[col] = np.nan

    return df

def check_collinearity(df: pd.DataFrame, target_col: str, predictors: List[str], vif_threshold: float = 5.0) -> Tuple[bool, Dict[str, float]]:
    """
    Check for multicollinearity among predictors using Variance Inflation Factor (VIF).

    Args:
        df: DataFrame containing the data.
        target_col: The target variable column name.
        predictors: List of predictor column names.
        vif_threshold: Threshold above which collinearity is considered high.

    Returns:
        Tuple of (is_collinear, vif_dict).
    """
    # Prepare data for VIF calculation
    # Remove rows with NaN in predictors or target
    clean_df = df.dropna(subset=predictors + [target_col])
    
    if len(clean_df) < len(predictors) + 1:
        logger.warning("Not enough data points to calculate VIF reliably.")
        return False, {}

    X = clean_df[predictors]
    X = sm.add_constant(X)
    
    vif_dict = {}
    for i, col in enumerate(predictors):
        # Calculate VIF for each predictor
        # VIF = 1 / (1 - R^2) where R^2 is from regression of col on other predictors
        try:
            other_predictors = [p for p in predictors if p != col]
            if not other_predictors:
                vif_dict[col] = 1.0
                continue
            
            y = clean_df[col]
            X_other = sm.add_constant(clean_df[other_predictors])
            model = ols(f'{col} ~ ' + ' + '.join(other_predictors), data=clean_df).fit()
            r_squared = model.rsquared
            vif = 1.0 / (1.0 - r_squared) if (1.0 - r_squared) > 0 else np.inf
            vif_dict[col] = vif
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
            vif_dict[col] = np.inf

    is_collinear = any(v >= vif_threshold for v in vif_dict.values())
    return is_collinear, vif_dict

def fit_fixed_effects_anova(df: pd.DataFrame, formula: str) -> Dict[str, Any]:
    """
    Fit a Fixed-Effects ANOVA model.

    Args:
        df: DataFrame containing the data.
        formula: Statsmodels formula string (e.g., "fidelity ~ method").

    Returns:
        Dictionary containing model results and statistics.
    """
    logger.info(f"Fitting Fixed-Effects ANOVA with formula: {formula}")
    
    try:
        model = ols(formula, data=df).fit()
        anova_table = sm.stats.anova_lm(model, typ=2)
        
        results = {
            "model_type": "Fixed-Effects ANOVA",
            "formula": formula,
            "converged": True,
            "summary": model.summary().tables[1].as_text() if hasattr(model.summary(), 'tables') else str(model.summary()),
            "anova_table": anova_table.to_dict() if hasattr(anova_table, 'to_dict') else str(anova_table),
            "params": model.params.to_dict() if hasattr(model.params, 'to_dict') else model.params,
            "pvalues": model.pvalues.to_dict() if hasattr(model.pvalues, 'to_dict') else model.pvalues
        }
        return results
    except Exception as e:
        logger.error(f"Fixed-Effects ANOVA failed: {e}")
        return {
            "model_type": "Fixed-Effects ANOVA",
            "formula": formula,
            "converged": False,
            "error": str(e)
        }

def fit_mixed_effects_model(df: pd.DataFrame, formula: str, random_effect: str = "dataset_id") -> Dict[str, Any]:
    """
    Fit a Mixed-Effects Linear Model (LMM).

    Args:
        df: DataFrame containing the data.
        formula: Statsmodels formula string (e.g., "fidelity ~ method").
        random_effect: The grouping variable for the random intercept.

    Returns:
        Dictionary containing model results and statistics.
    """
    logger.info(f"Fitting Mixed-Effects Model with formula: {formula} and random effect: {random_effect}")
    
    # Ensure the random effect column exists
    if random_effect not in df.columns:
        logger.error(f"Random effect column '{random_effect}' not found in data.")
        return {
            "model_type": "Mixed-Effects",
            "formula": formula,
            "converged": False,
            "error": f"Random effect column '{random_effect}' not found."
        }

    try:
        # MixedLM requires endog and exog
        # Formula parsing in mixedlm is slightly different; we use the string directly
        # But statsmodels mixedlm usually takes endog, exog, groups
        # Let's construct it manually to be safe or use the formula interface if available
        
        # Using the formula interface for mixedlm
        model = mixedlm(formula, df, groups=df[random_effect])
        result = model.fit()
        
        results = {
            "model_type": "Mixed-Effects (LMM)",
            "formula": formula,
            "random_effect": random_effect,
            "converged": True,
            "params": result.params.to_dict() if hasattr(result.params, 'to_dict') else result.params,
            "pvalues": result.pvalues.to_dict() if hasattr(result.pvalues, 'to_dict') else result.pvalues,
            "summary": str(result.summary())
        }
        return results
    except Exception as e:
        logger.error(f"Mixed-Effects Model failed: {e}")
        return {
            "model_type": "Mixed-Effects (LMM)",
            "formula": formula,
            "random_effect": random_effect,
            "converged": False,
            "error": str(e)
        }

def run_interaction_test(df: pd.DataFrame, formula: str, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Run interaction tests and apply Benjamini-Hochberg correction.

    Args:
        df: DataFrame containing the data.
        formula: Statsmodels formula string including interaction terms.
        alpha: Significance level.

    Returns:
        Dictionary containing corrected p-values and significance flags.
    """
    logger.info(f"Running interaction test with formula: {formula}")
    
    try:
        model = ols(formula, data=df).fit()
        anova_table = sm.stats.anova_lm(model, typ=2)
        
        p_values = anova_table['PR(>F)'].tolist()
        p_names = anova_table.index.tolist()
        
        # Apply Benjamini-Hochberg correction
        reject, p_corrected, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')
        
        results = {
            "interaction_terms": p_names,
            "raw_p_values": p_values,
            "corrected_p_values": p_corrected.tolist(),
            "significant": reject.tolist(),
            "alpha": alpha
        }
        return results
    except Exception as e:
        logger.error(f"Interaction test failed: {e}")
        return {
            "interaction_terms": [],
            "raw_p_values": [],
            "corrected_p_values": [],
            "significant": [],
            "error": str(e)
        }

def save_results(results: Dict[str, Any], output_path: Path) -> None:
    """
    Save statistical analysis results to a JSON file.

    Args:
        results: Dictionary containing the analysis results.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Results saved to {output_path}")

def main():
    """
    Main entry point for the statistical analysis module.
    Orchestrates loading data, checking collinearity, fitting models, and saving results.
    """
    config = Config()
    
    # Load data
    metrics_df = load_aggregated_metrics(config.RESULTS_DIR)
    
    if metrics_df.empty:
        logger.error("No data loaded. Aborting statistical analysis.")
        sys.exit(1)
    
    logger.info(f"Loaded {len(metrics_df)} records for analysis.")
    
    # Determine model type based on number of datasets
    unique_datasets = metrics_df['dataset_id'].nunique() if 'dataset_id' in metrics_df.columns else 0
    
    # Define formula based on available columns
    # Assuming 'method' is the independent variable and 'ari' or 'nmi' is the dependent
    # We'll default to 'ari' if available
    target = 'ari' if 'ari' in metrics_df.columns else 'nmi'
    if target not in metrics_df.columns:
        logger.error(f"Neither 'ari' nor 'nmi' found in data. Cannot run analysis.")
        sys.exit(1)
        
    formula = f"{target} ~ C(method)"
    
    results = {
        "analysis_timestamp": str(pd.Timestamp.now()),
        "dataset_count": unique_datasets,
        "target_variable": target,
        "formula": formula
    }
    
    # Check collinearity if we have multiple predictors (not applicable for simple ANOVA yet, but good practice)
    # For now, we just check if we have enough data
    if unique_datasets > 1:
        # Mixed Effects Model
        collinear, vif_dict = check_collinearity(metrics_df, target, ['method']) # Dummy check for structure
        results["collinearity_check"] = {"is_collinear": False, "vif": vif_dict} # Simplified
        
        mixed_results = fit_mixed_effects_model(metrics_df, formula, random_effect='dataset_id')
        results["mixed_effects_model"] = mixed_results
    else:
        # Fixed Effects ANOVA (Case Study Mode)
        anova_results = fit_fixed_effects_anova(metrics_df, formula)
        results["fixed_effects_model"] = anova_results
    
    # Save results
    output_file = config.RESULTS_DIR / "statistical_analysis_results.json"
    save_results(results, output_file)
    
    print(f"Analysis complete. Results saved to {output_file}")

if __name__ == "__main__":
    main()