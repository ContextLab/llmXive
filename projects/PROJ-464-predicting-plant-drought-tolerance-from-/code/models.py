from __future__ import annotations

from typing import Optional, Dict, Any, Tuple, List
from pydantic import BaseModel, Field, field_validator, model_validator
from pathlib import Path
import re
import logging
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import GroupKFold, cross_val_score
from sklearn.linear_model import Ridge, Lasso
from sklearn.preprocessing import StandardScaler
from sklearn.exceptions import ConvergenceWarning
import warnings
import pickle

# Suppress sklearn convergence warnings for cleaner logs during batch processing
warnings.filterwarnings("ignore", category=ConvergenceWarning)

# --- Models (Pydantic) ---

class RootImage(BaseModel):
    id: str
    path: str
    species: str

class RSAMetrics(BaseModel):
    species_id: str
    depth: float
    branching_density: float
    surface_area: float

    @field_validator('depth', 'branching_density', 'surface_area')
    @classmethod
    def must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError(f"Value must be positive, got {v}")
        return v

class PhysioTrait(BaseModel):
    species: str
    conductance: float
    photosynthesis: float
    survival_rate: Optional[float] = None

# --- Core Logic Functions ---

def binarize_target(df: pd.DataFrame, proxy_col: str = 'survival_rate') -> pd.DataFrame:
    """
    Binarizes the target variable using a median split.
    
    Args:
        df: The dataframe containing the proxy column.
        proxy_col: The name of the column to binarize.
        
    Returns:
        A copy of the dataframe with a new 'target_binary' column (0 or 1).
        
    Raises:
        ValueError: If the proxy column does not exist or contains no data.
    """
    if proxy_col not in df.columns:
        raise ValueError(f"Proxy column '{proxy_col}' not found in dataframe. Cannot binarize.")
    
    if df[proxy_col].isna().all():
        raise ValueError(f"Proxy column '{proxy_col}' contains only NaN values.")

    # Calculate median
    median_val = df[proxy_col].median()
    
    # Binarize: 1 if > median, 0 otherwise
    df_copy = df.copy()
    df_copy['target_binary'] = (df_copy[proxy_col] > median_val).astype(int)
    
    return df_copy

def fit_rf_classification(
    df: pd.DataFrame,
    features: List[str],
    target_col: str = 'target_binary',
    species_col: str = 'species_id',
    n_estimators: int = 100,
    random_state: int = 42
) -> Tuple[Any, Dict[str, float]]:
    """
    Fits a Random Forest Classification model to predict drought tolerance class.
    
    CRITICAL ASSERTION:
    This function asserts that the target variable for binarization is NOT the same
    as the dependent variable used in regression models (e.g., 'conductance').
    This prevents circular classification where the model predicts what it was trained on
    via the same physiological metric.
    
    Args:
        df: Input dataframe.
        features: List of feature column names.
        target_col: Name of the target column (should be binarized).
        species_col: Column name for GroupKFold grouping.
        n_estimators: Number of trees in the forest.
        random_state: Random seed.
        
    Returns:
        Tuple of (trained_model, metrics_dict).
        
    Raises:
        ValueError: If circular classification is detected or if proxy is missing.
        RuntimeError: If GroupKFold validation fails.
    """
    # 1. Explicit "No Circular Classification" Assertion
    # The target_col must be a proxy (e.g., survival_rate binarized), NOT conductance/photosynthesis directly
    # unless those were explicitly binarized from a DIFFERENT proxy, which is unlikely.
    # We enforce that target_col is not 'conductance' or 'photosynthesis' to prevent direct leakage.
    
    regression_targets = {'conductance', 'photosynthesis'}
    
    if target_col in regression_targets:
        raise ValueError(
            f"Circular Classification Detected: Target column '{target_col}' is a direct "
            f"physiological regression target ({', '.join(regression_targets)}). "
            f"Classification must be based on an independent proxy (e.g., survival_rate), "
            f"not the variable we are trying to predict in regression."
        )

    # 2. Validate data existence
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found. Ensure binarize_target was run.")
    
    if species_col not in df.columns:
        raise ValueError(f"Species column '{species_col}' not found for GroupKFold.")

    # 3. Prepare data
    X = df[features].dropna()
    y = df.loc[X.index, target_col]
    groups = df.loc[X.index, species_col]

    if len(X) == 0:
        raise ValueError("No valid data points available after dropping NaNs.")

    # 4. Initialize Model
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=None,
        min_samples_leaf=1,
        random_state=random_state,
        n_jobs=-1
    )

    # 5. Cross-Validation with GroupKFold to prevent phylogenetic leakage
    # Ensure no species appears in both train and test within a fold
    gkf = GroupKFold(n_splits=5)
    
    # Verify GroupKFold integrity (optional but recommended for strictness)
    # We rely on sklearn's implementation, but we ensure groups are passed correctly.
    try:
        scores = cross_val_score(model, X, y, groups=groups, cv=gkf, scoring='f1')
        mean_f1 = float(np.mean(scores))
    except Exception as e:
        raise RuntimeError(f"GroupKFold validation failed: {e}")

    # 6. Train final model on full data (optional, or keep CV scores only)
    # Typically for production, we retrain on all data.
    model.fit(X, y)

    metrics = {
        'mean_f1_cv': mean_f1,
        'n_samples': len(X),
        'n_species': groups.nunique(),
        'model_type': 'RandomForestClassifier'
    }

    return model, metrics

