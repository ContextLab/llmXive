import os
import csv
import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field

import pandas as pd
import numpy as np

from src.models.genomic_feature import GenomicFeature
from src.models.isolate import Isolate
from src.models.species_aggregate import SpeciesAggregate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class MergeResult:
    merged_df: Optional[pd.DataFrame] = None
    species_aggregates: Optional[pd.DataFrame] = None
    aggregated_results: Optional[pd.DataFrame] = None
    stats: Dict[str, Any] = field(default_factory=dict)
    needs_aggregation: bool = False

def load_genomic_features(genomic_path: Path) -> pd.DataFrame:
    """Load genomic features from a Parquet or CSV file."""
    if not genomic_path.exists():
        raise FileNotFoundError(f"Genomic features file not found: {genomic_path}")
    
    if genomic_path.suffix == '.parquet':
        return pd.read_parquet(genomic_path)
    elif genomic_path.suffix == '.csv':
        return pd.read_csv(genomic_path)
    else:
        raise ValueError(f"Unsupported file format: {genomic_path.suffix}")

def load_phenotypic_scores(phenotypic_path: Path) -> pd.DataFrame:
    """Load phenotypic scores from a Parquet or CSV file."""
    if not phenotypic_path.exists():
        raise FileNotFoundError(f"Phenotypic scores file not found: {phenotypic_path}")
    
    if phenotypic_path.suffix == '.parquet':
        return pd.read_parquet(phenotypic_path)
    elif phenotypic_path.suffix == '.csv':
        return pd.read_csv(phenotypic_path)
    else:
        raise ValueError(f"Unsupported file format: {phenotypic_path.suffix}")

def align_genomic_phenotypic(genomic_df: pd.DataFrame, phenotypic_df: pd.DataFrame) -> Tuple[pd.DataFrame, int, int]:
    """
    Align genomic features with phenotypic scores by isolate/species ID.
    
    Args:
        genomic_df: DataFrame with genomic features
        phenotypic_df: DataFrame with phenotypic scores
        
    Returns:
        Tuple of (merged DataFrame, count of dropped rows, total rows before merge)
    """
    total_rows = len(genomic_df)
    
    # Identify common key column (assuming 'strain_id' or 'species_name')
    key_col = None
    if 'strain_id' in genomic_df.columns and 'strain_id' in phenotypic_df.columns:
        key_col = 'strain_id'
    elif 'species_name' in genomic_df.columns and 'species_name' in phenotypic_df.columns:
        key_col = 'species_name'
    else:
        raise ValueError("No common key column found for merging")
    
    # Merge on the key column
    merged_df = pd.merge(
        genomic_df, 
        phenotypic_df, 
        on=key_col, 
        how='inner'  # Inner join to keep only matched rows
    )
    
    dropped_count = total_rows - len(merged_df)
    
    if dropped_count > 0:
        logger.warning(f"Dropped {dropped_count} rows due to missing phenotype data")
    
    return merged_df, dropped_count, total_rows

def detect_aggregation_need(merged_df: pd.DataFrame, threshold: float = 0.5) -> bool:
    """
    Detect if aggregation is needed based on linkage ratio.
    
    Args:
        merged_df: Merged DataFrame
        threshold: Minimum ratio of linked isolates to total isolates
        
    Returns:
        True if aggregation is needed (ratio < threshold), False otherwise
    """
    if merged_df.empty:
        return True
    
    total_isolates = len(merged_df)
    # Assuming we have a column 'strain_id' to count unique isolates
    if 'strain_id' in merged_df.columns:
        linked_isolate_count = merged_df['strain_id'].nunique()
    else:
        # If no strain_id, assume each row is an isolate
        linked_isolate_count = total_isolates
    
    ratio = linked_isolate_count / total_isolates if total_isolates > 0 else 0
    needs_agg = ratio < threshold
    
    logger.info(f"Linkage ratio: {ratio:.2f}, needs aggregation: {needs_agg}")
    return needs_agg

