"""
Merge genomic features with phenotypic scores and handle aggregation fallbacks.

This module implements the data merging logic for User Story 1, including:
- Loading and aligning genomic and phenotypic data
- Detecting when species-level aggregation is needed
- Performing aggregation and writing intermediate/final datasets
"""

import os
import csv
import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import pandas as pd
import numpy as np

from src.models.species_aggregate import SpeciesAggregate
from src.utils.errors import DataFetchError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATA_ROOT = Path(os.environ.get('DATA_ROOT', 'data'))
PROCESSED_DIR = DATA_ROOT / 'processed'

# Ensure output directory exists
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


class MergeResult:
    """Result container for merge operations."""
    def __init__(
        self,
        merged_df: Optional[pd.DataFrame] = None,
        species_aggregates: Optional[pd.DataFrame] = None,
        needs_aggregation: bool = False,
        total_isolates: int = 0,
        linked_isolates: int = 0,
        missing_phenotypes: int = 0
    ):
        self.merged_df = merged_df
        self.species_aggregates = species_aggregates
        self.needs_aggregation = needs_aggregation
        self.total_isolates = total_isolates
        self.linked_isolates = linked_isolates
        self.missing_phenotypes = missing_phenotypes


def load_genomic_features(genomic_path: Path) -> pd.DataFrame:
    """
    Load genomic features from a parquet or CSV file.
    
    Args:
        genomic_path: Path to the genomic features file
        
    Returns:
        DataFrame with genomic features
        
    Raises:
        DataFetchError: If file cannot be loaded
    """
    try:
        if genomic_path.suffix == '.parquet':
            return pd.read_parquet(genomic_path)
        elif genomic_path.suffix == '.csv':
            return pd.read_csv(genomic_path)
        else:
            raise DataFetchError(str(genomic_path), 0, "Unsupported file format")
    except Exception as e:
        logger.error(f"Failed to load genomic features from {genomic_path}: {e}")
        raise DataFetchError(str(genomic_path), 0, f"Failed to load genomic features: {e}")


def load_phenotypic_scores(phenotypic_path: Path) -> pd.DataFrame:
    """
    Load phenotypic scores from a parquet or CSV file.
    
    Args:
        phenotypic_path: Path to the phenotypic scores file
        
    Returns:
        DataFrame with phenotypic scores
        
    Raises:
        DataFetchError: If file cannot be loaded
    """
    try:
        if phenotypic_path.suffix == '.parquet':
            return pd.read_parquet(phenotypic_path)
        elif phenotypic_path.suffix == '.csv':
            return pd.read_csv(phenotypic_path)
        else:
            raise DataFetchError(str(phenotypic_path), 0, "Unsupported file format")
    except Exception as e:
        logger.error(f"Failed to load phenotypic scores from {phenotypic_path}: {e}")
        raise DataFetchError(str(phenotypic_path), 0, f"Failed to load phenotypic scores: {e}")


def align_genomic_phenotypic(
    genomic_df: pd.DataFrame,
    phenotypic_df: pd.DataFrame,
    key_col: str = 'species_name'
) -> Tuple[pd.DataFrame, int, int]:
    """
    Align genomic features with phenotypic scores by species/isolate ID.
    
    Args:
        genomic_df: DataFrame with genomic features
        phenotypic_df: DataFrame with phenotypic scores
        key_col: Column name to join on
        
    Returns:
        Tuple of (merged DataFrame, total rows, rows with missing phenotype)
    """
    total_rows = len(genomic_df)
    
    # Perform inner join to keep only matched records
    merged = pd.merge(
        genomic_df,
        phenotypic_df,
        on=key_col,
        how='inner',
        suffixes=('_genomic', '_phenotypic')
    )
    
    # Count missing phenotypes (should be 0 after inner join, but check for NaN)
    missing_count = merged['phenotype_score'].isna().sum()
    
    # Drop rows with missing phenotype scores
    merged = merged.dropna(subset=['phenotype_score'])
    
    logger.info(f"Aligned {len(merged)} records out of {total_rows} total. "
               f"Dropped {total_rows - len(merged)} due to missing phenotypes.")
    
    return merged, total_rows, missing_count


