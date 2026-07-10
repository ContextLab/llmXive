"""
Logistic Regression model implementation for molecular toxicity prediction.

This model uses global molecular descriptors as features and applies
Logistic Regression with cross-validation for toxicity prediction.
"""
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import StratifiedKFold
    from sklearn.metrics import roc_auc_score, f1_score
    from sklearn.preprocessing import StandardScaler
except ImportError:
    LogisticRegression = None
    StratifiedKFold = None
    roc_auc_score = None
    f1_score = None
    StandardScaler = None


class LogisticModel:
    """
    Logistic Regression model for molecular toxicity prediction.

    This model uses molecular descriptors as features and applies
    cross-validation for robust evaluation.
    """

    def __init__(
        self,
        n_splits: int = 5,
        n_repeats: int = 3,
        random_state: int = 42,
        C: float = 1.0,
        max_iter: int = 1000
    ):
        """
        Initialize the logistic regression model.

        Args:
            n_splits: Number of CV splits.
            n_repeats: Number of repeats for each split.
            random_state: Random seed for reproducibility.
            C: Inverse of regularization strength.
            max_iter: Maximum number of iterations.
        """
        if LogisticRegression is None:
            raise ImportError(
                "scikit-learn is required for logistic model. "
                "Install with: pip install scikit-learn"
            )

        self.n_splits = n_splits
        self.n_repeats = n_repeats
        self.random_state = random_state
        self.C = C
        self.max_iter = max_iter

        self.model: Optional[LogisticRegression] = None
        self.scaler: Optional[StandardScaler] = None
        self.cv_results: List[Dict[str, Any]] = []
        self.oof_predictions: Optional[np.ndarray] = None
        self.oof_indices: Optional[np.ndarray] = None

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        return_oof: bool = False
    ) -> Dict[str, Any]:
        """
        Fit the model using cross-validation.

        Args:
            X: Feature matrix (n_samples, n_features).
            y: Target labels (n_samples,).
            return_oof: If True, return out-of-fold predictions.

        Returns:
            Dictionary with CV results and optionally OOF predictions.
        """
        if StratifiedKFold is None or StandardScaler is None:
            raise ImportError("scikit-learn is required for fitting")

        X = np.array(X)
        y = np.array(y)

        # Initialize scaler and model
        self.scaler = StandardScaler()
        self.model = LogisticRegression(
            C=self.C,
            max_iter=self.max_iter,
            random_state=self.random_state,
            solver='lbfgs'
        )

        # Cross-validation setup
        cv = StratifiedKFold(
            n_splits=self.n_splits,
            shuffle=True,
            random_state=self.random_state
        )

        # For OOF predictions
        if return_oof:
            oof_probs = np.zeros(len(y))
            oof_indices = np.zeros(len(y), dtype=int)

        results = []

        # Perform CV with repeats
        for repeat in range(self.n_repeats):
            for fold_idx, (train_idx, test_idx) in enumerate(cv.split(X, y)):
                # Scale features
                X_train = self.scaler.fit_transform(X[train_idx])
                X_test = self.scaler.transform(X[test_idx])

                # Train model
                self.model.fit(X_train, y[train_idx])

                # Predict
                y_prob = self.model.predict_proba(X_test)[:, 1]
                y_pred = self.model.predict(X_test)

                # Calculate metrics
                auc = roc_auc_score(y[test_idx], y_prob)
                f1 = f1_score(y[test_idx], y_pred)

                result = {
                    "repeat": repeat,
                    "fold": fold_idx,
                    "auc": float(auc),
                    "f1": float(f1),
                    "train_size": len(train_idx),
                    "test_size": len(test_idx)
                }
                results.append(result)

                # Store OOF predictions
                if return_oof:
                    oof_probs[test_idx] = y_prob
                    oof_indices[test_idx] = repeat * self.n_splits + fold_idx

        self.cv_results = results

        if return_oof:
            self.oof_predictions = oof_probs
            self.oof_indices = oof_indices
            return {
                "results": results,
                "oof_predictions": oof_probs.tolist(),
                "oof_indices": oof_indices.tolist()
            }

        return {"results": results}

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict probabilities for new samples.

        Args:
            X: Feature matrix.

        Returns:
            Predicted probabilities of positive class.
        """
        if self.model is None or self.scaler is None:
            raise ValueError("Model not fitted. Call fit() first.")

        X = np.array(X)
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)[:, 1]

    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        """
        Predict binary labels for new samples.

        Args:
            X: Feature matrix.
            threshold: Probability threshold.

        Returns:
            Predicted binary labels.
        """
        probs = self.predict_proba(X)
        return (probs >= threshold).astype(int)

    def get_best_params(self) -> Dict[str, Any]:
        """
        Get the best parameters from cross-validation.

        Returns:
            Dictionary with best parameters.
        """
        if not self.cv_results:
            return {}

        best_result = max(self.cv_results, key=lambda x: x['auc'])
        return {
            "best_auc": best_result['auc'],
            "best_f1": best_result['f1'],
            "best_repeat": best_result['repeat'],
            "best_fold": best_result['fold']
        }

    def __repr__(self) -> str:
        return (
            f"LogisticModel(n_splits={self.n_splits}, "
            f"n_repeats={self.n_repeats}, C={self.C})"
        )


def load_logistic_model(
    n_splits: int = 5,
    n_repeats: int = 3,
    random_state: int = 42
) -> LogisticModel:
    """
    Factory function to load a logistic regression model.

    Args:
        n_splits: Number of CV splits.
        n_repeats: Number of repeats.
        random_state: Random seed.

    Returns:
        Initialized LogisticModel instance.
    """
    return LogisticModel(
        n_splits=n_splits,
        n_repeats=n_repeats,
        random_state=random_state
    )
