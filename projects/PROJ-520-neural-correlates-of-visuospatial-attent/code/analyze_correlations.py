import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import hashlib

# Configure logging
logger = logging.getLogger(__name__)

def load_feature_matrix(path: str) -> pd.DataFrame:
    """Load the feature matrix from CSV."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Feature matrix not found at {path}")
    return pd.read_csv(path)

def compute_correlation_matrix(features: pd.DataFrame) -> np.ndarray:
    """Compute the correlation matrix for all features."""
    # Drop non-numeric columns if any (e.g., condition labels)
    numeric_features = features.select_dtypes(include=[np.number])
    if numeric_features.empty:
        raise ValueError("No numeric features found in the matrix.")
    return numeric_features.corr().values

def compute_variance_inflation_factors(features: pd.DataFrame) -> Dict[str, float]:
    """
    Compute Variance Inflation Factors (VIF) for each feature.
    VIF = 1 / (1 - R^2) where R^2 is from regressing the feature against all others.
    """
    numeric_features = features.select_dtypes(include=[np.number])
    if numeric_features.empty:
        return {}

    vif_data = {}
    # Add a small constant to avoid singular matrix issues if needed, though correlation handles it usually
    # We use the correlation matrix approach for VIF: VIF_i = 1 / (1 - R_i^2)
    # R_i^2 is the R-squared of regressing feature i on all other features.
    # Using the inverse of the correlation matrix: VIF_i = C_ii where C is the inverse correlation matrix.
    
    corr_matrix = numeric_features.corr()
    
    # Check for perfect collinearity (correlation of 1 or -1) which makes matrix singular
    # We'll handle this by adding a tiny epsilon if necessary, but standard VIF calculation
    # usually assumes full rank.
    try:
        corr_inv = np.linalg.inv(corr_matrix.values)
    except np.linalg.LinAlgError:
        logger.warning("Correlation matrix is singular. VIF calculation may be unstable.")
        # Fallback: return high VIF for correlated features or handle gracefully
        # For this implementation, we'll try to return a dictionary indicating failure or high VIF
        # But strictly, we should fail or warn. Let's try to compute via regression if inverse fails?
        # No, inverse of correlation matrix is the standard way.
        # If singular, it means perfect collinearity.
        # We will return a dict with 'error' or similar if we can't compute.
        # However, for the purpose of this task, let's assume we can compute it or handle the exception.
        # We'll raise a specific error or return a placeholder.
        # Let's just log and return a dict with high values or error.
        # Actually, let's try to use the pseudo-inverse or handle the error.
        # But the task asks to document the structure.
        # Let's just raise if it's truly singular, as that's a critical finding.
        raise RuntimeError("Correlation matrix is singular. Perfect collinearity detected.")

    for col in numeric_features.columns:
        idx = list(numeric_features.columns).index(col)
        vif = corr_inv[idx, idx]
        vif_data[col] = float(vif)

    return vif_data

def compute_feature_stats(features: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """Compute basic statistics (mean, std, min, max) for each feature."""
    numeric_features = features.select_dtypes(include=[np.number])
    stats = {}
    for col in numeric_features.columns:
        stats[col] = {
            "mean": float(numeric_features[col].mean()),
            "std": float(numeric_features[col].std()),
            "min": float(numeric_features[col].min()),
            "max": float(numeric_features[col].max())
        }
    return stats

def run_correlation_analysis(features_path: str, output_path: str) -> Dict[str, Any]:
    """
    Run the full correlation analysis pipeline.
    1. Load features.
    2. Compute correlation matrix.
    3. Compute VIF.
    4. Compute basic stats.
    5. Save results to JSON with checksum.
    """
    logger.info(f"Loading feature matrix from {features_path}")
    df = load_feature_matrix(features_path)

    logger.info("Computing correlation matrix")
    corr_matrix = compute_correlation_matrix(df)

    logger.info("Computing Variance Inflation Factors (VIF)")
    vif_data = compute_variance_inflation_factors(df)

    logger.info("Computing feature statistics")
    feature_stats = compute_feature_stats(df)

    # Prepare the metadata structure
    metadata = {
        "source_file": features_path,
        "n_features": len(df.columns),
        "n_samples": len(df),
        "correlation_matrix": corr_matrix.tolist(),
        "vif": vif_data,
        "feature_stats": feature_stats,
        "collinearity_notes": []
    }

    # Add notes based on VIF
    for feature, vif in vif_data.items():
        if vif > 5:
            metadata["collinearity_notes"].append(f"High VIF ({vif:.2f}) detected for {feature}")
        if vif > 10:
            metadata["collinearity_notes"].append(f"Severe collinearity (VIF > 10) for {feature}")

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Write JSON
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    # Compute checksum
    with open(output_path, 'rb') as f:
        checksum = hashlib.sha256(f.read()).hexdigest()

    # Update metadata with checksum and save again? Or just return it?
    # The task says "Ensure file is checksummed". Usually means the file content is hashed.
    # We can append the checksum to the JSON or store it separately.
    # Let's append it to the JSON file for self-containment.
    metadata["checksum_sha256"] = checksum
    
    # Re-write with checksum
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Correlation analysis saved to {output_path} with checksum {checksum}")
    return metadata

def main():
    """Entry point for the script."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Default paths relative to project root
    # Assuming this script is run from project root or code/
    # We need to determine the base path.
    # Let's assume the script is in code/ and we need to go up to project root.
    base_dir = Path(__file__).parent.parent
    features_path = base_dir / "data" / "processed" / "features_matrix.csv"
    output_path = base_dir / "data" / "processed" / "feature_metadata.json"

    if not features_path.exists():
        logger.error(f"Input file not found: {features_path}")
        sys.exit(1)

    try:
        run_correlation_analysis(str(features_path), str(output_path))
        logger.info("Analysis completed successfully.")
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
