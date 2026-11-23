"""
Training module for L1-regularized Logistic Regression with Nested VIF Analysis.
Implements FR-004: Training function for predictive host-range model.
"""
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, List, Optional, Dict, Any, Union
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from loguru import logger

from src.utils.logging import get_logger
from src.config import Paths

# Initialize logger
logger = get_logger(__name__)


def calculate_vif(X: np.ndarray, feature_names: List[str]) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        feature_names: List of feature names
        
    Returns:
        DataFrame with feature names and VIF values
    """
    if X.shape[1] == 0:
        return pd.DataFrame({'feature': [], 'vif': []})
    
    # Add intercept column for VIF calculation
    X_with_intercept = np.column_stack([np.ones(X.shape[0]), X])
    feature_names_with_intercept = ['intercept'] + feature_names
    
    vif_data = []
    
    for i in range(1, X_with_intercept.shape[1]):
        # Get the feature column (skip intercept)
        feature_col = X_with_intercept[:, i]
        
        # Regress this feature against all other features
        other_features = np.delete(X_with_intercept, i, axis=1)
        
        # Skip if only intercept remains
        if other_features.shape[1] <= 1:
            vif = np.inf
        else:
            # Simple linear regression to calculate R^2
            # Using numpy's lstsq for least squares
            try:
                coeffs, residuals, rank, s = np.linalg.lstsq(
                    other_features, feature_col, rcond=None
                )
                
                # Calculate predicted values
                y_pred = other_features @ coeffs
                
                # Calculate R^2
                ss_res = np.sum((feature_col - y_pred) ** 2)
                ss_tot = np.sum((feature_col - np.mean(feature_col)) ** 2)
                
                if ss_tot == 0:
                    r_squared = 0
                else:
                    r_squared = 1 - (ss_res / ss_tot)
                
                # VIF = 1 / (1 - R^2)
                if r_squared >= 1.0:
                    vif = np.inf
                else:
                    vif = 1 / (1 - r_squared)
            except np.linalg.LinAlgError:
                vif = np.inf
        
        vif_data.append({
            'feature': feature_names_with_intercept[i],
            'vif': vif
        })
    
    return pd.DataFrame(vif_data)


def run_vif_selection(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: List[str],
    vif_threshold: float = 5.0,
    logger: Optional[Any] = None
) -> Tuple[np.ndarray, List[str], pd.DataFrame]:
    """
    Perform VIF-based feature selection.
    Iteratively removes features with VIF >= threshold until all features pass.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target labels (n_samples,)
        feature_names: List of feature names
        vif_threshold: VIF threshold for removal (default: 5.0)
        logger: Optional logger instance
        
    Returns:
        Tuple of (reduced feature matrix, reduced feature names, VIF history DataFrame)
    """
    if logger is None:
        logger = get_logger(__name__)
    
    logger.info(f"Starting VIF selection with threshold={vif_threshold}")
    logger.info(f"Initial features: {len(feature_names)}")
    
    X_current = X.copy()
    names_current = feature_names.copy()
    vif_history = []
    
    iteration = 0
    max_iterations = len(feature_names)  # Safety limit
    
    while iteration < max_iterations:
        iteration += 1
        
        # Calculate VIF for current features
        vif_df = calculate_vif(X_current, names_current)
        
        # Record current state
        vif_history.append(vif_df.copy())
        
        # Find features above threshold
        high_vif = vif_df[vif_df['vif'] >= vif_threshold]
        
        if len(high_vif) == 0:
            logger.info(f"VIF selection complete after {iteration} iterations")
            logger.info(f"Final features: {len(names_current)}")
            break
        
        # Remove feature with highest VIF (tie-break: lower variance)
        # Calculate variance for tie-breaking
        variances = np.var(X_current, axis=0)
        
        # Get the feature with highest VIF
        max_vif_idx = high_vif['vif'].idxmax()
        feature_to_remove = high_vif.loc[max_vif_idx, 'feature']
        
        # If there are ties, use variance as tie-breaker
        max_vif_value = high_vif.loc[max_vif_idx, 'vif']
        tied_features = high_vif[high_vif['vif'] == max_vif_value]
        
        if len(tied_features) > 1:
            # Find the one with lowest variance among tied features
            lowest_var_feature = None
            lowest_var = np.inf
            
            for _, row in tied_features.iterrows():
                feat_name = row['feature']
                feat_idx = names_current.index(feat_name)
                feat_var = variances[feat_idx]
                
                if feat_var < lowest_var:
                    lowest_var = feat_var
                    lowest_var_feature = feat_name
            
            feature_to_remove = lowest_var_feature
        
        # Remove the feature
        remove_idx = names_current.index(feature_to_remove)
        names_current.remove(feature_to_remove)
        X_current = np.delete(X_current, remove_idx, axis=1)
        
        logger.debug(f"Removed feature '{feature_to_remove}' (VIF={vif_df.loc[max_vif_idx, 'vif']:.2f})")
        
        # Safety check: if no features left, break
        if len(names_current) == 0:
            logger.warning("All features removed by VIF selection!")
            break
    
    # Final VIF check
    final_vif_df = calculate_vif(X_current, names_current)
    vif_history.append(final_vif_df.copy())
    
    vif_history_df = pd.concat(vif_history, keys=range(len(vif_history)), names=['iteration', 'row'])
    vif_history_df = vif_history_df.reset_index()
    
    return X_current, names_current, vif_history_df


def train_l1_logistic_regression(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: List[str],
    vif_threshold: float = 5.0,
    C: float = 1.0,
    random_state: int = 42,
    logger: Optional[Any] = None
) -> Tuple[LogisticRegression, List[str], pd.DataFrame]:
    """
    Train L1-regularized Logistic Regression with VIF-based feature selection.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target labels (n_samples,)
        feature_names: List of feature names
        vif_threshold: VIF threshold for feature removal (default: 5.0)
        C: Inverse of regularization strength (default: 1.0)
        random_state: Random seed for reproducibility
        logger: Optional logger instance
        
    Returns:
        Tuple of (trained model, selected feature names, VIF history DataFrame)
    """
    if logger is None:
        logger = get_logger(__name__)
    
    logger.info("Starting L1 Logistic Regression training")
    logger.info(f"Input shape: {X.shape}")
    logger.info(f"Positive class ratio: {np.mean(y):.3f}")
    
    # Step 1: VIF-based feature selection
    X_reduced, selected_features, vif_history = run_vif_selection(
        X, y, feature_names, vif_threshold=vif_threshold, logger=logger
    )
    
    if len(selected_features) == 0:
        raise ValueError("No features remaining after VIF selection!")
    
    logger.info(f"Features after VIF selection: {len(selected_features)}")
    
    # Step 2: Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_reduced)
    
    # Step 3: Train L1-regularized Logistic Regression
    # Using liblinear solver which supports L1 penalty
    model = LogisticRegression(
        penalty='l1',
        solver='liblinear',
        C=C,
        random_state=random_state,
        max_iter=1000,
        class_weight='balanced'  # Handle class imbalance
    )
    
    model.fit(X_scaled, y)
    
    logger.info(f"Model trained successfully")
    logger.info(f"Number of non-zero coefficients: {np.sum(model.coef_ != 0)}")
    
    return model, selected_features, vif_history


def train_model_fold(
    X_train: np.ndarray,
    y_train: np.ndarray,
    feature_names: List[str],
    fold_idx: int,
    output_dir: Path,
    vif_threshold: float = 5.0,
    C: float = 1.0,
    random_state: int = 42,
    logger: Optional[Any] = None
) -> Tuple[LogisticRegression, List[str], Dict[str, Any]]:
    """
    Train a model on a single fold with VIF filtering and save metadata.
    
    Args:
        X_train: Training feature matrix
        y_train: Training labels
        feature_names: List of all feature names
        fold_idx: Current fold index
        output_dir: Directory to save VIF filtered features
        vif_threshold: VIF threshold for feature removal
        C: Inverse of regularization strength
        random_state: Random seed
        logger: Optional logger instance
        
    Returns:
        Tuple of (trained model, selected feature names, metadata dict)
    """
    if logger is None:
        logger = get_logger(__name__)
    
    logger.info(f"Training fold {fold_idx}")
    
    # Train model with VIF selection
    model, selected_features, vif_history = train_l1_logistic_regression(
        X_train, y_train, feature_names,
        vif_threshold=vif_threshold,
        C=C,
        random_state=random_state,
        logger=logger
    )
    
    # Save VIF filtered features for this fold
    vif_output_path = output_dir / f"vif_filtered_features_fold_{fold_idx}.csv"
    vif_history.to_csv(vif_output_path, index=False)
    logger.info(f"Saved VIF history to {vif_output_path}")
    
    # Save selected features
    selected_features_df = pd.DataFrame({
        'feature': selected_features,
        'fold': fold_idx
    })
    selected_features_path = output_dir / f"selected_features_fold_{fold_idx}.csv"
    selected_features_df.to_csv(selected_features_path, index=False)
    logger.info(f"Saved selected features to {selected_features_path}")
    
    metadata = {
        'fold': fold_idx,
        'initial_features': len(feature_names),
        'final_features': len(selected_features),
        'vif_threshold': vif_threshold,
        'C': C,
        'selected_features': selected_features,
        'vif_history_path': str(vif_output_path),
        'selected_features_path': str(selected_features_path)
    }
    
    return model, selected_features, metadata


def save_model(
    model: LogisticRegression,
    selected_features: List[str],
    output_path: Path,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Save trained model and metadata to disk.
    
    Args:
        model: Trained LogisticRegression model
        selected_features: List of feature names used in training
        output_path: Path to save the model
        metadata: Optional metadata dictionary
    """
    import pickle
    
    model_data = {
        'model': model,
        'selected_features': selected_features,
        'metadata': metadata
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'wb') as f:
        pickle.dump(model_data, f)
    
    logger.info(f"Model saved to {output_path}")


def load_model(model_path: Path) -> Tuple[LogisticRegression, List[str], Dict[str, Any]]:
    """
    Load trained model and metadata from disk.
    
    Args:
        model_path: Path to the saved model
        
    Returns:
        Tuple of (model, selected_features, metadata)
    """
    import pickle
    
    with open(model_path, 'rb') as f:
        model_data = pickle.load(f)
    
    logger.info(f"Model loaded from {model_path}")
    logger.info(f"Features: {len(model_data['selected_features'])}")
    
    return (
        model_data['model'],
        model_data['selected_features'],
        model_data.get('metadata', {})
    )
