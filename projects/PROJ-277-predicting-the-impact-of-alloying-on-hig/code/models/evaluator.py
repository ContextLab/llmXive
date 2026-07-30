"""
Model evaluation and gap analysis module.

This module provides functionality for:
- Comparative error analysis between composition-only and augmented models
- Gap analysis to quantify microstructural effects
- Statistical power calculation for insufficient data scenarios
- Identification of high microstructural sensitivity samples
"""
import os
import sys
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple, List
from scipy import stats
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
import logging

# Add parent directory to path for imports when running as script
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import get_logger


def calculate_statistical_power(n_samples: int, effect_size: float = 0.5, 
                              alpha: float = 0.05) -> Dict[str, Any]:
    """
    Calculate statistical power for a given sample size and effect size.
    
    Args:
        n_samples: Number of samples in the dataset
        effect_size: Expected effect size (Cohen's d), default 0.5 (medium)
        alpha: Significance level, default 0.05
    
    Returns:
        Dict containing:
            - power: Calculated statistical power (0-1)
            - status: 'insufficient', 'adequate', or 'good'
            - min_samples_required: Minimum samples for 80% power
    """
    logger = get_logger("calculate_statistical_power")
    
    if n_samples <= 0:
        return {
            'power': 0.0,
            'status': 'insufficient',
            'min_samples_required': 64,  # Approximate for medium effect size
            'message': 'No samples available'
        }
    
    # Calculate power using t-test approximation
    # For two-sample t-test with equal variance
    # Power = P(reject H0 | H1 is true)
    
    # Effect size (Cohen's d)
    d = effect_size
    
    # Sample size per group (assuming equal groups for simplicity)
    n_per_group = n_samples / 2 if n_samples > 1 else 1
    
    # Non-centrality parameter
    ncp = d * np.sqrt(n_per_group / 2)
    
    # Critical t-value
    df = n_samples - 2
    t_crit = stats.t.ppf(1 - alpha/2, df)
    
    # Power calculation using non-central t-distribution
    # Power = 1 - CDF(t_crit, df, ncp) + CDF(-t_crit, df, ncp)
    power = 1 - stats.nct.cdf(t_crit, df, ncp) + stats.nct.cdf(-t_crit, df, ncp)
    
    # Determine status
    if power < 0.5:
        status = 'insufficient'
    elif power < 0.8:
        status = 'adequate'
    else:
        status = 'good'
    
    # Calculate minimum samples required for 80% power
    # Using approximation: n ≈ 2 * (z_alpha + z_beta)^2 / d^2
    z_alpha = stats.norm.ppf(1 - alpha/2)
    z_beta = stats.norm.ppf(0.8)  # For 80% power
    min_samples = int(np.ceil(2 * (z_alpha + z_beta)**2 / d**2))
    
    result = {
        'power': float(power),
        'status': status,
        'min_samples_required': min_samples,
        'effect_size': effect_size,
        'alpha': alpha,
        'n_samples': n_samples
    }
    
    logger.info(f"Statistical power calculated: {power:.3f} ({status})")
    
    return result


