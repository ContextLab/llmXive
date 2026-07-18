import os
import sys
import json
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.tools import add_constant

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/collinearity.log')
    ]
)
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from code/config.yaml."""
    config_path = Path('code/config.yaml')
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config

def load_analysis_results():
    """
    Load analysis results from the final report or intermediate CSVs.
    We expect the analysis to have produced a combined metrics file or 
    we reconstruct from lzc_metrics.csv and pe_metrics.csv if they exist.
    """
    # Check for the combined complexity metrics file first (produced by analysis.py or features.py aggregation)
    combined_path = Path('data/processed/complexity_metrics.csv')
    lzc_path = Path('data/processed/lzc_metrics.csv')
    pe_path = Path('data/processed/pe_metrics.csv')
    
    if combined_path.exists():
        logger.info(f"Loading combined complexity metrics from {combined_path}")
        return pd.read_csv(combined_path)
    
    # Fallback: try to merge lzc and pe if they exist
    if lzc_path.exists() and pe_path.exists():
        logger.info("Merging LZC and PE metrics for collinearity analysis")
        df_lzc = pd.read_csv(lzc_path)
        df_pe = pd.read_csv(pe_path)
        
        # Pivot to wide format for merging
        df_lzc_wide = df_lzc.pivot(index='participant_id', columns='channel', values='lzc_value')
        df_pe_wide = df_pe.pivot(index='participant_id', columns='channel', values='pe_value')
        
        # Merge on participant_id
        merged = df_lzc_wide.join(df_pe_wide, lsuffix='_lzc', rsuffix='_pe')
        merged = merged.reset_index()
        
        logger.info(f"Merged dataset shape: {merged.shape}")
        return merged
    
    # If neither exists, we cannot proceed
    logger.error("Cannot find complexity metrics files (complexity_metrics.csv or lzc_metrics.csv + pe_metrics.csv).")
    logger.error("Ensure T014 and T015 have successfully generated the required CSVs.")
    sys.exit(1)

def calculate_vif(df, feature_columns):
    """
    Calculate Variance Inflation Factor (VIF) for a list of features.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing the features.
    feature_columns : list
        List of column names to calculate VIF for.
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with columns: ['feature', 'vif'].
    """
    # Select only the requested features
    X = df[feature_columns].copy()
    
    # Drop rows with NaN values in any of the selected features
    X = X.dropna()
    
    if X.empty:
        logger.warning("No valid data rows after dropping NaNs for VIF calculation.")
        return pd.DataFrame(columns=['feature', 'vif'])
    
    # Add constant for intercept
    X_const = add_constant(X)
    
    # Calculate VIF
    vif_data = []
    for i, col in enumerate(X_const.columns):
        if col == 'const':
            continue
        
        try:
            vif = variance_inflation_factor(X_const.values, i)
            vif_data.append({'feature': col, 'vif': vif})
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
            vif_data.append({'feature': col, 'vif': np.nan})
    
    return pd.DataFrame(vif_data)

def run_collinearity_diagnostics():
    """
    Main routine to run collinearity diagnostics.
    1. Load metrics.
    2. Identify numeric features (complexity metrics).
    3. Calculate VIF for all features.
    4. Check if any VIF >= 5 (threshold per SC-004).
    5. Save results to data/analysis/collinearity_report.json.
    """
    logger.info("Starting collinearity diagnostics.")
    
    # Load data
    df = load_analysis_results()
    
    # Identify numeric columns that are likely features (exclude participant_id if present)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if 'participant_id' in numeric_cols:
        numeric_cols.remove('participant_id')
    
    if not numeric_cols:
        logger.error("No numeric feature columns found in the dataset for VIF calculation.")
        # Write a failure report
        report = {
            "status": "fail",
            "message": "No numeric features found to calculate VIF.",
            "vif_results": []
        }
        save_collinearity_report(report)
        return report
    
    logger.info(f"Calculating VIF for {len(numeric_cols)} features: {numeric_cols}")
    
    vif_results = calculate_vif(df, numeric_cols)
    
    # Determine if collinearity is acceptable (VIF < 5)
    high_vif = vif_results[vif_results['vif'] >= 5]
    
    status = "pass" if high_vif.empty else "warning"
    
    report = {
        "status": status,
        "threshold": 5.0,
        "features_analyzed": len(numeric_cols),
        "high_vif_count": len(high_vif),
        "high_vif_features": high_vif['feature'].tolist() if not high_vif.empty else [],
        "vif_results": vif_results.to_dict(orient='records')
    }
    
    logger.info(f"Collinearity check complete. Status: {status}")
    if not high_vif.empty:
        logger.warning(f"Found {len(high_vif)} features with VIF >= 5: {high_vif['feature'].tolist()}")
    
    save_collinearity_report(report)
    return report

def save_collinearity_report(report):
    """Save the collinearity report to data/analysis/collinearity_report.json."""
    output_dir = Path('data/analysis')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / 'collinearity_report.json'
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Collinearity report saved to {output_path}")

def main():
    """Entry point for the collinearity diagnostics script."""
    try:
        load_config() # Just to ensure config exists, though not strictly used in VIF logic itself
        run_collinearity_diagnostics()
    except Exception as e:
        logger.error(f"Collinearity diagnostics failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
