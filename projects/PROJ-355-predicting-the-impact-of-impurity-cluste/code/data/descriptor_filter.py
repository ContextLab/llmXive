"""
Module to compute Variance Inflation Factor (VIF) on clustering descriptors.
Implements FR-007: Report collinearity (VIF >= 10) without removing features.
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor

from config import get_project_root, get_data_paths

logger = logging.getLogger(__name__)

def load_descriptors(data_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the computed descriptors from the processed data file.
    
    Args:
        data_path: Optional path to the descriptors CSV. If None, uses default path.
        
    Returns:
        DataFrame containing descriptor columns.
        
    Raises:
        FileNotFoundError: If the descriptors file does not exist.
        ValueError: If required columns are missing.
    """
    if data_path is None:
        data_paths = get_data_paths()
        data_path = data_paths.get("processed_descriptors")
    
    if not data_path.exists():
        raise FileNotFoundError(f"Descriptors file not found at {data_path}")
    
    df = pd.read_csv(data_path)
    
    required_cols = ["rdf_peak", "pair_corr", "voronoi_count"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required descriptor columns: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} samples with columns: {list(df.columns)}")
    return df

def compute_vif(df: pd.DataFrame, feature_cols: Optional[List[str]] = None) -> Dict[str, float]:
    """
    Compute Variance Inflation Factor (VIF) for each descriptor feature.
    
    VIF measures how much the variance of an estimated regression coefficient 
    increases if your predictors are correlated. A VIF >= 10 indicates high 
    collinearity.
    
    Args:
        df: DataFrame containing the feature columns.
        feature_cols: List of column names to compute VIF for. Defaults to 
                      ['rdf_peak', 'pair_corr', 'voronoi_count'].
                      
    Returns:
        Dictionary mapping feature names to their VIF scores.
        
    Raises:
        ValueError: If input data has constant columns or insufficient samples.
    """
    if feature_cols is None:
        feature_cols = ["rdf_peak", "pair_corr", "voronoi_count"]
    
    # Ensure all requested columns exist
    available_cols = [col for col in feature_cols if col in df.columns]
    if len(available_cols) != len(feature_cols):
        missing = set(feature_cols) - set(available_cols)
        raise ValueError(f"Missing columns for VIF computation: {missing}")
    
    X = df[available_cols].values
    
    # Check for constant columns (variance = 0)
    for i, col in enumerate(available_cols):
        if np.var(X[:, i]) < 1e-10:
            raise ValueError(f"Column '{col}' has near-zero variance, cannot compute VIF")
    
    # Check for sufficient samples
    if X.shape[0] < X.shape[1] + 1:
        raise ValueError(
            f"Insufficient samples ({X.shape[0]}) for VIF computation with "
            f"{X.shape[1]} features"
        )
    
    vif_scores = {}
    for i, col in enumerate(available_cols):
        try:
            vif = variance_inflation_factor(X, i)
            vif_scores[col] = float(vif)
        except Exception as e:
            logger.warning(f"Could not compute VIF for {col}: {e}")
            vif_scores[col] = float('inf')
    
    return vif_scores

