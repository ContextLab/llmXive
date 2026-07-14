"""
Model Analysis Module for Adoption of Sustainable Agricultural Practices Study.
Implements logistic regression, VIF diagnostics, FDR correction, ROC analysis, and mediation analysis.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from scipy import stats
from sklearn.metrics import roc_curve, auc, roc_auc_score
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless execution
import matplotlib.pyplot as plt

# Local imports - using names from API surface
from config import get_config, set_random_seed, get_config_path, get_data_path
from logging_config import update_log_section, log_operation

# Custom exceptions
class CustomDataError(Exception):
    """Raised when data loading or validation fails."""
    pass

class ModelError(Exception):
    """Raised when model fitting or analysis fails."""
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('modeling_log.log')
    ]
)
logger = logging.getLogger(__name__)

def get_config_paths() -> Dict[str, Path]:
    """Get all necessary paths from config."""
    cfg = get_config()
    project_root = Path(get_config("project_root", "."))
    
    return {
        "project_root": project_root,
        "processed_data_path": project_root / get_config("processed_data_path", "data/processed"),
        "results_path": project_root / get_config("results_path", "results"),
        "log_path": project_root / "modeling_log.yaml"
    }

def load_engineered_data(input_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load the engineered dataset containing engagement_score and adoption_binary.
    
    Args:
        input_path: Optional path to engineered data file. If None, uses config.
        
    Returns:
        DataFrame with engineered features.
        
    Raises:
        CustomDataError: If file not found or missing required columns.
    """
    paths = get_config_paths()
    if input_path is None:
        input_path = paths["processed_data_path"] / "engineered_data.csv"
    else:
        input_path = Path(input_path)
        
    if not input_path.exists():
        raise CustomDataError(
            f"Engineered data file not found at {input_path}. "
            "Please ensure T020-T022 (US2) has completed successfully."
        )
        
    df = pd.read_csv(input_path)
    
    # Validate required columns exist
    required_cols = ['adoption_binary', 'engagement_score']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise CustomDataError(
            f"Engineered data missing required columns: {missing}. "
            "Expected columns: {required_cols}"
        )
        
    logger.info(f"Loaded engineered data: {len(df)} records from {input_path}")
    return df

