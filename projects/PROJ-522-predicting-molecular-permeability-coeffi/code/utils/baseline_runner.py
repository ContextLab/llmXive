"""
Utility script to orchestrate baseline training using the BaselineTrainer.
This serves as a wrapper for the training loop logic.
"""
import logging
from pathlib import Path
import pandas as pd
from models.baselines import BaselineTrainer, RandomForestBaseline, LinearRegressionBaseline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_baselines(input_csv: str, output_csv: str, n_splits: int = 5) -> None:
    """
    Run baseline training loop on the provided dataset.

    Args:
        input_csv: Path to the processed dataset (e.g., merged_dataset.csv)
        output_csv: Path to save predictions
        n_splits: Number of CV folds
    """
    logger.info(f"Starting baseline training from {input_csv}")
    
    # Load data to verify columns
    df = pd.read_csv(input_csv)
    
    # Assume standard columns from ingestion pipeline
    feature_cols = [col for col in df.columns if col not in ['smiles', 'source_id', 'target_mean', 'count']]
    target_col = 'target_mean'

    if target_col not in df.columns:
        raise ValueError(f"Expected target column '{target_col}' not found in {input_csv}")
    
    trainer = BaselineTrainer(output_path=output_csv)
    trainer.run_from_dataset(
        input_path=input_csv,
        feature_cols=feature_cols,
        target_col=target_col,
        n_splits=n_splits
    )
    logger.info("Baseline training completed.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/processed/merged_dataset.csv")
    parser.add_argument("--output", default="data/processed/baseline_predictions.csv")
    parser.add_argument("--splits", type=int, default=5)
    args = parser.parse_args()
    run_baselines(args.input, args.output, args.splits)
