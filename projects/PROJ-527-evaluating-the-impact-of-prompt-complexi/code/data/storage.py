"""
Storage module for saving generated code and metadata to Parquet format.

This module implements the storage layer for User Story 1, writing
generated code samples and their associated metadata to a Parquet file
for efficient analysis and downstream processing.
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
from pydantic import BaseModel

from config import Paths
from models.data_models import GeneratedCode, model_to_dict, ComplexityLabel
from utils.logger import get_logger

logger = get_logger(__name__)


def save_variants_to_parquet(
    variants: List[GeneratedCode],
    output_path: Optional[Path] = None
) -> Path:
    """
    Save a list of GeneratedCode variants to a Parquet file.
    
    Args:
        variants: List of GeneratedCode objects containing prompt variants,
                 generated code, and metadata.
        output_path: Optional custom output path. If None, uses the default
                    path from config: data/processed/prompt_variants.parquet
    
    Returns:
        Path to the created Parquet file.
    
    Raises:
        ValueError: If the variants list is empty.
        RuntimeError: If the file write fails.
    """
    if not variants:
        raise ValueError("Cannot save empty list of variants")
    
    if output_path is None:
        output_path = Paths.data_processed / "prompt_variants.parquet"
    
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert Pydantic models to dictionaries
    records = []
    for variant in variants:
        record = model_to_dict(variant)
        # Add timestamp for reproducibility tracking
        record['saved_at'] = datetime.utcnow().isoformat()
        records.append(record)
    
    # Create DataFrame
    df = pd.DataFrame(records)
    
    # Ensure consistent column ordering for reproducibility
    expected_columns = [
        'problem_id', 'problem_name', 'complexity_label', 'prompt_text',
        'generated_code', 'token_count', 'structural_element_count',
        'examples_count', 'constraints_count', 'instructions_count',
        'state_transition_proxy', 'saved_at'
    ]
    
    # Reorder columns if they exist, otherwise just use existing order
    existing_cols = [c for c in expected_columns if c in df.columns]
    other_cols = [c for c in df.columns if c not in expected_columns]
    final_columns = existing_cols + other_cols
    df = df[final_columns]
    
    # Write to Parquet
    try:
        df.to_parquet(output_path, index=False, engine='pyarrow')
        logger.info(f"Saved {len(variants)} variants to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write Parquet file: {e}")
        raise RuntimeError(f"Failed to save variants to Parquet: {e}")
    
    return output_path


def load_variants_from_parquet(
    input_path: Optional[Path] = None
) -> List[GeneratedCode]:
    """
    Load generated code variants from a Parquet file.
    
    Args:
        input_path: Optional custom input path. If None, uses the default
                   path from config: data/processed/prompt_variants.parquet
    
    Returns:
        List of GeneratedCode objects.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        RuntimeError: If the file read fails.
    """
    if input_path is None:
        input_path = Paths.data_processed / "prompt_variants.parquet"
    
    if not input_path.exists():
        raise FileNotFoundError(f"Parquet file not found: {input_path}")
    
    try:
        df = pd.read_parquet(input_path, engine='pyarrow')
    except Exception as e:
        logger.error(f"Failed to read Parquet file: {e}")
        raise RuntimeError(f"Failed to load variants from Parquet: {e}")
    
    variants = []
    for _, row in df.iterrows():
        # Convert row dict back to GeneratedCode model
        try:
            variant = GeneratedCode.model_validate(row.to_dict())
            variants.append(variant)
        except Exception as e:
            logger.warning(f"Failed to parse row: {e}, skipping")
            continue
    
    logger.info(f"Loaded {len(variants)} variants from {input_path}")
    return variants


def get_variant_counts_by_complexity(
    variants: List[GeneratedCode]
) -> Dict[ComplexityLabel, int]:
    """
    Count variants grouped by complexity label.
    
    Args:
        variants: List of GeneratedCode objects.
    
    Returns:
        Dictionary mapping complexity labels to counts.
    """
    counts = {label: 0 for label in ComplexityLabel}
    for variant in variants:
        counts[variant.complexity_label] += 1
    return counts


def main() -> None:
    """
    Main entry point for testing the storage module.
    
    This function demonstrates the save/load cycle with sample data
    if no existing data is present.
    """
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    from models.data_models import HumanEvalProblem, PromptVariant
    
    # Create sample data for demonstration
    sample_problem = HumanEvalProblem(
        problem_id="test_001",
        prompt="Write a function to add two numbers.",
        test_case="assert add(1, 2) == 3",
        entry_point="add"
    )
    
    sample_variants = [
        GeneratedCode(
            problem_id=sample_problem.problem_id,
            problem_name="test_001",
            complexity_label=ComplexityLabel.SIMPLE,
            prompt_text="Write a function to add two numbers.",
            generated_code="def add(a, b):\n    return a + b",
            token_count=15,
            structural_element_count=1,
            examples_count=0,
            constraints_count=0,
            instructions_count=1,
            state_transition_proxy=0.5
        ),
        GeneratedCode(
            problem_id=sample_problem.problem_id,
            problem_name="test_001",
            complexity_label=ComplexityLabel.MODERATE,
            prompt_text="Write a function to add two numbers. Ensure it handles integers.",
            generated_code="def add(a: int, b: int) -> int:\n    return a + b",
            token_count=25,
            structural_element_count=2,
            examples_count=0,
            constraints_count=1,
            instructions_count=1,
            state_transition_proxy=0.6
        )
    ]
    
    output_path = save_variants_to_parquet(sample_variants)
    print(f"Saved variants to: {output_path}")
    
    loaded_variants = load_variants_from_parquet(output_path)
    print(f"Loaded {len(loaded_variants)} variants")
    
    counts = get_variant_counts_by_complexity(loaded_variants)
    print(f"Counts by complexity: {counts}")


if __name__ == "__main__":
    main()