import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import pandas as pd
import numpy as np
from scipy import stats

# --- Logging Configuration ---
def setup_logging():
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

logger = setup_logging()

# --- Helper Functions ---

def get_project_root() -> Path:
    """Returns the project root directory."""
    return Path(__file__).resolve().parent.parent

def load_descriptors() -> pd.DataFrame:
    """Loads the processed descriptors CSV."""
    root = get_project_root()
    path = root / "data" / "processed" / "descriptors.csv"
    if not path.exists():
        raise FileNotFoundError(f"Descriptors file not found at {path}")
    return pd.read_csv(path)

def load_cleaned_data() -> pd.DataFrame:
    """Loads the cleaned metallic glass data."""
    root = get_project_root()
    path = root / "data" / "processed" / "cleaned_mg.csv"
    if not path.exists():
        raise FileNotFoundError(f"Cleaned data file not found at {path}")
    return pd.read_csv(path)

def load_model() -> Any:
    """Loads the trained model artifact."""
    root = get_project_root()
    path = root / "artifacts" / "models" / "best_model.pkl"
    if not path.exists():
        raise FileNotFoundError(f"Model file not found at {path}")
    with open(path, 'rb') as f:
        import pickle
        return pickle.load(f)

def calculate_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates Pearson and Spearman correlation coefficients and p-values
    for numeric columns in the dataframe.
    """
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.empty:
        raise ValueError("No numeric columns found in dataframe for correlation.")

    features = numeric_df.columns.tolist()
    results = []

    for i, feat1 in enumerate(features):
        for j, feat2 in enumerate(features):
            if i > j:  # Only upper triangle + diagonal
                continue

            # Pearson
            pearson_r, pearson_p = stats.pearsonr(numeric_df[feat1], numeric_df[feat2])
            # Spearman
            spearman_r, spearman_p = stats.spearmanr(numeric_df[feat1], numeric_df[feat2])

            results.append({
                'feature_pair': f"{feat1}_vs_{feat2}",
                'feature_1': feat1,
                'feature_2': feat2,
                'pearson_coeff': pearson_r,
                'pearson_pvalue': pearson_p,
                'spearman_coeff': spearman_r,
                'spearman_pvalue': spearman_p
            })

    return pd.DataFrame(results)

def calculate_p_values(correlation_df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts p-values from the correlation dataframe for FDR correction.
    Returns a dataframe with feature pairs and their raw p-values.
    """
    # We will correct both Pearson and Spearman p-values, or just one?
    # Usually, we focus on one metric for significance. Let's correct Pearson p-values
    # as they are standard for linear association.
    if 'pearson_pvalue' not in correlation_df.columns:
        raise ValueError("Pearson p-values not found in correlation dataframe.")

    # Flatten to a simple list for correction
    p_values = correlation_df['pearson_pvalue'].values
    feature_pairs = correlation_df['feature_pair'].values

    return pd.DataFrame({
        'feature_pair': feature_pairs,
        'raw_pvalue': p_values
    })

def benjamini_hochberg_fdr(p_values: np.ndarray, alpha: float = 0.05) -> Tuple[np.ndarray, np.ndarray]:
    """
    Performs the Benjamini-Hochberg FDR correction on an array of p-values.
    
    Args:
        p_values: Array of raw p-values.
        alpha: Significance level (default 0.05).
        
    Returns:
        Tuple of (corrected_pvalues, boolean_mask_rejected)
    """
    if len(p_values) == 0:
        return np.array([]), np.array([])

    # Sort p-values
    sorted_indices = np.argsort(p_values)
    sorted_pvalues = p_values[sorted_indices]
    n = len(sorted_pvalues)

    # Calculate BH critical values
    # Rank (1-based)
    ranks = np.arange(1, n + 1)
    # BH threshold: (i / m) * alpha
    # We want to find the largest k such that p_(k) <= (k/m)*alpha
    # But for the standard output (adjusted p-values), we use the formula:
    # p_adj(i) = min(1, min_{j>=i} (m/j * p_(j)))
    
    # Step 1: Multiply sorted p-values by n/rank
    adjusted = sorted_pvalues * n / ranks
    
    # Step 2: Ensure monotonicity (cumulative min from the end)
    # We iterate backwards to ensure p_adj(i) <= p_adj(i+1)
    for i in range(n - 2, -1, -1):
        adjusted[i] = min(adjusted[i], adjusted[i+1])
    
    # Step 3: Cap at 1.0
    adjusted = np.minimum(adjusted, 1.0)
    
    # Restore original order
    corrected_pvalues = np.zeros(n)
    corrected_pvalues[sorted_indices] = adjusted

    # Determine rejection mask (True if corrected p <= alpha)
    rejected = corrected_pvalues <= alpha

    return corrected_pvalues, rejected

def save_correlation_matrix(correlation_df: pd.DataFrame, output_path: Path):
    """Saves the correlation matrix to a CSV file."""
    correlation_df.to_csv(output_path, index=False)
    logger.info(f"Saved correlation matrix to {output_path}")

def verify_correlation_matrix(path: Path):
    """Verifies that the correlation matrix file exists and is non-empty."""
    if not path.exists():
        raise FileNotFoundError(f"Correlation matrix not found at {path}")
    df = pd.read_csv(path)
    if df.empty:
        raise ValueError("Correlation matrix is empty.")
    required_cols = ['feature_pair', 'pearson_coeff', 'pearson_pvalue', 'spearman_coeff', 'spearman_pvalue']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Correlation matrix missing required columns. Found: {df.columns.tolist()}")
    logger.info("Correlation matrix verification passed.")

