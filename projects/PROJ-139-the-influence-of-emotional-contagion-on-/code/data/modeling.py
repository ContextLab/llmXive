import os
import json
import logging
import warnings
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf

from config.settings import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_processed_data(file_path: str) -> pd.DataFrame:
    """Load a processed CSV file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Processed data file not found: {file_path}")
    return pd.read_csv(path)

def save_processed_data(df: pd.DataFrame, file_path: str) -> None:
    """Save a DataFrame to a CSV file."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Saved processed data to {file_path}")

def fit_beta_regression(y: pd.Series, X: pd.DataFrame) -> sm.RegressionResults:
    """Fit a beta regression model for bounded outcomes (0, 1)."""
    # Beta regression requires y strictly in (0, 1)
    # Apply a small transformation if necessary
    y_transformed = y * (1 - 2e-7) + 1e-7
    model = smf.glm(
        formula="y ~ " + " + ".join(X.columns),
        data=pd.concat([y_transformed, X], axis=1),
        family=sm.families.Beta(link=sm.links.logit())
    )
    return model.fit()

def fit_gamma_regression(y: pd.Series, X: pd.DataFrame) -> sm.RegressionResults:
    """Fit a Gamma regression for continuous positive outcomes."""
    model = smf.glm(
        formula="y ~ " + " + ".join(X.columns),
        data=pd.concat([y, X], axis=1),
        family=sm.families.Gamma(link=sm.links.log())
    )
    return model.fit()

def fit_count_regression(y: pd.Series, X: pd.DataFrame) -> sm.RegressionResults:
    """Fit a Poisson or Negative Binomial regression for count outcomes."""
    # Try Poisson first, then Negative Binomial if overdispersion detected
    try:
        model = smf.glm(
            formula="y ~ " + " + ".join(X.columns),
            data=pd.concat([y, X], axis=1),
            family=sm.families.Poisson()
        )
        result = model.fit()
        # Check for overdispersion
        pearson_chi2 = result.pearson_chi2
        df_resid = result.df_resid
        if pearson_chi2 / df_resid > 1.5:
            logger.warning("Overdispersion detected, switching to Negative Binomial")
            model = smf.glm(
                formula="y ~ " + " + ".join(X.columns),
                data=pd.concat([y, X], axis=1),
                family=sm.families.NegativeBinomial()
            )
            result = model.fit()
        return result
    except Exception as e:
        logger.error(f"Error fitting count regression: {e}")
        raise

def fit_glmm_with_random_intercepts(
    df: pd.DataFrame,
    formula: str,
    random_effect: str = "thread_id",
    family: Any = sm.families.Gaussian()
) -> sm.RegressionResults:
    """Fit a GLMM with random intercepts for thread-level correlation."""
    # Use MixedLM for Gaussian, or GLMER for others (requires statsmodels >= 0.13)
    try:
        model = smf.mixedlm(
            formula=formula,
            data=df,
            groups=df[random_effect]
        )
        return model.fit()
    except Exception as e:
        logger.error(f"Error fitting GLMM: {e}")
        raise

def run_wald_tests(result: sm.RegressionResults, alpha: float = 0.05) -> Dict[str, Any]:
    """Run Wald tests for model coefficients."""
    p_values = result.pvalues
    coefficients = result.params
    significant = p_values < alpha
    return {
        "coefficients": coefficients.to_dict(),
        "p_values": p_values.to_dict(),
        "significant": significant.to_dict()
    }

def apply_multiple_comparison_correction(
    p_values: List[float],
    method: str = "bonferroni"
) -> List[float]:
    """Apply multiple comparison correction (Bonferroni or Benjamini-Hochberg)."""
    if method == "bonferroni":
        corrected = [p * len(p_values) for p in p_values]
    elif method == "fdr_bh":
        # Benjamini-Hochberg FDR
        sorted_indices = np.argsort(p_values)
        sorted_p = np.array(p_values)[sorted_indices]
        n = len(p_values)
        corrected_sorted = np.minimum(1, (sorted_p * n) / (np.arange(1, n + 1)))
        corrected = np.empty(n)
        corrected[sorted_indices] = corrected_sorted
    else:
        raise ValueError(f"Unknown correction method: {method}")
    return [min(p, 1.0) for p in corrected]

