"""
Refactored data alignment module.

This module provides functions for aligning genomic and metabolomic data
across species, including validation, merging, and metric calculation.

Key functions:
- align_data: Merge genomic and metabolomic data by species
- save_aligned_matrix: Write aligned data to CSV
- calculate_alignment_success_rate: Calculate success metrics
"""

import os
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List, Union
import pandas as pd
import numpy as np

from utils.logging import get_logger

logger = get_logger(__name__)


def align_data(
    genomic_data: pd.DataFrame,
    metabolite_data: pd.DataFrame,
    species_column: str = 'species_name'
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Align genomic and metabolomic data by species.

    Args:
        genomic_data: DataFrame containing BGC features
        metabolite_data: DataFrame containing metabolite abundances
        species_column: Column name for species identification

    Returns:
        Tuple of (aligned DataFrame, metrics dict)

    Raises:
        ValueError: If required columns are missing
    """
    logger.info("Starting data alignment")

    # Validate inputs
    if species_column not in genomic_data.columns:
        raise ValueError(f"Species column '{species_column}' not found in genomic data")
    if species_column not in metabolite_data.columns:
        raise ValueError(f"Species column '{species_column}' not found in metabolite data")

    # Normalize species names
    genomic_data = genomic_data.copy()
    metabolite_data = metabolite_data.copy()
    genomic_data[species_column] = genomic_data[species_column].str.strip().str.lower()
    metabolite_data[species_column] = metabolite_data[species_column].str.strip().str.lower()

    # Merge data
    aligned = pd.merge(
        genomic_data,
        metabolite_data,
        on=species_column,
        how='inner'
    )

    # Calculate metrics
    total_genomic = len(genomic_data)
    total_metabolite = len(metabolite_data)
    total_aligned = len(aligned)
    alignment_rate = (total_aligned / min(total_genomic, total_metabolite)) * 100 if min(total_genomic, total_metabolite) > 0 else 0

    # Filter partial rows (rows with any NaN in key columns)
    key_columns = [species_column]
    if 'bgc_count' in aligned.columns:
        key_columns.append('bgc_count')
    if 'abundance' in aligned.columns:
        key_columns.append('abundance')

    valid_rows = aligned.dropna(subset=key_columns)
    valid_count = len(valid_rows)

    metrics = {
        'total_genomic_species': total_genomic,
        'total_metabolite_species': total_metabolite,
        'total_aligned_species': total_aligned,
        'valid_species_count': valid_count,
        'alignment_rate_percent': round(alignment_rate, 2),
        'success_rate_percent': round((valid_count / total_aligned) * 100, 2) if total_aligned > 0 else 0
    }

    logger.info(f"Alignment complete: {valid_count}/{total_aligned} valid species ({metrics['success_rate_percent']}%)")

    return valid_rows, metrics


def save_aligned_matrix(
    data: pd.DataFrame,
    output_path: Union[str, Path],
    index: bool = False
) -> None:
    """
    Save aligned data matrix to CSV file.

    Args:
        data: Aligned DataFrame to save
        output_path: Path to output CSV file
        index: Whether to write row index
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data.to_csv(output_path, index=index)
    logger.info(f"Saved aligned matrix to {output_path}")


def calculate_alignment_success_rate(
    aligned_data: pd.DataFrame,
    min_species: int = 5
) -> float:
    """
    Calculate alignment success rate for SC-004 compliance.

    Args:
        aligned_data: Aligned DataFrame with species data
        min_species: Minimum number of species required for valid alignment

    Returns:
        Success rate as a percentage (0-100)
    """
    if aligned_data.empty:
        return 0.0

    valid_count = len(aligned_data)
    if valid_count < min_species:
        logger.warning(f"Only {valid_count} species found, below minimum of {min_species}")
        return 0.0

    return round((valid_count / len(aligned_data)) * 100, 2)


def log_alignment_metrics(metrics: Dict[str, Any], output_path: Union[str, Path]) -> None:
    """
    Log alignment metrics to JSON file.

    Args:
        metrics: Dictionary of alignment metrics
        output_path: Path to output JSON file
    """
    import json
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Logged alignment metrics to {output_path}")


def main() -> None:
    """Main entry point for alignment script."""
    logger.info("Running data alignment pipeline")

    # Example usage (would be replaced with actual data loading)
    # genomic = pd.read_csv('data/raw/genomic_data.csv')
    # metabolite = pd.read_csv('data/raw/metabolite_data.csv')
    # aligned, metrics = align_data(genomic, metabolite)
    # save_aligned_matrix(aligned, 'data/processed/aligned_matrix.csv')

    logger.info("Alignment pipeline complete")