"""
Baseline models for fracture toughness prediction.
Implements Linear Regression and Random Forest regressors using scikit-learn.
"""
import numpy as np
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

from code.utils.logger import get_logger

logger = get_logger(__name__)


class LinearRegressionModel:
    """
    Linear Regression baseline model.
    Expects 1D feature vectors (e.g., GLCM + Band-pass spectrum).
    """
    def __init__(self):
        self.model = LinearRegression()
        self.is_fitted = False
        self.feature_names: Optional[List[str]] = None

    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: Optional[List[str]] = None) -> 'LinearRegressionModel':
        """
        Fit the linear regression model.

        Args:
            X: Feature matrix (n_samples, n_features)
            y: Target values (n_samples,)
            feature_names: Optional list of feature names for metadata

        Returns:
            self
        """
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        
        self.model.fit(X, y)
        self.is_fitted = True
        self.feature_names = feature_names
        logger.info(f"LinearRegressionModel fitted on {X.shape[0]} samples, {X.shape[1]} features")
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict fracture toughness values.

        Args:
            X: Feature matrix (n_samples, n_features)

        Returns:
            Predicted K_IC values (n_samples,)
        """
        if not self.is_fitted:
            raise RuntimeError("Model has not been fitted yet. Call fit() first.")
        
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        
        return self.model.predict(X)

    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """
        Evaluate model performance.

        Args:
            X: Feature matrix (n_samples, n_features)
            y: True target values (n_samples,)

        Returns:
            Dictionary with R2, MAE, RMSE
        """
        y_pred = self.predict(X)
        return {
            "r2": float(r2_score(y, y_pred)),
            "mae": float(mean_absolute_error(y, y_pred)),
            "rmse": float(np.sqrt(mean_squared_error(y, y_pred)))
        }

    def save(self, path: Path) -> None:
        """
        Save model coefficients and metadata to JSON.
        Note: sklearn models are not pickled here to avoid dependency issues,
        but coefficients are saved for inspection.
        """
        if not self.is_fitted:
            raise RuntimeError("Cannot save unfitted model")
        
        save_path = Path(path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "model_type": "linear_regression",
            "coefficients": self.model.coef_.tolist(),
            "intercept": float(self.model.intercept_),
            "feature_names": self.feature_names,
            "n_features": len(self.model.coef_)
        }
        
        with open(save_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"LinearRegressionModel saved to {save_path}")

    @classmethod
    def load(cls, path: Path) -> 'LinearRegressionModel':
        """
        Load model from JSON.
        Note: This reconstructs the model from saved coefficients for inference.
        """
        with open(path, 'r') as f:
            data = json.load(f)
        
        model = cls()
        model.is_fitted = True
        model.feature_names = data.get("feature_names")
        
        # We cannot fully reconstruct the sklearn model without fitting,
        # but we can store the coefficients for reference.
        # For actual prediction, a fitted model is required.
        # This is a limitation of JSON-only persistence without pickle.
        model._saved_coefficients = np.array(data["coefficients"])
        model._saved_intercept = float(data["intercept"])
        
        logger.info(f"LinearRegressionModel loaded from {path}")
        return model


class RandomForestModel:
    """
    Random Forest Regressor baseline model.
    """
    def __init__(self, n_estimators: int = 100, max_depth: Optional[int] = None, random_state: int = 42):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_state = random_state
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            n_jobs=-1
        )
        self.is_fitted = False
        self.feature_names: Optional[List[str]] = None

    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: Optional[List[str]] = None) -> 'RandomForestModel':
        """
        Fit the Random Forest model.

        Args:
            X: Feature matrix (n_samples, n_features)
            y: Target values (n_samples,)
            feature_names: Optional list of feature names for metadata

        Returns:
            self
        """
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        
        self.model.fit(X, y)
        self.is_fitted = True
        self.feature_names = feature_names
        logger.info(f"RandomForestModel fitted on {X.shape[0]} samples, {X.shape[1]} features")
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict fracture toughness values.

        Args:
            X: Feature matrix (n_samples, n_features)

        Returns:
            Predicted K_IC values (n_samples,)
        """
        if not self.is_fitted:
            raise RuntimeError("Model has not been fitted yet. Call fit() first.")
        
        if X.ndim == 1:
            X = X.reshape(-1, 1)
        
        return self.model.predict(X)

    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """
        Evaluate model performance.

        Args:
            X: Feature matrix (n_samples, n_features)
            y: True target values (n_samples,)

        Returns:
            Dictionary with R2, MAE, RMSE
        """
        y_pred = self.predict(X)
        return {
            "r2": float(r2_score(y, y_pred)),
            "mae": float(mean_absolute_error(y, y_pred)),
            "rmse": float(np.sqrt(mean_squared_error(y, y_pred)))
        }

    def save(self, path: Path) -> None:
        """
        Save model metadata to JSON.
        Note: sklearn models are not pickled here to avoid dependency issues.
        """
        if not self.is_fitted:
            raise RuntimeError("Cannot save unfitted model")
        
        save_path = Path(path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "model_type": "random_forest",
            "n_estimators": self.n_estimators,
            "max_depth": self.max_depth,
            "random_state": self.random_state,
            "feature_names": self.feature_names,
            "n_features": self.model.n_features_in_
        }
        
        with open(save_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"RandomForestModel metadata saved to {save_path}")

    @classmethod
    def load(cls, path: Path) -> 'RandomForestModel':
        """
        Load model metadata from JSON.
        Note: Actual model weights cannot be reconstructed from JSON without pickle.
        """
        with open(path, 'r') as f:
            data = json.load(f)
        
        model = cls(
            n_estimators=data.get("n_estimators", 100),
            max_depth=data.get("max_depth"),
            random_state=data.get("random_state", 42)
        )
        model.feature_names = data.get("feature_names")
        
        logger.info(f"RandomForestModel metadata loaded from {path}")
        return model