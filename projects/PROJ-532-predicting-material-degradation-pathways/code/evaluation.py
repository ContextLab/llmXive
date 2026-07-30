import os
import json
import logging
import pickle
from pathlib import Path
from typing import Tuple, Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, confusion_matrix
from sklearn.ensemble import RandomForestClassifier
from sklearn.utils import shuffle

from utils import setup_logging, save_json, load_json, ensure_dir, get_env_var
from config_env import configure_environment

# Configure environment and logging
configure_environment()
logger = setup_logging(__name__)

# Constants
DEFAULT_SEED = 42
DEFAULT_N_PERMUTATIONS = 1000
DEFAULT_ALPHA = 0.05

def generate_stratified_baseline(y_true: np.ndarray, random_state: int = DEFAULT_SEED) -> np.ndarray:
    """
    Generate a stratified random baseline preserving the multi-label correlation structure.
    
    This function shuffles the joint label vector (all labels per sample) to preserve
    the correlation structure between labels while breaking the relationship with features.
    
    Args:
        y_true: Array of shape (n_samples, n_labels) containing the true multi-label targets.
        random_state: Random seed for reproducibility.
        
    Returns:
        y_shuffled: Array of shape (n_samples, n_labels) with shuffled joint labels.
    """
    rng = np.random.RandomState(random_state)
    # Shuffle rows of the joint label vector to preserve multi-label correlations
    indices = rng.permutation(len(y_true))
    return y_true[indices]

def perform_permutation_test(
    model: Any,
    X: np.ndarray,
    y_true: np.ndarray,
    n_permutations: int = DEFAULT_N_PERMUTATIONS,
    random_state: int = DEFAULT_SEED,
    alpha: float = DEFAULT_ALPHA
) -> Dict[str, Any]:
    """
    Perform a permutation test to validate model significance.
    
    This test shuffles the joint label vector n_permutations times and calculates
    the macro-F1 score for each shuffled dataset. It then compares the actual
    model performance against this null distribution to compute a p-value.
    
    Args:
        model: Trained sklearn classifier (e.g., RandomForestClassifier).
        X: Feature matrix of shape (n_samples, n_features).
        y_true: True labels of shape (n_samples, n_labels).
        n_permutations: Number of permutations to perform (default: 1000).
        random_state: Random seed for reproducibility.
        alpha: Significance level threshold (default: 0.05).
        
    Returns:
        Dict containing:
            - 'p_value': Calculated p-value from the permutation test.
            - 'is_significant': Boolean indicating if p < alpha.
            - 'observed_f1': Macro-F1 score of the actual model.
            - 'null_distribution_f1': List of F1 scores from permuted labels.
            - 'n_permutations': Number of permutations performed.
    """
    logger.info(f"Starting permutation test with n={n_permutations} permutations...")
    
    # Calculate observed performance
    y_pred = model.predict(X)
    observed_f1 = f1_score(y_true, y_pred, average='macro')
    logger.info(f"Observed macro-F1: {observed_f1:.4f}")
    
    # Generate null distribution
    rng = np.random.RandomState(random_state)
    null_f1_scores = []
    
    for i in range(n_permutations):
        # Shuffle the joint label vector to preserve multi-label correlations
        y_shuffled = generate_stratified_baseline(y_true, random_state=rng.randint(0, 2**31))
        
        # Train a new model on shuffled data (or evaluate if using a fixed model structure)
        # For efficiency, we re-train a model with the same hyperparameters on shuffled data
        # Note: In a full pipeline, we might use the same model instance if it's already trained
        # but here we re-train to get a fair comparison of the learning algorithm's capability
        # on random data.
        
        # Create a fresh model with same hyperparameters as original
        # We assume the model passed in is a RandomForestClassifier or similar
        # For permutation test, we need to re-train on shuffled data to get a fair baseline
        # However, to save time, we can just predict with the original model on shuffled labels?
        # No, that's not correct. We need to train a model on shuffled data.
        
        # Re-train model on shuffled data
        # We'll use the same hyperparameters as the original model
        # Since we don't have access to original hyperparameters, we use default RF
        temp_model = RandomForestClassifier(
            n_estimators=100, 
            random_state=rng.randint(0, 2**31),
            n_jobs=-1
        )
        temp_model.fit(X, y_shuffled)
        
        # Evaluate
        y_pred_shuffled = temp_model.predict(X)
        f1_shuffled = f1_score(y_shuffled, y_pred_shuffled, average='macro')
        null_f1_scores.append(f1_shuffled)
        
        if (i + 1) % 100 == 0:
            logger.info(f"Permutation {i + 1}/{n_permutations} completed")
    
    null_f1_scores = np.array(null_f1_scores)
    
    # Calculate p-value: proportion of null scores >= observed score
    # If observed is better than random, p-value should be small
    p_value = np.mean(null_f1_scores >= observed_f1)
    
    # Adjust for the fact that we might have perfect separation in some cases
    # Add 1 to numerator and denominator for conservative estimate
    p_value = (np.sum(null_f1_scores >= observed_f1) + 1) / (n_permutations + 1)
    
    is_significant = p_value < alpha
    
    logger.info(f"Permutation test complete: p-value = {p_value:.4f}, significant = {is_significant}")
    
    return {
        'p_value': float(p_value),
        'is_significant': bool(is_significant),
        'observed_f1': float(observed_f1),
        'null_distribution_f1': null_f1_scores.tolist(),
        'n_permutations': n_permutations,
        'alpha': alpha
    }