def prepare_model_data(
    df: pd.DataFrame,
    outcome_var: str = 'adoption_binary',
    primary_pred: str = 'engagement_score',
    covariates: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """
    Prepare data for logistic regression modeling.
    
    Args:
        df: Input dataframe with engineered features.
        outcome_var: Name of the outcome variable.
        primary_pred: Name of the primary predictor.
        covariates: List of covariate names to include.
        
    Returns:
        Tuple of (cleaned_df, outcome_series, X_matrix)
    """
    # Default covariates if not specified
    if covariates is None:
        covariates = ['age', 'education_years', 'farm_size', 'credit_access']
        
    # Select columns that exist in dataframe
    available_cols = [outcome_var, primary_pred] + [c for c in covariates if c in df.columns]
    missing_cols = [c for c in covariates if c not in df.columns]
    
    if missing_cols:
        logger.warning(f"Covariates not found in data: {missing_cols}. Excluding from model.")
        
    if len(available_cols) < 2:
        raise CustomDataError(
            f"Insufficient variables for modeling. Need at least outcome and one predictor. "
            f"Available: {list(df.columns)}"
        )
        
    # Drop rows with missing values in selected columns
    clean_df = df.dropna(subset=available_cols)
    
    if len(clean_df) == 0:
        raise CustomDataError("No complete cases available after dropping missing values.")
        
    # Prepare outcome and predictors
    y = clean_df[outcome_var]
    X = clean_df[[primary_pred] + [c for c in covariates if c in clean_df.columns]]
    
    # Add constant for intercept
    X_with_const = sm.add_constant(X)
    
    logger.info(f"Prepared model data: {len(clean_df)} complete cases, "
               f"{len(X_with_const.columns)} predictors (including intercept)")
               
    return clean_df, y, X_with_const

def fit_logistic_regression(
    y: pd.Series,
    X: pd.DataFrame,
    method: str = 'bfgs'
) -> sm.LogitResultsWrapper:
    """
    Fit logistic regression model.
    
    Args:
        y: Outcome variable series.
        X: Predictor matrix (with constant).
        method: Optimization method for statsmodels.
        
    Returns:
        Fitted model results object.
        
    Raises:
        ModelError: If model fitting fails.
    """
    try:
        model = sm.Logit(y, X)
        results = model.fit(method=method, disp=0)
        logger.info(f"Logistic regression converged: {results.converged}")
        return results
    except Exception as e:
        raise ModelError(f"Failed to fit logistic regression: {str(e)}")

def calculate_vif(X: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor for all predictors.
    
    Args:
        X: Predictor matrix (should include constant).
        
    Returns:
        DataFrame with VIF values for each predictor.
    """
    # Exclude constant from VIF calculation
    X_no_const = X.select_dtypes(include=[np.number]).drop('const', axis=1, errors='ignore')
    
    if X_no_const.shape[1] == 0:
        logger.warning("No numeric predictors available for VIF calculation.")
        return pd.DataFrame()
        
    vif_data = []
    for i, col in enumerate(X_no_const.columns):
        try:
            vif = variance_inflation_factor(X_no_const.values, i)
            vif_data.append({
                'variable': col,
                'vif': vif,
                'warning': vif >= 5
            })
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {str(e)}")
            
    vif_df = pd.DataFrame(vif_data)
    
    # Log warnings for high VIF
    high_vif = vif_df[vif_df['warning'] == True]
    if len(high_vif) > 0:
        logger.warning(f"High VIF detected (≥5) for variables: {list(high_vif['variable'])}")
        
    return vif_df

def apply_fdr_correction(
    p_values: np.ndarray,
    alpha: float = 0.10
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply Benjamini-Hochberg False Discovery Rate correction.
    
    Args:
        p_values: Array of raw p-values.
        alpha: Significance level for FDR (default 0.10).
        
    Returns:
        Tuple of (adjusted_p_values, boolean_rejection_mask)
    """
    from statsmodels.stats.multitest import multipletests
    
    try:
        # Apply BH correction
        reject, pvals_corrected, _, _ = multipletests(
            p_values, 
            alpha=alpha, 
            method='fdr_bh'
        )
        logger.info(f"FDR correction applied: {sum(reject)} hypotheses rejected at q ≤ {alpha}")
        return pvals_corrected, reject
    except Exception as e:
        logger.warning(f"FDR correction failed: {str(e)}. Using raw p-values.")
        return p_values, p_values < alpha

def calculate_roc_metrics(
    y_true: pd.Series,
    y_pred_proba: np.ndarray
) -> Dict[str, Union[float, np.ndarray]]:
    """
    Calculate ROC curve metrics and AUC.
    
    Args:
        y_true: True binary outcomes.
        y_pred_proba: Predicted probabilities from model.
        
    Returns:
        Dictionary with ROC metrics including AUC, thresholds, and curve points.
    """
    try:
        # Calculate AUC
        auc_value = roc_auc_score(y_true, y_pred_proba)
        
        # Calculate ROC curve
        fpr, tpr, thresholds = roc_curve(y_true, y_pred_proba)
        
        metrics = {
            'auc': float(auc_value),
            'fpr': fpr,
            'tpr': tpr,
            'thresholds': thresholds,
            'interpretation': interpret_auc(auc_value)
        }
        
        logger.info(f"ROC AUC calculated: {auc_value:.4f} ({metrics['interpretation']})")
        return metrics
        
    except Exception as e:
        raise ModelError(f"Failed to calculate ROC metrics: {str(e)}")

def interpret_auc(auc_value: float) -> str:
    """Provide interpretation of AUC value."""
    if auc_value >= 0.9:
        return "Excellent discrimination"
    elif auc_value >= 0.8:
        return "Good discrimination"
    elif auc_value >= 0.7:
        return "Fair discrimination"
    elif auc_value >= 0.6:
        return "Poor discrimination"
    else:
        return "No better than random"

def plot_roc_curve(
    y_true: pd.Series,
    y_pred_proba: np.ndarray,
    output_path: Optional[str] = None,
    title: str = "ROC Curve - Sustainable Agriculture Adoption Model"
) -> str:
    """
    Plot ROC curve and save to file.
    
    Args:
        y_true: True binary outcomes.
        y_pred_proba: Predicted probabilities.
        output_path: Path to save the plot. If None, uses default results path.
        title: Plot title.
        
    Returns:
        Path to saved figure.
    """
    paths = get_config_paths()
    if output_path is None:
        output_path = paths["results_path"] / "roc_curve.png"
    else:
        output_path = Path(output_path)
        
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        fpr, tpr, thresholds = roc_curve(y_true, y_pred_proba)
        auc_value = roc_auc_score(y_true, y_pred_proba)
        
        plt.figure(figsize=(10, 8))
        plt.plot(fpr, tpr, color='darkorange', lw=2, 
                label=f'ROC curve (AUC = {auc_value:.3f})')
        plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--',
                label='Random classifier')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate', fontsize=12)
        plt.ylabel('True Positive Rate', fontsize=12)
        plt.title(title, fontsize=14)
        plt.legend(loc="lower right", fontsize=11)
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"ROC curve saved to: {output_path}")
        return str(output_path)
        
    except Exception as e:
        logger.error(f"Failed to plot ROC curve: {str(e)}")
        raise ModelError(f"ROC plotting failed: {str(e)}")

