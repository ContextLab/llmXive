"""
Minimal Tobit (censored regression) wrapper.

Uses :mod:`statsmodels.miscmodels.tobit` which is part of the
``statsmodels`` package shipped with the project. The wrapper provides a
simple ``fit`` method that stores the model result for downstream use.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

try:
    # The correct import path for Tobit in statsmodels
    from statsmodels.miscmodels.tobit import Tobit
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "statsmodels does not provide a Tobit implementation at the expected location."
    ) from exc

logger = logging.getLogger(__name__)

class TobitModel:
    """
    Simple wrapper around ``statsmodels.miscmodels.tobit.Tobit``.
    """
    def __init__(self, dependent: str, independents: list[str], censor_left: float = 0.0):
        """
        Parameters
        ----------
        dependent : str
            Name of the dependent variable column in the DataFrame.
        independents : list[str]
            List of column names to be used as regressors.
        censor_left : float, optional
            Left‑censoring point (default is 0.0).
        """
        self.dependent = dependent
        self.independents = independents
        self.censor_left = censor_left
        self.result: Optional[object] = None

    def fit(self, df: pd.DataFrame) -> "TobitModel":
        """
        Fit the Tobit model to ``df`` and store the result.

        Returns
        -------
        TobitModel
            The instance itself (for method chaining).
        """
        exog = df[self.independents]
        endog = df[self.dependent]
        model = Tobit(endog, exog, left=self.censor_left)
        self.result = model.fit(disp=False)
        logger.info("Tobit model fitted successfully.")
        return self

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """
        Predict the dependent variable for new data.

        Parameters
        ----------
        df : pd.DataFrame
            New data containing the independent variables.

        Returns
        -------
        np.ndarray
            Predicted values.
        """
        if self.result is None:
            raise RuntimeError("Model has not been fitted yet.")
        return self.result.predict(df[self.independents])

    def summary(self) -> str:
        """
        Return a text summary of the fitted model.
        """
        if self.result is None:
            raise RuntimeError("Model has not been fitted yet.")
        return self.result.summary().as_text()
