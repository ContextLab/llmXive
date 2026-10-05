import os
import sys
import logging
import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import spearmanr
from statsmodels.stats.multitest import multipletests

# Import utilities from sibling modules as per API surface
from utils.logging import get_logger, setup_logging
from utils.resource_guard import check_cpu_only, enforce_resource_limits

# Configure logging
logger = get_logger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
RUN_LOG_PATH = DATA_PROCESSED / "run.log"

def load_preprocessed_data():
    """Load the rarefied genus table and cognitive scores."""
    input_path = DATA_PROCESSED / "rarefied_genus_table.parquet"
    if not input_path.exists():
        raise FileNotFoundError(f"Preprocessed data not found at {input_path}. Run preprocessing first.")
    
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded preprocessed data with shape {df.shape}")
    return df

def clr_transform(data_df):
    """
    Perform Centered Log-Ratio (CLR) transformation.
    Adds a small pseudo-count to avoid log(0).
    """
    # Ensure no zeros before log transform
    pseudo_count = 1e-6
    data_clean = data_df + pseudo_count
    
    # Calculate geometric mean for each sample (row)
    # axis=1 for row-wise calculation
    geo_mean = np.exp(np.log(data_clean).mean(axis=1))
    
    # CLR transform: log(x_i / geo_mean)
    clr_data = np.log(data_clean / geo_mean.values[:, np.newaxis])
    
    return pd.DataFrame(clr_data, index=data_df.index, columns=data_df.columns)

def calculate_spearman_correlations(genus_df, cognitive_series):
    """
    Calculate Spearman rank correlation between each genus and cognitive score.
    Returns a DataFrame with rho and raw p-value.
    """
    results = []
    for genus in genus_df.columns:
        rho, p_val = spearmanr(genus_df[genus], cognitive_series)
        results.append({
            'genus': genus,
            'rho': rho,
            'p_value': p_val
        })
    
    return pd.DataFrame(results)

def apply_fdr_correction(correlation_df, alpha=0.05):
    """
    Apply Benjamini-Hochberg FDR correction to raw p-values.
    Returns DataFrame with adjusted p-values.
    """
    p_values = correlation_df['p_value'].values
    reject, p_adj, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')
    
    correlation_df['adj_p_value'] = p_adj
    correlation_df['significant'] = reject
    
    logger.info(f"FDR correction applied. {reject.sum()} significant associations found at alpha={alpha}.")
    return correlation_df

def filter_significant_associations(correlation_df, alpha=0.05):
    """
    Filter for significant associations (adj-p < 0.05) and label them as "associational".
    """
    significant_df = correlation_df[correlation_df['adj_p_value'] < alpha].copy()
    
    # Add the interpretation column as required by T024
    significant_df['interpretation'] = "associational"
    
    logger.info(f"Filtered {len(significant_df)} significant associations. Added 'interpretation' column.")
    return significant_df

def generate_summary_report(significant_df, output_path):
    """
    Generate summary report of significant genus-score pairs.
    """
    significant_df.to_csv(output_path, index=False)
    logger.info(f"Summary report saved to {output_path}")
    return significant_df

def run_analysis_pipeline():
    """Main pipeline execution for User Story 2."""
    # Resource checks
    check_cpu_only()
    enforce_resource_limits()

    # Setup logging
    setup_logging(log_file=RUN_LOG_PATH)
    logger.info("Starting correlation analysis pipeline (US2)")

    # 1. Load data
    df = load_preprocessed_data()
    
    # Assume the last column is cognitive score or we need to identify it
    # Based on typical pipeline, let's assume 'cognitive_score' column exists
    # If not, we might need to infer from the data structure
    if 'cognitive_score' not in df.columns:
        # Fallback: assume the last column is the target if named differently
        # This is a heuristic; in a real scenario, column names should be explicit
        logger.warning("'cognitive_score' column not found. Attempting to identify target column.")
        # For this implementation, we'll assume the column is named 'cognitive_score'
        # If the data model is different, this would need adjustment
        raise ValueError("Cognitive score column 'cognitive_score' not found in dataset.")

    cognitive_series = df['cognitive_score']
    genus_df = df.drop(columns=['cognitive_score'])

    # 2. CLR Transform
    logger.info("Applying CLR transformation...")
    clr_genus_df = clr_transform(genus_df)

    # 3. Calculate Correlations
    logger.info("Calculating Spearman correlations...")
    corr_results = calculate_spearman_correlations(clr_genus_df, cognitive_series)

    # 4. FDR Correction
    logger.info("Applying FDR correction...")
    corr_results = apply_fdr_correction(corr_results)

    # 5. Filter and Flag Significant Associations (T024)
    logger.info("Filtering significant associations and labeling as 'associational'...")
    significant_results = filter_significant_associations(corr_results)

    # 6. Generate Report
    output_path = DATA_PROCESSED / "correlation_results.csv"
    generate_summary_report(significant_results, output_path)

    # Log the "associational" framing explicitly (T024b)
    logger.info("Framing: All reported associations are 'associational' (not causal).")

    logger.info("Correlation analysis pipeline completed successfully.")
    return significant_results

def main():
    """Entry point for the script."""
    try:
        run_analysis_pipeline()
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()