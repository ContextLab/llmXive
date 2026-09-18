import os
import logging
import random
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any, Callable

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, LeaveOneOut, KFold
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet
from sklearn.metrics import r2_score

# Import existing phylogenetic utilities
from code.modeling.phylo import load_phylogeny, construct_covariance_matrix, train_pgls
from code.config import get_config

logger = logging.getLogger(__name__)


class ModelTrainingError(Exception):
    """Custom exception for model training failures."""
    pass


class StratifiedSplitError(Exception):
    """Custom exception for stratified split failures."""
    pass


def get_clade_members(tree, clade_labels: Dict[str, str]) -> Dict[str, List[str]]:
    """
    Extract members of each clade from a phylogenetic tree and label mapping.

    Args:
        tree: Dendropy Tree object.
        clade_labels: Dict mapping tip labels to clade names.

    Returns:
        Dict mapping clade name to list of species in that clade.
    """
    clade_members = {}
    for tip in tree.leaf_node_iter():
        label = tip.taxon.label
        if label in clade_labels:
            clade = clade_labels[label]
            clade_members.setdefault(clade, []).append(label)
    return clade_members


def find_balanced_clades(clade_members: Dict[str, List[str]], min_size: int = 2) -> List[str]:
    """
    Filter clades that are large enough to be useful for stratification.

    Args:
        clade_members: Dict of clade -> members.
        min_size: Minimum number of members required.

    Returns:
        List of valid clade names.
    """
    return [c for c, members in clade_members.items() if len(members) >= min_size]


def create_stratified_split(
    species_list: List[str],
    clade_labels: Dict[str, str],
    train_ratio: float = 0.8,
    random_seed: int = 42
) -> Tuple[List[str], List[str]]:
    """
    Split species into train/test sets while preserving phylogenetic clade structure.

    Args:
        species_list: List of all species.
        clade_labels: Dict mapping species to clade.
        train_ratio: Fraction for training.
        random_seed: Random seed for reproducibility.

    Returns:
        Tuple of (train_species, test_species).
    """
    random.seed(random_seed)
    clade_members = get_clade_members(None, clade_labels)
    valid_clades = find_balanced_clades(clade_members)

    train_species = []
    test_species = []

    for clade in valid_clades:
        members = clade_members[clade]
        random.shuffle(members)
        split_idx = int(len(members) * train_ratio)
        train_species.extend(members[:split_idx])
        test_species.extend(members[split_idx:])

    # Handle species not in valid clades (random split)
    remaining = [s for s in species_list if s not in train_species and s not in test_species]
    random.shuffle(remaining)
    split_idx = int(len(remaining) * train_ratio)
    train_species.extend(remaining[:split_idx])
    test_species.extend(remaining[split_idx:])

    return train_species, test_species


def apply_pca(
    X: np.ndarray,
    y: np.ndarray,
    target_variance: float = 0.95,
    max_components: Optional[int] = None
) -> Tuple[np.ndarray, PCA, int]:
    """
    Apply PCA for dimensionality reduction.

    Args:
        X: Feature matrix (n_samples, n_features).
        y: Target vector (n_samples,).
        target_variance: Cumulative variance to retain.
        max_components: Maximum number of components to keep.

    Returns:
        Tuple of (reduced_X, fitted_pca, n_components_kept).
    """
    if X.shape[0] == 0:
        raise ModelTrainingError("Input feature matrix is empty.")

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    pca = PCA(n_components=target_variance)
    X_reduced = pca.fit_transform(X_scaled)

    n_components = X_reduced.shape[1]
    if max_components and n_components > max_components:
        pca = PCA(n_components=max_components)
        X_reduced = pca.fit_transform(X_scaled)
        n_components = max_components

    logger.info(f"PCA reduced features from {X.shape[1]} to {n_components} "
                f"(retained variance: {sum(pca.explained_variance_ratio_):.4f})")

    return X_reduced, pca, n_components


def load_pca_features(pca_path: Path) -> pd.DataFrame:
    """Load PCA-reduced features from disk."""
    if not pca_path.exists():
        raise FileNotFoundError(f"PCA features file not found: {pca_path}")
    return pd.read_csv(pca_path)


def determine_cv_method(n_samples: int, n_folds: int = 5) -> Union[KFold, LeaveOneOut]:
    """
    Determine appropriate cross-validation method based on sample size.

    Args:
        n_samples: Number of samples.
        n_folds: Number of folds for KFold.

    Returns:
        CV splitter object.
    """
    if n_samples < 20:
        logger.info(f"Sample size {n_samples} < 20, using Leave-One-Out CV")
        return LeaveOneOut()
    else:
        logger.info(f"Sample size {n_samples} >= 20, using {n_folds}-fold CV")
        return KFold(n_splits=n_folds, shuffle=True, random_state=42)


def train_models_loo(
    X: np.ndarray,
    y: np.ndarray,
    clade_labels: Optional[Dict[str, str]] = None
) -> Dict[str, Dict[str, float]]:
    """
    Train models using Leave-One-Out Cross-Validation.

    Args:
        X: Feature matrix.
        y: Target vector.
        clade_labels: Optional clade mapping for stratification.

    Returns:
        Dict of model metrics.
    """
    cv = determine_cv_method(len(y))
    models = {
        "RandomForest": RandomForestRegressor(n_estimators=100, random_state=42),
        "ElasticNet": ElasticNet(random_state=42, max_iter=1000),
    }

    results = {}
    for name, model in models.items():
        r2_scores = []
        for train_idx, test_idx in cv.split(X):
            model.fit(X[train_idx], y[train_idx])
            preds = model.predict(X[test_idx])
            r2_scores.append(r2_score(y[test_idx], preds))
        results[name] = {"mean_r2": float(np.mean(r2_scores))}

    return results


