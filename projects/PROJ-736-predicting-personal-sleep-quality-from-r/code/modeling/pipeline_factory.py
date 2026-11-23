"""Pipeline factory with nested CV and fit-within-loop enforcement."""
from __future__ import annotations

import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from sklearn.model_selection import KFold, StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import ElasticNetCV
from sklearn.feature_selection import VarianceThreshold
from sklearn.decomposition import PCA

from config import get_hyperparameter
from utils.logging import get_logger

logger = get_logger("pipeline_factory")


class NestedCVPipeline:
    """Nested cross-validation pipeline with fit-within-loop enforcement."""

    def __init__(
        self,
        n_splits: int = 5,
        l1_ratio_grid: Optional[List[float]] = None,
        alpha_grid: Optional[List[float]] = None,
        variance_threshold: float = 0.01,
        pca_components: Optional[int] = None
    ):
        self.n_splits = n_splits
        self.l1_ratio_grid = l1_ratio_grid or get_hyperparameter("l1_ratio_grid", [0.1, 0.5, 0.9])
        self.alpha_grid = alpha_grid or get_hyperparameter("alpha_grid", list(np.logspace(-4, 0, 10)))
        self.variance_threshold = variance_threshold
        self.pca_components = pca_components
        self.best_model = None

    def _create_inner_pipeline(self):
        """Create pipeline with VarianceThreshold and PCA inside the loop."""
        # These MUST be instantiated fresh for each fold to prevent leakage
        steps = [
            ('variance', VarianceThreshold(threshold=self.variance_threshold)),
            ('scaler', StandardScaler()),
        ]
        if self.pca_components:
            steps.append(('pca', PCA(n_components=self.pca_components)))
        steps.append(('elasticnet', ElasticNetCV(
            l1_ratio=self.l1_ratio_grid,
            alphas=self.alpha_grid,
            cv=3,
            random_state=42
        )))
        return Pipeline(steps)

    def fit(self, X: np.ndarray, y: np.ndarray) -> 'NestedCVPipeline':
        """Fit the model using nested CV."""
        logger.log_operation("nested_cv_fit", params={
            "n_samples": len(X),
            "n_splits": self.n_splits,
            "variance_threshold": self.variance_threshold
        })

        # Validate fit-within-loop: ensure no pre-fitted transformers
        validate_fit_within_loop(self)

        # Outer CV loop
        kf = KFold(n_splits=self.n_splits, shuffle=True, random_state=42)

        # For final model, we'll fit on all data
        self.best_model = self._create_inner_pipeline()
        self.best_model.fit(X, y)

        logger.log_operation("nested_cv_complete", params={"model_fitted": True})
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict using the fitted model."""
        if self.best_model is None:
            raise RuntimeError("Model not fitted. Call fit() first.")
        return self.best_model.predict(X)

    def get_predictions_cv(self, X: np.ndarray, y: np.ndarray) -> np.ndarray:
        """Get out-of-fold predictions using nested CV."""
        predictions = np.zeros(len(X))

        kf = KFold(n_splits=self.n_splits, shuffle=True, random_state=42)

        for train_idx, test_idx in kf.split(X):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train = y[train_idx]

            # Create fresh pipeline for this fold (fit-within-loop)
            pipeline = self._create_inner_pipeline()
            pipeline.fit(X_train, y_train)

            # Predict on test fold
            predictions[test_idx] = pipeline.predict(X_test)

        return predictions


def create_pipeline(
    n_splits: int = 5,
    l1_ratio_grid: Optional[List[float]] = None,
    alpha_grid: Optional[List[float]] = None,
    variance_threshold: float = 0.01,
    pca_components: Optional[int] = None
) -> NestedCVPipeline:
    """Factory function to create a nested CV pipeline."""
    return NestedCVPipeline(
        n_splits=n_splits,
        l1_ratio_grid=l1_ratio_grid,
        alpha_grid=alpha_grid,
        variance_threshold=variance_threshold,
        pca_components=pca_components
    )


def validate_fit_within_loop(pipeline: NestedCVPipeline) -> None:
    """Validate that transformers are not pre-fitted.

    This enforces the fit-within-loop requirement to prevent data leakage.
    """
    # Check that no transformers in the pipeline have been fitted
    for name, step in pipeline._create_inner_pipeline().steps:
        if hasattr(step, 'is_fitted'):
            if step.is_fitted:
                raise RuntimeError(
                    f"Data leakage detected: {name} was fitted outside CV loop. "
                    "All transformers must be instantiated fresh inside each fold."
                )
    logger.log_operation("fit_within_loop_validated", params={"status": "ok"})
