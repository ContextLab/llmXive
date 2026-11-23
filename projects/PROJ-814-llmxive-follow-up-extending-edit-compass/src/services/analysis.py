import os
import sys
import json
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from scipy import stats
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.tools import add_constant

from src.data_models import RegressionResult
from src.utils.logging import get_logger

logger = get_logger(__name__)

class CircularValidationRiskError(Exception):
    """Raised when correlation between independent and dependent variables is too high."""
    pass

def load_filtered_instances(path: str = "data/filtered/edit-compass.json") -> List[Dict[str, Any]]:
    """Load filtered instances from JSON file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Filtered data not found at {path}")
    with open(path, 'r') as f:
        return json.load(f)

def load_scores(path: str = "data/scores/scores.json") -> List[Dict[str, Any]]:
    """Load scores from JSON file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Scores not found at {path}")
    with open(path, 'r') as f:
        return json.load(f)

def extract_human_scores(instances: List[Dict[str, Any]]) -> np.ndarray:
    """Extract human judgment scores."""
    scores = [inst.get('human_judgment_score') for inst in instances]
    if any(s is None for s in scores):
        raise ValueError("ERROR: Human Judgment Score missing")
    return np.array(scores, dtype=float)

def extract_logic_scores(scores: List[Dict[str, Any]]) -> np.ndarray:
    """Extract logic scores."""
    return np.array([s.get('logic_score') for s in scores], dtype=float)

def extract_fidelity_scores(scores: List[Dict[str, Any]]) -> np.ndarray:
    """Extract fidelity scores."""
    return np.array([s.get('fidelity_score') for s in scores], dtype=float)

def check_independence(human_scores: np.ndarray, logic_scores: np.ndarray) -> Tuple[float, bool]:
    """Check Pearson correlation between human and logic scores."""
    r, _ = stats.pearsonr(human_scores, logic_scores)
    return r, abs(r) >= 0.5

