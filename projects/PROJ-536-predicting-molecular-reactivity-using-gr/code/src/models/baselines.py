"""
Baseline models for reaction yield prediction.

This module provides:
- Molecular descriptor calculation (MW, logP, TPSA)
- Morgan fingerprint calculation
- Feature preparation helpers
- RandomForest and LinearRegression baseline wrappers
- Convenience function to train both baselines and persist them
- A minimal CLI entry‑point for manual execution

All public names are declared in the project API surface and are therefore
re‑exported at module level.
"""

import os
import json
import logging
import pickle
from typing import Dict, Any, Optional, Tuple, List, Union

import numpy as np
import pandas as pd

# scikit‑learn models
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.exceptions import NotFittedError

# RDKit for chemistry feature extraction
from rdkit import Chem
from rdkit.Chem import Descriptors, AllChem

# Project‑specific logger
from src.utils.logging import get_logger, log_invalid_smiles, log_message

__all__ = [
    "calculate_morgan_fingerprint",
    "calculate_descriptors",
    "prepare_fp_features",
    "prepare_descriptor_features",
    "RandomForestBaseline",
    "LinearRegressionBaseline",
    "train_and_save_baselines",
    "main",
]

# ---------------------------------------------------------------------------
# Feature extraction utilities
# ---------------------------------------------------------------------------

def calculate_morgan_fingerprint(smiles: str, radius: int = 2, n_bits: int = 2048) -> np.ndarray:
    """
    Compute a Morgan (circular) fingerprint for a SMILES string.

    Parameters
    ----------
    smiles: str
        SMILES representation of the molecule.
    radius: int, default 2
        Radius of the fingerprint.
    n_bits: int, default 2048
        Length of the bit vector.

    Returns
    -------
    np.ndarray
        1‑D array of 0/1 bits.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        log_invalid_smiles(smiles)
        raise ValueError(f"Invalid SMILES: {smiles}")

    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    arr = np.zeros((n_bits,), dtype=np.int8)
    Chem.DataStructs.ConvertToNumpyArray(fp, arr)
    return arr

def calculate_descriptors(smiles: str) -> Tuple[float, float, float]:
    """
    Calculate three standard molecular descriptors:
    - Molecular weight (MW)
    - Octanol‑water partition coefficient (LogP)
    - Topological polar surface area (TPSA)

    Parameters
    ----------
    smiles: str
        SMILES representation of the molecule.

    Returns
    -------
    Tuple[float, float, float]
        (MW, LogP, TPSA)
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        log_invalid_smiles(smiles)
        raise ValueError(f"Invalid SMILES: {smiles}")

    mw = Descriptors.MolWt(mol)
    logp = Descriptors.MolLogP(mol)
    tpsa = Descriptors.TPSA(mol)
    return mw, logp, tpsa

# ---------------------------------------------------------------------------
# Feature preparation helpers
# ---------------------------------------------------------------------------

def _filter_valid_smiles(df: pd.DataFrame, smiles_col: str = "smiles") -> pd.DataFrame:
    """
    Remove rows with invalid SMILES strings, logging each occurrence.
    """
    valid_mask = []
    for smi in df[smiles_col]:
        if Chem.MolFromSmiles(smi) is None:
            log_invalid_smiles(smi)
            valid_mask.append(False)
        else:
            valid_mask.append(True)
    return df[valid_mask].reset_index(drop=True)

def prepare_fp_features(df: pd.DataFrame, smiles_col: str = "smiles") -> np.ndarray:
    """
    Convert a DataFrame of SMILES strings to a matrix of Morgan fingerprints.

    Returns
    -------
    np.ndarray
        Shape (n_samples, n_bits)
    """
    df_valid = _filter_valid_smiles(df, smiles_col)
    fingerprints = [
        calculate_morgan_fingerprint(smi) for smi in df_valid[smiles_col]
    ]
    return np.stack(fingerprints, axis=0)

def prepare_descriptor_features(df: pd.DataFrame, smiles_col: str = "smiles") -> np.ndarray:
    """
    Convert a DataFrame of SMILES strings to a matrix of descriptor values
    (MW, LogP, TPSA).

    Returns
    -------
    np.ndarray
        Shape (n_samples, 3)
    """
    df_valid = _filter_valid_smiles(df, smiles_col)
    descriptors = [calculate_descriptors(smi) for smi in df_valid[smiles_col]]
    return np.stack(descriptors, axis=0)

# ---------------------------------------------------------------------------
# Baseline model wrappers
# ---------------------------------------------------------------------------

class RandomForestBaseline:
    """
    Wrapper around scikit‑learn's RandomForestRegressor for the reaction yield task.
    """

    def __init__(self, n_estimators: int = 200, random_state: int = 42,
                 model_path: str = "data/models/rf_baseline.pkl"):
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.model_path = model_path
        self.model: Optional[RandomForestRegressor] = None
        self.logger = get_logger(__name__)

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        self.logger.info("Training RandomForest baseline")
        self.model = RandomForestRegressor(
            n_estimators=self.n_estimators,
            random_state=self.random_state,
            n_jobs=1,  # CPU‑only constraint
        )
        self.model.fit(X, y)

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.model is None:
            raise NotFittedError("RandomForestBaseline model has not been fitted yet.")
        return self.model.predict(X)

    def save(self) -> None:
        if self.model is None:
            raise NotFittedError("Cannot save an unfitted RandomForestBaseline.")
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, "wb") as f:
            pickle.dump(self.model, f)
        self.logger.info(f"RandomForest baseline saved to {self.model_path}")

    def load(self) -> None:
        with open(self.model_path, "rb") as f:
            self.model = pickle.load(f)
        self.logger.info(f"RandomForest baseline loaded from {self.model_path}")

