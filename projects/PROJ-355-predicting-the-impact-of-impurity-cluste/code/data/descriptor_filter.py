"""
descriptor_filter.py

Implements Variance Inflation Factor (VIF) calculation to detect multicollinearity
in the descriptor dataset. Generates a descriptive report (data/processed/collinearity_report.md)
explaining joint relationships without removing features, adhering to FR-007.
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor

from config import get_project_root, get_data_paths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Threshold for VIF indicating high collinearity (per task description: VIF >= 10)
VIF_THRESHOLD = 10.0

def load_descriptors() -> pd.DataFrame:
    """
    Loads the processed descriptors CSV file.
    Expects data/processed/descriptors.csv with columns: [species, rdf_peak, pair_corr, voronoi_count]
    """
    project_root = get_project_root()
    data_paths = get_data_paths()
    descriptors_path = data_paths['processed'] / 'descriptors.csv'

    if not descriptors_path.exists():
        raise FileNotFoundError(
            f"Descriptors file not found at {descriptors_path}. "
            "Please ensure T015 (descriptor computation) has been completed."
        )

    df = pd.read_csv(descriptors_path)
    logger.info(f"Loaded {len(df)} rows from {descriptors_path}")
    return df

def compute_vif(df: pd.DataFrame, feature_columns: List[str]) -> pd.DataFrame:
    """
    Computes the Variance Inflation Factor (VIF) for each feature.

    Args:
        df: DataFrame containing the data.
        feature_columns: List of column names to compute VIF for.

    Returns:
        DataFrame with columns: ['feature', 'vif']
    """
    # Select only the numeric features for VIF calculation
    X = df[feature_columns].astype(float)

    # Add intercept for statsmodels (though VIF calculation usually handles it or requires it)
    # statsmodels VIF calculation typically expects X without intercept if using the function directly
    # on the design matrix, but the standard formula VIF_j = 1 / (1 - R_j^2)
    # where R_j^2 is from regressing X_j on all other X's.
    
    vif_data = []
    
    for i, col in enumerate(feature_columns):
        # Calculate VIF for feature i
        # We use the formula: VIF = 1 / (1 - R^2)
        # where R^2 is from regressing column i on all other columns
        try:
            vif = variance_inflation_factor(X.values, i)
            vif_data.append({'feature': col, 'vif': vif})
        except Exception as e:
            logger.warning(f"Could not compute VIF for {col}: {e}")
            vif_data.append({'feature': col, 'vif': np.nan})

    return pd.DataFrame(vif_data)

def generate_report(vif_df: pd.DataFrame, output_path: Path) -> None:
    """
    Generates a markdown report explaining collinearity based on VIF scores.
    Does NOT remove features.
    """
    high_vif_features = vif_df[vif_df['vif'] >= VIF_THRESHOLD]
    
    report_lines = [
        "# Collinearity Report (Variance Inflation Factor Analysis)",
        "",
        "## Summary",
        f"- **Threshold**: VIF ≥ {VIF_THRESHOLD} indicates potential multicollinearity.",
        f"- **Total Features Analyzed**: {len(vif_df)}",
        f"- **Features with High Collinearity**: {len(high_vif_features)}",
        ""
    ]

    if len(high_vif_features) == 0:
        report_lines.append("No features exceeded the VIF threshold. The descriptor set appears to have low multicollinearity.")
    else:
        report_lines.append("### High Collinearity Detected")
        report_lines.append("The following features exhibit high variance inflation, suggesting strong linear relationships with other features:")
        report_lines.append("")
        report_lines.append("| Feature | VIF Score | Interpretation |")
        report_lines.append("|---|---|---|")
        
        for _, row in high_vif_features.iterrows():
            vif_val = row['vif']
            interpretation = "Severe multicollinearity" if vif_val > 100 else "High multicollinearity"
            report_lines.append(f"| {row['feature']} | {vif_val:.2f} | {interpretation} |")
        
        report_lines.append("")
        report_lines.append("### Joint Relationships Description")
        report_lines.append("")
        report_lines.append("Based on the VIF scores, the following joint relationships are observed:")
        report_lines.append("")
        
        # Generate descriptive text for joint relationships
        # Since we don't have the correlation matrix here, we infer from VIF magnitude
        # In a real scenario, one might compute pairwise correlations to explain specific pairs.
        # Here we describe the implication of the VIF values found.
        
        for _, row in high_vif_features.iterrows():
            feature = row['feature']
            vif_val = row['vif']
            report_lines.append(f"- **{feature}**: With a VIF of {vif_val:.2f}, this feature is highly predictable from the linear combination of the other descriptors. "
                              f"This suggests that {feature} contains redundant information relative to the other clustering descriptors (e.g., RDF, pair correlation, Voronoi counts). "
                              f"According to FR-007, this feature is retained for the model, but its coefficient estimates may be unstable.")
        
        report_lines.append("")
        report_lines.append("### Recommendation")
        report_lines.append("")
        report_lines.append("Per the project specification (FR-007), features are **not** removed. "
                          "However, users should be aware that regression coefficients for these features may have inflated standard errors.")

    report_content = "\n".join(report_lines)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(report_content)
    
    logger.info(f"Collinearity report generated at {output_path}")

def run_vif_analysis() -> Dict[str, Any]:
    """
    Main function to run the VIF analysis pipeline.
    """
    try:
        # 1. Load data
        df = load_descriptors()
        
        # Define feature columns (exclude 'species' which is likely categorical or ID)
        # Based on T015: columns [species, rdf_peak, pair_corr, voronoi_count]
        numeric_cols = ['rdf_peak', 'pair_corr', 'voronoi_count']
        
        # Verify columns exist
        missing_cols = [c for c in numeric_cols if c not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required descriptor columns: {missing_cols}")
        
        # 2. Compute VIF
        vif_df = compute_vif(df, numeric_cols)
        
        # 3. Generate Report
        project_root = get_project_root()
        data_paths = get_data_paths()
        report_path = data_paths['processed'] / 'collinearity_report.md'
        
        generate_report(vif_df, report_path)
        
        # 4. Save VIF scores to JSON for programmatic access (optional but useful)
        json_path = data_paths['processed'] / 'vif_scores.json'
        with open(json_path, 'w') as f:
            json.dump(vif_df.to_dict(orient='records'), f, indent=2)
        
        logger.info("VIF analysis completed successfully.")
        return {"status": "success", "report_path": str(report_path), "vif_path": str(json_path)}
        
    except Exception as e:
        logger.error(f"VIF analysis failed: {e}")
        raise

def main():
    """Entry point for script execution."""
    run_vif_analysis()

if __name__ == "__main__":
    main()
