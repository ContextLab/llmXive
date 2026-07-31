import os
import sys
import json
import logging
import warnings
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.regression.mixed_linear_model import MixedLM
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.genmod import families
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_processed_data(file_path: str) -> pd.DataFrame:
    """Load processed data from a CSV file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")
    return pd.read_csv(path)

def save_processed_data(df: pd.DataFrame, file_path: str):
    """Save processed data to a CSV file."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Saved processed data to {file_path}")

def compute_collinearity_diagnostics(valid_threads_path: str, thread_metrics_path: str, output_path: str):
    """
    Compute Variance Inflation Factor (VIF) for predictors.
    Implements T030 requirements.
    """
    logger.info("Computing collinearity diagnostics...")
    
    # Load data
    try:
        valid_threads = load_processed_data(valid_threads_path)
        thread_metrics = load_processed_data(thread_metrics_path)
    except FileNotFoundError as e:
        logger.error(f"Data loading failed: {e}")
        return {"vif_scores": {}, "threshold": 5, "flagged": False}

    # Merge on thread_id
    df = pd.merge(valid_threads, thread_metrics, on='thread_id', how='inner')
    
    # Select predictors for VIF
    predictors = ['sentiment', 'thread_length', 'time_to_decision', 'external_validation_score']
    # Filter to numeric columns that exist
    available_predictors = [p for p in predictors if p in df.columns and pd.api.types.is_numeric_dtype(df[p])]
    
    if len(available_predictors) < 2:
        logger.warning("Insufficient predictors for VIF calculation.")
        result = {
            "vif_scores": {p: None for p in predictors},
            "threshold": 5,
            "flagged": False
        }
        save_processed_data(pd.DataFrame([result]), output_path) # Save as JSON compatible format later
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        return result

    # Check pairwise correlations first (as per T030 logic)
    corr_matrix = df[available_predictors].corr()
    high_corr_pairs = []
    for i in range(len(available_predictors)):
        for j in range(i+1, len(available_predictors)):
            if abs(corr_matrix.iloc[i, j]) > 0.0:
                high_corr_pairs.append((available_predictors[i], available_predictors[j]))
    
    if len(high_corr_pairs) < 2:
        logger.info("No significant pairwise correlations found. Skipping VIF.")
        result = {
            "vif_scores": {p: None for p in predictors},
            "threshold": 5,
            "flagged": False
        }
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        return result

    # Compute VIF
    X = df[available_predictors].dropna()
    if X.empty or len(X) < 5:
        logger.warning("Insufficient data for VIF computation.")
        result = {
            "vif_scores": {p: None for p in predictors},
            "threshold": 5,
            "flagged": False
        }
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        return result

    # Add constant for intercept
    X_const = sm.add_constant(X)
    vif_data = {}
    flagged = False
    
    for col in X.columns:
        try:
            vif = variance_inflation_factor(X_const.values, X_const.columns.get_loc(col))
            vif_data[col] = float(vif)
            if vif > 5:
                flagged = True
        except Exception as e:
            logger.warning(f"Could not compute VIF for {col}: {e}")
            vif_data[col] = None

    result = {
        "vif_scores": {p: vif_data.get(p) for p in predictors},
        "threshold": 5,
        "flagged": flagged
    }

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Collinearity diagnostics saved to {output_path}. Flagged: {flagged}")
    return result

def run_collinearity_pipeline():
    """Main entry point for collinearity diagnostics."""
    valid_threads_path = "data/processed/valid_threads.csv"
    thread_metrics_path = "data/processed/thread_metrics.csv"
    output_path = "data/processed/collinearity_diagnostics.json"
    compute_collinearity_diagnostics(valid_threads_path, thread_metrics_path, output_path)