class LinearRegressionBaseline:
    """
    Wrapper around scikit‑learn's LinearRegression for the reaction yield task.
    Uses only three physicochemical descriptors (MW, LogP, TPSA).
    """

    def __init__(self, model_path: str = "data/models/lr_baseline.pkl"):
        self.model_path = model_path
        self.model: Optional[LinearRegression] = None
        self.logger = get_logger(__name__)

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """
        Fit the linear regression model.

        Parameters
        ----------
        X: np.ndarray, shape (n_samples, n_features)
            Descriptor matrix (expected 3 columns).
        y: np.ndarray, shape (n_samples,)
            Target yields.
        """
        if X.ndim != 2:
            raise ValueError("Feature matrix X must be 2‑dimensional")
        if y.ndim != 1:
            raise ValueError("Target vector y must be 1‑dimensional")
        if X.shape[0] != y.shape[0]:
            raise ValueError("Number of samples in X and y must match")
        self.logger.info("Training LinearRegression baseline")
        self.model = LinearRegression()
        self.model.fit(X, y)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict using the trained linear regression model.
        """
        if self.model is None:
            raise NotFittedError("LinearRegressionBaseline model has not been fitted yet.")
        if X.ndim != 2:
            raise ValueError("Feature matrix X must be 2‑dimensional")
        return self.model.predict(X)

    def save(self) -> None:
        """
        Persist the trained model to disk.
        """
        if self.model is None:
            raise NotFittedError("Cannot save an unfitted LinearRegressionBaseline.")
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, "wb") as f:
            pickle.dump(self.model, f)
        self.logger.info(f"LinearRegression baseline saved to {self.model_path}")

    def load(self) -> None:
        """
        Load a persisted model from disk.
        """
        with open(self.model_path, "rb") as f:
            self.model = pickle.load(f)
        self.logger.info(f"LinearRegression baseline loaded from {self.model_path}")

# ---------------------------------------------------------------------------
# Training orchestration
# ---------------------------------------------------------------------------

def train_and_save_baselines(
    data: pd.DataFrame,
    target_col: str = "yield",
    smiles_col: str = "smiles",
    rf_kwargs: Optional[Dict[str, Any]] = None,
    lr_kwargs: Optional[Dict[str, Any]] = None,
) -> Tuple[RandomForestBaseline, LinearRegressionBaseline]:
    """
    Train both RandomForest and LinearRegression baselines on the supplied
    reaction DataFrame and persist the models.

    Parameters
    ----------
    data: pd.DataFrame
        Must contain at least ``smiles`` and ``target_col`` columns.
    target_col: str, default "yield"
        Column name for the regression target.
    smiles_col: str, default "smiles"
        Column name containing SMILES strings.
    rf_kwargs: Optional[Dict[str, Any]]
        Additional arguments passed to ``RandomForestBaseline`` constructor.
    lr_kwargs: Optional[Dict[str, Any]]
        Additional arguments passed to ``LinearRegressionBaseline`` constructor.

    Returns
    -------
    Tuple[RandomForestBaseline, LinearRegressionBaseline]
        The trained baseline objects (already saved to disk).
    """
    logger = get_logger(__name__)

    # Basic validation
    if smiles_col not in data.columns:
        raise KeyError(f"Column '{smiles_col}' not found in data")
    if target_col not in data.columns:
        raise KeyError(f"Column '{target_col}' not found in data")

    # Filter out rows with invalid SMILES early – both baselines need valid inputs
    df_valid = _filter_valid_smiles(data[[smiles_col, target_col]].copy(), smiles_col)

    y = df_valid[target_col].to_numpy(dtype=float)

    # -------------------- Random Forest --------------------
    X_fp = prepare_fp_features(df_valid, smiles_col=smiles_col)
    rf = RandomForestBaseline(**(rf_kwargs or {}))
    rf.fit(X_fp, y)
    rf.save()

    # -------------------- Linear Regression --------------------
    X_desc = prepare_descriptor_features(df_valid, smiles_col=smiles_col)
    lr = LinearRegressionBaseline(**(lr_kwargs or {}))
    lr.fit(X_desc, y)
    lr.save()

    logger.info("Both baselines trained and saved successfully")
    return rf, lr

# ---------------------------------------------------------------------------
# Minimal CLI for manual execution
# ---------------------------------------------------------------------------

def _load_csv(path: str) -> pd.DataFrame:
    logger = get_logger(__name__)
    logger.info(f"Loading data from {path}")
    return pd.read_csv(path)

def main() -> None:
    """
    Simple command‑line interface:

    ``python -m src.models.baselines <path_to_csv>``

    The CSV must contain ``smiles`` and ``yield`` columns.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Train baseline models")
    parser.add_argument(
        "csv_path",
        type=str,
        help="Path to a CSV file containing at least 'smiles' and 'yield' columns",
    )
    args = parser.parse_args()

    df = _load_csv(args.csv_path)
    train_and_save_baselines(df)

if __name__ == "__main__":
    main()