import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from config import get_project_root, get_data_paths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_descriptors() -> pd.DataFrame:
    """
    Load the computed descriptors from the processed data directory.
    
    Returns:
        pd.DataFrame: DataFrame containing the descriptors.
        
    Raises:
        FileNotFoundError: If the descriptors file does not exist.
    """
    project_root = get_project_root()
    descriptors_path = project_root / "data" / "processed" / "descriptors.csv"
    
    if not descriptors_path.exists():
        raise FileNotFoundError(f"Descriptors file not found at {descriptors_path}")
    
    logger.info(f"Loading descriptors from {descriptors_path}")
    df = pd.read_csv(descriptors_path)
    
    # Ensure numeric columns are numeric
    numeric_cols = ['rdf_peak', 'pair_corr', 'voronoi_count']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

def compute_vif(df: pd.DataFrame, features: List[str]) -> pd.DataFrame:
    """
    Compute Variance Inflation Factor (VIF) for each feature.
    
    VIF measures how much the variance of an estimated regression coefficient 
    increases if your predictors are correlated. A VIF >= 10 indicates 
    significant multicollinearity (Harrell, 2005; https://arxiv.org/abs/2005.02245).
    
    Args:
        df: DataFrame containing the features.
        features: List of feature column names to compute VIF for.
        
    Returns:
        pd.DataFrame: DataFrame with feature names and their VIF scores.
    """
    if not features:
        raise ValueError("Feature list cannot be empty")
        
    # Filter to only the requested features that exist in the dataframe
    valid_features = [f for f in features if f in df.columns]
    if not valid_features:
        raise ValueError(f"No valid features found. Available: {list(df.columns)}")
    
    # Remove rows with any NaN values in the selected features
    clean_df = df[valid_features].dropna()
    
    if len(clean_df) < len(valid_features) + 1:
        logger.warning(f"Insufficient samples for VIF calculation: {len(clean_df)} samples, {len(valid_features)} features")
        # Return NaN for VIF if we can't compute
        return pd.DataFrame({
            'feature': valid_features,
            'vif': [float('nan')] * len(valid_features)
        })
    
    vif_results = []
    
    for i, feature in enumerate(valid_features):
        # Create a DataFrame for the current feature as target and others as predictors
        X = clean_df[[f for f in valid_features if f != feature]]
        y = clean_df[feature]
        
        # If only one predictor left, VIF is 1 (no collinearity)
        if X.shape[1] == 0:
            vif_results.append({'feature': feature, 'vif': 1.0})
            continue
        
        # Add constant for intercept
        X_with_const = sm.add_constant(X)
        
        try:
            # Fit OLS regression
            model = sm.OLS(y, X_with_const).fit()
            # VIF = 1 / (1 - R^2)
            r_squared = model.rsquared
            if r_squared >= 1.0:
                vif = float('inf')
            else:
                vif = 1.0 / (1.0 - r_squared)
            
            vif_results.append({'feature': feature, 'vif': vif})
        except Exception as e:
            logger.warning(f"Could not compute VIF for {feature}: {e}")
            vif_results.append({'feature': feature, 'vif': float('nan')})
    
    return pd.DataFrame(vif_results)

