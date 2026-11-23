import sys
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd
import json

from src.config import DATA_PROCESSED_PATH, DATA_RAW_PATH
from src.utils.logging import get_logger, setup_log_file

logger = get_logger(__name__)

def merge_datasets(features_df: pd.DataFrame, scores_df: pd.DataFrame) -> pd.DataFrame:
    """
    Joins the feature dataframe and the ISG score dataframe on the 'strain_accession' column.
    
    Pre-conditions:
      - T018a, T018b, T018c, T018d, T020 must be completed (features_df populated).
      - T016 must be completed (scores_df populated).
    
    Args:
        features_df: DataFrame containing viral genomic features (k-mers, GC, stability, etc.)
                     with a 'strain_accession' column.
        scores_df: DataFrame containing ISG scores with a 'strain_accession' column.
    
    Returns:
        pd.DataFrame: The merged dataset containing all features and the target ISG score.
    
    Side Effects:
        Saves the resulting DataFrame to `data/processed/merged_dataset.csv`.
    
    Raises:
        ValueError: If 'strain_accession' is missing in either input.
        RuntimeError: If the merge results in fewer than 30 samples (FR-013).
    """
    if 'strain_accession' not in features_df.columns:
        raise ValueError("features_df must contain 'strain_accession' column")
    if 'strain_accession' not in scores_df.columns:
        raise ValueError("scores_df must contain 'strain_accession' column")

    logger.info(f"Starting merge: features_df shape {features_df.shape}, scores_df shape {scores_df.shape}")
    
    # Perform inner join to ensure only valid strain links are kept
    merged_df = pd.merge(
        features_df,
        scores_df,
        on='strain_accession',
        how='inner'
    )
    
    logger.info(f"Merged dataset shape: {merged_df.shape}")
    
    # Validate minimum sample count per FR-013
    if len(merged_df) < 30:
        error_msg = f"FR-013 Violation: Merged dataset has {len(merged_df)} samples, which is less than the required minimum of 30."
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    # Ensure output directory exists
    processed_path = Path(DATA_PROCESSED_PATH)
    processed_path.mkdir(parents=True, exist_ok=True)
    
    output_file = processed_path / "merged_dataset.csv"
    merged_df.to_csv(output_file, index=False)
    logger.info(f"Saved merged dataset to {output_file}")
    
    return merged_df

def aggregate_by_strain(merged_df: pd.DataFrame) -> pd.DataFrame:
    """
    Groups the merged dataset by 'strain_accession' and averages the 'isg_score' column.
    
    Pre-condition: T021 completed. Input: data/processed/merged_dataset.csv.
    
    Args:
        merged_df: The merged dataset from merge_datasets.
    
    Returns:
        pd.DataFrame: Aggregated dataset with one row per strain.
    
    Side Effects:
        Saves the resulting DataFrame to `data/processed/aggregated_dataset.csv`.
    """
    logger.info("Aggregating data by strain...")
    
    if 'strain_accession' not in merged_df.columns:
        raise ValueError("Input DataFrame must contain 'strain_accession' column")
    if 'isg_score' not in merged_df.columns:
        raise ValueError("Input DataFrame must contain 'isg_score' column")
    
    # Group by strain and aggregate. We assume other feature columns are constant per strain
    # or we just take the first value for them, but specifically average the isg_score.
    # If features vary per sample of the same strain, this task implies averaging the target.
    # Standard approach: group by strain, take mean of numeric columns.
    
    aggregated_df = merged_df.groupby('strain_accession', as_index=False).mean(numeric_only=True)
    
    # Ensure isg_score is explicitly averaged (mean is default for numeric_only=True)
    # If there are non-numeric columns that should be preserved (e.g. virus family),
    # we might need a more complex aggregation, but for now mean(numeric_only=True) is safe for the target.
    
    processed_path = Path(DATA_PROCESSED_PATH)
    output_file = processed_path / "aggregated_dataset.csv"
    aggregated_df.to_csv(output_file, index=False)
    logger.info(f"Saved aggregated dataset to {output_file}")
    
    return aggregated_df

def log_metrics(metrics: dict) -> None:
    """
    Writes metrics dict to `data/artifacts/metrics.json`.
    
    Args:
        metrics: Dictionary containing r2, rmse, permutation_pvalue, fdr_min_pvalue.
    """
    artifacts_path = Path(DATA_PROCESSED_PATH).parent / "artifacts"
    artifacts_path.mkdir(parents=True, exist_ok=True)
    
    output_file = artifacts_path / "metrics.json"
    with open(output_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {output_file}")

def run_pipeline():
    """
    Orchestrates the full data processing pipeline for User Story 1.
    """
    setup_log_file()
    logger.info("Pipeline started.")
    
    # Placeholder for loading data - in a real run, these would be loaded from disk
    # or passed as arguments. For this task implementation, we assume the caller
    # provides the dataframes or we load them from the expected locations if they exist.
    # However, the task specifically asks to implement the function that joins them.
    # To make this runnable as a script that produces the output, we simulate
    # loading the intermediate artifacts created by T016 and T018-T020.
    
    # Since T018-T020 and T016 are marked complete, we assume their outputs exist.
    # We will attempt to load them. If they don't exist, the script will fail loudly.
    
    try:
        # Load ISG Scores (Output of T016)
        scores_path = Path(DATA_PROCESSED_PATH) / "isg_scores.csv"
        if not scores_path.exists():
            raise FileNotFoundError(f"Expected ISG scores at {scores_path}. Has T016 run?")
        scores_df = pd.read_csv(scores_path)
        
        # Load Features (Output of T018-T020)
        # We assume features were saved to a single file or need to be merged first.
        # Based on typical pipelines, T018-T020 likely wrote to a features file.
        # Let's assume a combined features file exists or we construct it.
        # For this specific task, we assume a file 'features.csv' exists from previous steps.
        features_path = Path(DATA_PROCESSED_PATH) / "features.csv"
        if not features_path.exists():
            # Fallback: try to load individual feature files if they exist, but 
            # the task description implies a single features_df input.
            # We'll raise an error if the expected combined file is missing.
            raise FileNotFoundError(f"Expected combined features at {features_path}. Has T018-T020 run?")
        
        features_df = pd.read_csv(features_path)
        
        # Execute Merge
        merged_df = merge_datasets(features_df, scores_df)
        
        # Execute Aggregate
        aggregate_by_strain(merged_df)
        
        logger.info("Pipeline completed successfully.")
        
    except FileNotFoundError as e:
        logger.critical(f"Data not found: {e}")
        sys.exit(1)
    except RuntimeError as e:
        logger.critical(f"Validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_pipeline()
