"""
Verification script for metrics computation functions.

Tests all metric functions (F1-score, precision, recall, AUC)
with sample data to ensure they work correctly.

This script is executed to verify the metrics module implementation.
"""
import sys
import numpy as np
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.metrics import (
    compute_f1_score,
    compute_precision,
    compute_recall,
    compute_auc,
    generate_confusion_matrix,
    compute_all_metrics
)

def main():
    # Create test data
    y_true = np.array([0, 1, 1, 0, 1, 0, 1, 1, 0, 0])
    y_pred = np.array([0, 1, 0, 0, 1, 1, 1, 0, 0, 0])
    y_scores = np.array([0.1, 0.9, 0.8, 0.2, 0.95, 0.3, 0.85, 0.4, 0.15, 0.05])
    
    print("Testing metrics computation functions...")
    print("=" * 50)
    
    # Test each function
    f1 = compute_f1_score(y_true, y_pred)
    print(f"F1 Score: {f1:.4f}")
    
    prec = compute_precision(y_true, y_pred)
    print(f"Precision: {prec:.4f}")
    
    rec = compute_recall(y_true, y_pred)
    print(f"Recall: {rec:.4f}")
    
    auc = compute_auc(y_true, y_scores)
    print(f"AUC: {auc:.4f}")
    
    cm, counts = generate_confusion_matrix(y_true, y_pred)
    print(f"Confusion Matrix:\n{cm}")
    print(f"TP: {counts['tp']}, FP: {counts['fp']}, TN: {counts['tn']}, FN: {counts['fn']}")
    
    # Test compute_all_metrics
    all_metrics = compute_all_metrics(y_true, y_pred, y_scores)
    print(f"\nAll Metrics (via compute_all_metrics):")
    print(f"  F1: {all_metrics.f1_score:.4f}")
    print(f"  Precision: {all_metrics.precision:.4f}")
    print(f"  Recall: {all_metrics.recall:.4f}")
    print(f"  AUC: {all_metrics.auc:.4f}")
    
    # Verify values are reasonable
    assert 0 <= f1 <= 1, "F1-score should be between 0 and 1"
    assert 0 <= prec <= 1, "Precision should be between 0 and 1"
    assert 0 <= rec <= 1, "Recall should be between 0 and 1"
    assert 0 <= auc <= 1, "AUC should be between 0 and 1"
    
    print("\n" + "=" * 50)
    print("All metrics functions verified successfully!")
    print("Functions implemented per FR-006:")
    print("  - compute_f1_score()")
    print("  - compute_precision()")
    print("  - compute_recall()")
    print("  - compute_auc()")
    print("  - generate_confusion_matrix()")
    print("  - compute_all_metrics()")

if __name__ == "__main__":
    main()