def compute_sensitivity_analysis(valid_threads_path: str, thread_metrics_path: str, output_path: str):
    """
    Compute sensitivity analysis for agreement and entropy thresholds.
    Implements T023b requirements.
    """
    logger.info("Computing sensitivity analysis...")
    
    # Load data
    try:
        valid_threads = load_processed_data(valid_threads_path)
        thread_metrics = load_processed_data(thread_metrics_path)
    except FileNotFoundError as e:
        logger.error(f"Data loading failed: {e}")
        return

    # Merge
    df = pd.merge(valid_threads, thread_metrics, on='thread_id', how='inner')
    
    # Define grid
    agreement_cutoffs = [0.5, 0.6, 0.7]
    entropy_thresholds = [0.2, 0.4, 0.6]
    
    results = []
    
    for ac in agreement_cutoffs:
        for et in entropy_thresholds:
            # Filter
            mask = (df['agreement_proportion'] >= ac) & (df['shannon_entropy'] <= et)
            subset = df[mask]
            thread_count = len(subset)
            
            corr_agreement = None
            corr_entropy = None
            corr_validation = None
            fp_rate = None
            fn_rate = None
            
            if thread_count >= 2:
                try:
                    # Correlation with agreement_proportion
                    if 'agreement_proportion' in subset.columns and 'contagion_index' in subset.columns:
                        corr_agreement, _ = stats.pearsonr(subset['agreement_proportion'], subset['contagion_index'])
                    
                    # Correlation with shannon_entropy
                    if 'shannon_entropy' in subset.columns and 'contagion_index' in subset.columns:
                        corr_entropy, _ = stats.pearsonr(subset['shannon_entropy'], subset['contagion_index'])
                    
                    # Correlation with external_validation_score
                    if 'external_validation_score' in subset.columns and 'contagion_index' in subset.columns:
                        valid_scores = subset.dropna(subset=['external_validation_score', 'contagion_index'])
                        if len(valid_scores) >= 2:
                            corr_validation, _ = stats.pearsonr(valid_scores['external_validation_score'], valid_scores['contagion_index'])
                    
                    # FP/FN (simplified logic for demonstration, assumes consensus logic exists in data)
                    # In a real scenario, this would depend on specific ground truth columns
                    if 'consensus_score' in subset.columns and 'ground_truth' in subset.columns:
                        # Example logic
                        tp = ((subset['consensus_score'] == 1) & (subset['ground_truth'] == 1)).sum()
                        fp = ((subset['consensus_score'] == 1) & (subset['ground_truth'] == 0)).sum()
                        fn = ((subset['consensus_score'] == 0) & (subset['ground_truth'] == 1)).sum()
                        tn = ((subset['consensus_score'] == 0) & (subset['ground_truth'] == 0)).sum()
                        
                        if (fp + tn) > 0: fp_rate = fp / (fp + tn)
                        if (fn + tp) > 0: fn_rate = fn / (fn + tp)
                except Exception as e:
                    logger.warning(f"Error computing metrics for cutoff {ac}, threshold {et}: {e}")
            else:
                logger.warning(f"Insufficient data points ({thread_count}) for cutoff {ac}, threshold {et}")

            results.append({
                'agreement_cutoff': ac,
                'entropy_threshold': et,
                'correlation_agreement': corr_agreement,
                'correlation_entropy': corr_entropy,
                'correlation_validation': corr_validation,
                'false_positive_rate': fp_rate,
                'false_negative_rate': fn_rate,
                'thread_count': thread_count,
                'grid_coverage': True if thread_count >= 2 else False
            })
    
    result_df = pd.DataFrame(results)
    
    # Add trend summary (T023c)
    # Check correlation_agreement trend across 0.5 -> 0.6 -> 0.7 for a fixed entropy
    # Simplified: just check the first valid entropy threshold
    valid_rows = result_df[result_df['correlation_agreement'].notna()].groupby('entropy_threshold').first()
    if not valid_rows.empty:
        vals = valid_rows['correlation_agreement'].values
        if len(vals) >= 2:
            if vals[0] > vals[-1]:
                trend = "decreasing trend"
            elif vals[0] < vals[-1]:
                trend = "increasing trend"
            else:
                trend = "stable trend"
            result_df['trend_summary'] = trend
        else:
            result_df['trend_summary'] = "insufficient data for trend"
    else:
        result_df['trend_summary'] = "no valid data for trend"

    save_processed_data(result_df, output_path)
    logger.info(f"Sensitivity analysis saved to {output_path}")

def run_sensitivity_pipeline():
    """Main entry point for sensitivity analysis."""
    valid_threads_path = "data/processed/valid_threads.csv"
    thread_metrics_path = "data/processed/thread_metrics.csv"
    output_path = "data/processed/sensitivity_analysis.csv"
    compute_sensitivity_analysis(valid_threads_path, thread_metrics_path, output_path)

