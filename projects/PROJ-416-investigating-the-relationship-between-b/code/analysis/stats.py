import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

from code.config import Config
from code.utils.logging import setup_logging

logger = logging.getLogger(__name__)


def calculate_vif(df: pd.DataFrame, feature_names: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for given features.

    Args:
        df: DataFrame containing the features.
        feature_names: List of column names to calculate VIF for.

    Returns:
        Dictionary mapping feature names to their VIF values.
    """
    X = df[feature_names].values
    # Add constant for intercept
    X_with_const = sm.add_constant(X)
    
    vif_data = {}
    for i, name in enumerate(feature_names):
        vif = variance_inflation_factor(X_with_const, i + 1) # +1 because index 0 is const
        vif_data[name] = vif
    
    logger.info(f"VIF calculated: {vif_data}")
    return vif_data


def apply_fdr_correction(p_values: List[float], alpha: float = 0.05) -> List[bool]:
    """
    Apply False Discovery Rate (FDR) correction to a list of p-values.

    Args:
        p_values: List of p-values.
        alpha: Significance level.

    Returns:
        List of booleans indicating significance after FDR correction.
    """
    from statsmodels.stats.multitest import multipletests
    
    if not p_values:
        return []
    
    _, pvals_corrected, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')
    
    # Return boolean mask of significant results
    return [p < alpha for p in pvals_corrected]


def run_power_analysis(
    n_subjects: int,
    effect_size: float = 0.5,
    alpha: float = 0.05,
    power: float = 0.8
) -> Dict[str, Any]:
    """
    Perform a power analysis to determine required sample size.

    Args:
        n_subjects: Current number of subjects.
        effect_size: Expected effect size (Cohen's d).
        alpha: Significance level.
        power: Desired power.

    Returns:
        Dictionary with power analysis results.
    """
    from statsmodels.stats.power import TTestIndPower
    
    analysis = TTestIndPower()
    
    # Calculate required sample size
    try:
        required_n = analysis.solve_power(
            effect_size=effect_size,
            alpha=alpha,
            power=power,
            ratio=1.0
        )
    except Exception:
        required_n = float('inf')

    result = {
        "current_n": n_subjects,
        "required_n": int(np.ceil(required_n)) if required_n != float('inf') else -1,
        "sufficient": n_subjects >= required_n if required_n != float('inf') else False,
        "effect_size": effect_size,
        "alpha": alpha,
        "power": power
    }

    logger.info(f"Power analysis: Current N={n_subjects}, Required N={result['required_n']}")
    return result


def run_ancova_analysis(
    df: pd.DataFrame,
    dependent_var: str,
    independent_vars: List[str],
    covariates: List[str],
    fd_covariate: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run ANCOVA analysis.

    Args:
        df: DataFrame with data.
        dependent_var: Name of the dependent variable column.
        independent_vars: List of independent variable names.
        covariates: List of covariate names.
        fd_covariate: Optional name of the Framewise Displacement covariate.

    Returns:
        Dictionary containing regression results.
    """
    formula_parts = [dependent_var]
    formula_parts.extend(independent_vars)
    formula_parts.extend(covariates)
    if fd_covariate and fd_covariate in df.columns:
        formula_parts.append(fd_covariate)
    
    formula = " + ".join(formula_parts)
    
    try:
        model = sm.OLS.from_formula(formula, data=df)
        results = model.fit()
        
        return {
            "summary": results.summary().as_text(),
            "params": results.params.to_dict(),
            "pvalues": results.pvalues.to_dict(),
            "rsquared": results.rsquared,
            "aic": results.aic,
            "bic": results.bic
        }
    except Exception as e:
        logger.error(f"ANCOVA failed: {e}")
        return {"error": str(e)}


def run_sensitivity_analysis(
    df: pd.DataFrame,
    dependent_var: str,
    independent_vars: List[str],
    motion_thresholds: List[float],
    p_values: List[float]
) -> List[Dict[str, Any]]:
    """
    Run sensitivity analysis by varying motion thresholds and p-values.

    Args:
        df: DataFrame with data.
        dependent_var: Dependent variable name.
        independent_vars: Independent variable names.
        motion_thresholds: List of motion thresholds to test.
        p_values: List of p-value thresholds to test.

    Returns:
        List of results dictionaries for each configuration.
    """
    results_list = []
    
    for thresh in motion_thresholds:
        # Filter data based on motion threshold (assuming a 'fd' column exists)
        if 'fd' in df.columns:
            sub_df = df[df['fd'] <= thresh]
        else:
            sub_df = df.copy()
        
        if len(sub_df) < 5:
            logger.warning(f"Sample size too small for threshold {thresh}: {len(sub_df)}")
            continue
        
        for p_thresh in p_values:
            # Run simple regression for demonstration
            # In real implementation, run full ANCOVA
            try:
                model = sm.OLS.from_formula(
                    f"{dependent_var} ~ {' + '.join(independent_vars)}",
                    data=sub_df
                )
                res = model.fit()
                
                # Apply FDR if multiple metrics
                p_vals = res.pvalues.drop('Intercept', errors='ignore').tolist()
                sig_mask = apply_fdr_correction(p_vals, alpha=p_thresh)
                
                results_list.append({
                    "motion_threshold": thresh,
                    "p_threshold": p_thresh,
                    "n_subjects": len(sub_df),
                    "significant": sig_mask,
                    "coefficients": res.params.to_dict()
                })
            except Exception as e:
                logger.warning(f"Sensitivity analysis failed for thresh={thresh}, p={p_thresh}: {e}")
                continue

    return results_list


def run_analysis(
    data_path: Path,
    output_path: Path,
  config: Config
) -> None:
    """
    Run the statistical analysis pipeline.

    Args:
        data_path: Path to the input data CSV.
        output_path: Path to save statistical results.
        config: Configuration object.
    """
    try:
        df = pd.read_csv(data_path)
        
        # Example: Run ANCOVA
        # Assuming columns: 'post_treatment_score', 'pre_treatment_score', 'network_metric', 'fd'
        if 'post_treatment_score' in df.columns and 'pre_treatment_score' in df.columns:
            ancova_result = run_ancova_analysis(
                df=df,
                dependent_var='post_treatment_score',
                independent_vars=['network_metric'],
                covariates=['pre_treatment_score'],
                fd_covariate='fd'
            )
            
            if 'error' not in ancova_result:
                # Calculate VIF
                vif_res = calculate_vif(df, ['pre_treatment_score', 'network_metric'])
                
                # Save results
                results_df = pd.DataFrame([{
                    'metric': 'network_metric',
                    'coefficient': ancova_result['params'].get('network_metric', 0),
                    'p_value': ancova_result['pvalues'].get('network_metric', 1),
                    'vif': vif_res.get('network_metric', 0)
                }])
                
                output_path.parent.mkdir(parents=True, exist_ok=True)
                results_df.to_csv(output_path, index=False)
                logger.info(f"Statistical results saved to {output_path}")
            else:
                logger.error("ANCOVA failed, no results saved.")
        else:
            logger.warning("Required columns for ANCOVA not found.")
    except Exception as e:
        logger.error(f"Statistical analysis failed: {e}")
        raise


def main():
    """Main entry point for the statistical analysis script."""
    setup_logging()
    config = Config()
    
    data_path = Path(config.metrics_output_dir) / "network_metrics.csv" # Simplified path
    output_path = Path(config.metrics_output_dir) / "statistical_results.csv"
    
    run_analysis(data_path, output_path, config)


if __name__ == "__main__":
    main()
