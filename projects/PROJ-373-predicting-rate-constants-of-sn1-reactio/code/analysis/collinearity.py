import os
import sys
import json
import logging
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import DataConfig, AnalysisConfig, ensure_dirs
from utils.logger import get_logger

logger = get_logger(__name__)

def load_processed_data(config: DataConfig) -> pd.DataFrame:
    """Load the cleaned dataset from T016."""
    input_path = config.processed_data_path / "cleaned_sn1.csv"
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def extract_feature_matrix(df: pd.DataFrame, config: AnalysisConfig) -> pd.DataFrame:
    """
    Extract the feature matrix for VIF calculation.
    Per FR-007: Uses topological descriptors only; Gasteiger charges are excluded.
    """
    # Identify topological descriptor columns
    # Based on data-model.md and typical RDKit outputs, these are usually prefixed with 'topo_'
    # or are specific topological indices (e.g., 'wiener_index', 'balaban_index').
    # We will select columns that match the schema's topological indices.
    # If specific column names are not known, we assume columns containing 'topo' or specific known indices.
    # However, to be robust, we look for columns that are numeric and likely descriptors.
    # The schema defines: smiles, rate_constant, substrate_class, gasteiger_charges, topological_indices, source_id.
    # We need to expand 'topological_indices' if it's a nested structure or select specific columns.
    # Assuming the CSV has flattened columns for topological indices.
    
    # Filter for numeric columns that are likely topological descriptors
    # We exclude 'rate_constant' (target), 'substrate_class' (categorical), 'source_id' (id), and 'smiles'.
    # We also exclude columns related to Gasteiger charges if they are present and named distinctly.
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Heuristic: Exclude target and known non-descriptor numeric columns
    exclude_cols = ['rate_constant', 'substrate_class', 'source_id', 'smiles'] # smiles is str, but safe to list
    
    # Identify Gasteiger columns (usually prefixed with 'gasteiger' or 'charge')
    gasteiger_cols = [col for col in numeric_cols if 'gasteiger' in col.lower() or 'charge' in col.lower()]
    
    # The remaining numeric columns are assumed to be topological descriptors
    feature_cols = [col for col in numeric_cols if col not in exclude_cols and col not in gasteiger_cols]
    
    if not feature_cols:
        logger.warning("No topological descriptor columns found. Checking for all numeric columns excluding target.")
        feature_cols = [col for col in numeric_cols if col not in exclude_cols]
    
    logger.info(f"Extracting {len(feature_cols)} feature columns for VIF: {feature_cols[:5]}...")
    
    # Handle missing values in features (VIF cannot handle NaN)
    # We drop rows with NaN in any of the selected features
    feature_df = df[feature_cols].dropna()
    
    if len(feature_df) == 0:
        raise ValueError("No valid rows after dropping NaNs in feature matrix.")
    
    logger.info(f"Feature matrix shape: {feature_df.shape}")
    return feature_df

def calculate_vif(X: pd.DataFrame) -> pd.Series:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.
    """
    # Add constant for intercept
    X_with_const = sm.add_constant(X)
    vif_data = pd.Series(
        [variance_inflation_factor(X_with_const.values, i) for i in range(X_with_const.shape[1])],
        index=X_with_const.columns
    )
    # Remove the constant term from the result
    vif_data = vif_data.drop('const')
    return vif_data

def identify_highly_correlated_pairs(vif_series: pd.Series, threshold: float = 5.0) -> list:
    """
    Identify pairs of predictors with VIF > threshold.
    Note: VIF is calculated per variable. High VIF implies collinearity with *other* variables.
    The task asks to "flag pairs". Since VIF is a scalar per variable, we flag variables with VIF > threshold.
    To form "pairs", we can identify the variables involved.
    However, strictly speaking, VIF > 5 for a variable X implies X is linearly dependent on others.
    We will report the variables that exceed the threshold.
    If the task strictly requires "pairs", we might need correlation matrix, but the prompt says "calculate VIF... flag pairs > 5".
    Interpretation: Flag the variables (which form the collinear sets) that have VIF > 5.
    We will return a list of objects describing the high-VIF variables.
    """
    flagged = []
    for var, vif in vif_series.items():
        if vif > threshold:
            flagged.append({
                "descriptor": var,
                "vif_score": float(vif),
                "is_flagged": True,
                "flag_reason": f"VIF ({vif:.2f}) exceeds threshold ({threshold})"
            })
    return flagged

def perform_pca_if_needed(X: pd.DataFrame, threshold: float = 5.0) -> dict:
    """
    Perform PCA if high collinearity is detected.
    Returns PCA summary.
    """
    vif_series = calculate_vif(X)
    high_vif_vars = vif_series[vif_series > threshold]
    
    if len(high_vif_vars) == 0:
        return {"pca_needed": False, "message": "No high collinearity detected."}
    
    from sklearn.decomposition import PCA
    pca = PCA()
    pca.fit(X)
    explained_variance = pca.explained_variance_ratio_
    
    return {
        "pca_needed": True,
        "high_vif_variables": high_vif_vars.to_dict(),
        "explained_variance_ratio": explained_variance.tolist(),
        "cumulative_variance": np.cumsum(explained_variance).tolist()
    }

def generate_chemical_description(flagged_pairs: list) -> list:
    """
    Generate a report list.
    Constraint: Do NOT invent chemical interpretations.
    """
    # The prompt asks for a JSON report with flagged pairs, VIF values, and boolean is_flagged.
    # It explicitly forbids chemical interpretation dictionaries.
    # We return the flagged items as is, perhaps formatted for the report.
    return flagged_pairs

def run_collinearity_analysis(config: DataConfig, analysis_config: AnalysisConfig):
    """
    Main routine for collinearity analysis.
    """
    ensure_dirs()
    
    # 1. Load data
    df = load_processed_data(config)
    
    # 2. Extract feature matrix (Topological only)
    X = extract_feature_matrix(df, analysis_config)
    
    if X.empty:
        logger.error("Feature matrix is empty. Cannot calculate VIF.")
        return
    
    # 3. Calculate VIF
    vif_series = calculate_vif(X)
    
    # 4. Identify high VIF variables (pairs/sets)
    # Since VIF is per variable, we report variables > threshold.
    # The "pairs" interpretation is handled by reporting the set of collinear variables.
    flagged_items = identify_highly_correlated_pairs(vif_series, threshold=analysis_config.vif_threshold)
    
    # 5. Generate Report
    report = {
        "analysis_type": "VIF Collinearity Check",
        "threshold": analysis_config.vif_threshold,
        "total_features_analyzed": len(vif_series),
        "flagged_count": len(flagged_items),
        "flagged_pairs": flagged_items,
        "all_vif_scores": {k: float(v) for k, v in vif_series.items()}
    }
    
    # 6. Save Report
    output_path = analysis_config.collinearity_report_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Collinearity report saved to {output_path}")
    return report

def main():
    config = DataConfig()
    analysis_config = AnalysisConfig()
    
    parser = argparse.ArgumentParser(description="Run collinearity analysis on SN1 dataset.")
    parser.add_argument("--threshold", type=float, default=5.0, help="VIF threshold for flagging.")
    args = parser.parse_args()
    
    analysis_config.vif_threshold = args.threshold
    
    try:
        run_collinearity_analysis(config, analysis_config)
    except Exception as e:
        logger.error(f"Collinearity analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
