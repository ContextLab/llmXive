"""Abstract base class for uncertainty quantification methods.

This module defines the `UncertaintyMethod` interface that all predictive
uncertainty models must implement to be integrated into the calibration
evaluation pipeline.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict, Any, Union

import numpy as np
import pandas as pd

from utils.logging import get_logger

logger = get_logger(__name__)


class UncertaintyMethod(ABC):
    """Abstract base class for uncertainty quantification methods.

    All uncertainty quantification models in this pipeline must inherit from
    this class and implement the required interface methods. This ensures
    consistent integration with the evaluation pipeline and metrics calculation.

    Attributes:
        name (str): Human-readable name of the method.
        config (Dict[str, Any]): Configuration parameters for the method.
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize the uncertainty method.

        Args:
            name: Human-readable identifier for this method.
            config: Dictionary of hyperparameters and settings.
        """
        self.name = name
        self.config = config or {}
        logger.debug(f"Initialized {name} with config: {self.config}")

    @abstractmethod
    def fit(self, X: Union[np.ndarray, pd.DataFrame], y: Union[np.ndarray, pd.Series]) -> "UncertaintyMethod":
        """Fit the model to the training data.

        Args:
            X: Training features of shape (n_samples, n_features).
            y: Training targets of shape (n_samples,).

        Returns:
            self: The fitted model instance.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        pass

    @abstractmethod
    def predict_interval(
        self,
        X: Union[np.ndarray, pd.DataFrame],
        confidence_level: float = 0.90
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Predict prediction intervals for the given features.

        Args:
            X: Test features of shape (n_samples, n_features).
            confidence_level: Target coverage probability (e.g., 0.90 for 90% intervals).
                              Must be between 0 and 1.

        Returns:
            Tuple of (lower_bounds, upper_bounds) where each is an array of shape (n_samples,).
            lower_bounds[i] <= upper_bounds[i] for all i.

        Raises:
            ValueError: If confidence_level is not in (0, 1).
            NotImplementedError: If the subclass does not implement this method.
        """
        pass

    def predict(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """Predict point estimates for the given features.

        This is a convenience method that many uncertainty methods can use.
        If not overridden, it may raise NotImplementedError depending on the
        specific implementation requirements.

        Args:
            X: Test features of shape (n_samples, n_features).

        Returns:
            Array of point predictions of shape (n_samples,).
        """
        raise NotImplementedError(
            f"Method '{self.name}' does not implement point prediction. "
            "Override predict() in the subclass."
        )

    def get_params(self) -> Dict[str, Any]:
        """Get the parameters of this method.

        Returns:
            Dictionary of parameter names and values.
        """
        return {
            "name": self.name,
            "config": self.config
        }

    def __repr__(self) -> str:
        """Return a string representation of the method."""
        return f"{self.__class__.__name__}(name='{self.name}', config={self.config})"