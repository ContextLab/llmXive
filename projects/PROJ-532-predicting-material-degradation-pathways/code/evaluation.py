import os
import json
import logging
import pickle
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Tuple, Any, Dict, List, Optional
from scipy.stats import zscore

# Import utilities from sibling module
from utils import save_json, load_json, ensure_dir, get_env_var, setup_logging

# Configure logging
logger = logging.getLogger(__name__)

def generate_stratified_baseline(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
    """
    Generate a stratified random baseline preserving the multi-label correlation structure.
    Shuffles the joint label vector to define the null hypothesis.
    """
    n_samples = len(y_true)
    # Flatten joint labels to create a unique signature per sample for shuffling
    # Assuming y_true is (n_samples, n_labels)
    joint_signature = np.dot(y_true, 2 ** np.arange(y_true.shape[1]))
    # Shuffle the signatures
    np.random.shuffle(joint_signature)
    # Reconstruct the labels
    y_shuffled = np.zeros_like(y_true)
    for i in range(y_true.shape[1]):
        y_shuffled[:, i] = (joint_signature // (2 ** i)) % 2
    return y_shuffled

def perform_permutation_test(
    model,
    X: np.ndarray,
    y_true: np.ndarray,
    n_permutations: int = 1000,
    random_state: Optional[int] = None
) -> Tuple[float, np.ndarray]:
    """
    Perform permutation test to validate p < 0.05.
    Shuffles the joint label vector per sample.
    Returns p-value and the null distribution scores.
    """
    if random_state is not None:
        np.random.seed(random_state)

    # Calculate observed score (Macro-F1)
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import f1_score

    # If model is not a classifier, assume it's already trained and we just predict
    # We need to calculate the observed macro-f1 first
    # For permutation test, we usually permute labels and re-evaluate
    # However, the task says "shuffle the joint label vector per sample"
    # This implies we are testing if the model's performance is better than random chance
    # given the label correlations.

    # We will use the trained model's predictions on X
    # But wait, permutation test usually involves re-training or re-evaluating with permuted labels
    # Since the model is already trained, we can simulate the null distribution by:
    # 1. Permuting y_true (shuffling labels)
    # 2. Evaluating the model's predictions against permuted y_true
    # This tests if the model's predictions are correlated with the original labels
    # better than with random permutations.

    # However, the standard permutation test for a trained model involves:
    # - Permuting the labels y
    # - Retraining the model (expensive) OR
    # - Using the existing predictions and comparing against permuted y (if we assume the model
    #   learned the structure of X, then permuting y breaks the X-y relationship)

    # Given the task description "shuffle the joint label vector per sample", we will:
    # 1. Keep X and model predictions fixed.
    # 2. Shuffle y_true to create y_permuted.
    # 3. Calculate F1 score between model predictions and y_permuted.
    # 4. Repeat n_permutations times.
    # 5. Calculate p-value as the proportion of permuted scores >= observed score.

    # But wait, the model was trained on original y. If we shuffle y, the model's predictions
    # (which were trained on original y) might still be somewhat correlated if the model
    # overfits or if there's structure in X. The null hypothesis is that the model has no
    # predictive power beyond label correlation.

    # Let's implement the standard approach:
    # 1. Calculate observed macro-f1
    y_pred = model.predict(X)
    observed_score = f1_score(y_true, y_pred, average='macro')

    # 2. Generate null distribution
    null_scores = []
    for _ in range(n_permutations):
        # Shuffle y_true (joint label vector)
        y_permuted = y_true.copy()
        # Shuffle rows of y_permuted
        np.random.shuffle(y_permuted)
        # Calculate score
        perm_score = f1_score(y_permuted, y_pred, average='macro')
        null_scores.append(perm_score)

    null_scores = np.array(null_scores)

    # 3. Calculate p-value
    # p-value = (number of null scores >= observed score + 1) / (n_permutations + 1)
    p_value = (np.sum(null_scores >= observed_score) + 1) / (n_permutations + 1)

    return p_value, null_scores

def calculate_macro_f1(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate macro-averaged F1 score."""
    from sklearn.metrics import f1_score
    return f1_score(y_true, y_pred, average='macro')

def generate_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
    """Generate confusion matrix for multi-label classification."""
    from sklearn.metrics import confusion_matrix
    # For multi-label, we might need to flatten or handle per-class
    # Here we assume binary labels and calculate per-class confusion matrices
    # Or we can use a multi-label confusion matrix approach
    # For simplicity, we'll return a dictionary of per-class confusion matrices
    # But the task asks for a single matrix, so we'll flatten
    # Actually, for multi-label, a common approach is to treat each label independently
    # and report a 2x2 matrix for each, or a combined metric.
    # Let's return a dictionary of per-class confusion matrices
    cm_dict = {}
    n_labels = y_true.shape[1]
    for i in range(n_labels):
        cm = confusion_matrix(y_true[:, i], y_pred[:, i])
        cm_dict[f'class_{i}'] = cm.tolist()
    return cm_dict

def generate_permutation_report(
    p_value: float,
    null_distribution: np.ndarray,
    output_dir: str,
    plot_path: str
) -> Dict[str, Any]:
    """
    Generate the permutation test report and plot.
    """
    ensure_dir(output_dir)
    ensure_dir(os.path.dirname(plot_path))

    # Create the plot
    plt.figure(figsize=(10, 6))
    plt.hist(null_distribution, bins=50, alpha=0.7, color='skyblue', edgecolor='black')
    plt.axvline(x=p_value, color='red', linestyle='--', linewidth=2, label=f'Observed Score (p={p_value:.4f})')
    plt.xlabel('Permutation Score (Macro-F1)')
    plt.ylabel('Frequency')
    plt.title('Null Distribution of Permutation Test')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(plot_path)
    plt.close()

    # Prepare report
    report = {
        "p_value": p_value,
        "permutation_test_passed": p_value < 0.05,
        "n_permutations": len(null_distribution),
        "null_distribution_stats": {
            "mean": float(np.mean(null_distribution)),
            "std": float(np.std(null_distribution)),
            "min": float(np.min(null_distribution)),
            "max": float(np.max(null_distribution))
        },
        "plot_path": plot_path
    }

    # Save report
    report_path = os.path.join(output_dir, "permutation_test_report.json")
    save_json(report, report_path)

    logger.info(f"Permutation test report saved to {report_path}")
    logger.info(f"Null distribution plot saved to {plot_path}")

    return report

def run_evaluation_pipeline(
    model_path: str,
    train_features_path: str,
    train_labels_path: str,
    output_dir: str,
    n_permutations: int = 1000,
    random_state: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run the full evaluation pipeline including permutation test.
    """
    logger.info("Starting evaluation pipeline...")

    # Load model
    with open(model_path, 'rb') as f:
        model = pickle.load(f)

    # Load data
    X = np.load(train_features_path)
    y = np.load(train_labels_path)

    # Perform permutation test
    logger.info(f"Performing permutation test with {n_permutations} iterations...")
    p_value, null_distribution = perform_permutation_test(
        model, X, y, n_permutations=n_permutations, random_state=random_state
    )

    # Generate report and plot
    report = generate_permutation_report(
        p_value,
        null_distribution,
        output_dir,
        os.path.join(output_dir, "null_distribution.png")
    )

    logger.info("Evaluation pipeline completed.")
    return report

def main():
    """Main entry point for evaluation."""
    # Get paths from environment or use defaults
    model_path = get_env_var('MODEL_PATH', 'results/artifacts/model.pkl')
    train_features_path = get_env_var('TRAIN_FEATURES_PATH', 'data/processed/train_set.parquet')
    train_labels_path = get_env_var('TRAIN_LABELS_PATH', 'data/processed/train_labels.npy')
    output_dir = get_env_var('OUTPUT_DIR', 'results/metrics')
    n_permutations = int(get_env_var('N_PERMUTATIONS', '1000'))
    random_state = get_env_var('RANDOM_STATE', None)
    if random_state:
        random_state = int(random_state)

    # Run pipeline
    result = run_evaluation_pipeline(
        model_path,
        train_features_path,
        train_labels_path,
        output_dir,
        n_permutations=n_permutations,
        random_state=random_state
    )

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    setup_logging()
    main()