def fit_ols(
    df: pd.DataFrame,
    features: List[str],
    target: str,
    species_col: str = 'species_id'
) -> Dict[str, Any]:
    """
    Fits an OLS model with GroupKFold cross-validation.
    Note: OLS does not support GroupKFold natively in sklearn, so we simulate
    or use statsmodels if strict phylogenetic control is needed. 
    Here we use a simplified approach or fallback to standard CV if GroupKFold 
    is not strictly required for OLS in this specific pipeline context, 
    but typically PGLS is preferred for phylogeny.
    
    For this implementation, we return a placeholder structure or basic stats
    if the specific OLS GroupKFold logic is not fully defined in the API surface
    beyond the function signature.
    """
    # Implementation would go here, currently returning basic stats
    return {
        "model_type": "OLS",
        "predictor": features,
        "target": target,
        "r2": 0.0,
        "note": "Basic OLS placeholder; PGLS preferred for phylogeny."
    }

def fit_ridge(
    df: pd.DataFrame,
    features: List[str],
    target: str,
    alpha: float = 1.0
) -> Dict[str, Any]:
    """
    Fits a Ridge Regression model.
    """
    return {
        "model_type": "Ridge",
        "alpha": alpha,
        "r2": 0.0,
        "note": "Ridge placeholder."
    }

def fit_lasso(
    df: pd.DataFrame,
    features: List[str],
    target: str,
    alpha: float = 1.0
) -> Dict[str, Any]:
    """
    Fits a Lasso Regression model.
    """
    return {
        "model_type": "Lasso",
        "alpha": alpha,
        "r2": 0.0,
        "note": "Lasso placeholder."
    }

def fit_random_forest(
    df: pd.DataFrame,
    features: List[str],
    target: str,
    species_col: str = 'species_id'
) -> Dict[str, Any]:
    """
    Fits a Random Forest Regression model.
    """
    return {
        "model_type": "RandomForestRegressor",
        "r2": 0.0,
        "note": "RF Regression placeholder."
    }

def fit_pgl(
    df: pd.DataFrame,
    features: List[str],
    target: str,
    tree_path: str
) -> Dict[str, Any]:
    """
    Fits a Phylogenetic Generalized Least Squares (PGLS) model.
    """
    return {
        "model_type": "PGLS",
        "r2": 0.0,
        "note": "PGLS placeholder; requires caper and tree file."
    }

def main():
    """
    Entry point for models.py.
    Primarily used for testing or standalone execution of specific functions.
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Models module loaded. Functions available: fit_ols, fit_ridge, fit_lasso, fit_random_forest, fit_pgl, fit_rf_classification, binarize_target.")

if __name__ == "__main__":
    main()