def detect_aggregation_need(merged_df: pd.DataFrame, key_col: str = 'species_name') -> Tuple[bool, int, int]:
    """
    Detect if species-level aggregation is needed based on isolate linkage.
    
    Criteria: If linked_isolate_count / total_isolate_count < 0.5, aggregation is needed.
    
    Args:
        merged_df: Merged DataFrame with genomic and phenotypic data
        key_col: Column name for grouping (species or isolate)
        
    Returns:
        Tuple of (needs_aggregation, total_isolates, linked_isolates)
    """
    # Count total unique isolates (assuming 'isolate_id' column exists)
    if 'isolate_id' in merged_df.columns:
        total_isolates = merged_df['isolate_id'].nunique()
    else:
        # Fallback to using species if isolate_id not present
        total_isolates = merged_df[key_col].nunique()
        logger.warning("No 'isolate_id' column found, using species as proxy for isolate count")
    
    # Count species with multiple isolates (linked)
    species_counts = merged_df[key_col].value_counts()
    linked_species = species_counts[species_counts > 1]
    linked_isolates = linked_species.sum() if len(linked_species) > 0 else 0
    
    if total_isolates == 0:
        logger.warning("No isolates found in merged data")
        return False, 0, 0
    
    linkage_ratio = linked_isolates / total_isolates
    needs_aggregation = linkage_ratio < 0.5
    
    logger.info(f"Linkage ratio: {linked_isolates}/{total_isolates} = {linkage_ratio:.2f}. "
               f"Needs aggregation: {needs_aggregation}")
    
    return needs_aggregation, total_isolates, linked_isolates


def aggregate_by_species(merged_df: pd.DataFrame, key_col: str = 'species_name') -> pd.DataFrame:
    """
    Aggregate data by species: average phenotype, count isolates, compute variance.
    
    Args:
        merged_df: Merged DataFrame
        key_col: Column name for grouping
        
    Returns:
        DataFrame with species-level aggregates
    """
    if key_col not in merged_df.columns:
        raise ValueError(f"Key column '{key_col}' not found in DataFrame. "
                       f"Available columns: {list(merged_df.columns)}")
    
    if 'phenotype_score' not in merged_df.columns:
        raise ValueError("'phenotype_score' column not found in DataFrame")
    
    # Group by species and compute aggregates
    aggregated = merged_df.groupby(key_col).agg(
        avg_phenotype=('phenotype_score', 'mean'),
        isolate_count=('isolate_id' if 'isolate_id' in merged_df.columns else key_col, 'count'),
        variance=('phenotype_score', 'var')
    ).reset_index()
    
    # Rename species column to species_name for consistency
    aggregated = aggregated.rename(columns={key_col: 'species_name'})
    
    # Handle variance NaN (when isolate_count=1)
    aggregated['variance'] = aggregated['variance'].fillna(0.0)
    
    logger.info(f"Aggregated {len(aggregated)} species from {len(merged_df)} records")
    
    return aggregated


def write_species_aggregates(aggregated_df: pd.DataFrame, output_path: Path) -> None:
    """
    Write species aggregates to parquet file.
    
    Args:
        aggregated_df: DataFrame with species aggregates
        output_path: Path to output file
    """
    try:
        aggregated_df.to_parquet(output_path, index=False)
        logger.info(f"Wrote species aggregates to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write species aggregates: {e}")
        raise DataFetchError(str(output_path), 0, f"Failed to write species aggregates: {e}")


