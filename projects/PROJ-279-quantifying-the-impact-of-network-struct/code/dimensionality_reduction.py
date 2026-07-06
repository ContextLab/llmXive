import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union

from sklearn.decomposition import PCA
from sklearn.linear_model import LassoCV, LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectFromModel
from sklearn.model_selection import cross_val_score, KFold, LeaveOneOut

from config.env_config import get_processed_dir
from logging_config import get_logger

logger = get_logger(__name__)

def run_stability_selection(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: List[str],
    n_iterations: int = 100,
    cv_folds: int = 5,
    random_state: int = 42
) -> Tuple[List[str], Dict[str, float]]:
    """
    Performs stability selection to identify robust features.
    
    Uses LassoCV with subsampling to determine which features
    consistently appear in the model across folds/iterations.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        feature_names: List of feature names corresponding to columns in X
        n_iterations: Number of subsampling iterations
        cv_folds: Number of folds for inner CV of LassoCV
        random_state: Random seed for reproducibility
        
    Returns:
        selected_features: List of feature names selected by stability selection
        stability_scores: Dict mapping feature name to its selection frequency
    """
    if X.shape[0] < 10:
        logger.warning(f"Sample size ({X.shape[0]}) too small for stability selection. Returning all features.")
        return list(feature_names), {name: 1.0 for name in feature_names}

    n_samples, n_features = X.shape
    selection_counts = np.zeros(n_features)
    
    # Use a subset of data for each iteration if dataset is large
    # but ensure we have enough samples for CV
    subsample_size = max(int(0.8 * n_samples), 10)
    
    for i in range(n_iterations):
        # Subsample
        rng = np.random.RandomState(random_state + i)
        indices = rng.choice(n_samples, size=subsample_size, replace=False)
        X_sub = X[indices]
        y_sub = y[indices]
        
        # Standardize within the subsample
        scaler = StandardScaler()
        X_sub_scaled = scaler.fit_transform(X_sub)
        
        # Fit LassoCV
        # Use a small number of alphas for speed in stability selection
        lasso = LassoCV(cv=3, random_state=random_state + i, n_jobs=1)
        try:
            lasso.fit(X_sub_scaled, y_sub)
            mask = lasso.coef_ != 0
            selection_counts += mask.astype(int)
        except Exception as e:
            logger.warning(f"Iteration {i} failed: {e}. Skipping.")
            continue

    stability_scores = selection_counts / n_iterations
    # Threshold: features selected in > 50% of iterations
    threshold = 0.5
    selected_mask = stability_scores > threshold
    selected_features = [feature_names[j] for j in range(n_features) if selected_mask[j]]
    
    logger.info(f"Stability Selection: Selected {len(selected_features)} features out of {n_features} (threshold={threshold})")
    logger.debug(f"Stability scores: {dict(zip(feature_names, stability_scores))}")
    
    return selected_features, dict(zip(feature_names, stability_scores))

def apply_dimensionality_reduction(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: List[str],
    mode: str = "stability",
    n_components: Optional[int] = None,
    threshold: float = 0.5
) -> Tuple[np.ndarray, List[str], Dict[str, Any]]:
    """
    Applies dimensionality reduction based on sample size (N).
    
    Logic:
    - If N < 30 (Small N): Uses Stability Selection (Lasso-based) to prevent overfitting.
    - If N >= 30 (Standard): Uses PCA if n_components is specified, otherwise returns original.
    
    Args:
        X: Feature matrix
        y: Target vector
        feature_names: List of original feature names
        mode: 'stability' (Lasso-based selection) or 'pca'
        n_components: Number of PCA components (only used if mode='pca')
        threshold: Stability threshold (only used if mode='stability')
        
    Returns:
        X_reduced: Transformed feature matrix
        reduced_names: List of feature names (original names for selection, 'PCx' for PCA)
        metadata: Dict with reduction details
    """
    n_samples = X.shape[0]
    metadata = {
        "original_n": n_samples,
        "original_features": len(feature_names),
        "mode": mode,
        "n_reduced_features": 0
    }

    if mode == "stability":
        logger.info(f"Sample size N={n_samples}. Applying Stability Selection for robustness.")
        selected_features, stability_scores = run_stability_selection(
            X, y, feature_names, random_state=42
        )
        
        if not selected_features:
            logger.warning("Stability selection resulted in no features. Falling back to top 5 by variance.")
            # Fallback: Keep top 5 by variance if nothing selected
            variances = np.var(X, axis=0)
            top_indices = np.argsort(variances)[-5:][::-1]
            selected_features = [feature_names[i] for i in top_indices]
            stability_scores = {name: 0.0 for name in feature_names}
            for f in selected_features:
                stability_scores[f] = 1.0 # Mark as kept by fallback

        # Filter X
        indices = [i for i, name in enumerate(feature_names) if name in selected_features]
        X_reduced = X[:, indices]
        reduced_names = selected_features
        metadata["stability_scores"] = stability_scores
        metadata["threshold"] = threshold

    elif mode == "pca":
        if n_samples < n_components:
            logger.warning(f"N ({n_samples}) < n_components ({n_components}). Adjusting n_components to N-1.")
            n_components = max(1, n_samples - 1)
        
        logger.info(f"Applying PCA with {n_components} components.")
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        pca = PCA(n_components=n_components)
        X_reduced = pca.fit_transform(X_scaled)
        reduced_names = [f"PC{i+1}" for i in range(n_components)]
        
        metadata["explained_variance_ratio"] = pca.explained_variance_ratio_.tolist()
        metadata["cumulative_variance"] = np.cumsum(pca.explained_variance_ratio_).tolist()
    
    else:
        # No reduction
        X_reduced = X
        reduced_names = feature_names

    metadata["n_reduced_features"] = X_reduced.shape[1]
    return X_reduced, reduced_names, metadata

