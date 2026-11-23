import os
import sys
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from scipy import stats
from utils.logging import get_logger
from utils.exceptions import DataInsufficientError, SchemaMismatchError
from utils.config import get_processed_data_path, get_model_results_path, get_log_path

logger = get_logger(__name__)

def load_model_results() -> Dict[str, Any]:
    """Load the model results from the evaluation step."""
    results_path = get_model_results_path()
    if not results_path.exists():
        raise FileNotFoundError(f"Model results file not found at {results_path}")
    
    with open(results_path, 'r') as f:
        return json.load(f)

def load_predictions_for_permutation() -> Tuple[np.ndarray, np.ndarray]:
    """
    Load the actual target values and model predictions from the processed data.
    Assumes the processed dataset contains 'potential_mV' as target and predictions
    are stored or can be regenerated. For this implementation, we assume the
    processed data contains the target and we need to load the predictions from
    a separate file or regenerate them.
    
    Since the task requires comparing against a mean baseline, we need:
    1. Actual target values (y_true)
    2. Model predictions (y_pred)
    
    We will assume the processed dataset has 'potential_mV' and we load the
    predictions from a file generated during training/evaluation.
    """
    processed_data_path = get_processed_data_path()
    if not processed_data_path.exists():
        raise FileNotFoundError(f"Processed data not found at {processed_data_path}")
    
    import pandas as pd
    df = pd.read_parquet(processed_data_path)
    
    if 'potential_mV' not in df.columns:
        raise SchemaMismatchError("Processed data missing 'potential_mV' column")
    
    y_true = df['potential_mV'].values
    
    # For predictions, we assume they are stored in a separate file or
    # we need to load them from the model results. Since the task is about
    # evaluating the null baseline, we need the actual model predictions.
    # We'll load them from a file that should be created during training.
    predictions_path = Path(get_model_results_path()).parent / "model_predictions.parquet"
    if not predictions_path.exists():
        # If predictions file doesn't exist, we need to handle this case.
        # For now, we'll raise an error.
        raise FileNotFoundError(f"Model predictions file not found at {predictions_path}")
    
    pred_df = pd.read_parquet(predictions_path)
    if 'prediction' not in pred_df.columns:
        raise SchemaMismatchError("Predictions file missing 'prediction' column")
    
    y_pred = pred_df['prediction'].values
    
    if len(y_true) != len(y_pred):
        raise SchemaMismatchError(f"Length mismatch: y_true={len(y_true)}, y_pred={len(y_pred)}")
    
    return y_true, y_pred

