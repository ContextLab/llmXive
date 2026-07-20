"""
Split Generator for MVP Testing (T013f).

Generates a random/mock split from the processed graphs parquet file.
Uses stratified sampling based on family_id to ensure reproducibility.
Overwrites data/processed/split_indices.json.

IMPORTANT: This is a mock split for MVP testing only. It does NOT satisfy
SC-002 (inter-family generalization).
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from sklearn.model_selection import train_test_split

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
RANDOM_STATE = 42
TEST_SIZE = 0.2
OUTPUT_PATH = Path("data/processed/split_indices.json")
INPUT_PATH = Path("data/processed/graphs_v1.parquet")


def load_graphs_from_parquet(path: Path) -> pd.DataFrame:
    """Load graphs from parquet file."""
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    
    logger.info(f"Loading graphs from {path}...")
    df = pd.read_parquet(path)
    logger.info(f"Loaded {len(df)} graphs.")
    return df


def generate_mock_split(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate a random stratified split based on family_id.
    
    Args:
        df: DataFrame containing graph data with 'family_id' column.
    
    Returns:
        Dictionary containing train and test indices.
    """
    if "family_id" not in df.columns:
        raise ValueError("DataFrame must contain 'family_id' column for stratification.")
    
    logger.info("Generating mock split with stratification by family_id...")
    
    # Create a temporary index column to track original positions
    df_temp = df.reset_index(drop=False)
    
    # Perform stratified split
    train_indices, test_indices = train_test_split(
        df_temp["index"],
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=df_temp["family_id"]
    )
    
    split_data = {
        "train_indices": train_indices.tolist(),
        "test_indices": test_indices.tolist(),
        "train_count": len(train_indices),
        "test_count": len(test_indices),
        "random_state": RANDOM_STATE,
        "test_size": TEST_SIZE,
        "stratify_by": "family_id",
        "disclaimer": "This is a mock split for MVP testing only. It does NOT satisfy SC-002 (inter-family generalization).",
        "metadata": {
            "total_entries": len(df),
            "unique_families_train": len(df_temp[df_temp["index"].isin(train_indices)]["family_id"].unique()),
            "unique_families_test": len(df_temp[df_temp["index"].isin(test_indices)]["family_id"].unique()),
        }
    }
    
    logger.info(f"Split generated: Train={split_data['train_count']}, Test={split_data['test_count']}")
    logger.info(f"Unique families - Train: {split_data['metadata']['unique_families_train']}, Test: {split_data['metadata']['unique_families_test']}")
    
    return split_data


def save_split(split_data: Dict[str, Any], output_path: Path) -> None:
    """Save split data to JSON file."""
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving split to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(split_data, f, indent=2)
    
    logger.info("Split saved successfully.")


def main() -> None:
    """Main entry point for the split generator."""
    parser = argparse.ArgumentParser(
        description="Generate a mock stratified split for MVP testing."
    )
    parser.add_argument(
        "--input",
        type=str,
        default=str(INPUT_PATH),
        help=f"Path to input parquet file (default: {INPUT_PATH})"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(OUTPUT_PATH),
        help=f"Path to output JSON file (default: {OUTPUT_PATH})"
    )
    
    args = parser.parse_args()
    
    try:
        input_path = Path(args.input)
        output_path = Path(args.output)
        
        # Load data
        df = load_graphs_from_parquet(input_path)
        
        # Generate split
        split_data = generate_mock_split(df)
        
        # Save split
        save_split(split_data, output_path)
        
        logger.info("MVP Split generation completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Value error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()