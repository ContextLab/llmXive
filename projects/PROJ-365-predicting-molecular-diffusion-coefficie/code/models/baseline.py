"""
Linear Regression baseline model for predicting molecular diffusion coefficients.

This model builds a feature vector for each molecule by concatenating:
  1. A Morgan fingerprint (binary vector) derived from the molecule's SMILES.
  2. Solvent descriptor values (any column in the input DataFrame that starts
     with the prefix ``solvent_``).

The combined feature vector is fed to a scikit‑learn ``LinearRegression``
estimator.  The class provides a simple ``fit`` / ``predict`` API that can
be used by the training pipeline (see T041) and the evaluation step
(T021).

The implementation deliberately avoids any GPU/torch dependencies – the
baseline is a pure CPU model.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List, Sequence

import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs
from rdkit.Chem import AllChem
from sklearn.linear_model import LinearRegression

logger = logging.getLogger(__name__)

__all__ = ["LinearRegressionBaseline"]


class LinearRegressionBaseline:
    """
    Baseline predictor based on a linear regression over molecular fingerprints
    and solvent descriptors.

    Parameters
    ----------
    n_bits: int, default 2048
        Length of the Morgan fingerprint bit vector.
    radius: int, default 2
        Radius for the Morgan fingerprint.
    """

    def __init__(self, n_bits: int = 2048, radius: int = 2) -> None:
        self.n_bits = n_bits
        self.radius = radius
        self._model = LinearRegression()
        self._solvent_columns: List[str] = []

    # -----------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------
    def _mol_from_smiles(self, smiles: str) -> Chem.Mol:
        """Convert a SMILES string to an RDKit Mol object, raising on failure."""
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.error("Invalid SMILES encountered: %s", smiles)
            raise ValueError(f"Invalid SMILES string: {smiles}")
        return mol

    def _fingerprint(self, mol: Chem.Mol) -> np.ndarray:
        """Return a binary Morgan fingerprint as a NumPy array."""
        fp = AllChem.GetMorganFingerprintAsBitVect(
            mol, self.radius, nBits=self.n_bits
        )
        arr = np.zeros((self.n_bits,), dtype=np.float32)
        DataStructs.ConvertToNumpyArray(fp, arr)
        return arr

    def _solvent_feature_vector(self, row: pd.Series) -> np.ndarray:
        """Extract solvent descriptor values from a DataFrame row."""
        # solvent descriptor columns are identified during ``fit`` and cached.
        values = row[self._solvent_columns].astype(np.float32).values
        return values

    def _build_feature_vector(self, smiles: str, solvent_features: Sequence[float]) -> np.ndarray:
        """Combine fingerprint and solvent descriptor vector."""
        mol = self._mol_from_smiles(smiles)
        fp_vec = self._fingerprint(mol)
        solvent_vec = np.asarray(solvent_features, dtype=np.float32)
        return np.concatenate([fp_vec, solvent_vec])

    def _prepare_features(self, df: pd.DataFrame) -> np.ndarray:
        """
        Convert a DataFrame into a 2‑D NumPy array of features.

        The DataFrame must contain a ``smiles`` column and one or more
        columns whose names start with ``solvent_``.
        """
        if "smiles" not in df.columns:
            raise KeyError("Input DataFrame must contain a 'smiles' column.")

        # Detect solvent descriptor columns on the first call.
        if not self._solvent_columns:
            self._solvent_columns = [
                col for col in df.columns if col.startswith("solvent_")
            ]
            if not self._solvent_columns:
                raise ValueError(
                    "No solvent descriptor columns found (expected columns "
                    "starting with 'solvent_')."
                )
            logger.debug("Detected solvent columns: %s", self._solvent_columns)

        feature_list: List[np.ndarray] = []
        for _, row in df.iterrows():
            smiles = row["smiles"]
            solvent_vec = self._solvent_feature_vector(row)
            feature = self._build_feature_vector(smiles, solvent_vec)
            feature_list.append(feature)

        return np.vstack(feature_list)

    # -----------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------
    def fit(self, df: pd.DataFrame, target_column: str = "diffusion_coeff") -> None:
        """
        Fit the linear regression model.

        Parameters
        ----------
        df: pd.DataFrame
            Training data containing ``smiles``, solvent descriptor columns,
            and the target column.
        target_column: str, default "diffusion_coeff"
            Name of the column containing the diffusion coefficient to predict.
        """
        if target_column not in df.columns:
            raise KeyError(f"Target column '{target_column}' not found in DataFrame.")

        X = self._prepare_features(df)
        y = df[target_column].astype(np.float32).values
        logger.info("Fitting LinearRegression baseline on %d samples.", X.shape[0])
        self._model.fit(X, y)

    def predict(
        self,
        smiles_list: Iterable[str],
        solvent_dicts: Iterable[Dict[str, Any]],
    ) -> np.ndarray:
        """
        Predict diffusion coefficients for new data.

        Parameters
        ----------
        smiles_list: iterable of str
            SMILES strings for the molecules to predict.
        solvent_dicts: iterable of dict
            Each dict must contain the same solvent descriptor keys that were
            present during training (e.g., ``{'solvent_viscosity': 0.89, ...}``).

        Returns
        -------
        np.ndarray
            Predicted diffusion coefficients.
        """
        # Ensure that the model has been fitted and solvent columns are known.
        if not self._solvent_columns:
            raise RuntimeError(
                "Baseline model has not been fitted yet – solvent descriptor "
                "columns are unknown."
            )

        feature_list: List[np.ndarray] = []
        for smiles, solvent_dict in zip(smiles_list, solvent_dicts):
            # Preserve ordering of solvent columns.
            solvent_vec = [
                float(solvent_dict[col]) for col in self._solvent_columns
            ]
            feature = self._build_feature_vector(smiles, solvent_vec)
            feature_list.append(feature)

        X_new = np.vstack(feature_list)
        predictions = self._model.predict(X_new)
        return predictions

    # -----------------------------------------------------------------
    # Convenience helpers
    # -----------------------------------------------------------------
    def get_coefficients(self) -> np.ndarray:
        """Return the learned regression coefficients (after fitting)."""
        if not hasattr(self._model, "coef_"):
            raise RuntimeError("Model coefficients are unavailable before fitting.")
        return self._model.coef_

    def score(self, df: pd.DataFrame, target_column: str = "diffusion_coeff") -> float:
        """
        Return the coefficient of determination R^2 of the prediction.

        Parameters
        ----------
        df: pd.DataFrame
            Test data containing ``smiles``, solvent descriptor columns,
            and the target column.
        target_column: str, default "diffusion_coeff"
            Column name of the true diffusion coefficients.

        Returns
        -------
        float
            R^2 score.
        """
        X = self._prepare_features(df)
        y_true = df[target_column].astype(np.float32).values
        return self._model.score(X, y_true)