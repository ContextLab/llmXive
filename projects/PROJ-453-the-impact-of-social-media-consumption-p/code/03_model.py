import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

from logging_config import setup_logging, get_logger
from config import DATA_ROOT, RESULTS_ROOT
from utils import causal_language_scanner

logger = get_logger("model")

def load_schema_contract(schema_path: Path) -> Dict[str, Any]:
    """Load the schema contract from YAML."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    import yaml
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_output_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Validate that the output dictionary matches the schema structure."""
    required_keys = list(schema.get("keys", {}).keys())
    missing = [k for k in required_keys if k not in data]
    if missing:
        raise ValueError(f"Output schema validation failed: Missing keys {missing}")
    return True

def mean_center(series: pd.Series) -> pd.Series:
    """Mean-center a pandas Series."""
    return series - series.mean()

def create_interaction(df: pd.DataFrame, var1: str, var2: str) -> pd.DataFrame:
    """Create an interaction term between two columns."""
    df[f"{var1}_x_{var2}"] = df[var1] * df[var2]
    return df

def calculate_vif(X: pd.DataFrame) -> Dict[str, float]:
    """Calculate Variance Inflation Factor for all predictors."""
    vif_data = {}
    # Add constant for intercept if not present
    if 'Intercept' not in X.columns:
        X_with_const = sm.add_constant(X)
    else:
        X_with_const = X
        
    for i, col in enumerate(X_with_const.columns):
        if col == 'const' or col == 'Intercept':
            continue
        try:
            vif = variance_inflation_factor(X_with_const.values, i)
            vif_data[col] = vif
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
            vif_data[col] = np.nan
    return vif_data

def benjamini_hochberg(p_values: List[float]) -> List[float]:
    """Apply Benjamini-Hochberg FDR correction to a list of p-values."""
    n = len(p_values)
    if n == 0:
        return []
    sorted_indices = sorted(range(n), key=lambda i: p_values[i])
    ranked_p_values = sorted(p_values)
    corrected = []
    for i, p in enumerate(ranked_p_values):
        corrected.append(min(p * n / (i + 1), 1.0))
    # Re-order to match original indices
    final_corrected = [0.0] * n
    for idx, val in zip(sorted_indices, corrected):
        final_corrected[idx] = val
    return final_corrected

def check_collinearity(df: pd.DataFrame, var1: str, var2: str, threshold: float = 0.7) -> Tuple[bool, float]:
    """Check correlation between two variables."""
    if var1 not in df.columns or var2 not in df.columns:
        raise ValueError(f"Columns {var1} or {var2} not found in dataframe")
    
    corr = df[[var1, var2]].corr().iloc[0, 1]
    flag = abs(corr) > threshold
    return flag, corr

def run_model(df: pd.DataFrame, outcome: str, predictors: List[str], 
              include_intercept: bool = True) -> Tuple[Any, Dict[str, Any]]:
    """
    Fit an OLS model and return results.
    Returns: (model_results, diagnostics_dict)
    """
    X = df[predictors]
    y = df[outcome]
    
    if include_intercept:
        X = sm.add_constant(X)
    
    model = sm.OLS(y, X).fit()
    
    # Calculate diagnostics
    vif_scores = calculate_vif(df[predictors])
    
    diagnostics = {
        "vif_scores": vif_scores,
        "r_squared": model.rsquared,
        "adj_r_squared": model.rsquared_adj,
        "f_statistic": model.f_pvalue,
        "coefficients": dict(model.params),
        "p_values": dict(model.pvalues)
    }
    
    return model, diagnostics

def run_sensitivity_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run sensitivity analysis with alternative definitions.
    Returns a DataFrame of results.
    """
    results = []
    
    definitions = [
        ("switching_index", ["switching_index", "total_screen_time", "age"]),
        ("platform_count", ["num_platforms", "total_screen_time", "age"]),
        ("switching_frequency", ["switching_frequency", "total_screen_time", "age"])
    ]
    
    p_values_raw = []
    
    for name, predictors in definitions:
        try:
            # Ensure predictors exist
            available = [p for p in predictors if p in df.columns]
            if len(available) < len(predictors):
                logger.warning(f"Missing predictors for definition {name}, skipping.")
                continue
              
            model, diagnostics = run_model(df, "cognitive_flexibility_score", available)
            
            # Get p-value for the primary predictor
            primary_p = diagnostics["p_values"].get(name, np.nan)
            p_values_raw.append(primary_p)
            
            results.append({
                "definition": name,
                "beta": diagnostics["coefficients"].get(name, np.nan),
                "p_value": primary_p,
                "sign": np.sign(diagnostics["coefficients"].get(name, 0)),
                "n": len(df),
                "fdr_p_value": np.nan # To be filled after correction
            })
        except Exception as e:
            logger.error(f"Error running sensitivity model for {name}: {e}")
            
    if p_values_raw:
        corrected_p = benjamini_hochberg(p_values_raw)
        for i, row in enumerate(results):
            if i < len(corrected_p):
                row["fdr_p_value"] = corrected_p[i]
                
    return pd.DataFrame(results)

def verify_robustness(results_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Verify robustness criteria (SC-003).
    """
    signs = results_df["sign"].tolist()
    p_values = results_df["fdr_p_value"].tolist()
    
    sign_stable = len(set(signs)) == 1
    p_significant = all(p < 0.10 for p in p_values if not np.isnan(p))
    
    status = "PASS" if (sign_stable and p_significant) else "FAIL"
    
    details = results_df.to_dict(orient='records')
    
    return {
        "sc003_status": status,
        "details": details,
        "message": "SC-003 Met: p < 0.10 across operationalizations" if status == "PASS" else "SC-003 FAIL: Sign instability or p > 0.10 detected"
    }

