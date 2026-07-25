import os
import sys
import json
import logging
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats

# Ensure imports work relative to project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ensure_dirs, AnalysisConfig
from utils.logger import get_logger

logger = get_logger(__name__)

# Load configuration
config = AnalysisConfig()

def load_processed_data(file_path: str) -> pd.DataFrame:
    """Load the cleaned dataset from CSV."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Processed data file not found: {file_path}")
    logger.info(f"Loading processed data from {file_path}")
    return pd.read_csv(file_path)

def extract_feature_matrix(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """
    Extract the feature matrix (predictors) and target from the dataset.
    Returns X (features), y (target), and feature names.
    """
    # Identify target column
    target_col = 'rate_constant'
    
    # Identify feature columns (exclude non-feature columns)
    exclude_cols = ['smiles', 'substrate_class', 'source_id', 'rate_constant', 'row_index']
    feature_cols = [col for col in df.columns if col not in exclude_cols and df[col].dtype in ['float64', 'int64', 'float32', 'int32']]
    
    if len(feature_cols) == 0:
        raise ValueError("No feature columns found in the dataset. Check data preprocessing.")
    
    logger.info(f"Extracting {len(feature_cols)} feature columns: {feature_cols}")
    
    X = df[feature_cols].dropna()
    y = df.loc[X.index, target_col]
    
    return X, y, feature_cols

def calculate_vif(X: pd.DataFrame) -> dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.
    VIF > 5 indicates potential multicollinearity.
    VIF > 10 indicates severe multicollinearity.
    """
    logger.info("Calculating VIF for all features...")
    vif_results = {}
    
    # Handle constant columns
    for col in X.columns:
        if X[col].std() == 0:
            vif_results[col] = float('inf')
            logger.warning(f"Constant column detected: {col}, VIF = inf")
            continue
    
    # Calculate VIF for non-constant columns
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    for i, col in enumerate(X.columns):
        if X[col].std() == 0:
            continue
        
        try:
            vif = variance_inflation_factor(X.values, i)
            vif_results[col] = vif
        except Exception as e:
            logger.error(f"Error calculating VIF for {col}: {e}")
            vif_results[col] = float('nan')
    
    return vif_results

def identify_highly_correlated_pairs(vif_results: dict[str, float], threshold: float = 5.0) -> list[dict]:
    """
    Identify pairs of features with VIF > threshold.
    Returns a list of dictionaries with feature pairs and their VIF values.
    """
    logger.info(f"Identifying highly correlated pairs (VIF > {threshold})...")
    high_vif_pairs = []
    
    # Convert to list of (feature, vif) tuples sorted by VIF descending
    sorted_vif = sorted(vif_results.items(), key=lambda x: x[1], reverse=True)
    
    for feature, vif in sorted_vif:
        if vif > threshold and not np.isnan(vif):
            high_vif_pairs.append({
                'feature': feature,
                'vif': vif,
                'severity': 'high' if vif > 10 else 'moderate'
            })
    
    logger.info(f"Found {len(high_vif_pairs)} features with VIF > {threshold}")
    return high_vif_pairs

def perform_pca_if_needed(X: pd.DataFrame, vif_results: dict[str, float], threshold: float = 10.0) -> tuple[pd.DataFrame, bool]:
    """
    Perform PCA on features with VIF > threshold as a fallback.
    Returns transformed data and a flag indicating if PCA was applied.
    """
    logger.info("Checking if PCA is needed...")
    
    features_to_pca = [col for col, vif in vif_results.items() if vif > threshold and not np.isnan(vif)]
    
    if len(features_to_pca) == 0:
        logger.info("No features with VIF > 10, PCA not needed")
        return X, False
    
    logger.info(f"Performing PCA on {len(features_to_pca)} high-VIF features: {features_to_pca}")
    
    from sklearn.decomposition import PCA
    
    # Extract high-VIF features
    X_high_vif = X[features_to_pca]
    
    # Apply PCA
    pca = PCA(n_components=0.95)  # Keep 95% variance
    X_pca = pca.fit_transform(X_high_vif)
    
    logger.info(f"PCA reduced {len(features_to_pca)} features to {X_pca.shape[1]} components")
    
    # Replace high-VIF features with PCA components
    X_transformed = X.drop(columns=features_to_pca)
    pca_cols = [f'pca_{i}' for i in range(X_pca.shape[1])]
    X_transformed[pca_cols] = X_pca
    
    return X_transformed, True