def evaluate_gap_analysis(df: pd.DataFrame, 
                        composition_models: Dict[str, Any],
                        augmented_models: Optional[Dict[str, Any]] = None,
                        min_sample_size: int = 50) -> Dict[str, Any]:
    """
    Perform comparative gap analysis between composition-only and augmented models.
    
    Args:
        df: DataFrame with processed alloy data including microstructural features
        composition_models: Dictionary of trained composition-only models
        augmented_models: Dictionary of trained augmented models (composition + microstructure)
        min_sample_size: Minimum samples required for valid gap analysis
    
    Returns:
        Dict containing:
            - status: 'success', 'inconclusive', or 'error'
            - reason: Explanation if status is not 'success'
            - composition_only_rmse: RMSE of composition-only model
            - augmented_rmse: RMSE of augmented model (if available)
            - error_reduction_pct: Percentage error reduction
            - statistical_power: Power analysis results
            - sensitive_samples: List of high-sensitivity alloy IDs
            - predictions: DataFrame with predictions from both models
    """
    logger = get_logger("evaluate_gap_analysis")
    
    result = {
        'status': 'error',
        'reason': '',
        'composition_only_rmse': None,
        'augmented_rmse': None,
        'error_reduction_pct': None,
        'statistical_power': None,
        'sensitive_samples': [],
        'predictions': None
    }
    
    # Check if augmented models are available
    if augmented_models is None:
        # Count samples with microstructural data
        microstructural_mask = df['grain_size_um'].notna() & df['precipitate_fraction'].notna()
        n_microstructural = microstructural_mask.sum()
        
        logger.info(f"Samples with microstructural data: {n_microstructural}")
        
        if n_microstructural < min_sample_size:
            # Calculate statistical power
            power_result = calculate_statistical_power(n_microstructural)
            
            result['status'] = 'inconclusive'
            result['reason'] = f'Insufficient microstructural data (n={n_microstructural} < {min_sample_size})'
            result['statistical_power'] = power_result
            
            logger.warning(result['reason'])
            logger.info(f"Statistical power: {power_result['power']:.3f} ({power_result['status']})")
            
            # Still generate composition-only predictions
            try:
                predictions = generate_predictions(df, composition_models, model_type='composition_only')
                result['predictions'] = predictions
                result['composition_only_rmse'] = calculate_rmse(
                    df['observed_weight_gain'].values,
                    predictions['predicted_weight_gain'].values
                )
            except Exception as e:
                logger.error(f"Failed to generate composition-only predictions: {str(e)}")
            
            return result
        else:
            # Should have augmented models but doesn't
            result['reason'] = 'Augmented models not provided despite sufficient data'
            return result
    
    # Check if we have enough samples with microstructural data
    microstructural_mask = df['grain_size_um'].notna() & df['precipitate_fraction'].notna()
    df_micro = df[microstructural_mask].copy()
    
    if len(df_micro) < min_sample_size:
        power_result = calculate_statistical_power(len(df_micro))
        
        result['status'] = 'inconclusive'
        result['reason'] = f'Insufficient microstructural data (n={len(df_micro)} < {min_sample_size})'
        result['statistical_power'] = power_result
        
        logger.warning(result['reason'])
        logger.info(f"Statistical power: {power_result['power']:.3f} ({power_result['status']})")
        
        # Generate predictions for all samples
        try:
            predictions = generate_predictions(df, composition_models, model_type='composition_only')
            result['predictions'] = predictions
            result['composition_only_rmse'] = calculate_rmse(
                df['observed_weight_gain'].values,
                predictions['predicted_weight_gain'].values
            )
        except Exception as e:
            logger.error(f"Failed to generate predictions: {str(e)}")
        
        return result
    
    # Perform gap analysis with sufficient data
    logger.info(f"Performing gap analysis with {len(df_micro)} microstructural samples")
    
    try:
        # Generate predictions for composition-only model
        comp_predictions = generate_predictions(df_micro, composition_models, model_type='composition_only')
        comp_rmse = calculate_rmse(
            df_micro['observed_weight_gain'].values,
            comp_predictions['predicted_weight_gain'].values
        )
        
        # Generate predictions for augmented model
        aug_predictions = generate_predictions(df_micro, augmented_models, model_type='augmented')
        aug_rmse = calculate_rmse(
            df_micro['observed_weight_gain'].values,
            aug_predictions['predicted_weight_gain'].values
        )
        
        # Calculate error reduction
        if comp_rmse > 0:
            error_reduction_pct = ((comp_rmse - aug_rmse) / comp_rmse) * 100
        else:
            error_reduction_pct = 0.0
        
        # Identify sensitive samples (high microstructural effect)
        sensitive_samples = identify_sensitive_samples(
            df_micro,
            comp_predictions,
            aug_predictions,
            threshold_factor=2.0
        )
        
        # Calculate statistical power
        power_result = calculate_statistical_power(len(df_micro))
        
        # Combine predictions
        all_predictions = pd.concat([
            comp_predictions.assign(model_type='composition_only'),
            aug_predictions.assign(model_type='augmented')
        ], ignore_index=True)
        
        result['status'] = 'success'
        result['composition_only_rmse'] = float(comp_rmse)
        result['augmented_rmse'] = float(aug_rmse)
        result['error_reduction_pct'] = float(error_reduction_pct)
        result['statistical_power'] = power_result
        result['sensitive_samples'] = sensitive_samples
        result['predictions'] = all_predictions
        
        logger.info(f"Gap analysis complete: RMSE reduced from {comp_rmse:.3f} to {aug_rmse:.3f} ({error_reduction_pct:.1f}% improvement)")
        logger.info(f"Sensitive samples identified: {len(sensitive_samples)}")
        
    except Exception as e:
        logger.error(f"Gap analysis failed: {str(e)}")
        result['reason'] = f'Gap analysis failed: {str(e)}'
    
    return result


