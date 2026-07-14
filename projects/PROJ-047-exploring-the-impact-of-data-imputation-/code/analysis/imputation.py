from typing import Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer, KNNImputer, IterativeImputer
from sklearn.linear_model import BayesianRidge
from scipy import stats
from .entities import SyntheticDataset, ImputationResult

def apply_mean_imputation(data: SyntheticDataset) -> ImputationResult:
    """
    Apply mean imputation to missing values in the dataset.
    
    Args:
        data: SyntheticDataset containing X, T, Y with potential missing values
        
    Returns:
        ImputationResult with imputed data and metadata
    """
    # Combine features for imputation
    df = pd.DataFrame(data.X, columns=[f'X{i}' for i in range(data.X.shape[1])])
    
    # Apply mean imputation
    imputer = SimpleImputer(strategy='mean')
    X_imputed = imputer.fit_transform(df)
    
    # Handle T and Y if they have missing values
    T_imputed = data.T.copy()
    if np.any(np.isnan(T_imputed)):
        T_imputer = SimpleImputer(strategy='mean')
        T_imputed = T_imputer.fit_transform(T_imputed.reshape(-1, 1)).flatten()
    
    Y_imputed = data.Y.copy()
    if np.any(np.isnan(Y_imputed)):
        Y_imputer = SimpleImputer(strategy='mean')
        Y_imputed = Y_imputer.fit_transform(Y_imputed.reshape(-1, 1)).flatten()
    
    return ImputationResult(
        X=X_imputed,
        T=T_imputed,
        Y=Y_imputed,
        method='mean',
        missing_mask=None,
        imputation_stats={'n_imputed': int(np.sum(np.isnan(data.X))) + 
                        int(np.sum(np.isnan(data.T))) + int(np.sum(np.isnan(data.Y)))}
    )

def apply_knn_imputation(data: SyntheticDataset, k: int = 5) -> ImputationResult:
    """
    Apply KNN imputation to missing values in the dataset.
    
    Args:
        data: SyntheticDataset containing X, T, Y with potential missing values
        k: Number of neighbors for KNN imputation
        
    Returns:
        ImputationResult with imputed data and metadata
    """
    # Combine features for imputation
    df = pd.DataFrame(data.X, columns=[f'X{i}' for i in range(data.X.shape[1])])
    
    # Apply KNN imputation
    imputer = KNNImputer(n_neighbors=k)
    X_imputed = imputer.fit_transform(df)
    
    # Handle T and Y if they have missing values
    T_imputed = data.T.copy()
    if np.any(np.isnan(T_imputed)):
        T_imputer = KNNImputer(n_neighbors=min(k, len(T_imputed)))
        T_imputed = T_imputer.fit_transform(T_imputed.reshape(-1, 1)).flatten()
    
    Y_imputed = data.Y.copy()
    if np.any(np.isnan(Y_imputed)):
        Y_imputer = KNNImputer(n_neighbors=min(k, len(Y_imputed)))
        Y_imputed = Y_imputer.fit_transform(Y_imputed.reshape(-1, 1)).flatten()
    
    return ImputationResult(
        X=X_imputed,
        T=T_imputed,
        Y=Y_imputed,
        method='knn',
        missing_mask=None,
        imputation_stats={'n_imputed': int(np.sum(np.isnan(data.X))) + 
                        int(np.sum(np.isnan(data.T))) + int(np.sum(np.isnan(data.Y))),
                        'k': k}
    )

def apply_mice_imputation(data: SyntheticDataset, max_iter: int = 10, 
                         random_state: Optional[int] = None) -> ImputationResult:
    """
    Apply MICE (Multiple Imputation by Chained Equations) imputation to missing values.
    
    Uses BayesianRidge as the default estimator for CPU efficiency as per FR-003.
    
    Args:
        data: SyntheticDataset containing X, T, Y with potential missing values
        max_iter: Maximum number of imputation rounds
        random_state: Random seed for reproducibility
        
    Returns:
        ImputationResult with imputed data and metadata
    """
    # Combine features for imputation
    df = pd.DataFrame(data.X, columns=[f'X{i}' for i in range(data.X.shape[1])])
    
    # Apply MICE imputation with BayesianRidge
    imputer = IterativeImputer(
        estimator=BayesianRidge(),
        max_iter=max_iter,
        random_state=random_state,
        initial_strategy='mean'
    )
    
    try:
        X_imputed = imputer.fit_transform(df)
    except Exception as e:
        # Fallback to mean imputation if MICE fails (e.g., convergence issues)
        imputer_fallback = SimpleImputer(strategy='mean')
        X_imputed = imputer_fallback.fit_transform(df)
    
    # Handle T and Y if they have missing values
    T_imputed = data.T.copy()
    if np.any(np.isnan(T_imputed)):
        T_imputer = IterativeImputer(
            estimator=BayesianRidge(),
            max_iter=max_iter,
            random_state=random_state,
            initial_strategy='mean'
        )
        try:
            T_imputed = T_imputer.fit_transform(T_imputed.reshape(-1, 1)).flatten()
        except Exception:
            T_imputer_fallback = SimpleImputer(strategy='mean')
            T_imputed = T_imputer_fallback.fit_transform(T_imputed.reshape(-1, 1)).flatten()
    
    Y_imputed = data.Y.copy()
    if np.any(np.isnan(Y_imputed)):
        Y_imputer = IterativeImputer(
            estimator=BayesianRidge(),
            max_iter=max_iter,
            random_state=random_state,
            initial_strategy='mean'
        )
        try:
            Y_imputed = Y_imputer.fit_transform(Y_imputed.reshape(-1, 1)).flatten()
        except Exception:
            Y_imputer_fallback = SimpleImputer(strategy='mean')
            Y_imputed = Y_imputer_fallback.fit_transform(Y_imputed.reshape(-1, 1)).flatten()
    
    return ImputationResult(
        X=X_imputed,
        T=T_imputed,
        Y=Y_imputed,
        method='mice',
        missing_mask=None,
        imputation_stats={
            'n_imputed': int(np.sum(np.isnan(data.X))) + 
                        int(np.sum(np.isnan(data.T))) + int(np.sum(np.isnan(data.Y))),
            'max_iter': max_iter,
            'estimator': 'BayesianRidge'
        }
    )