"""
Pipeline factory for nested cross-validation.
Implements Variance Thresholding and PCA strictly within training folds.
"""
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import ElasticNetCV
from sklearn.feature_selection import VarianceThreshold
from sklearn.decomposition import PCA
from config import get_paths
from utils.logging import log_stage_start, log_stage_complete, log_stage_error

def create_pipeline():
    """
    Creates a pipeline with nested CV logic.
    Returns a fitted pipeline object that can be used for predictions.
    """
    paths = get_paths()
    
    # Configuration from config.py
    variance_threshold = paths.get('variance_threshold', 0.01)
    pca_retention = paths.get('pca_retention', 0.95)
    alphas = paths.get('elasticnet_alphas', [0.01, 0.1, 1.0])
    l1_ratios = paths.get('elasticnet_l1_ratios', [0.1, 0.5, 0.9])
    
    # Create the inner CV pipeline
    # This pipeline will be fit within each training fold
    inner_pipeline = Pipeline([
        ('variance', VarianceThreshold(threshold=variance_threshold)),
        ('scaler', StandardScaler()),
        ('pca', PCA(n_components=pca_retention, svd_solver='full')),
        ('regressor', ElasticNetCV(
            alphas=alphas,
            l1_ratio=l1_ratios,
            cv=5,
            random_state=42,
            n_jobs=-1
        ))
    ])
    
    return NestedCVPipeline(inner_pipeline)

class NestedCVPipeline:
    """
    Wrapper class that implements nested cross-validation.
    The outer loop evaluates performance, the inner loop tunes hyperparameters.
    """
    def __init__(self, pipeline: Pipeline):
        self.pipeline = pipeline
        self.outer_cv = KFold(n_splits=5, shuffle=True, random_state=42)
        self.fold_metrics = []
        self.best_params = {}
        self.outer_predictions = None
        self.final_model = None

    def fit(self, X: np.ndarray, y: np.ndarray, subject_ids: List[str] = None) -> Dict[str, Any]:
        """
        Run nested cross-validation.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            y: Target vector (n_samples,)
            subject_ids: Optional list of subject IDs
            
        Returns:
            Dictionary with outer_predictions, fold_metrics, best_params
        """
        log_stage_start("Nested CV", "Starting nested cross-validation")
        
        self.fold_metrics = []
        self.outer_predictions = np.zeros(len(y))
        
        # Outer loop: evaluate performance
        for fold_idx, (train_idx, test_idx) in enumerate(self.outer_cv.split(X)):
            log_stage_start(f"Outer Fold {fold_idx + 1}", f"Training on {len(train_idx)} samples, testing on {len(test_idx)}")
            
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
            
            try:
                # Fit pipeline on training fold (inner CV happens inside ElasticNetCV)
                self.pipeline.fit(X_train, y_train)
                
                # Predict on test fold
                y_pred = self.pipeline.predict(X_test)
                
                # Store predictions at correct indices
                self.outer_predictions[test_idx] = y_pred
                
                # Calculate metrics
                r = np.corrcoef(y_test, y_pred)[0, 1]
                if np.isnan(r):
                    r = 0.0
                r2 = 1 - np.sum((y_test - y_pred) ** 2) / np.sum((y_test - np.mean(y_test)) ** 2)
                if np.isnan(r2) or np.isinf(r2):
                    r2 = 0.0
                
                fold_metric = {
                    'fold': fold_idx + 1,
                    'r': float(r),
                    'r2': float(r2),
                    'n_train': len(train_idx),
                    'n_test': len(test_idx)
                }
                self.fold_metrics.append(fold_metric)
                
                log_stage_complete(f"Outer Fold {fold_idx + 1}", 
                    f"R={r:.4f}, R²={r2:.4f}")
                
            except Exception as e:
                log_stage_error(f"Outer Fold {fold_idx + 1}", str(e))
                # Handle edge case: if variance threshold removes all features
                if "0 features" in str(e):
                    log_stage_start("Variance Threshold Warning", "Skipping fold due to zero features")
                    continue
                else:
                    raise
        
        # Store best parameters from the last fitted model (or average if needed)
        if hasattr(self.pipeline.named_steps['regressor'], 'best_alpha_'):
            self.best_params = {
                'alpha': float(self.pipeline.named_steps['regressor'].best_alpha_),
                'l1_ratio': float(self.pipeline.named_steps['regressor'].best_l1_ratio_)
            }
        
        # Fit final model on entire dataset for future use
        log_stage_start("Final Model", "Fitting on entire dataset")
        self.pipeline.fit(X, y)
        self.final_model = self.pipeline
        
        log_stage_complete("Nested CV", "Completed all folds")
        
        return {
            'outer_predictions': self.outer_predictions,
            'fold_metrics': self.fold_metrics,
            'best_params': self.best_params,
            'pipeline': self.pipeline
        }

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict using the final fitted model.
        """
        if self.final_model is None:
            raise ValueError("Pipeline not fitted. Call fit() first.")
        return self.final_model.predict(X)