def main():
    """Main entry point for model fitting and diagnostics."""
    logger.info("Starting model fitting pipeline.")
    
    # Paths
    data_path = Path(DATA_ROOT) / "processed" / "participants_cleaned.csv"
    schema_path = Path("contracts/output.schema.yaml")
    output_dir = Path(RESULTS_ROOT) / "models"
    sensitivity_path = Path(RESULTS_ROOT) / "sensitivity_comparison.csv"
    robustness_path = Path(RESULTS_ROOT) / "robustness_eevidence.json"
    
    if not data_path.exists():
        raise FileNotFoundError(f"Cleaned data not found: {data_path}")
    
    df = pd.read_csv(data_path)
    
    # Check Collinearity
    flag, corr = check_collinearity(df, "switching_index", "total_screen_time")
    if flag:
        logger.warning("Potential Mathematical Coupling detected between switching_index and total_screen_time.")
        # Log to specific file
        log_path = Path("logs") / "collinearity_check.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, 'a') as f:
            f.write(f"[{pd.Timestamp.now()}] Potential Mathematical Coupling: correlation={corr:.4f}\n")
        
        # Residual Model Logic (Optional per FR-006)
        # For now, we proceed with primary model but log the flag
        logger.info("Skipping residual model for this run, using primary model with flag.")
    else:
        logger.info("Collinearity check passed (correlation <= 0.7).")
    
    # Primary Model
    predictors = ["switching_index", "total_screen_time", "age"]
    # Ensure columns exist
    predictors = [p for p in predictors if p in df.columns]
    
    model, diagnostics = run_model(df, "cognitive_flexibility_score", predictors)
    
    # Interaction Model (if needed, but spec says optional/conditional)
    # For now, we save the core model
    output_dir.mkdir(parents=True, exist_ok=True)
    core_model_path = output_dir / "core_model.json"
    
    with open(core_model_path, 'w') as f:
        json.dump(diagnostics, f, indent=2, default=str)
    
    logger.info(f"Core model saved to {core_model_path}")
    
    # Sensitivity Analysis
    sens_df = run_sensitivity_analysis(df)
    sens_df.to_csv(sensitivity_path, index=False)
    logger.info(f"Sensitivity analysis saved to {sensitivity_path}")
    
    # Robustness Verification
    robustness = verify_robustness(sens_df)
    robustness_path.parent.mkdir(parents=True, exist_ok=True)
    with open(robustness_path, 'w') as f:
        json.dump(robustness, f, indent=2)
    logger.info(f"Robustness evidence saved to {robustness_path}")
    
    # Final Report (Regression Summary)
    final_report = {
        "coefficients": diagnostics["coefficients"],
        "p_values": diagnostics["p_values"],
        "r_squared": diagnostics["r_squared"],
        "vif_scores": diagnostics["vif_scores"],
        "diagnostics": {
            "vif_scores": diagnostics["vif_scores"],
            "correlation_matrix": df[["switching_index", "total_screen_time", "age"]].corr().to_dict() if "switching_index" in df.columns else {},
            "correlation_flag": flag
        },
        "interpretation": "Associational estimates only. No causal claims are made."
    }
    
    # Validate against schema
    schema = load_schema_contract(schema_path)
    validate_output_schema(final_report, schema)
    
    # Check causal language
    if causal_language_scanner(final_report["interpretation"], ["causes", "leads to", "impacts"]):
        raise ValueError("Causal language detected in interpretation. Failing per FR-004.")
    
    regression_summary_path = output_dir / "regression_summary.json"
    with open(regression_summary_path, 'w') as f:
        json.dump(final_report, f, indent=2, default=str)
    
    logger.info("Model fitting pipeline completed successfully.")

if __name__ == "__main__":
    setup_logging()
    main()
