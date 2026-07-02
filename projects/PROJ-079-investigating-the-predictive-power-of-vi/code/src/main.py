import sys
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd
import json
from src.config import SEED, MAX_RUNTIME_HOURS, ARTIFACTS_PATH, DATA_PROCESSED_PATH

logger = logging.getLogger(__name__)

def merge_datasets(features_df: pd.DataFrame, scores_df: pd.DataFrame, codon_bias_df: pd.DataFrame) -> pd.DataFrame:
    """
    Joins features, ISG scores, and codon bias on strain_accession.
    Pre-condition: T018c completed. Input: data/processed/features.csv, data/processed/isg_scores.csv, data/processed/host_codon_bias.csv.
    """
    logger.info("Merging datasets on strain_accession...")
    # Ensure all are DataFrames
    if not isinstance(features_df, pd.DataFrame):
        raise TypeError("features_df must be a DataFrame")
    if not isinstance(scores_df, pd.DataFrame):
        raise TypeError("scores_df must be a DataFrame")
    if not isinstance(codon_bias_df, pd.DataFrame):
        raise TypeError("codon_bias_df must be a DataFrame")

    # Validate required columns
    for df, name in [(features_df, "features"), (scores_df, "scores"), (codon_bias_df, "codon_bias")]:
        if "strain_accession" not in df.columns:
            raise ValueError(f"{name} dataframe missing 'strain_accession' column")

    # Merge
    merged = features_df.merge(scores_df, on="strain_accession", how="inner")
    merged = merged.merge(codon_bias_df, on="strain_accession", how="inner")

    logger.info(f"Merged dataset shape: {merged.shape}")
    return merged

def aggregate_by_strain(merged_df: pd.DataFrame) -> pd.DataFrame:
    """
    Groups by strain_accession and averages the isg_score column.
    Pre-condition: T021 completed. Input: data/processed/merged_dataset.csv.
    """
    logger.info("Aggregating by strain...")
    if "isg_score" not in merged_df.columns:
        raise ValueError("Input dataframe missing 'isg_score' column")
    if "strain_accession" not in merged_df.columns:
        raise ValueError("Input dataframe missing 'strain_accession' column")

    # Group by strain and average isg_score, keep first occurrence of other columns
    agg_dict = {col: 'first' for col in merged_df.columns if col not in ['strain_accession', 'isg_score']}
    agg_dict['isg_score'] = 'mean'

    aggregated = merged_df.groupby('strain_accession').agg(agg_dict).reset_index()
    logger.info(f"Aggregated dataset shape: {aggregated.shape}")
    return aggregated

def log_metrics(metrics: dict) -> None:
    """
    Writes metrics dict to data/artifacts/metrics.json with keys: r2, rmse, permutation_pvalue, fdr_min_pvalue.
    """
    logger.info("Logging metrics to artifacts...")
    
    required_keys = {'r2', 'rmse', 'permutation_pvalue', 'fdr_min_pvalue'}
    if not required_keys.issubset(metrics.keys()):
        missing = required_keys - set(metrics.keys())
        raise ValueError(f"Metrics dict missing required keys: {missing}")

    output_path = Path(ARTIFACTS_PATH) / "metrics.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Add timestamp for provenance
    metrics_with_meta = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "seed": SEED,
        **metrics
    }

    with open(output_path, 'w') as f:
        json.dump(metrics_with_meta, f, indent=2)

    logger.info(f"Metrics saved to {output_path}")

def run_pipeline():
    """
    Main entry point for the pipeline.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger.info("Starting pipeline...")
    # Placeholder for full pipeline execution logic
    logger.info("Pipeline finished.")

if __name__ == "__main__":
    run_pipeline()