def generate_predictions(df: pd.DataFrame, models: Dict[str, Any], 
                       model_type: str = 'composition_only') -> pd.DataFrame:
    """
    Generate predictions using specified model type.
    
    Args:
        df: Input DataFrame with features
        models: Dictionary of trained models
        model_type: Type of model to use ('composition_only' or 'augmented')
    
    Returns:
        DataFrame with predictions
    """
    logger = get_logger("generate_predictions")
    
    if model_type == 'composition_only':
        feature_cols = [col for col in df.columns if col not in 
                      ['alloy_id', 'observed_weight_gain', 'grain_size_um', 'precipitate_fraction']]
        X = df[feature_cols].values
    elif model_type == 'augmented':
        # Ensure all required columns exist
        required_cols = ['alloy_id', 'observed_weight_gain', 'grain_size_um', 'precipitate_fraction']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            logger.warning(f"Missing columns for augmented prediction: {missing_cols}")
            # Fall back to composition-only
            return generate_predictions(df, models, model_type='composition_only')
        
        feature_cols = [col for col in df.columns if col not in 
                      ['alloy_id', 'observed_weight_gain']]
        X = df[feature_cols].values
    else:
        raise ValueError(f"Unknown model_type: {model_type}")
    
    # Get the best model from the dictionary
    if 'best_model' in models:
        best_model = models['best_model']
    elif len(models) > 0:
        # Use first model if no best_model specified
        best_model = list(models.values())[0]
    else:
        raise ValueError("No models provided")
    
    # Generate predictions
    predictions = best_model.predict(X)
    
    # Calculate confidence intervals if available
    if 'confidence_intervals' in models:
        conf_intervals = models['confidence_intervals']
        lower = predictions - conf_intervals['std'] * 1.96
        upper = predictions + conf_intervals['std'] * 1.96
    else:
        # Estimate uncertainty
        std_error = np.std(predictions) * 0.1  # Rough estimate
        lower = predictions - std_error
        upper = predictions + std_error
    
    result_df = pd.DataFrame({
        'alloy_id': df['alloy_id'],
        'predicted_weight_gain': predictions,
        'prediction_uncertainty_lower': lower,
        'prediction_uncertainty_upper': upper
    })
    
    if model_type == 'augmented':
        result_df['grain_size_um'] = df['grain_size_um']
        result_df['precipitate_fraction'] = df['precipitate_fraction']
    
    return result_df


def calculate_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate Root Mean Squared Error."""
    return np.sqrt(mean_squared_error(y_true, y_pred))


def identify_sensitive_samples(df: pd.DataFrame, comp_predictions: pd.DataFrame,
                             aug_predictions: pd.DataFrame, 
                             threshold_factor: float = 2.0) -> List[str]:
    """
    Identify samples with high microstructural sensitivity.
    
    A sample is considered sensitive if the error reduction from 
    composition-only to augmented model is > 2x the median error reduction.
    
    Args:
        df: Original DataFrame
        comp_predictions: Composition-only predictions
        aug_predictions: Augmented predictions
        threshold_factor: Factor above median to consider sensitive
    
    Returns:
        List of alloy IDs with high sensitivity
    """
    logger = get_logger("identify_sensitive_samples")
    
    # Calculate absolute errors for both models
    comp_errors = np.abs(df['observed_weight_gain'].values - 
                       comp_predictions['predicted_weight_gain'].values)
    aug_errors = np.abs(df['observed_weight_gain'].values - 
                      aug_predictions['predicted_weight_gain'].values)
    
    # Error reduction for each sample
    error_reductions = comp_errors - aug_errors
    
    # Median error reduction
    median_reduction = np.median(error_reductions)
    
    # Threshold for sensitivity
    threshold = median_reduction * threshold_factor
    
    # Identify sensitive samples
    sensitive_mask = error_reductions > threshold
    sensitive_ids = df.loc[sensitive_mask, 'alloy_id'].tolist()
    
    logger.info(f"Identified {len(sensitive_ids)} sensitive samples out of {len(df)}")
    
    return sensitive_ids


def main():
    """Main function for standalone execution."""
    logger = get_logger("evaluator_main")
    logger.info("Starting gap analysis evaluation")
    
    # Example usage (would be populated with real data in production)
    print("Gap analysis evaluator module loaded successfully")
    print("Use evaluate_gap_analysis() to perform comparative analysis")


if __name__ == "__main__":
    main()