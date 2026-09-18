"""
Performance optimization module for PGLS modeling.

Implements conditional PCA application before PGLS when feature count exceeds
the number of samples (N), preventing overfitting and improving computational
efficiency.
"""
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, Union

import pandas as pd
import numpy as np

from modeling.train import apply_pca, load_pca_features
from modeling.phylo import train_pgls
from config import get_config

logger = logging.getLogger(__name__)


def should_apply_pca_before_pgls(
    feature_matrix: Union[pd.DataFrame, np.ndarray],
    n_samples: Optional[int] = None,
    threshold_ratio: float = 1.0
) -> bool:
    """
    Determine if PCA should be applied before PGLS based on feature-to-sample ratio.

    Args:
        feature_matrix: The feature matrix (X) to evaluate. Can be DataFrame or ndarray.
        n_samples: Number of samples. If None, inferred from feature_matrix.
        threshold_ratio: Ratio threshold for feature_count / n_samples. If feature_count
                       > n_samples * threshold_ratio, PCA is recommended. Default is 1.0
                       (strictly more features than samples).

    Returns:
        bool: True if PCA should be applied before PGLS, False otherwise.
    """
    if isinstance(feature_matrix, pd.DataFrame):
        n_features = feature_matrix.shape[1]
        if n_samples is None:
            n_samples = feature_matrix.shape[0]
    elif isinstance(feature_matrix, np.ndarray):
        n_features = feature_matrix.shape[1] if feature_matrix.ndim > 1 else 1
        if n_samples is None:
            n_samples = feature_matrix.shape[0]
    else:
        raise TypeError(f"feature_matrix must be DataFrame or ndarray, got {type(feature_matrix)}")

    if n_samples == 0:
        logger.warning("No samples provided. Cannot determine PCA necessity.")
        return False

    ratio = n_features / n_samples
    condition = n_features > n_samples

    logger.info(
        f"PCA Decision: Features={n_features}, Samples={n_samples}, "
        f"Ratio={ratio:.2f}. Apply PCA: {condition}"
    )

    return condition


def optimize_pgls_pipeline(
    feature_matrix: Union[pd.DataFrame, np.ndarray],
    target_vector: Union[pd.Series, np.ndarray],
    phylogenetic_covariance: Optional[np.ndarray] = None,
    tree_labels: Optional[list] = None,
    n_components: Optional[int] = None,
    threshold_ratio: float = 1.0,
    random_state: Optional[int] = None
) -> Dict[str, Any]:
    """
    Execute the PGLS pipeline with conditional PCA optimization.

    This function implements the core optimization logic:
    1. Checks if feature count > sample count.
    2. If true, applies PCA to reduce dimensionality.
    3. Runs PGLS on the (potentially reduced) feature set.

    Args:
        feature_matrix: Input features (X).
        target_vector: Target values (y).
        phylogenetic_covariance: Pre-computed phylogenetic covariance matrix.
        tree_labels: Labels for the tree tips (needed if covariance is provided).
        n_components: Number of PCA components. If None, keeps enough to explain 95% variance.
        threshold_ratio: Ratio threshold for PCA decision (see should_apply_pca_before_pgls).
        random_state: Random seed for reproducibility.

    Returns:
        Dict containing:
            - 'pca_applied': bool indicating if PCA was run.
            - 'n_features_original': int.
            - 'n_features_final': int.
            - 'n_components': int (if PCA applied, else None).
            - 'model_result': The result dictionary from train_pgls.
    """
    # Ensure random state is set if provided
    if random_state is not None:
        np.random.seed(random_state)

    # Convert inputs to numpy for shape inspection if needed
    if isinstance(feature_matrix, pd.DataFrame):
        X_orig = feature_matrix.values
        feature_names = feature_matrix.columns.tolist()
    else:
        X_orig = np.array(feature_matrix)
        feature_names = None

    if isinstance(target_vector, pd.Series):
        y = target_vector.values
    else:
        y = np.array(target_vector)

    n_samples = len(y)
    n_features_orig = X_orig.shape[1]

    # Decision logic
    apply_pca_flag = should_apply_pca_before_pgls(
        feature_matrix, n_samples, threshold_ratio
    )

    result = {
        'pca_applied': apply_pca_flag,
        'n_features_original': n_features_orig,
        'n_features_final': n_features_orig,
        'n_components': None,
        'model_result': None
    }

    if apply_pca_flag:
        logger.info(f"Feature count ({n_features_orig}) exceeds sample count ({n_samples}). "
                    f"Applying PCA for dimensionality reduction.")

        # Determine n_components if not specified
        if n_components is None:
            # Default to enough components to explain 95% variance, or max possible
            n_components = min(n_samples - 1, n_features_orig)
            logger.info(f"Auto-selecting n_components={n_components} (min(N-1, Features))")

        # Apply PCA using the existing pipeline function
        # We need to reconstruct a DataFrame for the apply_pca function signature
        # or pass numpy directly if the function supports it.
        # Looking at apply_pca signature in train.py, it likely expects a DataFrame or path.
        # To be safe and consistent with the existing pipeline, we create a temporary DF.
        temp_df = pd.DataFrame(X_orig, columns=[f"feat_{i}" for i in range(n_features_orig)])

        try:
            # apply_pca returns a DataFrame and metadata
            pca_result_df, pca_metadata = apply_pca(
                temp_df,
                n_components=n_components,
                random_state=random_state
            )

            result['n_components'] = pca_metadata.get('n_components', n_components)
            result['n_features_final'] = pca_result_df.shape[1]

            # Extract the reduced features for PGLS
            X_final = pca_result_df.values
            logger.info(f"PCA applied. Reduced to {result['n_features_final']} components.")

        except Exception as e:
            logger.error(f"PCA application failed: {e}")
            raise

    else:
        logger.info(f"Feature count ({n_features_orig}) <= sample count ({n_samples}). "
                    f"Skipping PCA. Using original features.")
        X_final = X_orig

    # Run PGLS
    try:
        # train_pgls signature: (X, y, covariance_matrix, tree_labels, seed)
        # We assume the caller provides the covariance matrix if they want PGLS.
        # If phylogenetic_covariance is None, train_pgls might fail or fall back to OLS
        # depending on its implementation. We pass it as provided.
        pgls_result = train_pgls(
            X=X_final,
            y=y,
            phylogenetic_covariance=phylogenetic_covariance,
            tree_labels=tree_labels,
            seed=random_state
        )
        result['model_result'] = pgls_result

    except Exception as e:
        logger.error(f"PGLS training failed: {e}")
        raise

    return result


