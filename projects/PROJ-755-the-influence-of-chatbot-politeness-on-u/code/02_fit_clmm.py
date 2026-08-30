"""
T026 Implementation: VIF check for politeness and conversation_length.
Loads scored_dialogues.parquet, calculates VIF, logs warnings, and drops
variables with VIF >= 5.
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Ensure we can import utils
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def ensure_directories(output_dir: Path) -> None:
    """Ensure output directories exist."""
    output_dir.mkdir(parents=True, exist_ok=True)

def load_scored_dialogues(input_path: Path) -> pd.DataFrame:
    """Load the scored dialogues dataset."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    logger.info(f"Loading data from {input_path}...")
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")
    return df

def calculate_vif(df: pd.DataFrame, features: List[str]) -> pd.Series:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.
    Returns a Series indexed by feature name.
    """
    # Add a constant for the intercept if statsmodels requires it,
    # though VIF is typically calculated on the design matrix excluding intercept.
    # We pass the dataframe slice directly.
    X = df[features].copy()
    
    # Handle NaNs in features for VIF calculation
    # VIF calculation requires no NaNs. We drop rows with NaNs in these specific columns for the calculation.
    X_clean = X.dropna()
    
    if X_clean.empty:
        logger.warning("No valid rows found for VIF calculation after dropping NaNs.")
        return pd.Series(index=features, dtype=float)

    # Add constant for intercept (statsmodels VIF expects this in the matrix usually, 
    # but variance_inflation_factor calculates VIF for each column in X)
    # The standard formula VIF_j = 1 / (1 - R_j^2) where R_j^2 is from regressing X_j on all other X's.
    # statsmodels implementation handles the matrix internally.
    
    vif_data = pd.Series(
        [variance_inflation_factor(X_clean.values, i) for i in range(len(features))],
        index=features
    )
    return vif_data

def check_collinearity(
    df: pd.DataFrame, 
    features: List[str], 
    threshold: float = 5.0
) -> Tuple[List[str], pd.Series]:
    """
    Check for multicollinearity using VIF.
    Logs warnings for features with VIF >= threshold.
    Returns a tuple of (features_to_drop, vif_series).
    """
    vif_series = calculate_vif(df, features)
    
    logger.info("Variance Inflation Factor (VIF) Results:")
    for feat, vif in vif_series.items():
        logger.info(f"  {feat}: VIF = {vif:.4f}")
    
    features_to_drop = []
    for feat, vif in vif_series.items():
        if vif >= threshold:
            logger.warning(
                f"High collinearity detected: '{feat}' has VIF = {vif:.4f} "
                f"(threshold = {threshold}). Dropping this variable."
            )
            features_to_drop.append(feat)
        elif vif > 2.5:
            logger.info(
                f"Moderate collinearity warning: '{feat}' has VIF = {vif:.4f}."
            )
    
    return features_to_drop, vif_series

def fit_clmm(df: pd.DataFrame, features: List[str]) -> None:
    """
    Placeholder for CLMM fitting logic.
    In T027, this will use rpy2 to fit the model.
    For T026, we ensure the data preparation and VIF check are done.
    """
    if not features:
        logger.warning("No features remaining for CLMM after VIF check.")
        return
    
    logger.info(f"Fitting CLMM with features: {features}")
    # Actual fitting logic is in T027
    pass

def save_convergence_report(output_path: Path, vif_results: Dict[str, Any]) -> None:
    """Save VIF and collinearity check results."""
    import json
    with open(output_path, 'w') as f:
        json.dump(vif_results, f, indent=2)
    logger.info(f"Saved VIF report to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="T026: VIF Check and Collinearity Handling")
    parser.add_argument(
        "--input", 
        type=Path, 
        default=Path("data/processed/scored_dialogues.parquet"),
        help="Path to scored_dialogues.parquet"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed"),
        help="Directory to save reports"
    )
    parser.add_argument(
        "--vif-threshold",
        type=float,
        default=5.0,
        help="VIF threshold for dropping variables"
    )
    args = parser.parse_args()

    ensure_directories(args.output_dir)

    # Load data
    df = load_scored_dialogues(args.input)

    # Identify target features for CLMM
    # Based on T027 formula: quality_rating ~ politeness + conversation_length
    target_features = ["politeness", "conversation_length"]
    
    # Check if columns exist
    missing_cols = [c for c in target_features if c not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns for VIF check: {missing_cols}")
        sys.exit(1)

    # Perform VIF check
    dropped_features, vif_series = check_collinearity(
        df, target_features, threshold=args.vif_threshold
    )

    # Determine final features
    final_features = [f for f in target_features if f not in dropped_features]
    
    logger.info(f"Features to be used in CLMM: {final_features}")
    logger.info(f"Features dropped due to high VIF: {dropped_features}")

    # Prepare results for saving
    vif_results = {
        "vif_scores": vif_series.to_dict(),
        "threshold": args.vif_threshold,
        "dropped_features": dropped_features,
        "retained_features": final_features
    }

    # Save report
    report_path = args.output_dir / "vif_check_report.json"
    save_convergence_report(report_path, vif_results)

    # Pass final features to the next stage (conceptually)
    # In a real pipeline, we might write a new dataframe or config file
    # For now, we log the outcome which is sufficient for T026
    logger.info("T026 VIF check completed successfully.")

if __name__ == "__main__":
    main()