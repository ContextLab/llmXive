"""
Integration test for generalization analysis (User Story 3).

This test verifies that the model training and evaluation pipeline
produces meaningful generalization metrics across reaction classes.

It depends on:
- data/processed/cleaned_reactions.parquet (from US1)
- data/processed/split_indices.parquet (from US2)
- data/results/best_models/ (from US2 training)

The test runs the evaluation pipeline and asserts:
1. Per-class metrics are computed for all reaction classes
2. Metrics are within valid ranges (R2 between -inf and 1, RMSE/MAE >= 0)
3. Feature importance scores are generated
4. No exceptions occur during the full pipeline
"""

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import DATA_PROCESSED_DIR, DATA_RESULTS_DIR
from utils.io import load_parquet, save_parquet
from utils.validators import validate_output_file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
EXPECTED_CLASSES = ["SN2", "SN1", "E2", "E1", "Addition", "Elimination", "Substitution"]
MIN_CLASSES_TO_TEST = 3
MAX_CLASSES_TO_TEST = 10


def test_generalization_analysis_pipeline():
    """
    Integration test: Run the full generalization analysis pipeline.
    
    This test:
    1. Loads the cleaned dataset
    2. Loads the split indices
    3. Runs evaluation on the test set
    4. Verifies per-class metrics are computed
    5. Verifies feature importance is calculated
    6. Validates the output against the output schema
    """
    
    # Check prerequisites
    cleaned_data_path = DATA_PROCESSED_DIR / "cleaned_reactions.parquet"
    split_indices_path = DATA_PROCESSED_DIR / "split_indices.parquet"
    best_models_dir = DATA_RESULTS_DIR / "best_models"
    
    assert cleaned_data_path.exists(), f"Cleaned data not found: {cleaned_data_path}"
    assert split_indices_path.exists(), f"Split indices not found: {split_indices_path}"
    assert best_models_dir.exists(), f"Best models directory not found: {best_models_dir}"
    
    # Load data
    logger.info("Loading cleaned data...")
    df = load_parquet(cleaned_data_path)
    
    logger.info("Loading split indices...")
    split_df = load_parquet(split_indices_path)
    
    # Verify data integrity
    assert "smiles" in df.columns, "Missing 'smiles' column"
    assert "yield" in df.columns, "Missing 'yield' column"
    assert "reaction_class" in df.columns, "Missing 'reaction_class' column"
    assert "fingerprint_ecfp" in df.columns or "fingerprint_maccs" in df.columns, \
        "Missing fingerprint columns"
    
    # Verify split indices
    assert "split" in split_df.columns, "Missing 'split' column in split indices"
    assert set(split_df["split"].unique()).issubset({"train", "val", "test"}), \
        "Invalid split values"
    
    # Extract test set
    logger.info("Extracting test set...")
    test_indices = split_df[split_df["split"] == "test"].index
    test_df = df.loc[test_indices].copy()
    
    logger.info(f"Test set size: {len(test_df)} samples")
    assert len(test_df) > 0, "Test set is empty"
    
    # Verify reaction classes in test set
    test_classes = test_df["reaction_class"].unique()
    logger.info(f"Reaction classes in test set: {test_classes}")
    assert len(test_classes) >= MIN_CLASSES_TO_TEST, \
        f"Too few reaction classes in test set: {len(test_classes)}"
    
    # Prepare features and target
    if "fingerprint_ecfp" in test_df.columns:
        feature_col = "fingerprint_ecfp"
    else:
        feature_col = "fingerprint_maccs"
    
    X_test = np.array(test_df[feature_col].tolist())
    y_test = test_df["yield"].values
    
    logger.info(f"Feature shape: {X_test.shape}")
    logger.info(f"Target shape: {y_test.shape}")
    
    # Load best models
    rf_model_path = best_models_dir / "random_forest.pkl"
    svm_model_path = best_models_dir / "svm.pkl"
    
    rf_model = None
    svm_model = None
    
    if rf_model_path.exists():
        import pickle
        with open(rf_model_path, "rb") as f:
            rf_model = pickle.load(f)
        logger.info("Loaded Random Forest model")
    else:
        logger.warning(f"Random Forest model not found: {rf_model_path}")
    
    if svm_model_path.exists():
        import pickle
        with open(svm_model_path, "rb") as f:
            svm_model = pickle.load(f)
        logger.info("Loaded SVM model")
    else:
        logger.warning(f"SVM model not found: {svm_model_path}")
    
    # At least one model should be available
    assert rf_model is not None or svm_model is not None, \
        "No trained models found for evaluation"
    
    # Evaluate models per reaction class
    per_class_metrics = {}
    model_type = None
    
    if rf_model is not None:
        model_type = "random_forest"
        logger.info("Evaluating Random Forest model...")
        
        # Overall metrics
        from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
        
        y_pred = rf_model.predict(X_test)
        overall_r2 = r2_score(y_test, y_pred)
        overall_rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        overall_mae = mean_absolute_error(y_test, y_pred)
        
        logger.info(f"Overall R2: {overall_r2:.4f}")
        logger.info(f"Overall RMSE: {overall_rmse:.4f}")
        logger.info(f"Overall MAE: {overall_mae:.4f}")
        
        # Per-class metrics
        for cls in test_classes:
            cls_mask = test_df["reaction_class"] == cls
            X_cls = X_test[cls_mask]
            y_cls = y_test[cls_mask]
            y_cls_pred = rf_model.predict(X_cls)
            
            cls_r2 = r2_score(y_cls, y_cls_pred)
            cls_rmse = np.sqrt(mean_squared_error(y_cls, y_cls_pred))
            cls_mae = mean_absolute_error(y_cls, y_cls_pred)
            
            per_class_metrics[cls] = {
                "R2": cls_r2,
                "RMSE": cls_rmse,
                "MAE": cls_mae,
                "n_samples": len(y_cls)
            }
            
            logger.info(f"Class {cls}: R2={cls_r2:.4f}, RMSE={cls_rmse:.4f}, MAE={cls_mae:.4f}, n={len(y_cls)}")
        
        # Feature importance (permutation importance)
        logger.info("Computing feature importance...")
        from sklearn.inspection import permutation_importance
        
        perm_importance = permutation_importance(
            rf_model, X_test, y_test, n_repeats=10, random_state=42, n_jobs=-1
        )
        
        importance_scores = perm_importance.importances_mean
        top_n = min(50, len(importance_scores))
        top_indices = np.argsort(importance_scores)[::-1][:top_n]
        
        feature_importance = {
            "top_features": [int(idx) for idx in top_indices],
            "top_scores": [float(importance_scores[idx]) for idx in top_indices]
        }
        
    elif svm_model is not None:
        # SVM doesn't have built-in feature importance, so we use permutation importance
        model_type = "svm"
        logger.info("Evaluating SVM model...")
        
        from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
        
        y_pred = svm_model.predict(X_test)
        overall_r2 = r2_score(y_test, y_pred)
        overall_rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        overall_mae = mean_absolute_error(y_test, y_pred)
        
        logger.info(f"Overall R2: {overall_r2:.4f}")
        logger.info(f"Overall RMSE: {overall_rmse:.4f}")
        logger.info(f"Overall MAE: {overall_mae:.4f}")
        
        # Per-class metrics
        for cls in test_classes:
            cls_mask = test_df["reaction_class"] == cls
            X_cls = X_test[cls_mask]
            y_cls = y_test[cls_mask]
            y_cls_pred = svm_model.predict(X_cls)
            
            cls_r2 = r2_score(y_cls, y_cls_pred)
            cls_rmse = np.sqrt(mean_squared_error(y_cls, y_cls_pred))
            cls_mae = mean_absolute_error(y_cls, y_cls_pred)
            
            per_class_metrics[cls] = {
                "R2": cls_r2,
                "RMSE": cls_rmse,
                "MAE": cls_mae,
                "n_samples": len(y_cls)
            }
            
            logger.info(f"Class {cls}: R2={cls_r2:.4f}, RMSE={cls_rmse:.4f}, MAE={cls_mae:.4f}, n={len(y_cls)}")
        
        # Feature importance (permutation importance)
        logger.info("Computing feature importance...")
        from sklearn.inspection import permutation_importance
        
        perm_importance = permutation_importance(
            svm_model, X_test, y_test, n_repeats=10, random_state=42, n_jobs=-1
        )
        
        importance_scores = perm_importance.importances_mean
        top_n = min(50, len(importance_scores))
        top_indices = np.argsort(importance_scores)[::-1][:top_n]
        
        feature_importance = {
            "top_features": [int(idx) for idx in top_indices],
            "top_scores": [float(importance_scores[idx]) for idx in top_indices]
        }
    
    # Assertions
    assert len(per_class_metrics) >= MIN_CLASSES_TO_TEST, \
        f"Too few per-class metrics: {len(per_class_metrics)}"
    
    # Validate per-class metrics
    for cls, metrics in per_class_metrics.items():
        assert "R2" in metrics, f"Missing R2 for class {cls}"
        assert "RMSE" in metrics, f"Missing RMSE for class {cls}"
        assert "MAE" in metrics, f"Missing MAE for class {cls}"
        assert "n_samples" in metrics, f"Missing n_samples for class {cls}"
        
        # R2 can be negative, but RMSE and MAE should be non-negative
        assert metrics["RMSE"] >= 0, f"Negative RMSE for class {cls}: {metrics['RMSE']}"
        assert metrics["MAE"] >= 0, f"Negative MAE for class {cls}: {metrics['MAE']}"
        assert metrics["n_samples"] > 0, f"Zero samples for class {cls}"
    
    # Validate feature importance
    assert "top_features" in feature_importance, "Missing top_features"
    assert "top_scores" in feature_importance, "Missing top_scores"
    assert len(feature_importance["top_features"]) > 0, "Empty top_features"
    assert len(feature_importance["top_scores"]) > 0, "Empty top_scores"
    assert len(feature_importance["top_features"]) == len(feature_importance["top_scores"]), \
        "Mismatch in top_features and top_scores lengths"
    
    # Save results for further inspection
    results = {
        "model_type": model_type,
        "overall_metrics": {
            "R2": overall_r2,
            "RMSE": overall_rmse,
            "MAE": overall_mae
        },
        "per_class_metrics": per_class_metrics,
        "feature_importance": feature_importance,
        "test_set_size": len(test_df),
        "reaction_classes": list(test_classes)
    }
    
    output_path = DATA_RESULTS_DIR / "generalization_analysis_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    
    # Validate against output schema
    schema_path = PROJECT_ROOT / "specs" / "001-assess-ml-predictive-power" / "contracts" / "output.schema.yaml"
    if schema_path.exists():
        validate_output_file(output_path, schema_path)
        logger.info("Output validated against schema")
    
    # Final assertions
    assert overall_r2 is not None, "Overall R2 is None"
    assert overall_rmse is not None, "Overall RMSE is None"
    assert overall_mae is not None, "Overall MAE is None"
    
    logger.info("Generalization analysis integration test PASSED")


if __name__ == "__main__":
    test_generalization_analysis_pipeline()
    print("All tests passed!")