def write_circular_validation_risk_report(r: float, output_path: str = "outputs/circular_validation_risk_report.json"):
    """Atomically write circular validation risk report."""
    report = {
        "r": float(r),
        "threshold": 0.5,
        "decision": "HALT",
        "timestamp": pd.Timestamp.now().isoformat()
    }
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=output_dir, suffix='.json')
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(report, f, indent=2)
        shutil.move(tmp_path, output_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

def run_regression_analysis(human_scores: np.ndarray, logic_scores: np.ndarray, fidelity_scores: np.ndarray) -> Dict[str, Any]:
    """Run multiple linear regression."""
    X = np.column_stack([logic_scores, fidelity_scores])
    X = add_constant(X)
    y = human_scores
    
    model = pd.DataFrame(X, columns=['const', 'logic', 'fidelity'])
    df = pd.DataFrame({'human': y, 'logic': logic_scores, 'fidelity': fidelity_scores})
    
    results = pd.ols(y=df['human'], x=df[['logic', 'fidelity']])
    # Fallback to statsmodels OLS if pandas ols is deprecated/unavailable
    try:
        import statsmodels.api as sm
        model_sm = sm.OLS(y, X).fit()
        results = model_sm
    except ImportError:
        pass

    return {
        "coefficients": results.params.to_dict() if hasattr(results, 'params') else {},
        "pvalues": results.pvalues.to_dict() if hasattr(results, 'pvalues') else {},
        "rsquared": results.rsquared if hasattr(results, 'rsquared') else 0.0,
        "model_summary": str(results.summary()) if hasattr(results, 'summary') else ""
    }

def benjamini_hochberg(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """Apply Benjamini-Hochberg FDR correction."""
    n = len(p_values)
    if n == 0:
        return []
    sorted_indices = np.argsort(p_values)
    sorted_pvals = np.array(p_values)[sorted_indices]
    ranks = np.arange(1, n + 1)
    corrected_pvals = (sorted_pvals * n) / ranks
    corrected_pvals = np.minimum(corrected_pvals, 1.0)
    # Ensure monotonicity
    for i in range(n - 2, -1, -1):
        corrected_pvals[i] = min(corrected_pvals[i], corrected_pvals[i + 1])
    
    final_pvals = np.empty(n)
    final_pvals[sorted_indices] = corrected_pvals
    return final_pvals.tolist()

def fisher_z_test(r1: float, r2: float, n: int) -> Dict[str, float]:
    """Perform Fisher's r-to-z transformation test."""
    if abs(r1) >= 1 or abs(r2) >= 1:
        raise ValueError("Correlation coefficients must be in (-1, 1)")
    
    z1 = 0.5 * np.log((1 + r1) / (1 - r1))
    z2 = 0.5 * np.log((1 + r2) / (1 - r2))
    
    se = np.sqrt(1 / (n - 3))
    z_score = (z1 - z2) / (se * np.sqrt(2))
    p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
    
    return {
        "z_score": float(z_score),
        "p_value": float(p_value),
        "correlation_difference": float(r1 - r2),
        "effect_size": float(abs(r1 - r2)),
        "conclusion": "Significant" if p_value < 0.05 else "Not Significant",
        "threshold_value": 0.05,
        "threshold_met": p_value < 0.05
    }

def calculate_vif(X: pd.DataFrame) -> Dict[str, float]:
    """Calculate Variance Inflation Factor for each predictor."""
    X_const = add_constant(X)
    vif_data = {}
    for i, col in enumerate(X_const.columns):
        if col == 'const':
            continue
        vif = variance_inflation_factor(X_const.values, i)
        vif_data[col] = float(vif)
    return vif_data

def run_correlation_difference_test(human_scores: np.ndarray, logic_scores: np.ndarray, fidelity_scores: np.ndarray) -> Dict[str, Any]:
    """Run Fisher's r-to-z test and beta difference."""
    r_logic, _ = stats.pearsonr(human_scores, logic_scores)
    r_fidelity, _ = stats.pearsonr(human_scores, fidelity_scores)
    
    n = len(human_scores)
    z_test_result = fisher_z_test(float(r_logic), float(r_fidelity), n)
    
    # Run regression to get betas
    X = np.column_stack([logic_scores, fidelity_scores])
    X = add_constant(X)
    y = human_scores
    try:
        import statsmodels.api as sm
        model = sm.OLS(y, X).fit()
        betas = model.betas if hasattr(model, 'betas') else model.params.values
        beta_logic = betas[1]
        beta_fidelity = betas[2]
        beta_diff = float(beta_logic - beta_fidelity)
    except Exception:
        beta_diff = 0.0
    
    z_test_result['beta_difference'] = beta_diff
    return z_test_result

def append_collinearity_warning(report_path: str, vif_results: Dict[str, float]):
    """Append a Collinearity Warning section to the regression report if VIF > 5.0."""
    if not os.path.exists(report_path):
        logger.warning(f"Report file {report_path} not found. Cannot append warning.")
        return

    high_vif_vars = {k: v for k, v in vif_results.items() if v > 5.0}
    
    if not high_vif_vars:
        logger.info("No collinearity detected (all VIF <= 5.0).")
        return

    warning_section = "\n\n## ⚠️ Collinearity Warning\n\n"
    warning_section += "The Variance Inflation Factor (VIF) analysis detected potential multicollinearity between predictors:\n\n"
    warning_section += "| Predictor | VIF Value | Interpretation |\n"
    warning_section += "|-----------|-----------|----------------|\n"
    for var, vif_val in high_vif_vars.items():
        warning_section += f"| {var} | {vif_val:.4f} | High (> 5.0) - Independent effects may be confounded. |\n"
    
    warning_section += "\n**Implication**: The regression coefficients for these variables may be unstable, and the interpretation of their individual contributions to the Human Judgment Score should be treated with caution.\n"
    
    with open(report_path, 'a') as f:
        f.write(warning_section)
    
    logger.warning(f"Collinearity warning appended to {report_path} for variables: {list(high_vif_vars.keys())}")

def main():
    """Main entry point for analysis stage."""
    logging.basicConfig(level=logging.INFO)
    
    try:
        instances = load_filtered_instances()
        scores = load_scores()
        
        if len(instances) == 0 or len(scores) == 0:
            logger.error("No data found for analysis.")
            sys.exit(1)

        human_scores = extract_human_scores(instances)
        logic_scores = extract_logic_scores(scores)
        fidelity_scores = extract_fidelity_scores(scores)

        # Independence Check
        r, is_dependent = check_independence(human_scores, logic_scores)
        if is_dependent:
            write_circular_validation_risk_report(r)
            raise CircularValidationRiskError(f"Circular validation risk: |r|={abs(r):.4f} >= 0.5")

        # Regression
        reg_results = run_regression_analysis(human_scores, logic_scores, fidelity_scores)
        
        # FDR Correction
        p_logic = reg_results['pvalues'].get('logic', 1.0)
        p_fidelity = reg_results['pvalues'].get('fidelity', 1.0)
        corrected_p_values = benjamini_hochberg([p_logic, p_fidelity])
        
        # VIF Calculation
        df_predictors = pd.DataFrame({'logic': logic_scores, 'fidelity': fidelity_scores})
        vif_results = calculate_vif(df_predictors)
        logger.info(f"VIF Results: {vif_results}")

        # Correlation Difference Test
        corr_diff_results = run_correlation_difference_test(human_scores, logic_scores, fidelity_scores)
        
        # Generate Report
        report_path = "outputs/regression_report.md"
        report_content = "# Regression Analysis Report\n\n"
        report_content += f"## Model Summary\n"
        report_content += f"- R-squared: {reg_results['rsquared']:.4f}\n\n"
        report_content += "## Coefficients\n"
        report_content += f"- Logic Score Beta: {reg_results['coefficients'].get('logic', 'N/A'):.4f}\n"
        report_content += f"- Fidelity Score Beta: {reg_results['coefficients'].get('fidelity', 'N/A'):.4f}\n\n"
        report_content += "## FDR Corrected P-values\n"
        report_content += f"- Logic: {corrected_p_values[0]:.4f}\n"
        report_content += f"- Fidelity: {corrected_p_values[1]:.4f}\n\n"
        report_content += "## Correlation Difference Test (Fisher's Z)\n"
        report_content += f"- Z-Score: {corr_diff_results['z_score']:.4f}\n"
        report_content += f"- P-Value: {corr_diff_results['p_value']:.4f}\n"
        report_content += f"- Conclusion: {corr_diff_results['conclusion']}\n"
        report_content += f"- Threshold Met: {corr_diff_results['threshold_met']}\n\n"
        
        with open(report_path, 'w') as f:
            f.write(report_content)

        # Append Collinearity Warning if needed
        append_collinearity_warning(report_path, vif_results)

        logger.info(f"Analysis complete. Report saved to {report_path}")

    except CircularValidationRiskError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()