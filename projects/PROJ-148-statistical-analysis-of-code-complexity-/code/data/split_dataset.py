from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Tuple, Dict, Any

import pandas as pd

from utils.logging import get_logger
from utils.config import get_seed

logger = get_logger(__name__)


def get_split_proportions() -> Tuple[float, float]:
    """
    Returns the train/test split proportions.
    Based on project specs: 70% train, 30% test.
    """
    return 0.7, 0.3


def document_split_proportions(output_dir: Path) -> None:
    """
    Documents the split proportions in a JSON file within the output directory.
    """
    train_prop, test_prop = get_split_proportions()
    doc = {
        "train_proportion": train_prop,
        "test_proportion": test_prop,
        "description": "Project-level stratified split: 70% train, 30% test",
        "stratification_column": "project_id"
    }
    doc_path = output_dir / "split_config.json"
    with open(doc_path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2)
    logger.info(f"Split configuration documented at {doc_path}")


def perform_project_stratified_split(
    data: pd.DataFrame,
    train_ratio: float,
    seed: int,
    project_column: str = "project_id"
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Performs a project-level stratified train/test split.
    
    Ensures that all code units from a specific project appear in ONLY ONE split.
    This prevents data leakage where a model could 'see' a project during training
    and then be tested on the same project.
    
    Args:
        data: The full dataset containing at least 'project_id' and target column.
        train_ratio: Fraction of projects to assign to training (e.g., 0.7).
        seed: Random seed for reproducibility.
        project_column: The column name identifying the project (default: "project_id").
        
    Returns:
        Tuple of (train_df, test_df) DataFrames.
    """
    if project_column not in data.columns:
        raise ValueError(f"Column '{project_column}' not found in data. Available: {list(data.columns)}")
    
    # Get unique projects
    unique_projects = data[project_column].unique()
    
    if len(unique_projects) == 0:
        raise ValueError("No projects found in the dataset.")
        
    logger.info(f"Found {len(unique_projects)} unique projects for stratified split.")
    
    # Shuffle projects deterministically
    import numpy as np
    rng = np.random.default_rng(seed)
    shuffled_projects = rng.permutation(unique_projects).tolist()
    
    # Calculate split index
    split_idx = int(len(shuffled_projects) * train_ratio)
    
    train_projects = set(shuffled_projects[:split_idx])
    test_projects = set(shuffled_projects[split_idx:])
    
    logger.info(f"Assigning {len(train_projects)} projects to train, {len(test_projects)} to test.")
    
    # Split the dataframe based on project membership
    train_df = data[data[project_column].isin(train_projects)].copy()
    test_df = data[data[project_column].isin(test_projects)].copy()
    
    # Verification: Ensure no project appears in both splits
    train_proj_set = set(train_df[project_column].unique())
    test_proj_set = set(test_df[project_column].unique())
    
    intersection = train_proj_set.intersection(test_proj_set)
    if intersection:
        raise AssertionError(f"Data leakage detected! Projects in both splits: {intersection}")
        
    logger.info("Verification passed: No project appears in both splits.")
    
    return train_df, test_df


def main() -> None:
    """
    CLI entry point to perform the project-level stratified split.
    
    Usage:
        python code/data/split_dataset.py \
            --input data/preprocessed_data.csv \
            --output-dir data/splits
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Perform project-level stratified train/test split")
    parser.add_argument("--input", required=True, help="Path to the preprocessed CSV data")
    parser.add_argument("--output-dir", required=True, help="Directory to save train/test splits")
    parser.add_argument("--project-column", default="project_id", help="Column name for project ID")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    # Load data
    logger.info(f"Loading data from {args.input}")
    if not os.path.exists(args.input):
        raise FileNotFoundError(f"Input file not found: {args.input}")
        
    df = pd.read_csv(args.input)
    logger.info(f"Loaded {len(df)} rows.")
    
    # Perform split
    train_ratio, _ = get_split_proportions()
    train_df, test_df = perform_project_stratified_split(
        df, 
        train_ratio=train_ratio, 
        seed=args.seed, 
        project_column=args.project_column
    )
    
    # Ensure output directory exists
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save splits
    train_path = output_path / "train.csv"
    test_path = output_path / "test.csv"
    
    logger.info(f"Saving train set ({len(train_df)} rows) to {train_path}")
    train_df.to_csv(train_path, index=False)
    
    logger.info(f"Saving test set ({len(test_df)} rows) to {test_path}")
    test_df.to_csv(test_path, index=False)
    
    # Document the split configuration
    document_split_proportions(output_path)
    
    logger.info("Split completed successfully.")


if __name__ == "__main__":
    main()