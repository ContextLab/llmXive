"""
Collinearity analysis for hand-crafted descriptors.

This module implements Variance Inflation Factor (VIF) calculation to detect
multicollinearity among the hand-crafted graph descriptors extracted in T017.

Inputs:
  - data/processed/descriptors.csv: CSV containing graph descriptors (degree, density, clustering_coeff, etc.)

Outputs:
  - data/processed/vif_results.csv: CSV with columns: feature, vif_score
  - analysis/collinearity_report.md: Markdown report summarizing collinearity findings
"""

import os
import sys
import logging
import csv
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import numpy as np
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DESCRIPTORS_PATH = PROJECT_ROOT / "data" / "processed" / "descriptors.csv"
VIF_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "vif_results.csv"
REPORT_OUTPUT_PATH = PROJECT_ROOT / "analysis" / "collinearity_report.md"

# Thresholds
HIGH_VIF_THRESHOLD = 10.0
MODERATE_VIF_THRESHOLD = 5.0


def load_descriptors(path: Path) -> pd.DataFrame:
    """
    Load the descriptors CSV and return a DataFrame.
    Raises FileNotFoundError if the file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Descriptors file not found: {path}")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded descriptors from {path}: {len(df)} rows, {len(df.columns)} columns")
    return df


def calculate_vif_scores(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Calculate Variance Inflation Factor (VIF) for each numerical feature.
    
    Args:
        df: DataFrame containing numerical features.
        
    Returns:
        Tuple of (DataFrame with VIF scores, Dict mapping feature names to VIF values)
    """
    # Select only numerical columns
    numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if len(numerical_cols) < 2:
        logger.warning("Less than 2 numerical features found. VIF calculation requires at least 2 features.")
        return pd.DataFrame(), {}

    # Remove any constant columns (zero variance) as they cause VIF to be undefined
    non_constant_cols = []
    for col in numerical_cols:
        if df[col].var() > 1e-8:  # Avoid division by zero
            non_constant_cols.append(col)
        else:
            logger.warning(f"Skipping constant column '{col}' for VIF calculation.")

    if len(non_constant_cols) < 2:
        logger.warning("Less than 2 non-constant numerical features found after filtering.")
        return pd.DataFrame(), {}

    X = df[non_constant_cols].values
    
    vif_data = []
    vif_scores = {}
    
    for i, col in enumerate(non_constant_cols):
        try:
            vif = variance_inflation_factor(X, i)
            vif_data.append({"feature": col, "vif_score": vif})
            vif_scores[col] = vif
        except Exception as e:
            logger.error(f"Error calculating VIF for '{col}': {e}")
            vif_data.append({"feature": col, "vif_score": np.nan})
            vif_scores[col] = np.nan

    vif_df = pd.DataFrame(vif_data)
    return vif_df, vif_scores


def generate_report(vif_df: pd.DataFrame, output_path: Path) -> None:
    """
    Generate a Markdown report summarizing the VIF analysis.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write("# Collinearity Analysis Report\n\n")
        f.write("This report summarizes the Variance Inflation Factor (VIF) analysis\n")
        f.write("performed on the hand-crafted graph descriptors.\n\n")
        
        f.write("## Methodology\n")
        f.write("- **Metric**: Variance Inflation Factor (VIF)\n")
        f.write("- **Thresholds**:\n")
        f.write(f"  - High Collinearity: VIF > {HIGH_VIF_THRESHOLD}\n")
        f.write(f"  - Moderate Collinearity: {MODERATE_VIF_THRESHOLD} < VIF ≤ {HIGH_VIF_THRESHOLD}\n")
        f.write("  - Low Collinearity: VIF ≤ {MODERATE_VIF_THRESHOLD}\n\n")
        
        if vif_df.empty:
            f.write("## Results\n")
            f.write("No VIF scores could be calculated. This may be due to insufficient\n")
            f.write("numerical features or constant columns in the input data.\n\n")
            return

        f.write("## VIF Scores by Feature\n\n")
        f.write("| Feature | VIF Score | Interpretation |\n")
        f.write("|---------|-----------|----------------|\n")
        
        high_collinear = []
        moderate_collinear = []
        
        for _, row in vif_df.iterrows():
            feature = row['feature']
            vif = row['vif_score']
            
            if np.isnan(vif):
                interpretation = "Undefined (constant or error)"
            elif vif > HIGH_VIF_THRESHOLD:
                interpretation = "High Collinearity"
                high_collinear.append(feature)
            elif vif > MODERATE_VIF_THRESHOLD:
                interpretation = "Moderate Collinearity"
                moderate_collinear.append(feature)
            else:
                interpretation = "Low Collinearity"
            
            f.write(f"| {feature} | {vif:.4f} | {interpretation} |\n")
        
        f.write("\n## Summary\n\n")
        f.write(f"- **Total Features Analyzed**: {len(vif_df)}\n")
        f.write(f"- **High Collinearity Detected**: {len(high_collinear)} features\n")
        if high_collinear:
            f.write(f"  - Affected features: {', '.join(high_collinear)}\n")
        f.write(f"- **Moderate Collinearity Detected**: {len(moderate_collinear)} features\n")
        if moderate_collinear:
            f.write(f"  - Affected features: {', '.join(moderate_collinear)}\n")
        
        f.write("\n## Recommendations\n\n")
        if high_collinear:
            f.write(f"Features with high VIF ({', '.join(high_collinear)}) suggest strong multicollinearity.\n")
            f.write("Consider removing one of the correlated features or using dimensionality reduction\n")
            f.write("techniques (e.g., PCA) before model training.\n")
        else:
            f.write("No features exhibit high multicollinearity. The current set of descriptors\n")
            f.write("appears suitable for regression modeling without further collinearity adjustment.\n")


def main() -> int:
    """
    Main entry point for VIF calculation.
    """
    logger.info("Starting VIF calculation for descriptors...")
    
    try:
        # Load data
        df = load_descriptors(DESCRIPTORS_PATH)
        
        # Calculate VIF
        vif_df, vif_scores = calculate_vif_scores(df)
        
        # Save results to CSV
        VIF_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        vif_df.to_csv(VIF_OUTPUT_PATH, index=False)
        logger.info(f"VIF results saved to {VIF_OUTPUT_PATH}")
        
        # Generate report
        generate_report(vif_df, REPORT_OUTPUT_PATH)
        logger.info(f"Collinearity report saved to {REPORT_OUTPUT_PATH}")
        
        # Print summary to stdout
        if not vif_df.empty:
            high_count = (vif_df['vif_score'] > HIGH_VIF_THRESHOLD).sum()
            print(f"\nVIF Analysis Complete:")
            print(f"  - Features analyzed: {len(vif_df)}")
            print(f"  - High collinearity (VIF > {HIGH_VIF_THRESHOLD}): {high_count}")
            print(f"  - Results saved to: {VIF_OUTPUT_PATH}")
            print(f"  - Report saved to: {REPORT_OUTPUT_PATH}")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        print(f"Error: {e}", file=sys.stderr)
        print("Ensure that 'data/processed/descriptors.csv' exists. Run T017 first.", file=sys.stderr)
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during VIF calculation: {e}", exc_info=True)
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())