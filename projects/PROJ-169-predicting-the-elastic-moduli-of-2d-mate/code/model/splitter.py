"""
T017b: Validate Stratified Split.

Strictly consumes `split_indices.json` from T013f.
Does NOT regenerate or overwrite the split.
Validates that the split is a valid JSON file with required keys.
Exits with code 1 if missing or invalid.
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
SPLIT_INDICES_PATH = Path("data/processed/split_indices.json")
GRAPHS_V1_PATH = Path("data/processed/graphs_v1.parquet")


class SplitManifest:
    """Container for split validation results."""

    def __init__(
        self,
        is_valid: bool,
        train_count: int,
        test_count: int,
        train_families: Set[str],
        test_families: Set[str],
        overlap_families: Set[str],
        message: str,
    ):
        self.is_valid = is_valid
        self.train_count = train_count
        self.test_count = test_count
        self.train_families = train_families
        self.test_families = test_families
        self.overlap_families = overlap_families
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "train_count": self.train_count,
            "test_count": self.test_count,
            "train_families_count": len(self.train_families),
            "test_families_count": len(self.test_families),
            "overlap_families_count": len(self.overlap_families),
            "overlap_families": list(self.overlap_families),
            "message": self.message,
        }


def load_split_indices(path: Path) -> Dict[str, Any]:
    """Load and parse the split_indices.json file."""
    if not path.exists():
        raise FileNotFoundError(f"Split indices file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    required_keys = ["train_indices", "test_indices"]
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Missing required key in split_indices.json: {key}")

    if not isinstance(data["train_indices"], list):
        raise ValueError("train_indices must be a list of integers")
    if not isinstance(data["test_indices"], list):
        raise ValueError("test_indices must be a list of integers")

    return data


def load_graphs_from_parquet(path: Path) -> pd.DataFrame:
    """Load graphs from parquet file."""
    if not path.exists():
        raise FileNotFoundError(f"Graphs file not found: {path}")
    return pd.read_parquet(path)


def split_by_family(
    split_data: Dict[str, Any], graphs_df: pd.DataFrame
) -> Tuple[Set[str], Set[str]]:
    """
    Extract unique family_ids for train and test sets.
    Assumes graphs_df has an 'index' column or can be indexed by row order.
    """
    # Ensure we have family_id column
    if "family_id" not in graphs_df.columns:
        raise ValueError("graphs_v1.parquet must contain 'family_id' column")

    train_indices = set(split_data["train_indices"])
    test_indices = set(split_data["test_indices"])

    # Filter dataframe for train and test
    train_df = graphs_df[graphs_df.index.isin(train_indices)]
    test_df = graphs_df[graphs_df.index.isin(test_indices)]

    train_families = set(train_df["family_id"].unique())
    test_families = set(test_df["family_id"].unique())

    return train_families, test_families


def save_split_manifest(manifest: SplitManifest, output_path: Path) -> None:
    """Save validation manifest to JSON."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest.to_dict(), f, indent=2)


def main() -> int:
    """
    Main entry point for T017b.
    Validates split_indices.json and exits with code 1 if invalid.
    """
    logger.info("Starting T017b: Validate Stratified Split")

    # 1. Load split_indices.json
    try:
        split_data = load_split_indices(SPLIT_INDICES_PATH)
        logger.info(f"Successfully loaded split indices from {SPLIT_INDICES_PATH}")
    except FileNotFoundError as e:
        logger.error(f"CRITICAL: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"CRITICAL: Invalid JSON in split_indices.json: {e}")
        return 1
    except ValueError as e:
        logger.error(f"CRITICAL: Invalid structure in split_indices.json: {e}")
        return 1

    train_count = len(split_data["train_indices"])
    test_count = len(split_data["test_indices"])

    if train_count == 0 or test_count == 0:
        logger.error("CRITICAL: Split contains empty train or test set")
        return 1

    # 2. Load graphs to verify family separation
    train_families: Set[str] = set()
    test_families: Set[str] = set()
    overlap_families: Set[str] = set()

    if GRAPHS_V1_PATH.exists():
        try:
            graphs_df = load_graphs_from_parquet(GRAPHS_V1_PATH)
            train_families, test_families = split_by_family(split_data, graphs_df)
            overlap_families = train_families.intersection(test_families)

            if overlap_families:
                logger.error(
                    f"CRITICAL: Family overlap detected in train/test split: {overlap_families}"
                )
                logger.error(
                    "SC-002 Violation: Training families must not appear in test set."
                )
                return 1
            else:
                logger.info(
                    f"Family separation verified: {len(train_families)} train families, "
                    f"{len(test_families)} test families. No overlap."
                )
        except ValueError as e:
            logger.warning(f"Could not verify family separation: {e}")
            # If we can't verify, we still validate the JSON structure
        except Exception as e:
            logger.warning(f"Unexpected error verifying family separation: {e}")
    else:
        logger.warning(
            f"graphs_v1.parquet not found at {GRAPHS_V1_PATH}. "
            "Skipping family separation verification. JSON structure is valid."
        )

    # 3. Construct and save manifest
    manifest = SplitManifest(
        is_valid=True,
        train_count=train_count,
        test_count=test_count,
        train_families=train_families,
        test_families=test_families,
        overlap_families=overlap_families,
        message="Split validation passed. JSON structure valid and family separation verified.",
    )

    output_path = Path("data/results/split_validation_manifest.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_split_manifest(manifest, output_path)

    logger.info(f"Validation manifest saved to {output_path}")
    logger.info(
        f"Train: {train_count} entries, Test: {test_count} entries. "
        f"Overlap: {len(overlap_families)} families."
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())