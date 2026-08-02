import os
import sys
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import pandas as pd
import pyarrow.parquet as pq
import json
from datetime import datetime

from config import get_data_path, get_reductions, get_seed, ConfigurationError
from utils.logging import get_logger
from data.preprocess import process_ebsd_dataset
from data.exclusion import apply_exclusion_logic
from data.models import EbsdDatasetMetadata

logger = get_logger(__name__)

def load_all_processed_datasets(
    base_path: Optional[Path] = None,
    reductions: Optional[List[int]] = None
) -> pd.DataFrame:
    """
    Load all processed EBSD datasets from the data/interim directory,
    apply exclusion logic, and consolidate them into a single DataFrame.

    Args:
        base_path: Base directory for data (defaults to config)
        reductions: List of reduction levels to include (defaults to config)

    Returns:
        Consolidated DataFrame with all valid samples
    """
    if base_path is None:
        base_path = get_data_path()
    
    if reductions is None:
        try:
            reductions = get_reductions()
        except ConfigurationError as e:
            logger.error(f"Configuration error: {e}")
            raise

    interim_path = base_path / "interim"
    processed_path = base_path / "processed"
    
    if not interim_path.exists():
        logger.warning(f"Interim directory not found: {interim_path}")
        return pd.DataFrame()

    all_dataframes = []
    metadata_records = []

    # Iterate through material directories
    for material_dir in sorted(interim_path.iterdir()):
        if not material_dir.is_dir():
            continue

        material_name = material_dir.name
        
        # Process each reduction level
        for reduction in reductions:
            input_file = material_dir / f"{material_name}_reduction_{reduction}_processed.parquet"
            
            if not input_file.exists():
                logger.warning(f"Missing processed file: {input_file}")
                continue

            try:
                # Load the processed dataset
                df = pd.read_parquet(input_file)
                
                if df.empty:
                    logger.info(f"Empty dataset for {material_name} at {reduction}% reduction")
                    continue

                # Add metadata columns
                df['material'] = material_name
                df['reduction'] = reduction
                df['source_file'] = input_file.name
                df['processed_at'] = datetime.now().isoformat()

                # Apply exclusion logic (T014)
                df_excluded, exclusion_stats = apply_exclusion_logic(df)
                
                if len(df_excluded) == 0:
                    logger.warning(f"All samples excluded for {material_name} at {reduction}% reduction")
                    continue

                # Log exclusion stats
                total_before = len(df)
                total_after = len(df_excluded)
                excluded_count = total_before - total_after
                logger.info(
                    f"Excluded {excluded_count} samples ({100*excluded_count/total_before:.1f}%) "
                    f"for {material_name} at {reduction}% reduction"
                )

                all_dataframes.append(df_excluded)

                # Record metadata
                metadata_records.append({
                    'material': material_name,
                    'reduction': reduction,
                    'total_points_before': total_before,
                    'total_points_after': total_after,
                    'excluded_points': excluded_count,
                    'exclusion_reason': 'low_reliability',
                    'source_file': str(input_file),
                    'processed_at': datetime.now().isoformat()
                })

            except Exception as e:
                logger.error(f"Error processing {input_file}: {e}")
                continue

    if not all_dataframes:
        logger.warning("No valid data found to consolidate")
        return pd.DataFrame()

    # Concatenate all dataframes
    consolidated_df = pd.concat(all_dataframes, ignore_index=True)
    
    # Sort by material and reduction for consistency
    consolidated_df = consolidated_df.sort_values(['material', 'reduction'])
    
    # Reset index
    consolidated_df = consolidated_df.reset_index(drop=True)
    
    # Save metadata
    if metadata_records:
        metadata_df = pd.DataFrame(metadata_records)
        metadata_path = processed_path / "consolidation_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata_records, f, indent=2)
        logger.info(f"Saved consolidation metadata to {metadata_path}")

    return consolidated_df

def write_consolidated_parquet(
    df: pd.DataFrame,
    output_path: Optional[Path] = None,
    include_metadata: bool = True
) -> Path:
    """
    Write the consolidated DataFrame to Parquet format with metadata.

    Args:
        df: Consolidated DataFrame
        output_path: Output file path (defaults to data/processed/cleaned_ebsd.parquet)
        include_metadata: Whether to include metadata in the Parquet file

    Returns:
        Path to the output file
    """
    if output_path is None:
        base_path = get_data_path()
        output_path = base_path / "processed" / "cleaned_ebsd.parquet"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Add metadata to Parquet file
    if include_metadata and not df.empty:
        # Create metadata dictionary
        metadata = {
            'created_at': datetime.now().isoformat(),
            'total_samples': len(df),
            'materials': df['material'].unique().tolist(),
            'reductions': sorted(df['reduction'].unique().tolist()),
            'version': '1.0',
            'pipeline': 'llmXive-US1-consolidation'
        }
        
        # Convert metadata to bytes for Parquet schema
        metadata_bytes = json.dumps(metadata).encode('utf-8')
        
        # Write with metadata
        table = pq.Table.from_pandas(df)
        new_metadata = table.schema.metadata
        if new_metadata:
            new_metadata[b'llmXive_metadata'] = metadata_bytes
        else:
            new_metadata = {b'llmXive_metadata': metadata_bytes}
        
        table = table.replace_schema_metadata(new_metadata)
        pq.write_table(table, output_path)
    else:
        df.to_parquet(output_path, index=False)

    logger.info(f"Consolidated data written to {output_path} with {len(df)} samples")
    return output_path

def main():
    """Main entry point for data consolidation."""
    logger.info("Starting EBSD data consolidation (T015)")
    
    try:
        # Load all processed datasets
        consolidated_df = load_all_processed_datasets()
        
        if consolidated_df.empty:
            logger.error("No data to consolidate. Exiting.")
            sys.exit(1)
        
        # Write to Parquet
        output_path = write_consolidated_parquet(consolidated_df)
        
        # Print summary
        logger.info("Consolidation Summary:")
        logger.info(f"  Total samples: {len(consolidated_df)}")
        logger.info(f"  Materials: {consolidated_df['material'].unique().tolist()}")
        logger.info(f"  Reductions: {sorted(consolidated_df['reduction'].unique().tolist())}")
        logger.info(f"  Output file: {output_path}")
        
        # Verify file exists and is readable
        if output_path.exists():
            verify_df = pd.read_parquet(output_path)
            logger.info(f"Verification: Read back {len(verify_df)} samples")
            assert len(verify_df) == len(consolidated_df), "Sample count mismatch"
            logger.info("Verification successful")
        else:
            logger.error(f"Output file not found: {output_path}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Consolidation failed: {e}")
        raise

if __name__ == "__main__":
    main()
