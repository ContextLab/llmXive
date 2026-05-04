"""
Script to verify confusion matrix generator functionality.

This script generates synthetic data, computes confusion matrix,
and saves visualization to verify the implementation works correctly.

Per T033: Create confusion matrix generator for model evaluation.
"""
import sys
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

# Add code directory to path
code_dir = Path(__file__).parent.parent
sys.path.insert(0, str(code_dir))

from src.evaluation.metrics import (
    generate_confusion_matrix,
    save_confusion_matrix_plot,
    compute_all_metrics,
    EvaluationMetrics
)

def main():
    """Run confusion matrix verification tests."""
    print("=" * 60)
    print("Confusion Matrix Generator Verification")
    print("=" * 60)
    
    # Create output directory
    output_dir = code_dir / "evaluation" / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Test 1: Generate synthetic labels
    print("\n[1] Generating synthetic test data...")
    np.random.seed(42)
    n_samples = 1000
    
    # Create ground truth with 10% anomaly rate
    y_true = np.random.choice([0, 1], size=n_samples, p=[0.9, 0.1])
    
    # Create predictions with ~85% accuracy
    y_pred = y_true.copy()
    error_indices = np.random.choice(n_samples, size=int(n_samples * 0.15), replace=False)
    y_pred[error_indices] = 1 - y_pred[error_indices]
    
    # Create anomaly scores for AUC computation
    y_scores = np.random.uniform(0, 1, size=n_samples)
    y_scores[y_true == 1] = np.random.uniform(0.7, 1.0, size=np.sum(y_true == 1))
    y_scores[y_true == 0] = np.random.uniform(0.0, 0.4, size=np.sum(y_true == 0))
    
    print(f"    Samples: {n_samples}")
    print(f"    Anomaly rate: {np.mean(y_true) * 100:.1f}%")
    
    # Test 2: Generate confusion matrix
    print("\n[2] Generating confusion matrix...")
    cm, counts = generate_confusion_matrix(y_true, y_pred)
    print(f"    Confusion Matrix:\n{cm}")
    print(f"    Counts: {counts}")
    
    # Test 3: Save confusion matrix plot
    print("\n[3] Saving confusion matrix visualization...")
    plot_path = output_dir / "confusion_matrix.png"
    cm_plot, counts_plot = save_confusion_matrix_plot(
        y_true, y_pred,
        str(plot_path),
        title="Model Evaluation Confusion Matrix"
    )
    print(f"    Saved to: {plot_path}")
    print(f"    File exists: {plot_path.exists()}")
    
    # Test 4: Compute all metrics
    print("\n[4] Computing all evaluation metrics...")
    metrics = compute_all_metrics(y_true, y_pred, y_scores)
    print(f"    F1-Score: {metrics.f1_score:.4f}")
    print(f"    Precision: {metrics.precision:.4f}")
    print(f"    Recall: {metrics.recall:.4f}")
    print(f"    AUC: {metrics.auc:.4f}")
    print(f"    TP: {metrics.tp}, FP: {metrics.fp}")
    print(f"    TN: {metrics.tn}, FN: {metrics.fn}")
    
    # Test 5: Verify metrics consistency
    print("\n[5] Verifying metrics consistency...")
    expected_tp = counts['tp']
    expected_fp = counts['fp']
    expected_tn = counts['tn']
    expected_fn = counts['fn']
    
    assert metrics.tp == expected_tp, f"TP mismatch: {metrics.tp} != {expected_tp}"
    assert metrics.fp == expected_fp, f"FP mismatch: {metrics.fp} != {expected_fp}"
    assert metrics.tn == expected_tn, f"TN mismatch: {metrics.tn} != {expected_tn}"
    assert metrics.fn == expected_fn, f"FN mismatch: {metrics.fn} != {expected_fn}"
    
    print("    All consistency checks passed!")
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE - All tests passed!")
    print("=" * 60)
    print(f"\nArtifacts generated:")
    print(f"  - {plot_path}")
    print(f"\nMetrics summary:")
    print(f"  - F1-Score: {metrics.f1_score:.4f}")
    print(f"  - Precision: {metrics.precision:.4f}")
    print(f"  - Recall: {metrics.recall:.4f}")
    print(f"  - AUC: {metrics.auc:.4f}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