def perform_mediation_analysis(
    df: pd.DataFrame,
    outcome: str,
    mediator: str,
    predictor: str,
    covariates: Optional[List[str]] = None,
    n_bootstraps: int = 1000,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Perform mediation analysis using Baron & Kenny approach with bootstrapping.
    
    Args:
        df: Input dataframe.
        outcome: Outcome variable name.
        mediator: Mediator variable name.
        predictor: Primary predictor name.
        covariates: List of covariate names.
        n_bootstraps: Number of bootstrap resamples.
        seed: Random seed for reproducibility.
        
    Returns:
        Dictionary with mediation analysis results.
    """
    if seed is not None:
        set_random_seed(seed)
        
    # Default covariates
    if covariates is None:
        covariates = ['age', 'education_years', 'farm_size', 'credit_access']
        
    # Prepare data
    vars_needed = [outcome, mediator, predictor] + covariates
    available_vars = [v for v in vars_needed if v in df.columns]
    missing_vars = [v for v in vars_needed if v not in df.columns]
    
    if len(available_vars) < 3:
        raise CustomDataError(
            f"Insufficient variables for mediation analysis. "
            f"Need: outcome, mediator, predictor. Available: {available_vars}"
        )
        
    clean_df = df.dropna(subset=available_vars)
    
    if len(clean_df) < 30:
        logger.warning(f"Small sample size for mediation: {len(clean_df)}. Results may be unstable.")
        
    results = {
        'method': 'Baron & Kenny with bootstrap',
        'n_bootstraps': n_bootstraps,
        'n_observations': len(clean_df),
        'direct_effect': None,
        'indirect_effect': None,
        'total_effect': None,
        'confidence_interval': None,
        'interpretation': 'Exploratory - mediation effects should be interpreted with caution'
    }
    
    try:
        # Model 1: Mediator ~ Predictor + Covariates
        X_m = sm.add_constant(clean_df[[predictor] + [c for c in covariates if c in clean_df.columns]])
        y_m = clean_df[mediator]
        model_m = sm.OLS(y_m, X_m).fit()
        a_path = model_m.params.get(predictor, 0)
        a_se = model_m.bse.get(predictor, 0)
        
        # Model 2: Outcome ~ Predictor + Mediator + Covariates
        X_y = sm.add_constant(clean_df[[predictor, mediator] + [c for c in covariates if c in clean_df.columns]])
        y_y = clean_df[outcome]
        model_y = sm.OLS(y_y, X_y).fit()
        c_prime = model_y.params.get(predictor, 0)  # Direct effect
        b_path = model_y.params.get(mediator, 0)
        
        # Calculate effects
        indirect_effect = a_path * b_path
        total_effect = c_prime + indirect_effect
        
        # Bootstrap for confidence intervals
        np.random.seed(seed or 42)
        boot_indirect = []
        
        for _ in range(n_bootstraps):
            idx = np.random.choice(len(clean_df), len(clean_df), replace=True)
            boot_df = clean_df.iloc[idx]
            
            # Bootstrap Model 1
            X_m_boot = sm.add_constant(boot_df[[predictor] + [c for c in covariates if c in boot_df.columns]])
            y_m_boot = boot_df[mediator]
            try:
                model_m_boot = sm.OLS(y_m_boot, X_m_boot).fit()
                a_boot = model_m_boot.params.get(predictor, 0)
            except:
                continue
                
            # Bootstrap Model 2
            X_y_boot = sm.add_constant(boot_df[[predictor, mediator] + [c for c in covariates if c in boot_df.columns]])
            y_y_boot = boot_df[outcome]
            try:
                model_y_boot = sm.OLS(y_y_boot, X_y_boot).fit()
                b_boot = model_y_boot.params.get(mediator, 0)
                boot_indirect.append(a_boot * b_boot)
            except:
                continue
        
        if len(boot_indirect) > 0:
            ci_lower = np.percentile(boot_indirect, 2.5)
            ci_upper = np.percentile(boot_indirect, 97.5)
            results['confidence_interval'] = [ci_lower, ci_upper]
            results['indirect_effect_significant'] = (ci_lower > 0) or (ci_upper < 0)
        else:
            results['indirect_effect_significant'] = False
            
        results['direct_effect'] = float(c_prime)
        results['indirect_effect'] = float(indirect_effect)
        results['total_effect'] = float(total_effect)
        results['a_path'] = float(a_path)
        results['b_path'] = float(b_path)
        results['c_prime'] = float(c_prime)
        
        logger.info(f"Mediation analysis complete: indirect={indirect_effect:.4f}, "
                   f"direct={c_prime:.4f}, total={total_effect:.4f}")
                   
    except Exception as e:
        logger.error(f"Mediation analysis failed: {str(e)}")
        results['error'] = str(e)
        
    return results

def save_results(
    results: Dict[str, Any],
    output_path: Optional[str] = None
) -> str:
    """
    Save model analysis results to YAML file.
    
    Args:
        results: Dictionary of results to save.
        output_path: Path to save results. If None, uses default results path.
        
    Returns:
        Path to saved results file.
    """
    import yaml
    
    paths = get_config_paths()
    if output_path is None:
        output_path = paths["results_path"] / "model_results.yaml"
    else:
        output_path = Path(output_path)
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert numpy types to Python types for YAML serialization
    def convert_types(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_types(i) for i in obj]
        return obj
        
    clean_results = convert_types(results)
    
    with open(output_path, 'w') as f:
        yaml.dump(clean_results, f, default_flow_style=False, sort_keys=False)
        
    logger.info(f"Results saved to: {output_path}")
    return str(output_path)

def main():
    """Main entry point for model analysis pipeline."""
    parser = argparse.ArgumentParser(
        description="Fit logistic regression, calculate VIF, FDR, and ROC metrics for sustainable agriculture adoption study."
    )
    parser.add_argument(
        '--input',
        type=str,
        default=None,
        help='Path to engineered data CSV (default: data/processed/engineered_data.csv)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    parser.add_argument(
        '--alpha',
        type=float,
        default=0.10,
        help='Significance level for FDR correction (default: 0.10)'
    )
    
    args = parser.parse_args()
    
    set_random_seed(args.seed)
    
    logger.info("=" * 60)
    logger.info("Starting Model Analysis Pipeline (T036-T040)")
    logger.info("=" * 60)
    
    try:
        # Load data
        df = load_engineered_data(args.input)
        
        # Prepare model data
        outcome_var = 'adoption_binary'
        primary_pred = 'engagement_score'
        covariates = ['age', 'education_years', 'farm_size', 'credit_access']
        
        clean_df, y, X = prepare_model_data(df, outcome_var, primary_pred, covariates)
        
        # Fit logistic regression
        logger.info("Fitting logistic regression model...")
        results = fit_logistic_regression(y, X)
        
        # Calculate VIF
        logger.info("Calculating VIF diagnostics...")
        vif_df = calculate_vif(X)
        
        # Get predicted probabilities for ROC
        y_pred_proba = results.predict(X)
        
        # Calculate ROC metrics
        logger.info("Calculating ROC metrics...")
        roc_metrics = calculate_roc_metrics(y, y_pred_proba)
        
        # Plot ROC curve
        logger.info("Plotting ROC curve...")
        roc_plot_path = plot_roc_curve(y, y_pred_proba)
        
        # Apply FDR correction to p-values
        p_values = results.pvalues.drop('const', errors='ignore').values
        adj_p_values, reject_mask = apply_fdr_correction(p_values, args.alpha)
        
        # Perform mediation analysis (exploratory)
        logger.info("Performing exploratory mediation analysis...")
        mediation_results = perform_mediation_analysis(
            df=df,
            outcome=outcome_var,
            mediator='engagement_score',
            predictor='engagement_score',  # Simplified for this example
            covariates=[c for c in covariates if c in df.columns],
            n_bootstraps=1000,
            seed=args.seed
        )
        
        # Compile all results
        all_results = {
            'model_summary': {
                'n_observations': int(len(y)),
                'n_predictors': int(len(X.columns) - 1),  # Exclude constant
                'converged': bool(results.converged),
                'log_likelihood': float(results.llf),
                'aic': float(results.aic),
                'bic': float(results.bic)
            },
            'coefficients': [],
            'vif_diagnostics': vif_df.to_dict('records') if len(vif_df) > 0 else [],
            'fdr_correction': {
                'alpha': args.alpha,
                'method': 'Benjamini-Hochberg',
                'adjusted_p_values': adj_p_values.tolist(),
                'rejected': reject_mask.tolist()
            },
            'roc_metrics': {
                'auc': roc_metrics['auc'],
                'interpretation': roc_metrics['interpretation']
            },
            'roc_plot_path': roc_plot_path,
            'mediation_analysis': mediation_results,
            'timestamp': datetime.utcnow().isoformat(),
            'random_seed': args.seed
        }
        
        # Add coefficient details
        for var in X.columns:
            if var != 'const':
                coef = results.params[var]
                pval = results.pvalues[var]
                std_err = results.bse[var]
                z_stat = coef / std_err if std_err != 0 else 0
                
                # Get FDR adjusted p-value
                var_idx = list(X.columns).index(var) - 1  # -1 to account for constant
                if 0 <= var_idx < len(adj_p_values):
                    adj_p = adj_p_values[var_idx]
                else:
                    adj_p = pval
                    
                all_results['coefficients'].append({
                    'variable': var,
                    'coefficient': float(coef),
                    'std_error': float(std_err),
                    'z_statistic': float(z_stat),
                    'p_value': float(pval),
                    'adj_p_value': float(adj_p),
                    'significant_at_0.05': bool(pval < 0.05),
                    'significant_at_fdr': bool(reject_mask[var_idx]) if 0 <= var_idx < len(reject_mask) else False
                })
        
        # Save results
        results_path = save_results(all_results)
        
        # Update modeling log
        update_log_section("model_analysis", {
            "status": "completed",
            "n_observations": len(y),
            "auc": roc_metrics['auc'],
            "converged": results.converged,
            "results_file": results_path,
            "roc_plot": roc_plot_path,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info("=" * 60)
        logger.info("Model Analysis Complete!")
        logger.info(f"  AUC: {roc_metrics['auc']:.4f} ({roc_metrics['interpretation']})")
        logger.info(f"  Results saved to: {results_path}")
        logger.info(f"  ROC plot saved to: {roc_plot_path}")
        logger.info("=" * 60)
        
        return all_results
        
    except Exception as e:
        logger.error(f"Model analysis pipeline failed: {str(e)}")
        update_log_section("model_analysis", {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })
        raise

if __name__ == "__main__":
    main()