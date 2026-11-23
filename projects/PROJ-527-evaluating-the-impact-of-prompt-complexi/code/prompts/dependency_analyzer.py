from __future__ import annotations

import re
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from pathlib import Path

from models.data_models import PromptVariant
from utils.logger import get_logger
from config import Paths

logger = get_logger(__name__)

# Regex pattern to identify instruction references that imply sequential dependency
# Matches keywords like 'First:', 'Next:', 'Step:', 'Constraint:', 'Then:', 'If:', 'When:', 'Also:', 'Furthermore:'
INSTRUCTION_REF_PATTERN = re.compile(
    r'(First|Next|Step|Constraint|Then|If|When|Also|Furthermore)[:\s]',
    re.IGNORECASE
)

def calculate_dependency_depth(prompt_text: str) -> int:
    """
    Calculate the maximum dependency chain depth for a given prompt text.

    Algorithm:
    1. Identify all instruction reference blocks using regex.
    2. Build a directed graph where nodes are instruction blocks.
    3. Edges represent sequential flow (index i -> index i+1).
    4. The depth is the length of the longest path (number of nodes in the chain).
    5. If no matches are found, return 0.

    Args:
        prompt_text: The full text of the prompt variant.

    Returns:
        The maximum dependency chain depth (int).
    """
    if not prompt_text or not isinstance(prompt_text, str):
        return 0

    matches = list(INSTRUCTION_REF_PATTERN.finditer(prompt_text))

    if not matches:
        return 0

    # Each match represents a node in the dependency chain.
    # Since the instructions are sequential in the text, the chain is linear.
    # The depth is simply the number of identified instruction blocks.
    # This represents the "depth" of the state transition chain induced by the prompt.
    return len(matches)

def analyze_variant_depth(variant: PromptVariant) -> int:
    """
    Analyze a single PromptVariant to determine its dependency depth.

    Args:
        variant: A PromptVariant object containing the prompt text.

    Returns:
        The calculated dependency depth.
    """
    return calculate_dependency_depth(variant.prompt_text)

def update_variants_with_depth(variants_df: pd.DataFrame) -> pd.DataFrame:
    """
    Update a DataFrame of prompt variants with a new 'dependency_depth' column.

    Args:
        variants_df: DataFrame containing prompt variants (expected to have 'prompt_text' or 'prompt' column).

    Returns:
        DataFrame with the new 'dependency_depth' column added.
    """
    if variants_df.empty:
        logger.warning("Input DataFrame is empty. Returning empty DataFrame.")
        return variants_df

    # Determine the correct column name for the prompt text
    prompt_col = 'prompt_text' if 'prompt_text' in variants_df.columns else 'prompt'
    if prompt_col not in variants_df.columns:
        raise ValueError(f"Input DataFrame missing required column: {prompt_col}")

    logger.info(f"Calculating dependency depth for {len(variants_df)} variants...")

    depths = []
    for idx, row in variants_df.iterrows():
        prompt_text = row[prompt_col]
        depth = calculate_dependency_depth(prompt_text)
        depths.append(depth)

        # Log a sample of depths for verification
        if idx < 5 or idx % 100 == 0:
            logger.debug(f"Variant ID {row.get('variant_id', idx)}: depth={depth}")

    variants_df['dependency_depth'] = depths
    logger.info(f"Dependency depth calculation complete. Max depth: {max(depths) if depths else 0}")

    return variants_df

def main():
    """
    Main entry point for the dependency analyzer.
    Reads prompt variants from data/processed/prompt_variants.parquet,
    calculates dependency depth, and writes the updated DataFrame back.
    """
    input_path = Paths.PROCESSED_DATA_DIR / "prompt_variants.parquet"
    output_path = Paths.PROCESSED_DATA_DIR / "prompt_variants.parquet"

    logger.info(f"Starting Dependency Chain Depth Analysis (Task T062).")
    logger.info(f"Input file: {input_path}")

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    try:
        # Load the data
        df = pd.read_parquet(input_path)
        logger.info(f"Loaded {len(df)} variants from {input_path}")

        # Update with depth
        updated_df = update_variants_with_depth(df)

        # Write back to the same file (overwriting) to persist the new column
        updated_df.to_parquet(output_path, index=False)
        logger.info(f"Successfully updated and saved to {output_path}")

        # Verify the column exists
        if 'dependency_depth' not in updated_df.columns:
            raise RuntimeError("Failed to add 'dependency_depth' column to DataFrame.")

        # Log summary statistics
        logger.info(f"Dependency Depth Statistics:")
        logger.info(f"  Min: {updated_df['dependency_depth'].min()}")
        logger.info(f"  Max: {updated_df['dependency_depth'].max()}")
        logger.info(f"  Mean: {updated_df['dependency_depth'].mean():.2f}")

    except Exception as e:
        logger.error(f"Error during dependency depth analysis: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()