def run_sensitivity_analysis(
    df_threads: pd.DataFrame,
    df_metrics: pd.DataFrame,
    agreement_cutoffs: List[float] = [0.5, 0.6, 0.7],
    entropy_thresholds: List[float] = [0.2, 0.4, 0.6]
) -> pd.DataFrame:
    """
    Run sensitivity analysis over agreement cutoff and entropy threshold grid.
    Handles empty grid cells by logging a warning and setting correlation to null.
    """
    results = []
    
    # Join dataframes on thread_id
    df = pd.merge(df_threads, df_metrics, on="thread_id", how="inner")
    
    for cutoff in agreement_cutoffs:
        for threshold in entropy_thresholds:
            # Filter threads based on current grid cell
            mask = (df["agreement_proportion"] >= cutoff) & (df["shannon_entropy"] <= threshold)
            cell_data = df[mask]
            
            cell_result = {
                "agreement_cutoff": cutoff,
                "entropy_threshold": threshold,
                "thread_count": len(cell_data),
                "correlation_agreement": None,
                "correlation_entropy": None,
                "correlation_validation": None,
                "false_positive_rate": None,
                "false_negative_rate": None,
                "grid_coverage": True
            }
            
            if len(cell_data) == 0:
                logger.warning(
                    f"Empty grid cell for agreement_cutoff={cutoff} and "
                    f"entropy_threshold={threshold}. No threads match criteria. "
                    "Setting correlation values to null."
                )
                # Explicitly set correlations to null (None)
                cell_result["correlation_agreement"] = None
                cell_result["correlation_entropy"] = None
                cell_result["correlation_validation"] = None
                cell_result["false_positive_rate"] = None
                cell_result["false_negative_rate"] = None
            else:
                # Compute correlations if data exists
                try:
                    # Correlation with agreement_proportion (should be 1.0 by definition, but compute anyway)
                    if cell_data["agreement_proportion"].std() > 0 and cell_data["contagion_index"].std() > 0:
                        corr_agr, _ = stats.pearsonr(
                            cell_data["agreement_proportion"], 
                            cell_data["contagion_index"]
                        )
                        cell_result["correlation_agreement"] = float(corr_agr)
                    else:
                        cell_result["correlation_agreement"] = None
                        
                    # Correlation with shannon_entropy
                    if cell_data["shannon_entropy"].std() > 0 and cell_data["contagion_index"].std() > 0:
                        corr_ent, _ = stats.pearsonr(
                            cell_data["shannon_entropy"], 
                            cell_data["contagion_index"]
                        )
                        cell_result["correlation_entropy"] = float(corr_ent)
                    else:
                        cell_result["correlation_entropy"] = None
                        
                    # Correlation with external_validation_score
                    valid_scores = cell_data["external_validation_score"].dropna()
                    if len(valid_scores) > 2 and valid_scores.std() > 0 and cell_data.loc[valid_scores.index, "contagion_index"].std() > 0:
                        corr_val, _ = stats.pearsonr(
                            valid_scores, 
                            cell_data.loc[valid_scores.index, "contagion_index"]
                        )
                        cell_result["correlation_validation"] = float(corr_val)
                    else:
                        cell_result["correlation_validation"] = None
                        
                    # FP/FN rates (simplified placeholder logic, actual implementation depends on T023a)
                    # Assuming T023a has populated these columns or we compute them here
                    # For now, set to null if not available
                    if "false_positive_rate" in cell_data.columns:
                        fp_rate = cell_data["false_positive_rate"].mean()
                        if not pd.isna(fp_rate):
                            cell_result["false_positive_rate"] = float(fp_rate)
                        
                    if "false_negative_rate" in cell_data.columns:
                        fn_rate = cell_data["false_negative_rate"].mean()
                        if not pd.isna(fn_rate):
                            cell_result["false_negative_rate"] = float(fn_rate)
                            
                except Exception as e:
                    logger.error(f"Error computing correlations for cell ({cutoff}, {threshold}): {e}")
                    # Keep values as None
            
            results.append(cell_result)
    
    return pd.DataFrame(results)