def calculate_macro_f1(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate macro-averaged F1 score for multi-label classification."""
    return float(f1_score(y_true, y_pred, average='macro'))

def generate_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray, 
                             label_names: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Generate confusion matrix and identify error modes.
    
    Args:
        y_true: True labels (n_samples, n_labels)
        y_pred: Predicted labels (n_samples, n_labels)
        label_names: Optional list of label names for interpretation
        
    Returns:
        Dict with confusion matrix data and error mode analysis
    """
    # For multi-label, we can generate per-label confusion matrices or a flattened one
    # Here we generate per-label confusion matrices
    cm_data = []
    n_labels = y_true.shape[1]
    
    for i in range(n_labels):
        cm = confusion_matrix(y_true[:, i], y_pred[:, i])
        cm_entry = {
            'label_index': i,
            'label_name': label_names[i] if label_names and i < len(label_names) else f"label_{i}",
            'confusion_matrix': cm.tolist(),
            'tn': int(cm[0, 0]),
            'fp': int(cm[0, 1]),
            'fn': int(cm[1, 0]),
            'tp': int(cm[1, 1])
        }
        cm_data.append(cm_entry)
    
    # Identify dominant error modes
    total_fp = sum(entry['fp'] for entry in cm_data)
    total_fn = sum(entry['fn'] for entry in cm_data)
    
    error_modes = {
        'total_false_positives': total_fp,
        'total_false_negatives': total_fn,
        'fp_rate': total_fp / (total_fp + total_fn) if (total_fp + total_fn) > 0 else 0,
        'per_label_errors': cm_data
    }
    
    return error_modes

def run_evaluation_pipeline(
    model_path: str,
    test_data_path: str,
    output_dir: str,
    n_permutations: int = DEFAULT_N_PERMUTATIONS,
    random_state: int = DEFAULT_SEED
) -> Dict[str, Any]:
    """
    Run the full evaluation pipeline including permutation test.
    
    Args:
        model_path: Path to the trained model pickle file.
        test_data_path: Path to the test dataset (parquet or csv).
        output_dir: Directory to save evaluation results.
        n_permutations: Number of permutations for the test.
        random_state: Random seed for reproducibility.
        
    Returns:
        Dictionary containing all evaluation results.
    """
    logger.info(f"Starting evaluation pipeline")
    logger.info(f"Model path: {model_path}")
    logger.info(f"Test data path: {test_data_path}")
    
    # Ensure output directory exists
    ensure_dir(output_dir)
    
    # Load model
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    logger.info("Model loaded successfully")
    
    # Load test data
    if test_data_path.endswith('.parquet'):
        df = pd.read_parquet(test_data_path)
    else:
        df = pd.read_csv(test_data_path)
    
    logger.info(f"Loaded test data with {len(df)} samples")
    
    # Separate features and labels
    # Assuming labels are columns starting with 'label_' or specific known columns
    # For now, we assume the last columns are labels, or we need to know the schema
    # In a real scenario, we'd use metadata or a schema definition
    label_cols = [col for col in df.columns if col.startswith('label_')]
    if not label_cols:
        # Fallback: assume last N columns are labels (common convention)
        n_labels = 3  # Example default
        label_cols = df.columns[-n_labels:].tolist()
    
    feature_cols = [col for col in df.columns if col not in label_cols]
    
    X = df[feature_cols].values
    y_true = df[label_cols].values
    
    logger.info(f"Features shape: {X.shape}, Labels shape: {y_true.shape}")
    
    # Calculate observed performance
    y_pred = model.predict(X)
    observed_f1 = calculate_macro_f1(y_true, y_pred)
    logger.info(f"Observed macro-F1: {observed_f1:.4f}")
    
    # Generate stratified baseline
    y_baseline = generate_stratified_baseline(y_true, random_state=random_state)
    baseline_f1 = calculate_macro_f1(y_baseline, y_baseline)  # This will be ~0.5 for random
    logger.info(f"Stratified baseline F1: {baseline_f1:.4f}")
    
    # Perform permutation test
    perm_results = perform_permutation_test(
        model, X, y_true, 
        n_permutations=n_permutations, 
        random_state=random_state
    )
    
    # Generate confusion matrix
    cm_results = generate_confusion_matrix(y_true, y_pred, label_names=label_cols)
    
    # Compile final report
    report = {
        'observed_f1': observed_f1,
        'baseline_f1': baseline_f1,
        'permutation_test': perm_results,
        'confusion_matrix': cm_results,
        'n_samples': len(df),
        'n_features': X.shape[1],
        'n_labels': y_true.shape[1],
        'label_names': label_cols,
        'random_state': random_state,
        'n_permutations': n_permutations
    }
    
    # Save results
    report_path = os.path.join(output_dir, 'evaluation_report.json')
    save_json(report, report_path)
    logger.info(f"Evaluation report saved to {report_path}")
    
    # Save null distribution for plotting
    null_dist_path = os.path.join(output_dir, 'null_distribution_f1.json')
    save_json({
        'null_f1_scores': perm_results['null_distribution_f1'],
        'observed_f1': perm_results['observed_f1'],
        'p_value': perm_results['p_value']
    }, null_dist_path)
    logger.info(f"Null distribution saved to {null_dist_path}")
    
    return report

def main():
    """Main entry point for evaluation script."""
    # Load configuration from environment or defaults
    model_path = get_env_var('MODEL_PATH', 'results/artifacts/model.pkl')
    test_data_path = get_env_var('TEST_DATA_PATH', 'data/processed/test_ood_set.parquet')
    output_dir = get_env_var('EVAL_OUTPUT_DIR', 'results/metrics')
    n_permutations = int(get_env_var('N_PERMUTATIONS', str(DEFAULT_N_PERMUTATIONS)))
    random_state = int(get_env_var('RANDOM_STATE', str(DEFAULT_SEED)))
    
    # Run pipeline
    report = run_evaluation_pipeline(
        model_path=model_path,
        test_data_path=test_data_path,
        output_dir=output_dir,
        n_permutations=n_permutations,
        random_state=random_state
    )
    
    # Print summary
    print(f"\n=== Evaluation Summary ===")
    print(f"Observed F1: {report['observed_f1']:.4f}")
    print(f"Permutation Test p-value: {report['permutation_test']['p_value']:.4f}")
    print(f"Significant (p < 0.05): {report['permutation_test']['is_significant']}")
    print(f"Null Distribution Mean: {np.mean(report['permutation_test']['null_distribution_f1']):.4f}")
    print(f"Null Distribution Std: {np.std(report['permutation_test']['null_distribution_f1']):.4f}")
    
    return report

if __name__ == '__main__':
    main()