"""
Model Training Module for Plant Pathogen Host Range Prediction.

Implements L1-regularized Logistic Regression with nested VIF analysis
for feature selection within each cross-validation fold.
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
from src.utils.validators import validate_dataframe_schema

# Initialize logger
logger = get_logger(__name__)


def calculate_vif(features: pd.DataFrame, exclude_first: bool = True) -> pd.Series:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.

    Args:
        features: DataFrame containing feature columns.
        exclude_first: If True, exclude the first column (intercept) from calculation.

    Returns:
        Series of VIF values indexed by feature name.
    """
    if features.shape[1] == 0:
        return pd.Series(dtype=float)

    # Add intercept column if needed (sklearn handles this, but VIF needs it)
    # VIF = 1 / (1 - R^2) where R^2 is from regressing feature i on all other features
    vif_data = []
    feature_names = features.columns.tolist()

    for i, col in enumerate(feature_names):
        # Skip the first column if exclude_first is True
        if exclude_first and i == 0:
            continue

        X_other = features.drop(columns=[col])
        if X_other.shape[1] == 0:
            # Only one feature left, VIF is undefined (or 1.0 by convention)
            vif_data.append((col, 1.0))
            continue

        # Fit OLS regression of current feature on others
        # Using numpy for simplicity: y = X * beta + error
        # R^2 = 1 - (SS_res / SS_tot)
        try:
            # Add constant for intercept
            X_with_const = np.column_stack([np.ones(X_other.shape[0]), X_other.values])
            y = features[col].values

            # Solve least squares
            beta, residuals, rank, s = np.linalg.lstsq(X_with_const, y, rcond=None)

            if residuals.size > 0:
                ss_res = residuals[0]
            else:
                # Perfect fit or singular matrix
                ss_res = 0.0

            ss_tot = np.sum((y - np.mean(y)) ** 2)

            if ss_tot == 0:
                r_squared = 0.0
            else:
                r_squared = 1.0 - (ss_res / ss_tot)

            # Clamp r_squared to [0, 1) to avoid division by zero
            r_squared = min(r_squared, 0.9999)
            r_squared = max(r_squared, 0.0)

            vif = 1.0 / (1.0 - r_squared)
            vif_data.append((col, vif))

        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
            vif_data.append((col, np.inf))

    return pd.Series([v for _, v in vif_data], index=[col for col, _ in vif_data])


