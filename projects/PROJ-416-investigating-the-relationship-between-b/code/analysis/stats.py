import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
from code.config import Config

logger = logging.getLogger(__name__)

def calculate_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.
    
    Args:
        df: DataFrame containing the features
        features: List of feature column names
        
    Returns:
        Dictionary mapping feature names to VIF values
    """
    vif_data = {}
    for feature in features:
        if feature not in df.columns:
            logger.warning(f"Feature {feature} not found in DataFrame")
            continue
        
        X = df[features].values
        if X.shape[1] < 2:
            vif_data[feature] = 0.0
            continue
        
        # Create design matrix for this feature
        y = df[feature].values
        X_other = np.column_stack([np.ones(len(df)), 
                                  np.delete(X, features.index(feature), axis=1)])
        
        try:
            # Fit linear model
            model = sm.OLS(y, X_other).fit()
            r_squared = model.rsquared
            vif = 1.0 / (1.0 - r_squared) if r_squared < 1.0 else float('inf')
            vif_data[feature] = vif
        except Exception as e:
            logger.error(f"Error calculating VIF for {feature}: {e}")
            vif_data[feature] = float('inf')
    
    return vif_data

def apply_fdr_correction(p_values: List[float], alpha: float = 0.05) -> Tuple[List[bool], List[float]]:
    """
    Apply False Discovery Rate (FDR) correction to p-values.
    
    Args:
        p_values: List of p-values
        alpha: Significance level
        
    Returns:
        Tuple of (rejection decisions, adjusted p-values)
    """
    if not p_values:
        return [], []
    
    try:
        reject, p_corrected, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')
        return list(reject), list(p_corrected)
    except Exception as e:
        logger.error(f"FDR correction failed: {e}")
        return [False] * len(p_values), p_values

def run_ancova_analysis(df: pd.DataFrame, 
                       dependent_var: str,
                       independent_vars: List[str],
                       confounds: List[str] = None,
                       fd_covariate: str = 'fd_mean',
                       motion_thresholds: List[float] = [2.0, 3.0],
                       p_values: List[str] = ['uncorrected', '0.05', '0.1']) -> Dict:
    """
    Run ANCOVA analysis with sensitivity analysis for motion thresholds and p-values.
    
    Args:
        df: DataFrame with all variables
        dependent_var: Name of dependent variable (post-treatment score)
        independent_vars: List of independent variables (pre-treatment score, network metrics)
        confounds: List of confound variables
        fd_covariate: Name of framewise displacement covariate
        motion_thresholds: List of motion thresholds to sweep (2mm, 3mm)
        p_values: List of p-value correction strategies to sweep
        
    Returns:
        Dictionary containing analysis results for each sweep configuration
    """
    results = {}
    
    # Ensure required columns exist
    required_cols = [dependent_var] + independent_vars + [fd_covariate]
    if confounds:
        required_cols.extend(confounds)
        
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Store baseline analysis results
    baseline_results = {
        'motion_threshold': 'baseline',
        'p_correction': 'uncorrected',
        'coefficients': {},
        'p_values': {},
        'vif': {},
        'n_samples': len(df)
    }
    
    # Run baseline analysis (all data, uncorrected)
    try:
        X = df[independent_vars + confounds + [fd_covariate] if confounds else [fd_covariate]].copy()
        X = sm.add_constant(X)
        y = df[dependent_var]
        
        model = sm.OLS(y, X).fit()
        
        baseline_results['coefficients'] = model.params.to_dict()
        baseline_results['p_values'] = model.pvalues.to_dict()
        baseline_results['rsquared'] = model.rsquared
        baseline_results['n_samples'] = model.nobs
        
        # Calculate VIF
        all_features = independent_vars + (confounds if confounds else []) + [fd_covariate]
        baseline_results['vif'] = calculate_vif(df, all_features)
        
        results['baseline'] = baseline_results
    except Exception as e:
        logger.error(f"Baseline ANCOVA failed: {e}")
        results['baseline_error'] = str(e)
    
    # Sensitivity analysis: Sweep motion thresholds
    for threshold in motion_thresholds:
        threshold_key = f"motion_{threshold}mm"
        
        # Filter data based on motion threshold
        motion_filtered_df = df[df[fd_covariate] <= threshold].copy()
        
        if len(motion_filtered_df) < 5:
            logger.warning(f"Insufficient samples ({len(motion_filtered_df)}) for motion threshold {threshold}mm")
            results[threshold_key] = {'error': f'Insufficient samples: {len(motion_filtered_df)}'}
            continue
        
        # Run analysis with filtered data
        try:
            X = motion_filtered_df[independent_vars + (confounds if confounds else []) + [fd_covariate]].copy()
            X = sm.add_constant(X)
            y = motion_filtered_df[dependent_var]
            
            model = sm.OLS(y, X).fit()
            
            threshold_results = {
                'motion_threshold': threshold,
                'p_correction': 'uncorrected',
                'coefficients': model.params.to_dict(),
                'p_values': model.pvalues.to_dict(),
                'rsquared': model.rsquared,
                'n_samples': model.nobs,
                'vif': calculate_vif(motion_filtered_df, independent_vars + (confounds if confounds else []) + [fd_covariate])
            }
            
            results[threshold_key] = threshold_results
        except Exception as e:
            logger.error(f"Motion threshold analysis {threshold}mm failed: {e}")
            results[f"{threshold_key}_error"] = str(e)
    
    # Sensitivity analysis: Sweep p-value corrections
    for p_val_strategy in p_values:
        p_key = f"p_{p_val_strategy}"
        
        # For uncorrected, we already have baseline
        if p_val_strategy == 'uncorrected':
            if 'baseline' in results:
                results[p_key] = results['baseline'].copy()
                results[p_key]['p_correction'] = 'uncorrected'
            continue
        
        # For corrected p-values, use baseline data but apply FDR
        try:
            if 'baseline' not in results or 'p_values' not in results['baseline']:
                raise ValueError("No baseline results available for p-value correction")
            
            p_values_list = list(results['baseline']['p_values'].values())
            alpha = float(p_val_strategy)
            
            reject, p_corrected = apply_fdr_correction(p_values_list, alpha=alpha)
            
            # Update p-values in results
            corrected_results = results['baseline'].copy()
            corrected_results['p_correction'] = p_val_strategy
            corrected_results['p_values_corrected'] = p_corrected
            corrected_results['rejected'] = reject
            
            results[p_key] = corrected_results
            
        except Exception as e:
            logger.error(f"P-value correction {p_val_strategy} failed: {e}")
            results[f"{p_key}_error"] = str(e)
    
    # Combined sensitivity: motion thresholds with p-value corrections
    for threshold in motion_thresholds:
        for p_val_strategy in p_values:
            if p_val_strategy == 'uncorrected':
                continue  # Already handled above
            
            combined_key = f"motion_{threshold}mm_p_{p_val_strategy}"
            
            # Get motion filtered results
            motion_key = f"motion_{threshold}mm"
            if motion_key not in results or 'error' in results[motion_key]:
                continue
            
            try:
                # Re-run analysis on motion-filtered data with p-value correction
                motion_filtered_df = df[df[fd_covariate] <= threshold].copy()
                
                X = motion_filtered_df[independent_vars + (confounds if confounds else []) + [fd_covariate]].copy()
                X = sm.add_constant(X)
                y = motion_filtered_df[dependent_var]
                
                model = sm.OLS(y, X).fit()
                
                p_values_list = list(model.pvalues.values())
                alpha = float(p_val_strategy)
                reject, p_corrected = apply_fdr_correction(p_values_list, alpha=alpha)
                
                combined_results = {
                    'motion_threshold': threshold,
                    'p_correction': p_val_strategy,
                    'coefficients': model.params.to_dict(),
                    'p_values': model.pvalues.to_dict(),
                    'p_values_corrected': p_corrected,
                    'rejected': reject,
                    'rsquared': model.rsquared,
                    'n_samples': model.nobs
                }
                
                results[combined_key] = combined_results
                
            except Exception as e:
                logger.error(f"Combined analysis {combined_key} failed: {e}")
                results[f"{combined_key}_error"] = str(e)
    
    return results

def run_analysis(config: Config) -> Dict:
    """
    Run the complete statistical analysis pipeline including sensitivity analysis.
    
    Args:
        config: Configuration object
        
    Returns:
        Dictionary containing all analysis results
    """
    logger.info("Starting statistical analysis with sensitivity analysis")
    
    # Load data
    metrics_path = config.DATA_METRICS_PATH / "network_metrics.csv"
    if not metrics_path.exists():
        raise FileNotFoundError(f"Network metrics file not found: {metrics_path}")
    
    df = pd.read_csv(metrics_path)
    logger.info(f"Loaded {len(df)} subjects from {metrics_path}")
    
    # Define analysis parameters from config or defaults
    dependent_var = config.get('DEPENDENT_VAR', 'post_treatment_score')
    independent_vars = [config.get('INDEPENDENT_VAR', 'pre_treatment_score')]
    confounds = config.get('CONFOUNDS', []).split(',') if config.get('CONFOUNDS') else []
    fd_covariate = config.get('FD_COVARIATE', 'fd_mean')
    
    # Sensitivity analysis parameters
    motion_thresholds = [2.0, 3.0]  # mm
    p_values = ['uncorrected', '0.05', '0.1']
    
    # Run ANCOVA with sensitivity analysis
    results = run_ancova_analysis(
        df=df,
        dependent_var=dependent_var,
        independent_vars=independent_vars,
        confounds=confounds,
        fd_covariate=fd_covariate,
        motion_thresholds=motion_thresholds,
        p_values=p_values
    )
    
    logger.info(f"Analysis complete. Results for {len(results)} configurations generated")
    
    return results

def main():
    """Main entry point for statistical analysis."""
    import sys
    from code.config import Config
    
    # Setup logging
    from code.utils.logging import setup_logging
    setup_logging()
    
    try:
        config = Config()
        results = run_analysis(config)
        
        # Save results
        output_path = config.DATA_METRICS_PATH / "statistical_results.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert results to DataFrame for saving
        flat_results = []
        for config_key, config_results in results.items():
            if 'error' in config_results:
                continue
            
            row = {'configuration': config_key}
            row.update(config_results)
            
            # Flatten nested dictionaries
            for key, value in config_results.items():
                if isinstance(value, dict):
                    for k, v in value.items():
                        row[f"{key}_{k}"] = v
            
            flat_results.append(row)
        
        if flat_results:
            results_df = pd.DataFrame(flat_results)
            results_df.to_csv(output_path, index=False)
            logger.info(f"Results saved to {output_path}")
        else:
            logger.warning("No valid results to save")
            
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()