import numpy as np
import pandas as pd
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from sklearn.decomposition import PCA
from statsmodels.stats.outliers_influence import variance_inflation_factor

logger = logging.getLogger(__name__)

def calculate_vif(df: pd.DataFrame, feature_names: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each predictor.

    Args:
        df: DataFrame containing the predictor variables.
        feature_names: List of column names to calculate VIF for.

    Returns:
        Dictionary mapping feature names to their VIF values.
    """
    if len(feature_names) < 2:
        logger.warning("Need at least 2 features to calculate VIF.")
        return {name: 0.0 for name in feature_names}

    X = df[feature_names].values
    
    # Add constant for intercept (statsmodels VIF requires it)
    try:
        from statsmodels.tools import add_constant
        X_with_const = add_constant(X)
    except ImportError:
        # Fallback if statsmodels.tools not available (though it should be)
        X_with_const = np.hstack([np.ones((X.shape[0], 1)), X])

    vif_data = []
    for i in range(len(feature_names)):
        try:
            # Calculate VIF for the i-th feature
            vif = variance_inflation_factor(X_with_const, i+1) # +1 because col 0 is constant
            vif_data.append((feature_names[i], vif))
            logger.debug(f"VIF for {feature_names[i]}: {vif:.4f}")
        except Exception as e:
            logger.error(f"Error calculating VIF for {feature_names[i]}: {e}")
            vif_data.append((feature_names[i], float('inf')))

    return {name: val for name, val in vif_data}

def run_pca_on_metrics(df: pd.DataFrame, feature_names: List[str], min_variance: float = 0.60) -> Dict[str, Any]:
    """
    Perform PCA on graph metrics to handle multicollinearity.

    Args:
        df: DataFrame containing the predictor variables.
        feature_names: List of column names to include in PCA.
        min_variance: Minimum cumulative variance explained required (default 0.60).

    Returns:
        Dictionary containing PCA results (eigenvalues, variance explained, components).
        Returns None if criteria are not met or if matrix is singular.
    """
    logger.info(f"Running PCA on features: {feature_names} with min variance {min_variance}")
    
    X = df[feature_names].values

    # Check for singular matrix / rank deficiency
    if np.linalg.rank(X) < X.shape[1]:
        logger.warning("Matrix is rank deficient. PCA may fail.")
        # Try PCA anyway, it might handle it, but expect potential issues
        pass

    try:
        pca = PCA()
        pca_transformed = pca.fit_transform(X)
        
        eigenvalues = pca.eigenvals_ if hasattr(pca, 'eigenvals_') else pca.singular_values_**2
        # statsmodels/numpy PCA usually provides explained_variance_ratio_
        explained_variance_ratio = pca.explained_variance_ratio_
        cumulative_variance = np.cumsum(explained_variance_ratio)
        
        logger.info(f"PCA eigenvalues: {pca.eexplained_variance_}")
        logger.info(f"Cumulative variance explained: {cumulative_variance[-1]:.4f}")

        if cumulative_variance[-1] < min_variance:
            logger.warning(f"Cumulative variance ({cumulative_variance[-1]:.4f}) < {min_variance}. PCA criteria not met.")
            return None

        # Check for positive eigenvalues (strictly speaking, PCA handles semi-definite, but spec asks for > 0)
        # Note: singular_values are always non-negative. If any are 0, it's rank deficient.
        if np.any(pca.singular_values_ == 0):
            logger.warning("PCA resulted in zero singular values (rank deficiency).")
            # Depending on strictness, we might return None here. 
            # Spec says "eigenvalues > 0". If singular values are 0, eigenvalues are 0.
            # Let's be strict: if any are 0, it's not strictly > 0.
            return None

        result = {
            "eigenvalues": pca.explained_variance_.tolist(),
            "explained_variance_ratio": explained_variance_ratio.tolist(),
            "cumulative_variance_explained": cumulative_variance.tolist(),
            "components": pca.components_.tolist(),
            "n_components_used": len(cumulative_variance),
            "success": True
        }
        logger.info("PCA successful. Criteria met.")
        return result

    except np.linalg.LinAlgError as e:
        logger.error(f"PCA failed due to linear algebra error (singular matrix): {e}")
        return None
    except Exception as e:
        logger.error(f"PCA failed with unexpected error: {e}")
        return None

def generate_descriptive_vif_report(df: pd.DataFrame, feature_names: List[str], output_path: Path):
    """
    Generate a descriptive report of VIF and correlations when PCA fails.
    
    Args:
        df: DataFrame with data.
        feature_names: List of feature names.
        output_path: Path to save the JSON report.
    """
    logger.info(f"Generating descriptive VIF report to {output_path}")
    
    vif_results = calculate_vif(df, feature_names)
    correlation_matrix = df[feature_names].corr()
    
    # Variance decomposition (simplified: proportion of variance due to each predictor's VIF)
    # A common heuristic: weight = (VIF_i - 1) / sum(VIF_j - 1)
    vif_values = list(vif_results.values())
    if sum(vif_values) > len(vif_values): # If there is any inflation
        weights = [(v - 1) / sum(v - 1 for v in vif_values) for v in vif_values]
    else:
        weights = [1.0 / len(vif_values)] * len(vif_values)

    report = {
        "status": "PCA_failed_or_criteria_not_met",
        "reason": "VIF > 5 detected, but PCA failed to meet eigenvalue > 0 or cumulative variance > 60% criteria.",
        "vif_values": vif_results,
        "correlation_matrix": correlation_matrix.round(4).to_dict(),
        "variance_decomposition": dict(zip(feature_names, [round(w, 4) for w in weights])),
        "recommendation": "Use descriptive statistics or drop highly collinear variables manually."
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Descriptive VIF report saved to {output_path}")

def check_and_handle_collinearity(
    df: pd.DataFrame, 
    feature_names: List[str], 
    vif_threshold: float = 5.0,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Main entry point to check VIF and attempt PCA if necessary.
    
    Args:
        df: DataFrame containing the data.
        feature_names: List of predictor column names.
        vif_threshold: Threshold for VIF to trigger PCA.
        output_dir: Directory to save output files. Defaults to 'data/results'.

    Returns:
        Dictionary indicating success/failure and paths to artifacts.
    """
    if output_dir is None:
        output_dir = Path("data/results")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    pca_output_path = output_dir / "pca_metrics.json"
    vif_report_path = output_dir / "descriptive_vif_report.json"

    logger.info(f"Checking multicollinearity for features: {feature_names}")
    
    vif_results = calculate_vif(df, feature_names)
    max_vif = max(vif_results.values())
    
    logger.info(f"Maximum VIF detected: {max_vif:.4f}")

    if max_vif <= vif_threshold:
        logger.info(f"All VIFs <= {vif_threshold}. No action needed.")
        return {
            "status": "no_collinearity",
            "max_vif": max_vif,
            "action_taken": "none"
        }

    logger.warning(f"Max VIF ({max_vif:.4f}) > {vif_threshold}. Attempting PCA.")
    
    pca_result = run_pca_on_metrics(df, feature_names)

    if pca_result is not None:
        # PCA Success
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(pca_output_path, 'w') as f:
            json.dump(pca_result, f, indent=2)
        logger.info(f"PCA successful. Results saved to {pca_output_path}")
        return {
            "status": "pca_success",
            "max_vif": max_vif,
            "action_taken": "pca",
            "output_file": str(pca_output_path),
            "pca_results": pca_result
        }
    else:
        # PCA Failed
        logger.warning("PCA failed or did not meet criteria. Generating descriptive report.")
        generate_descriptive_vif_report(df, feature_names, vif_report_path)
        return {
            "status": "pca_failed",
            "max_vif": max_vif,
            "action_taken": "descriptive_report",
            "output_file": str(vif_report_path)
        }

def main():
    """
    Main function to demonstrate the collinearity check.
    Expects data to be available or uses synthetic data for demonstration if in validation mode.
    """
    from config import is_methodology_validation_mode, set_synthetic_mode
    from synthetic_data import generate_dataset
    
    logging.basicConfig(level=logging.INFO)
    
    # Check if we are in methodology validation mode
    if is_methodology_validation_mode():
        logger.info("Running in Methodology Validation Mode. Generating synthetic data.")
        # Generate synthetic data for testing the pipeline logic
        df = generate_dataset(n_subjects=30, n_timepoints=2)
        feature_names = ['global_efficiency', 'local_efficiency', 'modularity']
    else:
        # In a real run, this would load from the preprocessed data file
        # For now, if not synthetic and no real data path provided, we might fail or assume data exists
        # The task implies this runs as part of the pipeline. 
        # We will attempt to load from a standard location if it exists, else error.
        data_path = Path("data/processed/metrics.csv")
        if not data_path.exists():
            logger.error("Real data file 'data/processed/metrics.csv' not found and not in synthetic mode.")
            # Create a dummy failure or exit? The spec says fail loudly if no real source.
            # But for the script to run in CI, we might need to handle the missing file gracefully 
            # if it's expected to be generated by T019/T020.
            # Let's assume the pipeline order: T019/T020 -> T021 -> T022a.
            # If this is run standalone without previous steps, it should error.
            raise FileNotFoundError(f"Expected data file {data_path} not found.")
        
        df = pd.read_csv(data_path)
        # Assume columns exist based on T019/T020 output
        feature_names = ['global_efficiency', 'local_efficiency', 'modularity']
        # Filter out any rows with NaN in these columns
        df = df.dropna(subset=feature_names)

    result = check_and_handle_collinearity(df, feature_names)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()