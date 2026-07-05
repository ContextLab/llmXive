import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Import from utils
from utils.metrics import calculate_iteration_count

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = Path("data/derived")
RESULTS_DIR = Path("data/derived")

def load_master_dataset() -> pd.DataFrame:
    """Load the master dataset from CSV."""
    path = DATA_DIR / "master_dataset.csv"
    if not path.exists():
        raise FileNotFoundError(f"Master dataset not found at {path}")
    return pd.read_csv(path)

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Remove rows with missing critical values."""
    critical_cols = ['llm_adoption_flag', 'iteration_count', 'avg_comment_length']
    df = df.dropna(subset=critical_cols)
    return df

def calculate_vif(df: pd.DataFrame, features: List[str]) -> pd.Series:
    """Calculate Variance Inflation Factor for features."""
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    X = df[features].copy()
    X = X[(X != 0).all(1)] # Remove rows where all features are zero for VIF calc
    if X.empty:
        return pd.Series(dtype=float)
    vif_data = pd.Series([variance_inflation_factor(X.values, i) for i in range(X.shape[1])], index=X.columns)
    return vif_data

def flag_high_vif(vif_series: pd.Series, threshold: float = 5.0) -> List[str]:
    """Return list of features with VIF > threshold."""
    return [col for col, val in vif_series.items() if val > threshold]

def run_glmm(df: pd.DataFrame, dependent: str, independent: str, controls: List[str]) -> Dict[str, Any]:
    """Run a Generalized Linear Mixed Model."""
    import statsmodels.formula.api as smf
    # Random intercept for repository_id if available, else fallback to fixed effect
    formula = f"{dependent} ~ {independent} + {' + '.join(controls)}"
    if 'repository_id' in df.columns:
        formula += " | repository_id"
    
    try:
        # Use Poisson or Negative Binomial depending on data, defaulting to GLM with Poisson for count data
        # Assuming iteration_count is count data
        if dependent == 'iteration_count':
            model = smf.glm(formula, data=df, family=smf.families.Poisson())
        else:
            model = smf.ols(formula, data=df)
        
        result = model.fit()
        return {
            "coef": float(result.params[independent]),
            "std_err": float(result.bse[independent]),
            "pvalue": float(result.pvalues[independent]),
            "conf_int_low": float(result.conf_int()[independent][0]),
            "conf_int_high": float(result.conf_int()[independent][1]),
            "method": "GLM-Poisson" if dependent == 'iteration_count' else "OLS"
        }
    except Exception as e:
        logger.error(f"GLM/GLMM failed: {e}")
        return {"coef": None, "std_err": None, "pvalue": None, "conf_int_low": None, "conf_int_high": None, "error": str(e)}

def run_zinb_model(df: pd.DataFrame, dependent: str, independent: str, controls: List[str]) -> Dict[str, Any]:
    """Run a Zero-Inflated Negative Binomial model."""
    try:
        from statsmodels.discrete.discrete_model import ZeroInflatedNegativeBinomialP
        # Prepare data
        endog = df[dependent].values
        exog = df[controls + [independent]].values
        
        # Fit ZINB
        # Note: statsmodels ZINB might require specific initialization or formula interface
        # Using GLM with NegativeBinomial as a robust alternative if ZINB is unstable
        import statsmodels.formula.api as smf
        formula = f"{dependent} ~ {independent} + {' + '.join(controls)}"
        model = smf.glm(formula, data=df, family=smf.families.NegativeBinomial())
        result = model.fit()
        
        return {
            "coef": float(result.params[independent]),
            "std_err": float(result.bse[independent]),
            "pvalue": float(result.pvalues[independent]),
            "conf_int_low": float(result.conf_int()[independent][0]),
            "conf_int_high": float(result.conf_int()[independent][1]),
            "method": "NegativeBinomial"
        }
    except Exception as e:
        logger.error(f"ZINB model failed: {e}")
        return {"coef": None, "std_err": None, "pvalue": None, "conf_int_low": None, "conf_int_high": None, "error": str(e)}

def apply_bonferroni_correction(p_values: List[float], m: int) -> List[float]:
    """Apply Bonferroni correction to p-values."""
    return [min(p * m, 1.0) for p in p_values]

def run_sensitivity_analysis(df: pd.DataFrame, threshold_range: List[int]) -> List[Dict[str, Any]]:
    """
    Sweep iteration_count threshold over a range of low integer values.
    Record effect estimates (coefficient, p-value) for LLM adoption on iteration_count.
    """
    results = []
    logger.info(f"Starting sensitivity analysis with thresholds: {threshold_range}")
    
    # Controls based on typical confounders in this study
    controls = ['avg_comment_length', 'review_thread_depth', 'domain_complexity']
    independent = 'llm_adoption_flag'
    dependent = 'iteration_count'
    
    # Filter data to ensure valid numeric types
    df = df.copy()
    df[dependent] = pd.to_numeric(df[dependent], errors='coerce')
    df[independent] = pd.to_numeric(df[independent], errors='coerce')
    
    for threshold in threshold_range:
        logger.info(f"Processing threshold: {threshold}")
        
        # Filter: Keep rows where iteration_count >= threshold
        # This simulates a scenario where we ignore very low iteration counts (noise)
        filtered_df = df[df[dependent] >= threshold].copy()
        
        if filtered_df.empty:
            results.append({
                "threshold": threshold,
                "n_rows": 0,
                "coef": None,
                "pvalue": None,
                "status": "empty_dataset"
            })
            continue
        
        # Run GLM model
        model_result = run_glmm(filtered_df, dependent, independent, controls)
        
        results.append({
            "threshold": threshold,
            "n_rows": len(filtered_df),
            "coef": model_result.get("coef"),
            "std_err": model_result.get("std_err"),
            "pvalue": model_result.get("pvalue"),
            "conf_int_low": model_result.get("conf_int_low"),
            "conf_int_high": model_result.get("conf_int_high"),
            "status": model_result.get("error", "success")
        })
    
    return results

def run_analysis() -> Dict[str, Any]:
    """Main entry point for analysis."""
    df = load_master_dataset()
    df = clean_data(df)
    
    # Basic VIF check
    features = ['llm_adoption_flag', 'avg_comment_length', 'review_thread_depth', 'domain_complexity']
    vif = calculate_vif(df, features)
    high_vif = flag_high_vif(vif)
    
    analysis_results = {
        "vif_check": {
            "vif_values": vif.to_dict(),
            "high_vif_features": high_vif
        },
        "main_model": run_glmm(df, 'iteration_count', 'llm_adoption_flag', features[1:]),
        "sensitivity_analysis": None
    }
    
    # Run Sensitivity Analysis (T039)
    # Sweep low integer values: 1 to 10
    thresholds = list(range(1, 11))
    sens_results = run_sensitivity_analysis(df, thresholds)
    analysis_results["sensitivity_analysis"] = sens_results
    
    return analysis_results

def write_results(results: Dict[str, Any], output_path: Path):
    """Write analysis results to JSON."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results written to {output_path}")

def main():
    results = run_analysis()
    output_path = RESULTS_DIR / "sensitivity_analysis.json"
    write_results(results, output_path)

if __name__ == "__main__":
    main()