def calculate_null_baseline_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Calculate metrics for the null baseline (mean prediction).
    
    Returns:
        Dict with 'r2_null', 'rmse_null', 'mean_prediction'
    """
    mean_prediction = np.mean(y_true)
    y_pred_null = np.full_like(y_true, mean_prediction)
    
    # Calculate R² for null model
    ss_res_null = np.sum((y_true - y_pred_null) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    r2_null = 1 - (ss_res_null / ss_tot) if ss_tot != 0 else 0.0
    
    # Calculate RMSE for null model
    rmse_null = np.sqrt(np.mean((y_true - y_pred_null) ** 2))
    
    return {
        'r2_null': float(r2_null),
        'rmse_null': float(rmse_null),
        'mean_prediction': float(mean_prediction)
    }

def permutation_test_on_aggregated_predictions(
    y_true: np.ndarray, 
    y_pred: np.ndarray, 
    n_permutations: int = 1000, 
    random_state: int = 42
) -> Tuple[float, float]:
    """
    Perform a one-sample permutation test on the aggregated predictions.
    
    Null hypothesis: The model's R² is not significantly different from 0.
    Alternative hypothesis: The model's R² is significantly greater than 0.
    
    We permute the target values and recalculate R² for each permutation.
    The p-value is the proportion of permuted R² values that are >= the observed R².
    
    Args:
        y_true: Actual target values
        y_pred: Model predictions
        n_permutations: Number of permutations
        random_state: Random seed for reproducibility
    
    Returns:
        Tuple of (observed_r2, p_value)
    """
    np.random.seed(random_state)
    
    # Calculate observed R²
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    observed_r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    
    # Permutation test
    permuted_r2_values = []
    for i in range(n_permutations):
        # Shuffle y_true
        y_true_permuted = np.random.permutation(y_true)
        ss_res_perm = np.sum((y_true_permuted - y_pred) ** 2)
        ss_tot_perm = np.sum((y_true_permuted - np.mean(y_true_permuted)) ** 2)
        r2_perm = 1 - (ss_res_perm / ss_tot_perm) if ss_tot_perm != 0 else 0.0
        permuted_r2_values.append(r2_perm)
    
    permuted_r2_values = np.array(permuted_r2_values)
    
    # Calculate p-value (one-tailed test: is observed R² significantly greater than permuted?)
    p_value = np.sum(permuted_r2_values >= observed_r2) / n_permutations
    
    return observed_r2, float(p_value)

def classify_learnability(observed_r2: float, p_value: float, threshold_r2: float = 0.0, threshold_p: float = 0.05) -> Dict[str, Any]:
    """
    Classify whether the model is "learnable" based on R² and p-value.
    
    Criteria:
    - R² > 0.0 (or threshold_r2)
    - p-value < 0.05 (or threshold_p)
    
    Args:
        observed_r2: Observed R² from the model
        p_value: P-value from the permutation test
        threshold_r2: Minimum R² threshold for learnability
        threshold_p: Maximum p-value threshold for learnability
    
    Returns:
        Dict with classification result and details
    """
    is_learnable = (observed_r2 > threshold_r2) and (p_value < threshold_p)
    
    return {
        'is_learnable': is_learnable,
        'observed_r2': observed_r2,
        'p_value': p_value,
        'r2_threshold': threshold_r2,
        'p_threshold': threshold_p,
        'classification': 'learnable' if is_learnable else 'not_learnable'
    }

def run_null_baseline_analysis(
    y_true: np.ndarray, 
    y_pred: np.ndarray, 
    n_permutations: int = 1000, 
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Run the complete null baseline analysis.
    
    Steps:
    1. Calculate null baseline metrics (mean prediction)
    2. Perform permutation test on aggregated predictions
    3. Classify learnability
    
    Args:
        y_true: Actual target values
        y_pred: Model predictions
        n_permutations: Number of permutations for the test
        random_state: Random seed
    
    Returns:
        Dict with all analysis results
    """
    # Calculate null baseline metrics
    null_metrics = calculate_null_baseline_metrics(y_true, y_pred)
    
    # Perform permutation test
    observed_r2, p_value = permutation_test_on_aggregated_predictions(
        y_true, y_pred, n_permutations, random_state
    )
    
    # Classify learnability
    learnability = classify_learnability(observed_r2, p_value)
    
    return {
        'null_baseline_metrics': null_metrics,
        'permutation_test': {
            'observed_r2': observed_r2,
            'p_value': p_value,
            'n_permutations': n_permutations,
            'random_state': random_state
        },
        'learnability': learnability
    }

def main():
    """Main entry point for the null baseline evaluation."""
    logger.info("Starting null baseline evaluation")
    
    try:
        # Load model results (for context, though we load predictions separately)
        model_results = load_model_results()
        logger.info(f"Loaded model results: {model_results.get('best_model', 'N/A')}")
        
        # Load predictions and true values
        y_true, y_pred = load_predictions_for_permutation()
        logger.info(f"Loaded {len(y_true)} predictions for analysis")
        
        # Run null baseline analysis
        analysis_results = run_null_baseline_analysis(y_true, y_pred)
        
        # Save results to a JSON file
        results_dir = Path(get_model_results_path()).parent
        output_path = results_dir / "null_baseline_results.json"
        
        with open(output_path, 'w') as f:
            json.dump(analysis_results, f, indent=2)
        
        logger.info(f"Null baseline results saved to {output_path}")
        logger.info(f"Learnability classification: {analysis_results['learnability']['classification']}")
        logger.info(f"Observed R²: {analysis_results['permutation_test']['observed_r2']:.4f}")
        logger.info(f"P-value: {analysis_results['permutation_test']['p_value']:.4f}")
        
        # Update the main model_results.json with learnability info
        model_results['null_baseline_analysis'] = analysis_results
        model_results['learnable'] = analysis_results['learnability']['is_learnable']
        
        with open(get_model_results_path(), 'w') as f:
            json.dump(model_results, f, indent=2)
        
        logger.info("Updated model_results.json with null baseline analysis")
        
    except Exception as e:
        logger.error(f"Error during null baseline evaluation: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
