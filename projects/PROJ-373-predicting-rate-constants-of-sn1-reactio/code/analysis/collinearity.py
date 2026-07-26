"""
Collinearity Analysis Module for SN1 Rate Constant Prediction.

This module calculates Variance Inflation Factors (VIF) for predictor features,
identifies highly correlated pairs, performs descriptive joint analysis,
and generates a markdown report.

It operates on the cleaned dataset produced by T016.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any

import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Static dictionary for chemical relationship descriptions
CHEMICAL_RELATIONSHIPS = {
    "Gasteiger_Charge_Max": "Electrophilic potential",
    "Topological_Index_Wiener": "Molecular size/branching",
    "CalcNumRotatableBonds": "Molecular flexibility",
    "LogP": "Lipophilicity"
}

# Setup logging
logger = logging.getLogger(__name__)

def load_processed_data(input_path: str) -> pd.DataFrame:
    """
    Load the cleaned dataset from the specified path.

    Args:
        input_path: Path to the cleaned CSV file (data/processed/cleaned_sn1.csv).

    Returns:
        pandas DataFrame containing the processed data.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Loading processed data from {input_path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
    return df

def extract_feature_matrix(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Extract the feature matrix (predictor variables) from the dataset.

    This function assumes the dataset contains specific descriptor columns.
    It filters out non-feature columns like 'smiles', 'rate_constant', etc.

    Args:
        df: The full processed DataFrame.

    Returns:
        Tuple of (feature_matrix, list_of_feature_names).
    """
    # Define known feature columns based on T013 descriptors and T012 cleaning
    # We try to select columns that are numeric and likely descriptors
    possible_features = [
        'Gasteiger_Charge_Max', 'Gasteiger_Charge_Min', 'Gasteiger_Charge_Sum',
        'Topological_Index_Wiener', 'Topological_Index_Zagreb',
        'CalcNumRotatableBonds', 'LogP', 'Molecular_Weight',
        'Num_H_Acceptors', 'Num_H_Donors', 'Num_Rings'
    ]

    # Filter features that actually exist in the dataframe
    available_features = [col for col in possible_features if col in df.columns]

    # If no predefined features found, try to select all numeric columns
    # excluding known non-feature columns
    if not available_features:
        exclude_cols = ['smiles', 'rate_constant', 'substrate_class', 'row_index', 'source_id']
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        available_features = [col for col in numeric_cols if col not in exclude_cols]

    if not available_features:
        raise ValueError("No numeric feature columns found in the dataset for VIF calculation.")

    logger.info(f"Extracting feature matrix with columns: {available_features}")
    feature_matrix = df[available_features].copy()

    # Handle missing values by dropping rows (VIF cannot handle NaN)
    initial_rows = len(feature_matrix)
    feature_matrix = feature_matrix.dropna()
    dropped_rows = initial_rows - len(feature_matrix)
    if dropped_rows > 0:
        logger.warning(f"Dropped {dropped_rows} rows due to missing values in features.")

    return feature_matrix, available_features

def calculate_vif(feature_matrix: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the Variance Inflation Factor (VIF) for each feature.

    Args:
        feature_matrix: DataFrame containing only numeric features.

    Returns:
        DataFrame with columns: 'feature', 'vif'.
    """
    logger.info("Calculating VIF for all features...")
    vif_data = []

    # Add a constant for the intercept if statsmodels requires it (usually does for regression)
    # However, for VIF calculation specifically, we just need the design matrix X.
    # VIF_i = 1 / (1 - R_i^2) where R_i^2 is from regressing X_i on all other X_j.

    # Ensure no constant column is present if we were doing regression, but for VIF
    # we iterate over features.
    for i, col in enumerate(feature_matrix.columns):
        try:
            vif = variance_inflation_factor(feature_matrix.values, i)
            vif_data.append({'feature': col, 'vif': vif})
        except Exception as e:
            logger.error(f"Error calculating VIF for {col}: {e}")
            vif_data.append({'feature': col, 'vif': np.nan})

    vif_df = pd.DataFrame(vif_data)
    vif_df = vif_df.sort_values(by='vif', ascending=False)
    logger.info(f"VIF calculation complete. Max VIF: {vif_df['vif'].max():.2f}")
    return vif_df

def identify_highly_correlated_pairs(vif_df: pd.DataFrame, threshold: float = 5.0) -> List[Dict[str, Any]]:
    """
    Identify features with VIF greater than the threshold.

    Args:
        vif_df: DataFrame of VIF values.
        threshold: VIF threshold above which a feature is considered highly correlated.

    Returns:
        List of dictionaries containing feature info and VIF value.
    """
    high_vif = vif_df[vif_df['vif'] > threshold].to_dict(orient='records')
    logger.info(f"Found {len(high_vif)} features with VIF > {threshold}")
    return high_vif

def perform_pca_if_needed(vif_df: pd.DataFrame, feature_matrix: pd.DataFrame, threshold: float = 10.0) -> Optional[Dict[str, Any]]:
    """
    Perform PCA as a fallback if any feature has VIF > threshold.

    Args:
        vif_df: DataFrame of VIF values.
        feature_matrix: Original feature matrix.
        threshold: VIF threshold to trigger PCA.

    Returns:
        Dictionary with PCA results or None if not triggered.
    """
    max_vif = vif_df['vif'].max()
    if max_vif <= threshold:
        logger.info(f"Max VIF ({max_vif:.2f}) <= {threshold}. PCA not triggered.")
        return None

    logger.warning(f"Max VIF ({max_vif:.2f}) > {threshold}. Triggering PCA fallback.")
    from sklearn.decomposition import PCA

    pca = PCA()
    pca.fit(feature_matrix)

    explained_variance_ratio = pca.explained_variance_ratio_
    cumulative_variance = np.cumsum(explained_variance_ratio)

    # Find number of components to explain 95% variance
    n_components = np.argmax(cumulative_variance >= 0.95) + 1

    return {
        'triggered': True,
        'max_vif': max_vif,
        'n_components_total': len(explained_variance_ratio),
        'n_components_95': n_components,
        'explained_variance_ratio': explained_variance_ratio.tolist(),
        'cumulative_variance': cumulative_variance.tolist()
    }

def generate_chemical_description(feature_name: str) -> str:
    """
    Generate a chemical description for a feature using the static dictionary.

    Args:
        feature_name: Name of the feature.

    Returns:
        Description string.
    """
    return CHEMICAL_RELATIONSHIPS.get(feature_name, "Chemical relationship: Undetermined (requires expert review)")

def run_collinearity_analysis(input_path: str, output_path: str, vif_threshold: float = 5.0, pca_threshold: float = 10.0) -> None:
    """
    Run the full collinearity analysis and generate the report.

    Args:
        input_path: Path to the cleaned dataset.
        output_path: Path to save the markdown report.
        vif_threshold: Threshold for flagging high VIF.
        pca_threshold: Threshold for triggering PCA.
    """
    logger.info("Starting Collinearity Analysis...")

    # 1. Load Data
    df = load_processed_data(input_path)

    # 2. Extract Features
    feature_matrix, feature_names = extract_feature_matrix(df)

    # 3. Calculate VIF
    vif_df = calculate_vif(feature_matrix)

    # 4. Identify High VIF Pairs (Features)
    # Note: VIF is per feature, not per pair. The task asks to "flag pairs > 5".
    # In standard VIF analysis, we flag individual features that have high multicollinearity
    # with the *set* of other features. We will list the features with VIF > threshold.
    # If the task strictly implies pairwise correlation, we would use correlation matrix,
    # but the prompt explicitly says "Calculate VIF... flag pairs > 5".
    # Interpretation: Flag features that are part of a collinear set (VIF > 5).
    high_vif_features = identify_highly_correlated_pairs(vif_df, vif_threshold)

    # 5. Perform PCA Fallback if needed
    pca_result = perform_pca_if_needed(vif_df, feature_matrix, pca_threshold)

    # 6. Generate Report
    report_lines = [
        "# Collinearity Analysis Report",
        "",
        f"**Input Data**: {input_path}",
        f"**VIF Threshold**: {vif_threshold}",
        f"**PCA Trigger Threshold**: {pca_threshold}",
        "",
        "## Summary",
        "",
        f"- Total features analyzed: {len(feature_names)}",
        f"- Features with VIF > {vif_threshold}: {len(high_vif_features)}",
        f"- PCA Triggered: {'Yes' if pca_result else 'No'}",
        ""
    ]

    if high_vif_features:
        report_lines.append("## Highly Correlated Features (VIF > {threshold})".format(threshold=vif_threshold))
        report_lines.append("")
        report_lines.append("| Feature | VIF | Chemical Relationship |")
        report_lines.append("| :--- | :--- | :--- |")
        for item in high_vif_features:
            feature = item['feature']
            vif_val = item['vif']
            desc = generate_chemical_description(feature)
            report_lines.append(f"| {feature} | {vif_val:.2f} | {desc} |")
        report_lines.append("")
    else:
        report_lines.append(f"## No features with VIF > {vif_threshold} found.")
        report_lines.append("")

    if pca_result:
        report_lines.append("## PCA Fallback Results")
        report_lines.append("")
        report_lines.append(f"- Max VIF: {pca_result['max_vif']:.2f}")
        report_lines.append(f"- Total Components: {pca_result['n_components_total']}")
        report_lines.append(f"- Components for 95% Variance: {pca_result['n_components_95']}")
        report_lines.append("")
        report_lines.append("### Explained Variance Ratio")
        for i, var in enumerate(pca_result['explained_variance_ratio']):
            report_lines.append(f"- Component {i+1}: {var:.4f}")
        report_lines.append("")

    # Detailed VIF Table for all features
    report_lines.append("## Full VIF Table")
    report_lines.append("")
    report_lines.append("| Feature | VIF | Description |")
    report_lines.append("| :--- | :--- | :--- |")
    for _, row in vif_df.iterrows():
        desc = generate_chemical_description(row['feature'])
        report_lines.append(f"| {row['feature']} | {row['vif']:.2f} | {desc} |")
    report_lines.append("")

    # Write Report
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        f.write('\n'.join(report_lines))

    logger.info(f"Collinearity report saved to {output_path}")

def main():
    """Main entry point for the collinearity analysis script."""
    parser = argparse.ArgumentParser(description="Run collinearity analysis on SN1 dataset.")
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/cleaned_sn1.csv",
        help="Path to the cleaned dataset CSV (default: data/processed/cleaned_sn1.csv)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="artifacts/collinearity_report.md",
        help="Path to save the markdown report (default: artifacts/collinearity_report.md)"
    )
    parser.add_argument(
        "--vif-threshold",
        type=float,
        default=5.0,
        help="VIF threshold for flagging high collinearity (default: 5.0)"
    )
    parser.add_argument(
        "--pca-threshold",
        type=float,
        default=10.0,
        help="VIF threshold for triggering PCA (default: 10.0)"
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        run_collinearity_analysis(
            input_path=args.input,
            output_path=args.output,
            vif_threshold=args.vif_threshold,
            pca_threshold=args.pca_threshold
        )
        logger.info("Collinearity analysis completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()