def main():
    """
    Main entry point to demonstrate dimensionality reduction on processed descriptors.
    This script reads the aggregated descriptors, applies reduction, and saves the results.
    """
    processed_dir = get_processed_dir()
    descriptors_path = Path(processed_dir) / "descriptors.csv"
    
    if not descriptors_path.exists():
        logger.error(f"Descriptors file not found at {descriptors_path}. Run aggregate_descriptors first.")
        return

    logger.info(f"Loading descriptors from {descriptors_path}")
    df = pd.read_csv(descriptors_path)
    
    # Identify feature columns (exclude 'config_id' and target 'thermal_conductivity')
    # Assuming 'thermal_conductivity' is the target column based on US3
    target_col = 'thermal_conductivity'
    if target_col not in df.columns:
        # Fallback: try to find a column with 'k' or 'conductivity'
        cols = [c for c in df.columns if 'conductivity' in c.lower() or c == 'k']
        if cols:
            target_col = cols[0]
        else:
            logger.error(f"Target column '{target_col}' not found. Cannot proceed.")
            return

    feature_cols = [c for c in df.columns if c != 'config_id' and c != target_col]
    
    if len(feature_cols) == 0:
        logger.error("No feature columns found.")
        return

    X = df[feature_cols].values
    y = df[target_col].values
    
    # Determine mode based on N
    N = len(X)
    if N < 30:
        mode = "stability"
        logger.info(f"Small sample size (N={N}). Enabling Stability Selection (T032).")
    else:
        mode = "pca" # Default to PCA for larger N if requested, or None for no reduction
        # For this specific task T032, we focus on the "small N" logic, 
        # but we run PCA if N is large to demonstrate the pipeline.
        # If the task strictly implies "only for small N", we might skip for large N.
        # However, "preprocessing step for small N" implies we *must* do it for small N.
        # Let's run PCA for large N to show the full capability, or skip if not needed.
        # To be safe and strictly follow "preprocessing step for small N", 
        # we will only apply reduction if N < 30 OR if we want to reduce features generally.
        # Let's stick to the prompt: "as a preprocessing step for small N".
        # So if N >= 30, we might not *need* it, but PCA is still useful.
        # We will run Stability for N < 30, and PCA for N >= 30 (optional but good practice).
        pass

    # Apply reduction
    X_reduced, reduced_names, metadata = apply_dimensionality_reduction(
        X, y, feature_cols, mode=mode, n_components=min(5, len(feature_cols))
    )

    logger.info(f"Reduction complete. Original: {X.shape[1]}, Reduced: {X_reduced.shape[1]}")
    
    # Create output DataFrame
    result_df = pd.DataFrame(X_reduced, columns=reduced_names)
    result_df['config_id'] = df['config_id']
    result_df[target_col] = y
    
    # Save results
    output_path = Path(processed_dir) / "descriptors_reduced.csv"
    result_df.to_csv(output_path, index=False)
    logger.info(f"Saved reduced descriptors to {output_path}")
    
    # Save metadata
    metadata_path = Path(processed_dir) / "reduction_metadata.json"
    import json
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved reduction metadata to {metadata_path}")

if __name__ == "__main__":
    main()
