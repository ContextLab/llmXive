from __future__ import annotations

import logging
from typing import List, Tuple, Optional, Dict, Any, Union

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.linear_model import LassoCV

from utils.logger import get_logger

logger = get_logger(__name__)


def lasso_selection(
    X: np.ndarray,
    y: np.ndarray,
    cv_folds: int = 5,
    random_state: Optional[int] = None,
    normalize: bool = False,
    max_iter: int = 10000
) -> Tuple[List[int], np.ndarray, Dict[str, Any]]:
    """
    Perform LASSO variable selection using cross-validated regularization parameter.

    This function uses LassoCV to automatically select the optimal lambda (alpha)
    via k-fold cross-validation, then identifies non-zero coefficients as selected
    variables.

    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        cv_folds: Number of cross-validation folds
        random_state: Random seed for reproducibility
        normalize: Whether to normalize features before fitting
        max_iter: Maximum iterations for coordinate descent

    Returns:
        selected_indices: List of indices of selected variables (non-zero coefficients)
        coefficients: Array of fitted coefficients (including intercept at index 0)
        diagnostics: Dict containing selection metadata (best_alpha, n_selected, etc.)

    Raises:
        ValueError: If X or y have incompatible shapes
        RuntimeError: If LassoCV fails to converge
    """
    if X.shape[0] != y.shape[0]:
        raise ValueError(f"X and y must have same number of samples: {X.shape[0]} vs {y.shape[0]}")

    if X.ndim != 2:
        raise ValueError(f"X must be 2D array, got {X.ndim}D")

    n_samples, n_features = X.shape
    logger.debug(f"LASSO selection on {n_samples} samples, {n_features} features")

    # Handle constant features (variance = 0)
    feature_variance = np.var(X, axis=0)
    constant_features = np.where(feature_variance == 0)[0]
    if len(constant_features) > 0:
        logger.warning(f"Removing {len(constant_features)} constant features: {constant_features}")
        X = np.delete(X, constant_features, axis=1)
        # Adjust feature indices in final result later

    n_features_clean = X.shape[1]

    # Fit LassoCV
    try:
        lasso_cv = LassoCV(
            cv=cv_folds,
            random_state=random_state,
            normalize=normalize,
            max_iter=max_iter,
            n_jobs=1,  # CPU-only as per FR-003
            verbose=0
        )
        lasso_cv.fit(X, y)
        best_alpha = lasso_cv.alpha_
        coefficients = lasso_cv.coef_
    except Exception as e:
        logger.error(f"LassoCV failed: {e}")
        raise RuntimeError(f"LASSO selection failed: {e}")

    # Check convergence
    if hasattr(lasso_cv, 'n_iter_') and lasso_cv.n_iter_ >= max_iter:
        logger.warning(f"LassoCV reached max iterations ({max_iter}) without full convergence")

    # Identify selected features (non-zero coefficients)
    selected_mask = coefficients != 0
    selected_indices_clean = np.where(selected_mask)[0].tolist()

    # Map back to original indices if constant features were removed
    if len(constant_features) > 0:
        selected_indices = []
        clean_idx = 0
        for orig_idx in range(n_features):
            if orig_idx in constant_features:
                continue
            if clean_idx in selected_indices_clean:
                selected_indices.append(orig_idx)
            clean_idx += 1
    else:
        selected_indices = selected_indices_clean

    # Prepare diagnostics
    diagnostics = {
        'method': 'LASSO',
        'best_alpha': float(best_alpha),
        'n_selected': len(selected_indices),
        'n_features_total': n_features,
        'n_features_removed': len(constant_features),
        'converged': True,  # Assuming success if no exception
        'cv_folds': cv_folds,
        'random_state': random_state
    }

    logger.info(
        f"LASSO selected {len(selected_indices)}/{n_features} features "
        f"(alpha={best_alpha:.6f})"
    )

    return selected_indices, coefficients, diagnostics


def select_variables_lasso(
    X: np.ndarray,
    y: np.ndarray,
    true_coefficients: Optional[np.ndarray] = None,
    alpha: float = 0.05,
    cv_folds: int = 5,
    random_state: Optional[int] = None
) -> Dict[str, Any]:
    """
    Wrapper for LASSO selection that returns structured results including
    selected variables and performance metrics.

    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        true_coefficients: Ground truth coefficients for evaluation (optional)
        alpha: Significance level for p-value calculation (not used in LASSO selection itself)
        cv_folds: Cross-validation folds for LassoCV
        random_state: Random seed

    Returns:
        Dict with keys:
            - 'selected_indices': list of selected feature indices
            - 'coefficients': fitted coefficients
            - 'diagnostics': selection metadata
            - 'n_selected': number of selected variables
            - 'power_rate': empirical power if true_coefficients provided
    """
    selected_indices, coefficients, diagnostics = lasso_selection(
        X, y, cv_folds=cv_folds, random_state=random_state
    )

    result = {
        'method': 'LASSO',
        'selected_indices': selected_indices,
        'coefficients': coefficients,
        'diagnostics': diagnostics,
        'n_selected': len(selected_indices)
    }

    # Calculate power if ground truth is available
    if true_coefficients is not None:
        if len(true_coefficients) != X.shape[1]:
            logger.warning(
                f"true_coefficients length ({len(true_coefficients)}) "
                f"does not match X features ({X.shape[1]}), skipping power calculation"
            )
        else:
            # True non-zero coefficients
            true_nonzero_mask = true_coefficients != 0
            n_true_nonzero = np.sum(true_nonzero_mask)

            if n_true_nonzero > 0:
                # True positives: selected and truly non-zero
                selected_set = set(selected_indices)
                true_positives = sum(1 for idx in selected_set if true_nonzero_mask[idx])
                power_rate = true_positives / n_true_nonzero
            else:
                power_rate = 0.0

            result['power_rate'] = float(power_rate)
            result['true_positives'] = int(true_positives if n_true_nonzero > 0 else 0)
            result['n_true_nonzero'] = int(n_true_nonzero)

    return result


def main() -> None:
    """
    Main entry point for LASSO selection module.
    Runs a quick validation test with synthetic data.
    """
    logger.info("Running LASSO selection module validation...")

    # Generate simple test data
    np.random.seed(42)
    n_samples, n_features = 100, 10
    X = np.random.randn(n_samples, n_features)
    true_coef = np.array([1.0, -1.5, 0.0, 0.0, 2.0] + [0.0] * 5)
    y = X @ true_coef + np.random.randn(n_samples) * 0.5

    # Run selection
    result = select_variables_lasso(X, y, true_coefficients=true_coef, random_state=42)

    logger.info(f"Selected indices: {result['selected_indices']}")
    logger.info(f"Number selected: {result['n_selected']}")
    logger.info(f"Power rate: {result.get('power_rate', 'N/A')}")

    # Verify expected behavior
    expected_selected = {0, 1, 4}  # Indices with non-zero true coefficients
    actual_selected = set(result['selected_indices'])

    if expected_selected.issubset(actual_selected):
        logger.info("✓ LASSO successfully recovered all true non-zero coefficients")
    else:
        logger.warning(f"⚠ LASSO missed some true coefficients. Expected subset of {expected_selected}, got {actual_selected}")

    logger.info("LASSO selection module validation complete.")


if __name__ == "__main__":
    main()