def generate_chemical_description(feature1: str, feature2: str) -> str:
    """
    Generate a brief chemical description of the relationship between two features.
    """
    descriptions = {
        'gasteiger': 'Partial atomic charge distribution',
        'topological': 'Molecular connectivity and branching',
        'molecular_weight': 'Molecular mass',
        'logp': 'Lipophilicity (hydrophobicity)',
        'rotatable_bonds': 'Molecular flexibility',
        'hbd': 'Hydrogen bond donors',
        'hba': 'Hydrogen bond acceptors',
        'polar_surface_area': 'Polar surface area',
        'ring_count': 'Number of rings',
        'aromatic_rings': 'Number of aromatic rings'
    }
    
    desc1 = next((d for k, d in descriptions.items() if k in feature1.lower()), feature1)
    desc2 = next((d for k, d in descriptions.items() if k in feature2.lower()), feature2)
    
    return f"{desc1} and {desc2} are chemically related descriptors often correlated in organic molecules."

def run_collinearity_analysis(data_path: str) -> dict:
    """
    Run full collinearity analysis: calculate VIF, identify high-VIF features,
    perform PCA if needed, and generate a descriptive report.
    """
    # Load data
    df = load_processed_data(data_path)
    
    # Extract features
    X, y, feature_names = extract_feature_matrix(df)
    
    # Calculate VIF
    vif_results = calculate_vif(X)
    
    # Identify high VIF pairs
    high_vif_pairs = identify_highly_correlated_pairs(vif_results, threshold=5.0)
    
    # Perform PCA if needed
    X_transformed, pca_applied = perform_pca_if_needed(X, vif_results, threshold=10.0)
    
    # Generate report
    report = {
        'summary': {
            'total_features': len(feature_names),
            'features_with_vif_gt_5': len([v for v in vif_results.values() if v > 5 and not np.isnan(v)]),
            'features_with_vif_gt_10': len([v for v in vif_results.values() if v > 10 and not np.isnan(v)]),
            'pca_applied': pca_applied
        },
        'vif_results': vif_results,
        'high_vif_pairs': high_vif_pairs,
        'chemical_relationships': [
            {
                'feature': pair['feature'],
                'vif': pair['vif'],
                'description': generate_chemical_description(pair['feature'], 'other_features')
            }
            for pair in high_vif_pairs
        ]
    }
    
    # Save report to artifacts
    output_path = Path("artifacts/collinearity_report.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write("# Collinearity Analysis Report\n\n")
        f.write(f"Generated on: {pd.Timestamp.now()}\n\n")
        f.write("## Summary\n\n")
        f.write(f"- Total features analyzed: {report['summary']['total_features']}\n")
        f.write(f"- Features with VIF > 5: {report['summary']['features_with_vif_gt_5']}\n")
        f.write(f"- Features with VIF > 10: {report['summary']['features_with_vif_gt_10']}\n")
        f.write(f"- PCA applied: {report['summary']['pca_applied']}\n\n")
        
        f.write("## High VIF Features (VIF > 5)\n\n")
        if high_vif_pairs:
            f.write("| Feature | VIF | Severity | Chemical Relationship |\n")
            f.write("|---------|-----|----------|----------------------|\n")
            for pair in high_vif_pairs:
                f.write(f"| {pair['feature']} | {pair['vif']:.2f} | {pair['severity']} | Correlated with other molecular descriptors |\n")
        else:
            f.write("No features with VIF > 5 detected.\n")
        
        f.write("\n## Detailed VIF Results\n\n")
        f.write("| Feature | VIF |\n")
        f.write("|---------|-----|\n")
        for feature, vif in sorted(vif_results.items(), key=lambda x: x[1], reverse=True):
            if not np.isnan(vif):
                f.write(f"| {feature} | {vif:.2f} |\n")
        
        f.write("\n## Recommendations\n\n")
        if report['summary']['features_with_vif_gt_10'] > 0:
            f.write("- **Severe multicollinearity detected**: Consider removing or combining highly correlated features.\n")
            f.write("- **PCA applied**: High-VIF features were transformed using PCA to reduce dimensionality.\n")
        elif report['summary']['features_with_vif_gt_5'] > 0:
            f.write("- **Moderate multicollinearity detected**: Monitor these features during model training.\n")
            f.write("- Consider feature selection if model performance is affected.\n")
        else:
            f.write("- **No significant multicollinearity detected**: All features have VIF < 5.\n")
            f.write("- Proceed with standard model training.\n")
    
    logger.info(f"Collinearity report saved to {output_path}")
    return report

def main():
    parser = argparse.ArgumentParser(description="Run collinearity analysis on processed SN1 dataset")
    parser.add_argument("--data", type=str, default="data/processed/cleaned_sn1.csv",
                      help="Path to the cleaned dataset CSV")
    args = parser.parse_args()

    ensure_dirs()
    
    try:
        run_collinearity_analysis(args.data)
        logger.info("Collinearity analysis completed successfully")
    except Exception as e:
        logger.error(f"Collinearity analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()