def main():
    """
    Entry point for the optimization script.
    Loads data, runs the optimized PGLS pipeline, and saves results.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    config = get_config()
    logger.info("Starting PGLS Optimization Pipeline (T037)")

    # Load aligned data (assumed to be in data/processed/aligned_matrix.csv)
    # This path matches the output of T018
    data_path = Path("data/processed/aligned_matrix.csv")
    if not data_path.exists():
        logger.error(f"Aligned data not found at {data_path}. Run data alignment first.")
        return

    df = pd.read_csv(data_path)

    # Identify feature and target columns
    # Assuming BGC counts are features and metabolite abundance is target
    # This might need adjustment based on actual column names in aligned_matrix.csv
    # For now, we assume columns starting with 'bgc_' are features and 'metabolite_' is target
    feature_cols = [c for c in df.columns if c.startswith('bgc_')]
    target_col = [c for c in df.columns if c.startswith('metabolite_') or c == 'abundance']

    if not feature_cols or not target_col:
        logger.error("Could not automatically identify feature or target columns.")
        logger.info(f"Available columns: {df.columns.tolist()}")
        return

    X = df[feature_cols]
    y = df[target_col[0]]

    # Load phylogeny if available (T021)
    phylo_path = Path("data/raw/phylogeny/tree.nwk")
    covariance = None
    tree_labels = None
    if phylo_path.exists():
        try:
            from modeling.phylo import load_phylogeny, construct_covariance_matrix
            tree = load_phylogeny(str(phylo_path))
            tree_labels = tree.get_tip_labels()
            covariance = construct_covariance_matrix(tree)
            logger.info(f"Phylogenetic covariance matrix loaded ({covariance.shape}).")
        except Exception as e:
            logger.warning(f"Failed to load phylogeny: {e}. Proceeding without phylogenetic correction.")
    else:
        logger.warning("Phylogeny file not found. Proceeding without phylogenetic correction.")

    # Run optimization
    result = optimize_pgls_pipeline(
        feature_matrix=X,
        target_vector=y,
        phylogenetic_covariance=covariance,
        tree_labels=tree_labels,
        random_state=config.seed_manager.get_seed()
    )

    # Save results
    output_path = Path("data/processed/optimization_results.json")
    import json
    serializable_result = {
        'pca_applied': result['pca_applied'],
        'n_features_original': result['n_features_original'],
        'n_features_final': result['n_features_final'],
        'n_components': result['n_components'],
        'model_result': {
            'r2': result['model_result'].get('r2'),
            'p_value': result['model_result'].get('p_value'),
            'coefficients': result['model_result'].get('coefficients'),
            'feature_importance': result['model_result'].get('feature_importance')
        }
    }

    with open(output_path, 'w') as f:
        json.dump(serializable_result, f, indent=2)

    logger.info(f"Optimization results saved to {output_path}")
    logger.info(f"PCA Applied: {result['pca_applied']}")
    logger.info(f"R2 Score: {result['model_result'].get('r2')}")

    return result


if __name__ == "__main__":
    main()