def write_aggregated_results(
    aggregated_df: pd.DataFrame,
    output_path: Path,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Write aggregated results to parquet file with optional metadata.
    
    Args:
        aggregated_df: DataFrame with aggregated results
        output_path: Path to output file
        metadata: Optional metadata dictionary
    """
    try:
        # Write to parquet
        aggregated_df.to_parquet(output_path, index=False)
        logger.info(f"Wrote aggregated results to {output_path}")
        
        # Write metadata if provided
        if metadata:
            metadata_path = output_path.with_suffix('.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Wrote metadata to {metadata_path}")
            
    except Exception as e:
        logger.error(f"Failed to write aggregated results: {e}")
        raise DataFetchError(str(output_path), 0, f"Failed to write aggregated results: {e}")


def write_merged_dataset(
    merged_df: pd.DataFrame,
    output_path: Path,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Write the final merged dataset to parquet.
    
    This function handles both the direct merge output (when no aggregation needed)
    and the aggregated output (when aggregation is needed).
    
    Args:
        merged_df: Final DataFrame to write (either original merge or aggregated)
        output_path: Path to output file
        metadata: Optional metadata dictionary
    """
    try:
        merged_df.to_parquet(output_path, index=False)
        logger.info(f"Wrote merged dataset to {output_path}")
        
        # Write metadata if provided
        if metadata:
            metadata_path = output_path.with_suffix('.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Wrote metadata to {metadata_path}")
            
    except Exception as e:
        logger.error(f"Failed to write merged dataset: {e}")
        raise DataFetchError(str(output_path), 0, f"Failed to write merged dataset: {e}")


def write_summary_report(
    output_path: Path,
    total_count: int,
    missing_count: int,
    aggregated: bool = False,
    aggregated_count: int = 0
) -> None:
    """
    Write a summary report of the merge operation.
    
    Args:
        output_path: Path to output report file
        total_count: Total number of input records
        missing_count: Number of records with missing phenotypes
        aggregated: Whether aggregation was performed
        aggregated_count: Number of records after aggregation
    """
    report = {
        'total_input_records': total_count,
        'missing_phenotype_records': missing_count,
        'records_after_dropping_missing': total_count - missing_count,
        'aggregation_performed': aggregated,
        'records_after_aggregation': aggregated_count if aggregated else total_count - missing_count
    }
    
    try:
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Wrote summary report to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write summary report: {e}")
        raise DataFetchError(str(output_path), 0, f"Failed to write summary report: {e}")


def run_merge_pipeline(
    genomic_path: Path,
    phenotypic_path: Path,
    output_path: Path,
    aggregated_output_path: Optional[Path] = None,
    summary_path: Optional[Path] = None
) -> MergeResult:
    """
    Run the full merge pipeline including detection and aggregation if needed.
    
    This is the main entry point for the merge pipeline.
    
    Args:
        genomic_path: Path to genomic features file
        phenotypic_path: Path to phenotypic scores file
        output_path: Path for final merged dataset
        aggregated_output_path: Path for species aggregates (optional)
        summary_path: Path for summary report (optional)
        
    Returns:
        MergeResult object with all relevant data and metadata
    """
    # Load data
    logger.info(f"Loading genomic features from {genomic_path}")
    genomic_df = load_genomic_features(genomic_path)
    
    logger.info(f"Loading phenotypic scores from {phenotypic_path}")
    phenotypic_df = load_phenotypic_scores(phenotypic_path)
    
    # Align data
    merged_df, total_rows, missing_count = align_genomic_phenotypic(
        genomic_df, phenotypic_df
    )
    
    # Detect if aggregation is needed
    needs_aggregation, total_isolates, linked_isolates = detect_aggregation_need(merged_df)
    
    if needs_aggregation:
        logger.info("Aggregation needed. Performing species-level aggregation...")
        
        # Aggregate by species
        aggregated_df = aggregate_by_species(merged_df)
        
        # Write species aggregates if path provided
        if aggregated_output_path:
            write_species_aggregates(aggregated_df, aggregated_output_path)
        
        # Write final merged dataset (aggregated)
        write_merged_dataset(
            aggregated_df,
            output_path,
            metadata={
                'aggregation_performed': True,
                'total_isolates': total_isolates,
                'linked_isolates': linked_isolates,
                'species_count': len(aggregated_df)
            }
        )
        
        # Write summary report
        if summary_path:
            write_summary_report(
                summary_path,
                total_count=total_rows,
                missing_count=missing_count,
                aggregated=True,
                aggregated_count=len(aggregated_df)
            )
        
        return MergeResult(
            merged_df=aggregated_df,
            needs_aggregation=True,
            total_isolates=total_isolates,
            linked_isolates=linked_isolates,
            missing_phenotypes=missing_count
        )
    else:
        logger.info("Aggregation not needed. Using direct merge.")
        
        # Write final merged dataset (direct)
        write_merged_dataset(
            merged_df,
            output_path,
            metadata={
                'aggregation_performed': False,
                'total_isolates': total_isolates,
                'linked_isolates': linked_isolates
            }
        )
        
        # Write summary report
        if summary_path:
            write_summary_report(
                summary_path,
                total_count=total_rows,
                missing_count=missing_count,
                aggregated=False,
                aggregated_count=len(merged_df)
            )
        
        return MergeResult(
            merged_df=merged_df,
            needs_aggregation=False,
            total_isolates=total_isolates,
            linked_isolates=linked_isolates,
            missing_phenotypes=missing_count
        )


def main():
    """Main entry point for the merge pipeline."""
    # Define paths
    genomic_path = PROCESSED_DIR / 'genomic_features.parquet'
    phenotypic_path = PROCESSED_DIR / 'phenotypic_scores.parquet'
    output_path = PROCESSED_DIR / 'merged_dataset.parquet'
    aggregated_output_path = PROCESSED_DIR / 'species_aggregates.parquet'
    summary_path = PROCESSED_DIR / 'merge_summary.json'
    
    # Run pipeline
    result = run_merge_pipeline(
        genomic_path=genomic_path,
        phenotypic_path=phenotypic_path,
        output_path=output_path,
        aggregated_output_path=aggregated_output_path,
        summary_path=summary_path
    )
    
    logger.info(f"Merge pipeline completed. Needs aggregation: {result.needs_aggregation}")
    logger.info(f"Total isolates: {result.total_isolates}, Linked: {result.linked_isolates}")
    logger.info(f"Missing phenotypes: {result.missing_phenotypes}")
    
    return result


if __name__ == '__main__':
    main()