def check_model_convergence(model_result, thread_id: str, log_path: str):
    """
    Check if a GLMM model converged and log diagnostics.
    Implements T068 requirement.
    """
    log_entries = []
    if Path(log_path).exists():
        with open(log_path, 'r') as f:
            log_entries = json.load(f) if f.read().strip() else []
    
    status = "converged"
    message = ""
    
    # Check convergence attribute if available (e.g., from statsmodels)
    if hasattr(model_result, 'converged'):
        if model_result.converged:
            message = "Model converged successfully."
        else:
            status = "failed"
            message = f"Model did not converge. Hessian status: {getattr(model_result, 'hess_inv_op', 'N/A')}"
    elif hasattr(model_result, 'mle_retvals'):
        # Fallback for some GLM/MixedLM versions
        if model_result.mle_retvals.get('converged', False):
            message = "Model converged successfully."
        else:
            status = "failed"
            message = f"Model did not converge. Retvals: {model_result.mle_retvals}"
    else:
        # Best effort: check if standard errors exist
        try:
            _ = model_result.bse
            message = "Model parameters estimated (convergence assumed)."
        except Exception as e:
            status = "failed"
            message = f"Model estimation failed: {str(e)}"

    entry = {
        "thread_id": thread_id,
        "status": status,
        "message": message,
        "iterations": getattr(model_result, 'mle_settings', {}).get('maxiter', 'N/A')
    }
    log_entries.append(entry)
    
    with open(log_path, 'w') as f:
        json.dump(log_entries, f, indent=2)
    
    if status == "failed":
        logger.warning(f"Model for thread {thread_id} did not converge: {message}")
    else:
        logger.info(f"Model for thread {thread_id} status: {status}")
    
    return status, message

def fit_glmm_with_convergence_check(data_path: str, output_path: str, log_path: str):
    """
    Fit GLMMs and check convergence.
    This is a wrapper to demonstrate T068 integration.
    """
    logger.info("Fitting GLMMs with convergence checks...")
    
    if not Path(data_path).exists():
        logger.error(f"Data file {data_path} not found. Skipping GLMM fit.")
        return

    df = pd.read_csv(data_path)
    
    # Ensure log file exists
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    if not Path(log_path).exists():
        with open(log_path, 'w') as f:
            json.dump([], f)

    # Example: Fit a simple model for demonstration of convergence check
    # In reality, this would loop over threads or fit a global model
    # Assuming 'contagion_index' is outcome and 'sentiment' is predictor
    if 'contagion_index' not in df.columns or 'sentiment' not in df.columns:
        logger.warning("Required columns missing for GLMM fit. Skipping.")
        return

    # Clean data
    clean_df = df.dropna(subset=['contagion_index', 'sentiment'])
    if len(clean_df) < 5:
        logger.warning("Insufficient data for GLMM fit.")
        return

    try:
        # Fit a basic MixedLM (random intercept per thread_id if available, else groupby)
        # If thread_id is not in df, we might group by a dummy or just use GLM
        if 'thread_id' in clean_df.columns:
            model = MixedLM.from_formula('contagion_index ~ sentiment', groups='thread_id', data=clean_df)
        else:
            # Fallback to GLM if no grouping variable
            model = GLM.from_formula('contagion_index ~ sentiment', data=clean_df, family=families.Gaussian())
        
        result = model.fit()
        
        # Check convergence
        check_model_convergence(result, "global_model", log_path)
        
        # Save results (simplified)
        results_df = pd.DataFrame({
            'thread_id': ['global'],
            'coef_sentiment': [result.params.get('sentiment', np.nan)],
            'pvalue_sentiment': [result.pvalues.get('sentiment', np.nan)],
            'converged': [result.converged if hasattr(result, 'converged') else True]
        })
        save_processed_data(results_df, output_path)
        
    except Exception as e:
        logger.error(f"GLMM fitting failed: {e}")
        check_model_convergence(type('obj', (object,), {'converged': False, 'mle_retvals': {'converged': False}}), "error_model", log_path)

def main():
    """Main entry point for the modeling module."""
    logger.info("Starting modeling pipeline...")
    # Run specific pipelines based on task requirements
    # T030: Collinearity
    run_collinearity_pipeline()
    # T023b: Sensitivity
    run_sensitivity_pipeline()
    # T020/T068: GLMM with convergence check
    fit_glmm_with_convergence_check("data/processed/valid_threads.csv", "data/processed/glmm_results.csv", "data/processed/model_convergence.log")
    logger.info("Modeling pipeline completed.")

if __name__ == "__main__":
    main()