def generate_report(
    vif_scores: Dict[str, float], 
    output_path: Optional[Path] = None,
    threshold: float = 10.0
) -> str:
    """
    Generate a markdown collinearity report based on VIF scores.
    
    Args:
        vif_scores: Dictionary of feature -> VIF score.
        output_path: Optional path to save the report. If None, uses default path.
        threshold: VIF threshold for flagging collinearity (default: 10.0).
        
    Returns:
        The markdown content of the report.
    """
    if output_path is None:
        data_paths = get_data_paths()
        output_path = data_paths.get("collinearity_report")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Analyze results
    high_vif_features = {k: v for k, v in vif_scores.items() if v >= threshold}
    low_vif_features = {k: v for k, v in vif_scores.items() if v < threshold}
    
    lines = [
        "# Collinearity Analysis Report",
        "",
        f"**Analysis Date**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**VIF Threshold**: {threshold}",
        "",
        "## Summary",
        ""
    ]
    
    if high_vif_features:
        lines.append(f"**Collinearity Detected**: {len(high_vif_features)} feature(s) have VIF >= {threshold}")
        lines.append("")
        lines.append("## Features with High Collinearity (VIF >= 10)")
        lines.append("")
        lines.append("| Feature | VIF Score | Interpretation |")
        lines.append("|---------|-----------|----------------|")
        for feat, score in sorted(high_vif_features.items(), key=lambda x: x[1], reverse=True):
            interpretation = "High collinearity - joint relationship with other features"
            if score >= 30:
                interpretation = "Severe collinearity - strong joint relationship"
            lines.append(f"| {feat} | {score:.2f} | {interpretation} |")
        lines.append("")
        lines.append("## Joint Relationship Analysis")
        lines.append("")
        lines.append("The following features exhibit significant joint relationships:")
        lines.append("")
        for feat in high_vif_features.keys():
            lines.append(f"- **{feat}**: This feature is highly correlated with one or more other descriptors, "
                        "indicating that it provides redundant information in a linear model context. "
                        "Per FR-007, this feature is retained for transparency, but users should be aware "
                        "that coefficient estimates may be unstable.")
        lines.append("")
        lines.append("## Recommendation")
        lines.append("")
        lines.append("While these features are retained as per project specifications (FR-007), "
                    "consider the following when interpreting model coefficients:")
        lines.append("1. Standard errors for these coefficients will be inflated.")
        lines.append("2. P-values may not be reliable for these features.")
        lines.append("3. Model predictions may still be accurate even with collinear features.")
    else:
        lines.append(f"**No Collinearity Detected**: All features have VIF < {threshold}")
        lines.append("")
        lines.append("## Feature Independence Analysis")
        lines.append("")
        lines.append("All descriptor features appear to be linearly independent within the "
                    "computed dataset:")
        lines.append("")
        lines.append("| Feature | VIF Score | Status |")
        lines.append("|---------|-----------|--------|")
        for feat, score in sorted(low_vif_features.items(), key=lambda x: x[1]):
            status = "Independent"
            lines.append(f"| {feat} | {score:.2f} | {status} |")
        lines.append("")
        lines.append("## Conclusion")
        lines.append("")
        lines.append("No significant collinearity was detected among the clustering descriptors. "
                    "Statistical inference (p-values, confidence intervals) should be reliable "
                    "for all features in downstream regression models.")
    
    report_content = "\n".join(lines)
    
    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    logger.info(f"Collinearity report saved to {output_path}")
    return report_content

def run_vif_analysis(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    threshold: float = 10.0
) -> Dict[str, Any]:
    """
    Run the full VIF analysis pipeline: load data, compute VIF, generate report.
    
    Args:
        input_path: Path to the descriptors CSV file.
        output_path: Path to save the collinearity report.
        threshold: VIF threshold for flagging collinearity.
        
    Returns:
        Dictionary containing analysis results (VIF scores, summary).
    """
    logger.info("Starting VIF analysis...")
    
    # Load descriptors
    df = load_descriptors(input_path)
    
    # Compute VIF
    vif_scores = compute_vif(df)
    
    # Generate report
    generate_report(vif_scores, output_path, threshold)
    
    # Prepare results
    high_vif_count = sum(1 for v in vif_scores.values() if v >= threshold)
    results = {
        "vif_scores": vif_scores,
        "high_vif_count": high_vif_count,
        "threshold": threshold,
        "total_features": len(vif_scores),
        "status": "collinearity_detected" if high_vif_count > 0 else "no_collinearity"
    }
    
    # Save JSON summary
    data_paths = get_data_paths()
    json_path = data_paths.get("collinearity_metrics", 
                               data_paths.get("processed_dir") / "vif_metrics.json")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"VIF analysis complete. Status: {results['status']}")
    return results

def main():
    """Main entry point for VIF analysis from command line."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        data_paths = get_data_paths()
        input_path = data_paths.get("processed_descriptors")
        output_path = data_paths.get("collinearity_report")
        
        if not input_path.exists():
            logger.error(f"Input descriptors file not found: {input_path}")
            logger.error("Please ensure T015 (descriptor computation) has been run first.")
            return 1
        
        results = run_vif_analysis(input_path, output_path)
        
        print("\n" + "="*50)
        print("VIF Analysis Results")
        print("="*50)
        print(f"Status: {results['status']}")
        print(f"Features analyzed: {results['total_features']}")
        print(f"High VIF features (>=10): {results['high_vif_count']}")
        print("\nVIF Scores:")
        for feat, score in sorted(results['vif_scores'].items(), key=lambda x: x[1], reverse=True):
            marker = " ⚠️" if score >= 10 else ""
            print(f"  {feat}: {score:.2f}{marker}")
        print(f"\nReport saved to: {output_path}")
        print("="*50)
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during VIF analysis: {e}")
        return 1

if __name__ == "__main__":
    exit(main())