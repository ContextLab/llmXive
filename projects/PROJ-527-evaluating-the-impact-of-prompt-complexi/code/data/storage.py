"""
Storage module for saving and loading prompt variants and execution results.

This module handles the persistence of generated code samples, prompt metadata,
and execution outcomes to Parquet and CSV formats.
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd

from config import Paths
from models.data_models import PromptVariant, GeneratedCode, model_to_dict


def save_variants_to_parquet(
    variants: List[PromptVariant],
    output_path: Optional[Path] = None
) -> Path:
    """
    Save a list of PromptVariant objects to a Parquet file.
    
    Args:
        variants: List of PromptVariant objects to save.
        output_path: Optional path to save to. Defaults to Paths.PROCESSED_DATA / "prompt_variants.parquet".
        
    Returns:
        Path to the saved file.
        
    Raises:
        ValueError: If variants list is empty.
        RuntimeError: If save operation fails.
    """
    if not variants:
        raise ValueError("Cannot save empty list of variants.")
    
    target_path = output_path or (Paths.PROCESSED_DATA / "prompt_variants.parquet")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert Pydantic models to dictionaries
    data = [model_to_dict(v) for v in variants]
    
    # Ensure timestamp is serializable
    for record in data:
        if isinstance(record.get('created_at'), datetime):
            record['created_at'] = record['created_at'].isoformat()
        if isinstance(record.get('dependency_depth_score'), float):
            # Handle NaN values which are not serializable in parquet
            if pd.isna(record['dependency_depth_score']):
                record['dependency_depth_score'] = None
        
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Ensure deterministic column ordering for reproducibility
    expected_columns = [
        'problem_id', 'variant_label', 'prompt_text', 'code_generation',
        'token_count', 'structural_element_count', 'created_at',
        'dependency_depth_score', 'constraint_position_index'
    ]
    
    # Filter to only expected columns that exist in the dataframe
    existing_columns = [col for col in expected_columns if col in df.columns]
    df = df[existing_columns]
    
    try:
        df.to_parquet(target_path, index=False, engine='pyarrow')
    except Exception as e:
        raise RuntimeError(f"Failed to save variants to {target_path}: {e}")
    
    return target_path


def load_variants_from_parquet(
    input_path: Optional[Path] = None
) -> List[PromptVariant]:
    """
    Load prompt variants from a Parquet file.
    
    Args:
        input_path: Optional path to load from. Defaults to Paths.PROCESSED_DATA / "prompt_variants.parquet".
        
    Returns:
        List of PromptVariant objects.
        
    Raises:
        FileNotFoundError: If file does not exist.
        RuntimeError: If load operation fails.
    """
    target_path = input_path or (Paths.PROCESSED_DATA / "prompt_variants.parquet")
    
    if not target_path.exists():
        raise FileNotFoundError(f"Parquet file not found: {target_path}")
    
    try:
        df = pd.read_parquet(target_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load variants from {target_path}: {e}")
    
    if df.empty:
        return []
    
    # Reconstruct PromptVariant objects from dictionaries
    variants = []
    for _, row in df.iterrows():
        # Convert timestamp string back to datetime if needed
        row_dict = row.to_dict()
        if 'created_at' in row_dict and isinstance(row_dict['created_at'], str):
            try:
                row_dict['created_at'] = datetime.fromisoformat(row_dict['created_at'])
            except ValueError:
                # Fallback for non-standard formats
                row_dict['created_at'] = datetime.now()
        
        # Handle NaN values for optional fields
        if 'dependency_depth_score' in row_dict and pd.isna(row_dict['dependency_depth_score']):
            row_dict['dependency_depth_score'] = None
            
        variant = PromptVariant(**row_dict)
        variants.append(variant)
    
    return variants


def get_variant_counts_by_complexity(
    variants: List[PromptVariant]
) -> Dict[str, int]:
    """
    Count variants by complexity label.
    
    Args:
        variants: List of PromptVariant objects.
        
    Returns:
        Dictionary mapping complexity labels to counts.
    """
    counts: Dict[str, int] = {}
    for variant in variants:
        label = variant.variant_label.value
        counts[label] = counts.get(label, 0) + 1
    return counts


def main() -> None:
    """
    Main entry point for storage module.
    
    This function is primarily for testing and demonstration.
    In production, the module is used as a library by other components.
    """
    print("Storage module loaded successfully.")
    print(f"Processed data directory: {Paths.PROCESSED_DATA}")
    print(f"Results directory: {Paths.RESULTS_DATA}")


if __name__ == "__main__":
    main()