def aggregate_by_species(merged_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate data by species: average phenotype, count isolates.
    
    Args:
        merged_df: Merged DataFrame
        
    Returns:
        DataFrame with species-level aggregates
    """
    if 'species_name' not in merged_df.columns:
        raise ValueError("Column 'species_name' not found in DataFrame")
    
    # Group by species and aggregate
    agg_df = merged_df.groupby('species_name').agg({
        'phenotype_score': 'mean',
        'strain_id': 'count'  # Count isolates
    }).reset_index()
    
    agg_df.columns = ['species_name', 'avg_phenotype', 'isolate_count']
    
    # Calculate variance if possible
    if 'phenotype_score' in merged_df.columns:
        variance_df = merged_df.groupby('species_name')['phenotype_score'].var().reset_index()
        variance_df.columns = ['species_name', 'variance']
        agg_df = pd.merge(agg_df, variance_df, on='species_name', how='left')
    
    return agg_df

def write_merged_dataset(df: pd.DataFrame, output_path: Path) -> None:
    """Write merged DataFrame to Parquet file."""
    df.to_parquet(output_path, index=False)
    logger.info(f"Wrote merged dataset to {output_path}")

def write_species_aggregates(df: pd.DataFrame, output_path: Path) -> None:
    """Write species aggregates to Parquet file."""
    df.to_parquet(output_path, index=False)
    logger.info(f"Wrote species aggregates to {output_path}")

def write_aggregated_results(df: pd.DataFrame, output_path: Path, analysis_results: Optional[pd.DataFrame] = None) -> None:
    """
    Write aggregated results, optionally combining with analysis results.
    
    Args:
        df: Species aggregates DataFrame
        output_path: Output file path
        analysis_results: Optional analysis results to include
    """
    if analysis_results is not None:
        # Merge aggregates with analysis results if available
        final_df = pd.merge(df, analysis_results, on='species_name', how='left')
    else:
        final_df = df
    
    final_df.to_csv(output_path, index=False)
    logger.info(f"Wrote aggregated results to {output_path}")

def write_summary_report(stats: Dict[str, Any], output_path: Path) -> None:
    """Write a summary report as JSON."""
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Wrote summary report to {output_path}")

def run_merge_pipeline(
    genomic_path: Path,
    phenotypic_path: Path,
    output_dir: Path,
    analysis_results_path: Optional[Path] = None
) -> MergeResult:
    """
    Run the full merge pipeline: load, align, detect aggregation, aggregate if needed, and write outputs.
    
    Args:
        genomic_path: Path to genomic features file
        phenotypic_path: Path to phenotypic scores file
        output_dir: Directory for output files
        analysis_results_path: Optional path to pre-computed analysis results (for T020c)
        
    Returns:
        MergeResult containing all outputs and statistics
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    logger.info(f"Loading genomic features from {genomic_path}")
    genomic_df = load_genomic_features(genomic_path)
    
    logger.info(f"Loading phenotypic scores from {phenotypic_path}")
    phenotypic_df = load_phenotypic_scores(phenotypic_path)
    
    # Align and merge
    merged_df, dropped_count, total_rows = align_genomic_phenotypic(genomic_df, phenotypic_df)
    
    # Detect if aggregation is needed
    needs_agg = detect_aggregation_need(merged_df)
    
    result = MergeResult(
        merged_df=merged_df,
        needs_aggregation=needs_agg,
        stats={
            'total_rows': total_rows,
            'dropped_rows': dropped_count,
            'final_rows': len(merged_df),
            'needs_aggregation': needs_agg
        }
    )
    
    if needs_agg:
        logger.info("Performing species aggregation...")
        species_agg_df = aggregate_by_species(merged_df)
        species_agg_path = output_dir / "species_aggregates.parquet"
        write_species_aggregates(species_agg_df, species_agg_path)
        result.species_aggregates = species_agg_df
        
        # If analysis results are provided, include them
        analysis_results_df = None
        if analysis_results_path and analysis_results_path.exists():
            if analysis_results_path.suffix == '.csv':
                analysis_results_df = pd.read_csv(analysis_results_path)
            elif analysis_results_path.suffix == '.parquet':
                analysis_results_df = pd.read_parquet(analysis_results_path)
        
        agg_results_path = output_dir / "aggregated_results.csv"
        write_aggregated_results(species_agg_df, agg_results_path, analysis_results_df)
        result.aggregated_results = species_agg_df if analysis_results_df is None else pd.merge(species_agg_df, analysis_results_df, on='species_name', how='left')
        
        # Use aggregated data for final output
        final_df = result.aggregated_results if result.aggregated_results is not None else species_agg_df
        result.stats['aggregated_species_count'] = len(species_agg_df)
    else:
        final_df = merged_df
        result.stats['aggregated_species_count'] = 0
    
    # Write final merged dataset
    final_output_path = output_dir / "merged_dataset.parquet"
    write_merged_dataset(final_df, final_output_path)
    result.merged_df = final_df
    
    # Write summary report
    summary_path = output_dir / "merge_summary.json"
    write_summary_report(result.stats, summary_path)
    
    return result

def main():
    """Main entry point for the merge pipeline."""
    # Define paths based on project structure
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_dir = base_dir / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    
    # Ensure processed directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Define input paths (adjust based on actual file names from previous tasks)
    # Assuming T015/T016 produce these files
    genomic_path = processed_dir / "genomic_features.parquet"
    phenotypic_path = processed_dir / "phenotypic_scores.parquet"
    
    # If T020c ran, there might be analysis results
    analysis_results_path = processed_dir / "aggregated_results.csv"
    if not analysis_results_path.exists():
        analysis_results_path = None
    
    # Check if input files exist
    if not genomic_path.exists():
        logger.error(f"Genomic features file not found: {genomic_path}")
        # Try to find alternative paths if standard ones don't exist
        # This handles cases where T019 might have output to a different name
        possible_genomic = list(processed_dir.glob("*genomic*.parquet")) + list(processed_dir.glob("*genomic*.csv"))
        if possible_genomic:
            genomic_path = possible_genomic[0]
            logger.info(f"Using alternative genomic path: {genomic_path}")
        else:
            raise FileNotFoundError("No genomic features file found in processed directory")
    
    if not phenotypic_path.exists():
        logger.error(f"Phenotypic scores file not found: {phenotypic_path}")
        # Try to find alternative paths
        possible_phenotypic = list(processed_dir.glob("*phenotypic*.parquet")) + list(processed_dir.glob("*phenotypic*.csv"))
        if possible_phenotypic:
            phenotypic_path = possible_phenotypic[0]
            logger.info(f"Using alternative phenotypic path: {phenotypic_path}")
        else:
            raise FileNotFoundError("No phenotypic scores file found in processed directory")
    
    # Run the pipeline
    try:
        result = run_merge_pipeline(
            genomic_path=genomic_path,
            phenotypic_path=phenotypic_path,
            output_dir=processed_dir,
            analysis_results_path=analysis_results_path
        )
        
        logger.info("Merge pipeline completed successfully")
        logger.info(f"Final dataset size: {len(result.merged_df)} rows")
        logger.info(f"Needs aggregation: {result.needs_aggregation}")
        if result.needs_aggregation:
            logger.info(f"Aggregated into {result.stats.get('aggregated_species_count', 0)} species")
        
    except Exception as e:
        logger.error(f"Merge pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()