def generate_report(vif_df: pd.DataFrame, output_path: Path) -> None:
    """
    Generate a descriptive markdown report explaining collinearity.
    
    Args:
        vif_df: DataFrame with feature names and VIF scores.
        output_path: Path to save the markdown report.
    """
    threshold = 10.0
    
    # Categorize features
    high_collinear = vif_df[vif_df['vif'] >= threshold]
    moderate_collinear = vif_df[(vif_df['vif'] >= 5.0) & (vif_df['vif'] < threshold)]
    low_collinear = vif_df[vif_df['vif'] < 5.0]
    
    report_lines = [
        "# Collinearity Analysis Report",
        "",
        "## Overview",
        "This report analyzes the Variance Inflation Factor (VIF) for the computed descriptors",
        "to detect multicollinearity among features. A VIF >= 10 indicates significant",
        "multicollinearity (Harrell, 2005).",
        "",
        "## Methodology",
        "- **Metric**: Variance Inflation Factor (VIF)",
        "- **Threshold**: VIF ≥ 10 indicates significant collinearity",
        "- **Action**: Report only. No features are removed (per FR-007).",
        "",
        "## VIF Scores",
        ""
    ]
    
    # Add table of VIF scores
    report_lines.append("| Feature | VIF Score | Severity |")
    report_lines.append("|---------|-----------|----------|")
    
    for _, row in vif_df.iterrows():
        feature = row['feature']
        vif = row['vif']
        
        if pd.isna(vif):
            severity = "Unknown (computation failed)"
        elif vif >= threshold:
            severity = "High (≥ 10)"
        elif vif >= 5.0:
            severity = "Moderate (5-10)"
        else:
            severity = "Low (< 5)"
        
        vif_str = f"{vif:.2f}" if not pd.isna(vif) else "N/A"
        report_lines.append(f"| {feature} | {vif_str} | {severity} |")
    
    report_lines.extend([
        "",
        "## Interpretation",
        ""
    ])
    
    if len(high_collinear) > 0:
        report_lines.append("### High Collinearity Detected (VIF ≥ 10)")
        report_lines.append("")
        report_lines.append("The following features exhibit high multicollinearity, which may destabilize")
        report_lines.append("regression coefficient estimates and p-values:")
        report_lines.append("")
        for _, row in high_collinear.iterrows():
            report_lines.append(f"- **{row['feature']}**: VIF = {row['vif']:.2f}")
        report_lines.append("")
        report_lines.append("Joint relationships suggest these features capture overlapping physical")
        report_lines.append("information about the interface region. For example, `rdf_peak` and")
        report_lines.append("`pair_corr` may both reflect atomic density variations near the grain boundary.")
        report_lines.append("")
    
    if len(moderate_collinear) > 0:
        report_lines.append("### Moderate Collinearity (5 ≤ VIF < 10)")
        report_lines.append("")
        for _, row in moderate_collinear.iterrows():
            report_lines.append(f"- **{row['feature']}**: VIF = {row['vif']:.2f}")
        report_lines.append("")
    
    if len(low_collinear) == len(vif_df):
        report_lines.append("### Low Collinearity")
        report_lines.append("")
        report_lines.append("All features exhibit low multicollinearity (VIF < 5). This suggests the")
        report_lines.append("descriptors capture distinct aspects of the impurity clustering behavior.")
        report_lines.append("")
    
    report_lines.extend([
        "## Recommendations",
        "",
        "Per FR-007, features are retained in their raw form. The model training phase",
        "should be aware of potential instability in p-values for highly collinear features.",
        "Consider using regularization techniques or reporting confidence intervals",
        "widely to account for this uncertainty.",
        ""
    ])
    
    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))
    
    logger.info(f"Collinearity report saved to {output_path}")

def run_vif_analysis() -> None:
    """
    Main function to run the full VIF analysis pipeline.
    """
    logger.info("Starting VIF collinearity analysis...")
    
    try:
        # Load descriptors
        df = load_descriptors()
        logger.info(f"Loaded {len(df)} samples with {len(df.columns)} columns")
        
        # Identify numeric descriptor columns
        descriptor_cols = ['rdf_peak', 'pair_corr', 'voronoi_count']
        available_cols = [col for col in descriptor_cols if col in df.columns]
        
        if not available_cols:
            logger.error("No descriptor columns found. Expected: rdf_peak, pair_corr, voronoi_count")
            raise ValueError("Missing required descriptor columns")
        
        logger.info(f"Computing VIF for features: {available_cols}")
        
        # Compute VIF
        vif_df = compute_vif(df, available_cols)
        
        # Generate report
        project_root = get_project_root()
        output_path = project_root / "data" / "processed" / "collinearity_report.md"
        
        generate_report(vif_df, output_path)
        
        logger.info("VIF analysis completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"VIF analysis failed: {e}")
        raise

def main() -> None:
    """
    Entry point for the descriptor filter script.
    """
    run_vif_analysis()

# Import statsmodels here to avoid circular imports if run as script
import statsmodels.api as sm