def train_models_5fold(
    X: np.ndarray,
    y: np.ndarray,
    clade_labels: Optional[Dict[str, str]] = None
) -> Dict[str, Dict[str, float]]:
    """
    Train models using 5-Fold Cross-Validation.

    Args:
        X: Feature matrix.
        y: Target vector.
        clade_labels: Optional clade mapping for stratification.

    Returns:
        Dict of model metrics.
    """
    cv = determine_cv_method(len(y), n_folds=5)
    models = {
        "RandomForest": RandomForestRegressor(n_estimators=100, random_state=42),
        "ElasticNet": ElasticNet(random_state=42, max_iter=1000),
    }

    results = {}
    for name, model in models.items():
        r2_scores = []
        for train_idx, test_idx in cv.split(X):
            model.fit(X[train_idx], y[train_idx])
            preds = model.predict(X[test_idx])
            r2_scores.append(r2_score(y[test_idx], preds))
        results[name] = {"mean_r2": float(np.mean(r2_scores))}

    return results


def train_pgls_with_pca_optimization(
    X: np.ndarray,
    y: np.ndarray,
    species_names: List[str],
    tree_path: Path,
    variance_threshold: float = 0.95,
    max_pca_components: Optional[int] = None
) -> Dict[str, Any]:
    """
    Train PGLS model with automatic PCA optimization if features > N.

    This function implements the performance optimization required by T037:
    If the number of features exceeds the number of samples (or a configurable
    threshold), PCA is applied before PGLS to prevent overfitting.

    Args:
        X: Feature matrix (n_samples, n_features).
        y: Target vector (n_samples,).
        species_names: List of species corresponding to rows in X.
        tree_path: Path to Newick tree file.
        variance_threshold: Variance to retain in PCA (default 0.95).
        max_pca_components: Maximum PCA components to keep.

    Returns:
        Dict containing model results and metadata.
    """
    n_samples, n_features = X.shape

    logger.info(f"Training PGLS with {n_samples} samples and {n_features} features")

    # Check if PCA optimization is needed
    use_pca = n_features > n_samples
    config = get_config()
    pca_threshold = getattr(config, 'pca_feature_threshold', n_samples)

    if n_features > pca_threshold:
        use_pca = True
        logger.info(f"Feature count ({n_features}) exceeds threshold ({pca_threshold}), "
                    f"applying PCA optimization before PGLS")

    X_processed = X
    pca_info = None

    if use_pca:
        X_processed, pca_model, n_comp = apply_pca(
            X, y,
            target_variance=variance_threshold,
            max_components=max_pca_components
        )
        pca_info = {
            "applied": True,
            "original_features": n_features,
            "reduced_features": n_comp,
            "variance_retained": float(sum(pca_model.explained_variance_ratio_))
        }
    else:
        pca_info = {"applied": False, "reason": "Features <= samples"}

    # Load phylogeny and construct covariance matrix
    try:
        tree = load_phylogeny(tree_path)
        cov_matrix = construct_covariance_matrix(tree, species_names)
    except Exception as e:
        raise ModelTrainingError(f"Failed to load phylogeny or construct covariance: {e}")

    # Train PGLS
    try:
        pgls_result = train_pgls(X_processed, y, cov_matrix, species_names)
    except Exception as e:
        raise ModelTrainingError(f"PGLS training failed: {e}")

    return {
        "model_results": pgls_result,
        "pca_info": pca_info,
        "optimization_applied": use_pca,
        "feature_count": n_features,
        "sample_count": n_samples
    }


def main():
    """
    Main entry point for running the training pipeline with PCA optimization.
    Demonstrates the T037 optimization logic.
    """
    config = get_config()
    data_path = config.get_data_path()

    # Load aligned data
    aligned_csv = Path(data_path) / "processed" / "aligned_matrix.csv"
    if not aligned_csv.exists():
        logger.error(f"Aligned matrix not found at {aligned_csv}")
        return

    df = pd.read_csv(aligned_csv)
    species_col = config.get_species_list()[0] if config.get_species_list() else "species"

    # Prepare features and target
    feature_cols = [c for c in df.columns if c not in [species_col, "metabolite_class"]]
    if len(feature_cols) < 2:
        logger.warning("Not enough features for training")
        return

    X = df[feature_cols].fillna(0).values
    y = df["metabolite_abundance"].fillna(0).values
    species_names = df[species_col].tolist()

    # Run PGLS with PCA optimization
    tree_path = Path(data_path) / "raw" / "phylogeny" / "species_tree.nwk"
    if not tree_path.exists():
        logger.warning(f"Tree file not found at {tree_path}, skipping PGLS")
        return

    try:
        result = train_pgls_with_pca_optimization(
            X, y, species_names, tree_path,
            variance_threshold=0.95,
            max_pca_components=10
        )
        logger.info(f"Optimization applied: {result['optimization_applied']}")
        logger.info(f"PCA info: {result['pca_info']}")
        logger.info(f"PGLS R²: {result['model_results'].get('r2', 'N/A')}")
    except ModelTrainingError as e:
        logger.error(f"Training failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
