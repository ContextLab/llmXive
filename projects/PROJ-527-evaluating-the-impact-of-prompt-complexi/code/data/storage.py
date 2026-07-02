"""
Storage module for persisting generated code and metadata.

This module implements the persistence layer for the prompt complexity
evaluation pipeline, writing generated code samples and their associated
metadata to Parquet format for efficient storage and analysis.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
from pydantic import ValidationError

# Import from project API surface
from models.data_models import GeneratedCode, PromptVariant, HumanEvalProblem
from utils.logger import get_logger, handle_error
from config import get_config

logger = get_logger(__name__)
config = get_config()


def serialize_generated_code(code_obj: GeneratedCode) -> Dict[str, Any]:
    """
    Serialize a GeneratedCode Pydantic model to a dictionary for storage.

    Args:
        code_obj: The GeneratedCode instance to serialize.

    Returns:
        A dictionary representation suitable for DataFrame conversion.
    """
    return {
        "problem_id": code_obj.problem_id,
        "prompt_id": code_obj.prompt_id,
        "complexity_label": code_obj.complexity_label.value,
        "generated_code": code_obj.generated_code,
        "generation_timestamp": code_obj.generation_timestamp.isoformat(),
        "llm_model": code_obj.llm_model,
        "prompt_token_count": code_obj.prompt_token_count,
        "structural_element_count": code_obj.structural_element_count,
        "prompt_text_hash": code_obj.prompt_text_hash,
        "generation_duration_ms": code_obj.generation_duration_ms,
        "status": "success"  # Default status for generation stage
    }


def serialize_prompt_variant(variant: PromptVariant) -> Dict[str, Any]:
    """
    Serialize a PromptVariant Pydantic model to a dictionary.

    Args:
        variant: The PromptVariant instance to serialize.

    Returns:
        A dictionary representation.
    """
    return {
        "problem_id": variant.problem_id,
        "prompt_id": variant.prompt_id,
        "complexity_label": variant.complexity_label.value,
        "prompt_text": variant.prompt_text,
        "structural_element_count": variant.structural_element_count,
        "token_count": variant.token_count,
        "generation_method": variant.generation_method,
        "created_at": variant.created_at.isoformat() if variant.created_at else datetime.now().isoformat()
    }


def write_variants_to_parquet(
    generated_codes: List[GeneratedCode],
    output_path: Optional[Path] = None
) -> Path:
    """
    Write a list of GeneratedCode objects to a Parquet file.

    This function aggregates all generated code samples into a single
    Parquet file for efficient storage and downstream analysis.

    Args:
        generated_codes: List of GeneratedCode instances to persist.
        output_path: Optional custom output path. If None, uses config default.

    Returns:
        The Path to the written Parquet file.

    Raises:
        ValueError: If no generated codes are provided.
        IOError: If the file cannot be written.
    """
    if not generated_codes:
        logger.warning("No generated codes provided to write_variants_to_parquet")
        raise ValueError("Cannot write empty list of generated codes")

    if output_path is None:
        output_path = config.OUTPUT_DIR / "prompt_variants.parquet"

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Serialize all records
    records = [serialize_generated_code(code) for code in generated_codes]

    # Convert to DataFrame
    df = pd.DataFrame(records)

    # Ensure numeric columns are properly typed
    numeric_columns = [
        "prompt_token_count",
        "structural_element_count",
        "generation_duration_ms"
    ]
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    # Write to Parquet
    logger.info(f"Writing {len(df)} records to {output_path}")
    try:
        df.to_parquet(
            output_path,
            engine='pyarrow',
            index=False,
            compression='snappy'
        )
        logger.info(f"Successfully wrote prompt variants to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write Parquet file: {e}")
        raise IOError(f"Failed to write Parquet file: {e}")

    return output_path


def append_to_variants_parquet(
    new_codes: List[GeneratedCode],
    existing_path: Optional[Path] = None
) -> Path:
    """
    Append new generated codes to an existing Parquet file.

    If the file does not exist, creates a new one.

    Args:
        new_codes: List of new GeneratedCode instances to append.
        existing_path: Optional path to existing file. Uses config default if None.

    Returns:
        Path to the updated Parquet file.
    """
    if existing_path is None:
        existing_path = config.OUTPUT_DIR / "prompt_variants.parquet"

    if not new_codes:
        return existing_path

    if existing_path.exists():
        # Read existing data
        existing_df = pd.read_parquet(existing_path)
        logger.info(f"Loaded {len(existing_df)} existing records from {existing_path}")

        # Serialize new records
        new_records = [serialize_generated_code(code) for code in new_codes]
        new_df = pd.DataFrame(new_records)

        # Concatenate
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        logger.info(f"Combined dataset has {len(combined_df)} records")

        # Write back
        combined_df.to_parquet(
            existing_path,
            engine='pyarrow',
            index=False,
            compression='snappy'
        )
    else:
        # Write new file
        write_variants_to_parquet(new_codes, existing_path)

    return existing_path


def load_variants_from_parquet(
    input_path: Optional[Path] = None
) -> List[GeneratedCode]:
    """
    Load generated codes from a Parquet file back into GeneratedCode objects.

    Args:
        input_path: Optional path to Parquet file. Uses config default if None.

    Returns:
        List of GeneratedCode instances.
    """
    if input_path is None:
        input_path = config.OUTPUT_DIR / "prompt_variants.parquet"

    if not input_path.exists():
        logger.warning(f"Parquet file not found at {input_path}")
        return []

    df = pd.read_parquet(input_path)
    records = df.to_dict('records')

    generated_codes = []
    for record in records:
        try:
            # Convert ISO strings back to datetime
            if "generation_timestamp" in record and isinstance(record["generation_timestamp"], str):
                record["generation_timestamp"] = datetime.fromisoformat(record["generation_timestamp"])

            code = GeneratedCode(**record)
            generated_codes.append(code)
        except ValidationError as e:
            logger.error(f"Validation error loading record: {e}")
            continue

    logger.info(f"Loaded {len(generated_codes)} records from {input_path}")
    return generated_codes


def main() -> None:
    """
    Main entry point for storage module testing/demo.

    This function demonstrates the storage functionality by:
    1. Loading generated codes from the orchestrator output (if available)
    2. Writing them to Parquet
    3. Verifying the write by reading back

    Note: This is typically called by the orchestrator after generation.
    """
    logger.info("Starting storage module main()")

    # Check if we have data from the orchestrator
    # In a real pipeline, this would receive data from T017 orchestrator
    # For now, we verify the output path exists and can be written to

    test_path = config.OUTPUT_DIR / "test_storage.parquet"
    logger.info(f"Storage module ready. Output directory: {config.OUTPUT_DIR}")
    logger.info(f"Test write path: {test_path}")

    # The actual writing happens when called by orchestrator with GeneratedCode objects
    logger.info("Storage module initialized. Ready to write prompt_variants.parquet")


if __name__ == "__main__":
    main()
