"""
Generate MVP Split for testing.

This script consumes the processed graph data from T013d and generates a
random/mock split for MVP testing purposes only. It uses stratified splitting
based on family_id to ensure reproducibility, but explicitly does NOT satisfy
the inter-family generalization constraint (SC-002).
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
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

INPUT_PATH = "data/processed/graphs_v1.parquet"
OUTPUT_PATH = "data/processed/split_indices.json"
RANDOM_STATE = 42


def load_graphs_from_parquet(path: Path) -> pd.DataFrame:
    """Load graphs from parquet file."""
    if not path.exists():
        logger.error(f"Input file not found: {path}")
        sys.exit(1)

    try:
        df = pd.read_parquet(path)
        logger.info(f"Loaded {len(df)} graphs from {path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load parquet file: {e}")
        sys.exit(1)


def generate_mock_split(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = RANDOM_STATE,
) -> Dict[str, Any]:
    """
    Generate a random stratified split based on family_id.

    This is a MOCK split for MVP testing only. It does NOT satisfy SC-002
    (inter-family generalization) because it randomly splits families,
    meaning some families may appear in both train and test sets.
    """
    if "family_id" not in df.columns:
        logger.error("DataFrame must contain 'family_id' column for stratification")
        sys.exit(1)

    # Perform stratified split based on family_id
    train_indices, test_indices = train_test_split(
        df.index.tolist(),
        test_size=test_size,
        random_state=random_state,
        stratify=df["family_id"].tolist(),
    )

    split_manifest = {
        "metadata": {
            "description": "This is a mock split for MVP testing only. It does NOT satisfy SC-002 (inter-family generalization).",
            "split_strategy": "random_stratified_by_family",
            "random_state": random_state,
            "test_size": test_size,
            "generated_by": "code/ingest/split_generator.py",
        },
        "train_indices": train_indices,
        "test_indices": test_indices,
        "counts": {
            "train_count": len(train_indices),
            "test_count": len(test_indices),
            "total_count": len(df),
        },
    }

    return split_manifest


def save_split_manifest(manifest: Dict[str, Any], output_path: Path) -> None:
    """Save the split manifest to a JSON file."""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Split manifest saved to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save split manifest: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point for the split generator."""
    parser = argparse.ArgumentParser(
        description="Generate a mock stratified split for MVP testing."
    )
    parser.add_argument(
        "--input",
        type=str,
        default=INPUT_PATH,
        help=f"Path to input parquet file (default: {INPUT_PATH})",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=OUTPUT_PATH,
        help=f"Path to output JSON file (default: {OUTPUT_PATH})",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Fraction of data to use for testing (default: 0.2)",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=RANDOM_STATE,
        help="Random state for reproducibility (default: 42)",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    logger.info("Starting MVP split generation...")

    # Load data
    df = load_graphs_from_parquet(input_path)

    # Generate split
    split_manifest = generate_mock_split(
        df, test_size=args.test_size, random_state=args.random_state
    )

    # Save split
    save_split_manifest(split_manifest, output_path)

    logger.info("MVP split generation completed successfully.")


if __name__ == "__main__":
    main()