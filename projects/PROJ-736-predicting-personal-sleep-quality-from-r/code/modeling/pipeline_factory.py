"""
Task T020a: Nested CV pipeline factory.

Encapsulates the nested CV logic with Variance Thresholding and PCA
fitted strictly within the training fold to prevent data leakage.
"""
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from sklearn.model_selection import KFold, cross_val_predict, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import ElasticNetCV
from sklearn.feature_selection import VarianceThreshold
from sklearn.decomposition import PCA
from utils.metrics import pearson_r, r_squared
from utils.logging import log_stage_start, log_stage_complete, get_logger


class NestedCVPipeline:
    """
    A class to handle nested cross-validation for ElasticNet regression.
    
    Attributes:
        variance_threshold (float): Threshold for VarianceThreshold.
        pca_retention (float): Variance retention for PCA.
        n_folds (int): Number of outer CV folds.
        inner_folds (int): Number of inner CV folds for hyperparameter tuning.
    """
    
    def __init__(
        self,
        variance_threshold: float = 0.01,
        pca_retention: float = 0.95,
        n_folds: int = 5,
        inner_folds: int = 3,
        random_state: int = 42
    ):
        self.variance_threshold = variance_threshold
        self.pca_retention = pca_retention
        self.n_folds = n_folds
        self.inner_folds = inner_folds
        self.random_state = random_state
        self.logger = get_logger("NestedCVPipeline")
        
        # Store results
        self.predictions = None
        self.metrics = []
        self.best_model = None

    def _create_inner_pipeline(self):
        """Create the pipeline for a single fold (fit on train, predict on test)."""
        return Pipeline([
            ('variance', VarianceThreshold(threshold=self.variance_threshold)),
            ('pca', PCA(n_components=self.pca_retention, random_state=self.random_state)),
            ('scaler', StandardScaler()),
            ('elasticnet', ElasticNetCV(
                l1_ratio=[0.1, 0.5, 0.9],
                cv=self.inner_folds,
                random_state=self.random_state,
                max_iter=1000
            ))
        ])

    def fit_predict(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """
        Run the nested CV loop.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            y: Target vector (n_samples,)
        
        Returns:
            dict: {
                "predictions": np.ndarray (outer-fold predictions),
                "metrics": List[dict] (per-fold metrics),
                "best_model": The final trained model (optional)
            }
        """
        self.logger.log("start_nested_cv", n_folds=self.n_folds, inner_folds=self.inner_folds)
        
        # Outer CV splitter
        outer_cv = KFold(n_splits=self.n_folds, shuffle=True, random_state=self.random_state)
        
        # Store predictions and metrics
        all_predictions = np.zeros_like(y, dtype=float)
        fold_metrics = []
        
        for fold_idx, (train_idx, test_idx) in enumerate(outer_cv.split(X)):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
            
            # Create pipeline for this fold
            pipeline = self._create_inner_pipeline()
            
            try:
                # Fit on training data
                pipeline.fit(X_train, y_train)
                
                # Predict on test data (outer fold prediction)
                y_pred = pipeline.predict(X_test)
                all_predictions[test_idx] = y_pred
                
                # Calculate metrics for this fold
                r = pearson_r(y_test, y_pred)
                r2 = r_squared(y_test, y_pred)
                
                fold_metrics.append({
                    "fold": fold_idx + 1,
                    "pearson_r": r,
                    "r_squared": r2,
                    "n_train": len(train_idx),
                    "n_test": len(test_idx)
                })
                
                self.logger.log(f"fold_{fold_idx+1}_complete", 
                                pearson_r=r, r_squared=r2)
                                
            except Exception as e:
                # Handle edge case: "all edges removed" (variance threshold removes all)
                self.logger.log(f"fold_{fold_idx+1}_error", error=str(e))
                # Fill with NaN or zero to maintain shape
                all_predictions[test_idx] = np.nan
                fold_metrics.append({
                    "fold": fold_idx + 1,
                    "error": str(e),
                    "pearson_r": np.nan,
                    "r_squared": np.nan
                })
        
        self.predictions = all_predictions
        self.metrics = fold_metrics
        
        # Fit a final model on the full data for potential use
        final_pipeline = self._create_inner_pipeline()
        final_pipeline.fit(X, y)
        self.best_model = final_pipeline
        
        self.logger.log("nested_cv_complete", n_folds=self.n_folds)
        
        return {
            "predictions": self.predictions,
            "metrics": self.metrics,
            "best_model": self.best_model
        }


def create_pipeline(
    variance_threshold: float = 0.01,
    pca_retention: float = 0.95,
    n_folds: int = 5,
    inner_folds: int = 3,
    random_state: int = 42
) -> NestedCVPipeline:
    """
    Factory function to create a NestedCVPipeline instance.
    
    Args:
        variance_threshold: Threshold for VarianceThreshold.
        pca_retention: Variance retention for PCA.
        n_folds: Number of outer CV folds.
        inner_folds: Number of inner CV folds.
        random_state: Random seed.
    
    Returns:
        NestedCVPipeline instance.
    """
    return NestedCVPipeline(
        variance_threshold=variance_threshold,
        pca_retention=pca_retention,
        n_folds=n_folds,
        inner_folds=inner_folds,
        random_state=random_state
    )