def run_vif_selection(
    X: pd.DataFrame,
    threshold: float = 5.0,
    logger: Optional[Any] = None
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Perform iterative VIF-based feature selection.

    Removes features with VIF >= threshold until all remaining features
    have VIF < threshold. Ties are broken by selecting the feature with
    lower variance.

    Args:
        X: Feature DataFrame.
        threshold: VIF threshold for removal (default 5.0).
        logger: Logger instance.

    Returns:
        Tuple of (reduced DataFrame, list of removed feature names).
    """
    if logger is None:
        logger = get_logger(__name__)

    current_features = X.copy()
    removed_features = []
    iteration = 0

    while True:
        iteration += 1
        if current_features.shape[1] == 0:
            logger.warning("All features removed during VIF selection!")
            break

        vif_series = calculate_vif(current_features)

        if vif_series.empty:
            break

        # Check if any feature exceeds threshold
        high_vif_mask = vif_series >= threshold

        if not high_vif_mask.any():
            logger.info(f"VIF selection complete after {iteration} iterations. "
                      f"Remaining features: {len(current_features.columns)}")
            break

        # Find features with highest VIF
        high_vif_features = vif_series[high_vif_mask]
        max_vif = high_vif_features.max()
        candidates = high_vif_features[high_vif_features == max_vif].index.tolist()

        # Tie-breaker: select feature with lowest variance
        if len(candidates) > 1:
            variances = current_features[candidates].var()
            to_remove = variances.idxmin()
            logger.debug(f"Tie-breaker: removing {to_remove} (variance: {variances[to_remove]:.4f}) "
                       f"among candidates with VIF={max_vif:.2f}")
        else:
            to_remove = candidates[0]

        logger.info(f"Iteration {iteration}: Removing feature '{to_remove}' with VIF={max_vif:.2f}")

        # Remove the feature
        current_features = current_features.drop(columns=[to_remove])
        removed_features.append(to_remove)

        # Safety check: prevent infinite loops
        if iteration > X.shape[1]:
            logger.error("VIF selection exceeded maximum iterations. Breaking.")
            break

    return current_features, removed_features


def train_l1_logistic_regression(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    vif_threshold: float = 5.0,
    random_state: int = 42,
    fold_id: Optional[int] = None,
    output_dir: Optional[Union[str, Path]] = None
) -> Tuple[LogisticRegression, pd.DataFrame, List[str]]:
    """
    Train an L1-regularized Logistic Regression model with VIF-based feature selection.

    This function performs:
    1. VIF-based feature selection on the training fold only.
    2. Standardization of features.
    3. Training of LogisticRegression with penalty='l1' and solver='liblinear'.

    Args:
        X_train: Feature DataFrame for training.
        y_train: Target Series for training.
        vif_threshold: VIF threshold for feature removal (default 5.0).
        random_state: Random seed for reproducibility.
        fold_id: Optional fold identifier for output file naming.
        output_dir: Directory to save VIF-filtered feature list.

    Returns:
        Tuple of:
            - Trained LogisticRegression model
            - DataFrame of selected features (with their indices)
            - List of removed feature names
    """
    logger.info(f"Starting training for L1 Logistic Regression (VIF threshold={vif_threshold})")

    # Ensure output directory exists
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

    # Step 1: VIF-based feature selection (strictly on training data)
    logger.info(f"Performing VIF selection on {X_train.shape[1]} features...")
    X_selected, removed_features = run_vif_selection(X_train, threshold=vif_threshold, logger=logger)

    selected_features = X_selected.columns.tolist()
    logger.info(f"Selected {len(selected_features)} features after VIF filtering: {selected_features}")

    # Save reduced feature set to file
    if output_dir and fold_id is not None:
        feature_file = output_path / f"vif_filtered_features_fold_{fold_id}.csv"
        selected_df = pd.DataFrame({
            'feature_index': range(len(selected_features)),
            'feature_name': selected_features
        })
        selected_df.to_csv(feature_file, index=False)
        logger.info(f"Saved VIF-filtered features to {feature_file}")

    # Handle edge case: no features remain
    if len(selected_features) == 0:
        logger.error("No features remain after VIF selection. Cannot train model.")
        raise ValueError("No features available after VIF selection. "
                       "Try lowering the VIF threshold or check input data quality.")

    # Step 2: Standardize features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_selected)
    X_train_scaled_df = pd.DataFrame(X_train_scaled, columns=selected_features, index=X_selected.index)

    # Step 3: Train L1-regularized Logistic Regression
    logger.info("Training LogisticRegression with penalty='l1', solver='liblinear'...")

    model = LogisticRegression(
        penalty='l1',
        solver='liblinear',
        random_state=random_state,
        max_iter=1000,
        C=1.0,  # Regularization strength
        class_weight='balanced'  # Handle class imbalance
    )

    model.fit(X_train_scaled_df, y_train)

    logger.info(f"Model training complete. Coefficients: {model.coef_}")

    return model, X_selected, removed_features


def train_model_fold(
    X: pd.DataFrame,
    y: pd.Series,
    train_idx: np.ndarray,
    val_idx: np.ndarray,
    vif_threshold: float = 5.0,
    random_state: int = 42,
    fold_id: int = 0,
    output_dir: Optional[Union[str, Path]] = None
) -> Tuple[LogisticRegression, float, Dict[str, Any]]:
    """
    Train a single fold of the cross-validation loop.

    Args:
        X: Full feature DataFrame.
        y: Full target Series.
        train_idx: Indices for training set.
        val_idx: Indices for validation set.
        vif_threshold: VIF threshold for feature selection.
        random_state: Random seed.
        fold_id: Fold identifier.
        output_dir: Directory to save VIF-filtered features.

    Returns:
        Tuple of:
            - Trained model
            - Validation AUPRC (placeholder, actual calculation in evaluate module)
            - Metrics dictionary
    """
    # Split data
    X_train = X.iloc[train_idx].reset_index(drop=True)
    y_train = y.iloc[train_idx].reset_index(drop=True)
    X_val = X.iloc[val_idx].reset_index(drop=True)
    y_val = y.iloc[val_idx].reset_index(drop=True)

    # Train model
    model, X_selected, removed_features = train_l1_logistic_regression(
        X_train=X_train,
        y_train=y_train,
        vif_threshold=vif_threshold,
        random_state=random_state,
        fold_id=fold_id,
        output_dir=output_dir
    )

    # Standardize validation data using training scaler
    scaler = StandardScaler()
    X_val_scaled = scaler.fit_transform(X_selected)  # Fit on train, transform val

    # Evaluate on validation set
    from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score

    y_val_pred_proba = model.predict_proba(X_val_scaled)[:, 1]
    y_val_pred = model.predict(X_val_scaled)

    metrics = {
        'fold_id': fold_id,
        'n_train_samples': len(train_idx),
        'n_val_samples': len(val_idx),
        'n_features_selected': len(X_selected.columns),
        'n_features_removed': len(removed_features),
        'vif_threshold': vif_threshold
    }

    # Calculate metrics (handle single-class case)
    try:
        if len(np.unique(y_val)) > 1:
            metrics['val_auprc'] = roc_auc_score(y_val, y_val_pred_proba)
        else:
            metrics['val_auprc'] = np.nan
    except Exception as e:
        logger.warning(f"Could not calculate AUPRC for fold {fold_id}: {e}")
        metrics['val_auprc'] = np.nan

    try:
        metrics['val_precision'] = precision_score(y_val, y_val_pred, zero_division=0)
    except:
        metrics['val_precision'] = 0.0

    try:
        metrics['val_recall'] = recall_score(y_val, y_val_pred, zero_division=0)
    except:
        metrics['val_recall'] = 0.0

    try:
        metrics['val_f1'] = f1_score(y_val, y_val_pred, zero_division=0)
    except:
        metrics['val_f1'] = 0.0

    return model, metrics['val_auprc'], metrics


def save_model(model: LogisticRegression, scaler: StandardScaler, output_path: Union[str, Path]) -> None:
    """
    Save trained model and scaler to disk.

    Args:
        model: Trained LogisticRegression model.
        scaler: Fitted StandardScaler.
        output_path: Path to save the model.
    """
    import joblib

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    model_data = {
        'model': model,
        'scaler': scaler
    }

    joblib.dump(model_data, output_path)
    logger.info(f"Model saved to {output_path}")


def load_model(model_path: Union[str, Path]) -> Tuple[LogisticRegression, StandardScaler]:
    """
    Load trained model and scaler from disk.

    Args:
        model_path: Path to the saved model.

    Returns:
        Tuple of (model, scaler).
    """
    import joblib

    model_path = Path(model_path)
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    model_data = joblib.load(model_path)
    return model_data['model'], model_data['scaler']
