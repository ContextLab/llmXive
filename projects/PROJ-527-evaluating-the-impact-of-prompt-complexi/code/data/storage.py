from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd

from config import Paths
from models.data_models import PromptVariant, GeneratedCode
from utils.logger import get_logger

logger = get_logger(__name__)


def save_variants_to_parquet(
    variants: List[Dict[str, Any]],
    generated_codes: List[Dict[str, Any]],
    output_path: Optional[Path] = None,
) -> Path:
    """
    Combine prompt variants and generated code metadata into a single DataFrame
    and write to a Parquet file.

    Args:
        variants: List of dictionaries representing PromptVariant objects.
        generated_codes: List of dictionaries representing GeneratedCode objects.
        output_path: Optional explicit path. If None, uses default from Paths.

    Returns:
        Path to the written file.
    """
    if output_path is None:
        output_path = Paths.PROCESSED_DIR / "prompt_variants.parquet"

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not variants:
        logger.warning("No variants provided to save.")
        # Create an empty DataFrame with expected schema if possible, or just return
        # For robustness, we create an empty DF with common columns if data is missing
        df = pd.DataFrame(columns=[
            "variant_id", "problem_id", "variant_label", "prompt_text",
            "token_count", "examples_count", "constraints_count", "steps_count",
            "dependency_depth", "code_id", "generated_code", "generation_metadata"
        ])
        df.to_parquet(output_path, index=False)
        logger.info(f"Empty parquet file written to {output_path}")
        return output_path

    # Normalize data
    # We expect variants and generated_codes to be aligned by index or merged by variant_id
    # Assuming generated_codes[i] corresponds to variants[i] based on orchestrator logic
    # If not, we would need a merge on variant_id, but the orchestrator likely emits them in pairs.
    # To be safe, we will construct rows by zipping if lengths match, or warning otherwise.

    if len(variants) != len(generated_codes):
        logger.warning(
            f"Mismatch in variant count ({len(variants)}) and code count ({len(generated_codes)}). "
            "Attempting to match by index; missing codes will be null."
        )

    rows = []
    for i, v in enumerate(variants):
        code_data = generated_codes[i] if i < len(generated_codes) else None

        row = {
            "variant_id": v.get("variant_id"),
            "problem_id": v.get("problem_id"),
            "variant_label": v.get("complexity_label"),
            "prompt_text": v.get("prompt_text"),
            "token_count": v.get("token_count"),
            "examples_count": v.get("structural_element_count", {}).get("examples", 0),
            "constraints_count": v.get("structural_element_count", {}).get("constraints", 0),
            "steps_count": v.get("structural_element_count", {}).get("steps", 0),
            "dependency_depth": v.get("dependency_depth", 0),
            "code_id": code_data.get("code_id") if code_data else None,
            "generated_code": code_data.get("code") if code_data else None,
            "generation_metadata": code_data.get("generation_metadata") if code_data else None,
        }
        rows.append(row)

    df = pd.DataFrame(rows)

    # Convert nested dicts to strings for Parquet compatibility if necessary
    # Pandas usually handles dicts in object columns, but explicit conversion ensures safety
    if "generation_metadata" in df.columns:
        df["generation_metadata"] = df["generation_metadata"].apply(
            lambda x: x if isinstance(x, str) else str(x) if x is not None else None
        )

    df.to_parquet(output_path, index=False)
    logger.info(f"Saved {len(df)} records to {output_path}")
    return output_path


def load_variants_from_parquet(
    input_path: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Load prompt variants and generated code from the Parquet file.

    Args:
        input_path: Optional explicit path. If None, uses default from Paths.

    Returns:
        Pandas DataFrame containing the data.
    """
    if input_path is None:
        input_path = Paths.PROCESSED_DIR / "prompt_variants.parquet"

    if not input_path.exists():
        raise FileNotFoundError(f"Parquet file not found at {input_path}")

    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} records from {input_path}")
    return df


def get_variant_counts_by_complexity(
    df: pd.DataFrame,
) -> Dict[str, int]:
    """
    Count the number of variants per complexity label.

    Args:
        df: DataFrame loaded from prompt_variants.parquet.

    Returns:
        Dictionary mapping complexity_label to count.
    """
    if df.empty:
        return {}
    counts = df["variant_label"].value_counts().to_dict()
    logger.info(f"Variant counts by complexity: {counts}")
    return counts


def main() -> None:
    """
    Main entry point for testing storage functionality.
    In a real pipeline, this would be called by the orchestrator after generation.
    This function demonstrates the save/load cycle with dummy data if no real data is passed,
    but strictly speaking, it should be invoked by the orchestrator with real data.
    For the purpose of this task, we ensure the function exists and is callable.
    """
    logger.info("Storage module main() called.")
    # This script is primarily a library for the orchestrator.
    # If invoked directly, it might be for testing.
    # We will not generate synthetic data here to avoid fabrication.
    # The orchestrator (T017) is responsible for calling save_variants_to_parquet.
    logger.info("Storage module ready. Call save_variants_to_parquet with real data.")


if __name__ == "__main__":
    main()