def compute_external_validation_correlation(
    df_valid: pd.DataFrame,
    df_metrics: pd.DataFrame
) -> pd.DataFrame:
    """Compute correlation between external validation score and decision quality metrics."""
    df = pd.merge(df_valid, df_metrics, on="thread_id", how="inner")
    
    results = []
    
    # Correlation with contagion_index
    valid_scores = df["external_validation_score"].dropna()
    if len(valid_scores) > 2 and valid_scores.std() > 0:
        corr_idx, p_idx = stats.pearsonr(
            valid_scores, 
            df.loc[valid_scores.index, "contagion_index"]
        )
        results.append({
            "metric": "contagion_index",
            "correlation": float(corr_idx),
            "p_value": float(p_idx)
        })
    
    # Correlation with agreement_proportion
    if df["agreement_proportion"].std() > 0 and valid_scores.std() > 0:
        corr_agr, p_agr = stats.pearsonr(
            valid_scores, 
            df.loc[valid_scores.index, "agreement_proportion"]
        )
        results.append({
            "metric": "agreement_proportion",
            "correlation": float(corr_agr),
            "p_value": float(p_agr)
        })
    
    # Correlation with shannon_entropy
    if df["shannon_entropy"].std() > 0 and valid_scores.std() > 0:
        corr_ent, p_ent = stats.pearsonr(
            valid_scores, 
            df.loc[valid_scores.index, "shannon_entropy"]
        )
        results.append({
            "metric": "shannon_entropy",
            "correlation": float(corr_ent),
            "p_value": float(p_ent)
        })
    
    return pd.DataFrame(results)

def compute_collinearity_diagnostics(df: pd.DataFrame, predictors: List[str]) -> Dict[str, Any]:
    """Compute Variance Inflation Factor (VIF) for predictors."""
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    X = df[predictors].dropna()
    if len(X) < 5:
        logger.warning("Not enough data points to compute VIF")
        return {"vif_scores": {}, "threshold": 5, "flagged": False}
    
    X = sm.add_constant(X)
    vif_scores = {}
    flagged = False
    
    for i, col in enumerate(predictors):
        try:
            vif = variance_inflation_factor(X.values, i + 1)  # +1 because of const
            vif_scores[col] = float(vif)
            if vif > 5:
                flagged = True
        except Exception as e:
            logger.error(f"Error computing VIF for {col}: {e}")
            vif_scores[col] = None
    
    return {
        "vif_scores": vif_scores,
        "threshold": 5,
        "flagged": flagged
    }

def run_collinearity_pipeline(df: pd.DataFrame, output_path: str) -> None:
    """Run collinearity diagnostics and save results."""
    predictors = ["sentiment", "thread_length", "time_to_decision", "external_validation_score"]
    # Filter out rows with NaN in any predictor
    df_clean = df[predictors].dropna()
    
    diagnostics = compute_collinearity_diagnostics(df_clean, predictors)
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(diagnostics, f, indent=2)
    logger.info(f"Saved collinearity diagnostics to {output_path}")

def run_modeling_pipeline(
    config: Dict[str, Any],
    threads_path: str,
    metrics_path: str,
    output_metrics_path: str,
    output_sensitivity_path: str,
    output_validation_path: str,
    output_collinearity_path: str
) -> None:
    """Main pipeline for modeling, sensitivity analysis, and diagnostics."""
    logger.info("Starting modeling pipeline...")
    
    # Load data
    df_threads = load_processed_data(threads_path)
    df_metrics = load_processed_data(metrics_path)
    
    # Run sensitivity analysis
    logger.info("Running sensitivity analysis...")
    df_sensitivity = run_sensitivity_analysis(df_threads, df_metrics)
    save_processed_data(df_sensitivity, output_sensitivity_path)
    
    # Run external validation correlation
    logger.info("Computing external validation correlations...")
    # Assuming df_threads has external_validation_score (from T019a)
    df_valid = df_threads[df_threads["is_valid"] == True] if "is_valid" in df_threads.columns else df_threads
    df_corr = compute_external_validation_correlation(df_valid, df_metrics)
    save_processed_data(df_corr, output_validation_path)
    
    # Run collinearity diagnostics
    logger.info("Running collinearity diagnostics...")
    # Prepare dataframe with required predictors
    # Join threads and metrics for diagnostics
    df_model = pd.merge(df_threads, df_metrics, on="thread_id", how="inner")
    run_collinearity_pipeline(df_model, output_collinearity_path)
    
    logger.info("Modeling pipeline completed successfully.")

def main():
    """Entry point for modeling pipeline."""
    config = get_config()
    
    # Define paths
    threads_path = config.data_paths.processed_valid_threads
    metrics_path = config.data_paths.processed_thread_metrics
    output_sensitivity = config.data_paths.processed_sensitivity_analysis
    output_validation = config.data_paths.processed_external_validation_correlation
    output_collinearity = config.data_paths.processed_collinearity_diagnostics
    
    run_modeling_pipeline(
        config=config,
        threads_path=threads_path,
        metrics_path=metrics_path,
        output_metrics_path="",  # Not used directly in this pipeline
        output_sensitivity_path=output_sensitivity,
        output_validation_path=output_validation,
        output_collinearity_path=output_collinearity
    )

if __name__ == "__main__":
    main()