def calculate_vif(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates Variance Inflation Factor (VIF) for each feature.
    Flags features with VIF > 5.
    """
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    numeric_df = df.select_dtypes(include=[np.number])
    # Add constant for intercept
    X = numeric_df.values
    # Check for constant columns (VIF undefined)
    if np.any(np.ptp(X, axis=0) == 0):
        logger.warning("Constant columns detected. VIF calculation may be unstable.")
    
    vif_data = []
    feature_names = numeric_df.columns.tolist()
    
    for i, name in enumerate(feature_names):
        try:
            vif = variance_inflation_factor(X, i)
            vif_data.append({"feature": name, "vif": vif})
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {name}: {e}")
            vif_data.append({"feature": name, "vif": float('inf')})
    
    return pd.DataFrame(vif_data)

def save_vif_diagnostic_log(vif_df: pd.DataFrame, output_path: Path):
    """Saves the VIF diagnostic log to a JSON file."""
    flagged = vif_df[vif_df['vif'] > 5]['feature'].tolist()
    vif_values = dict(zip(vif_df['feature'], vif_df['vif'].astype(float)))
    
    log_data = {
        "flagged_features": flagged,
        "vif_values": vif_values
    }
    
    with open(output_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    logger.info(f"Saved VIF diagnostic log to {output_path}")

def calculate_condition_number(df: pd.DataFrame) -> float:
    """Calculates the condition number of the design matrix."""
    numeric_df = df.select_dtypes(include=[np.number])
    X = numeric_df.values
    # Add constant column if not present
    if not np.allclose(X[:, 0], 1):
        X = np.hstack([np.ones((X.shape[0], 1)), X])
    
    try:
        # Use SVD to calculate condition number
        u, s, vh = np.linalg.svd(X, full_matrices=False)
        cond_num = s[0] / s[-1]
        return cond_num
    except Exception as e:
        logger.error(f"Failed to calculate condition number: {e}")
        return float('inf')

def log_collinearity_analysis(cond_num: float, output_path: Path):
    """Logs the collinearity condition number analysis."""
    status = "warning" if cond_num > 30 else "ok"
    log_data = {
        "condition_number": cond_num,
        "status": status
    }
    with open(output_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    logger.info(f"Collinearity analysis: Condition Number = {cond_num:.2f}, Status = {status}")

def sweep_max_depth(model_path: Path, data_path: Path, max_depths: List[int] = [3, 5, 7]) -> Dict:
    """
    Sweeps max_depth parameter for sensitivity analysis.
    Re-trains the model with different max_depths and collects R2 scores.
    """
    # This is a placeholder for the actual implementation which would re-train
    # For now, we assume the task is to implement the FDR correction, 
    # so this function is kept minimal to satisfy the API surface if called.
    # In a full implementation, this would load data, train, and return scores.
    logger.info(f"Sweeping max_depth over {max_depths}...")
    # Mock return for API compatibility if not fully implemented in this task
    return {"max_depth_sweep": [], "r2_variance": 0.0}

def main():
    """
    Main execution flow for T034: Benjamini-Hochberg FDR Correction.
    1. Load correlation matrix (from T033a).
    2. Extract p-values.
    3. Apply Benjamini-Hochberg procedure.
    4. Save corrected p-values to data/processed/fdr_corrected_pvalues.json.
    """
    root = get_project_root()
    corr_path = root / "data" / "processed" / "correlation_matrix.csv"
    output_path = root / "data" / "processed" / "fdr_corrected_pvalues.json"
    
    logger.info("Starting T034: Benjamini-Hochberg FDR Correction")
    
    # 1. Load Correlation Matrix
    if not corr_path.exists():
        # Try to generate it if missing (dependency T033a)
        logger.warning("Correlation matrix not found. Attempting to generate from descriptors...")
        try:
            df = load_descriptors()
            corr_df = calculate_correlation_matrix(df)
            save_correlation_matrix(corr_df, corr_path)
        except Exception as e:
            logger.error(f"Failed to generate or load correlation matrix: {e}")
            sys.exit(1)
    
    corr_df = pd.read_csv(corr_path)
    logger.info(f"Loaded correlation matrix with {len(corr_df)} pairs.")
    
    # 2. Extract P-values
    p_df = calculate_p_values(corr_df)
    raw_pvalues = p_df['raw_pvalue'].values
    feature_pairs = p_df['feature_pair'].values
    
    # 3. Apply FDR Correction
    logger.info("Applying Benjamini-Hochberg FDR correction (alpha=0.05)...")
    corrected_pvalues, rejected = benjamini_hochberg_fdr(raw_pvalues, alpha=0.05)
    
    # 4. Prepare Output
    # The schema requires the corrected p-values. We'll structure it clearly.
    fdr_results = []
    for i, pair in enumerate(feature_pairs):
        fdr_results.append({
            "feature_pair": pair,
            "raw_pvalue": float(raw_pvalues[i]),
            "corrected_pvalue": float(corrected_pvalues[i]),
            "is_significant": bool(rejected[i])
        })
    
    output_data = {
        "alpha": 0.05,
        "method": "Benjamini-Hochberg",
        "correction_results": fdr_results
    }
    
    # 5. Save Output
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Successfully saved FDR corrected p-values to {output_path}")
    logger.info(f"Number of significant pairs after correction: {sum(rejected)}")

if __name__ == "__main__":
    main()