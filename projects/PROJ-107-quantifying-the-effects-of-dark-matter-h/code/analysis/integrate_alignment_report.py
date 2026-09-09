"""
T040: Integrate misalignment results into final statistical report.

This script merges the alignment angles data (T038 output) with the primary
statistical results (T025 output) and the halo shapes data (T017 output)
to generate a comprehensive final report.

It ensures:
1. Data integrity checks on all inputs.
2. Merging on the common 'halo_id' key.
3. Calculation of summary statistics for misalignment angles.
4. Inclusion of the 'associational_only' flag (T026 requirement).
5. Output of a unified CSV to data/processed/final_report.csv.
"""

import os
import sys
import logging
import csv
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

# Ensure code root is in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.config import get_project_root, get_data_processed_path
from analysis.metadata_utils import load_metadata, save_metadata, add_associational_only_flag_to_csv

logger = logging.getLogger(__name__)

def load_halo_shapes() -> pd.DataFrame:
    """Load the processed halo shapes CSV."""
    path = get_data_processed_path() / "halo_shapes.csv"
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")
    logger.info(f"Loading halo shapes from {path}")
    return pd.read_csv(path)

def load_alignment_angles() -> pd.DataFrame:
    """Load the processed alignment angles CSV."""
    path = get_data_processed_path() / "alignment_angles.csv"
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")
    logger.info(f"Loading alignment angles from {path}")
    return pd.read_csv(path)

def load_statistical_results() -> pd.DataFrame:
    """Load the statistical results CSV."""
    path = get_data_processed_path() / "statistical_results.csv"
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")
    logger.info(f"Loading statistical results from {path}")
    return pd.read_csv(path)

def merge_datasets(
    shapes_df: pd.DataFrame,
    alignment_df: pd.DataFrame,
    stats_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge the three main datasets on 'halo_id'.
    
    Strategy:
    1. Start with halo_shapes (the base unit).
    2. Left join alignment_angles (some halos might not have pairs).
    3. Left join statistical_results (aggregated stats, join on halo_id if present, 
       or keep as is if stats are global). 
       
    Note: If statistical_results are global (one row), we broadcast them or 
    merge carefully. Assuming standard per-halo stats for this integration.
    """
    logger.info("Merging datasets...")
    
    # Ensure halo_id is consistent type
    shapes_df = shapes_df.copy()
    alignment_df = alignment_df.copy()
    stats_df = stats_df.copy()
    
    if 'halo_id' in shapes_df.columns:
        shapes_df['halo_id'] = shapes_df['halo_id'].astype(str)
    if 'halo_id' in alignment_df.columns:
        alignment_df['halo_id'] = alignment_df['halo_id'].astype(str)
    if 'halo_id' in stats_df.columns:
        stats_df['halo_id'] = stats_df['halo_id'].astype(str)

    # Merge Shapes + Alignment
    merged = pd.merge(
        shapes_df,
        alignment_df,
        on='halo_id',
        how='left'
    )
    
    # Merge with Stats
    # If stats_df has halo_id, merge. If not, assume global stats (append later).
    if 'halo_id' in stats_df.columns:
        merged = pd.merge(
            merged,
            stats_df,
            on='halo_id',
            how='left'
        )
    else:
        logger.warning("statistical_results.csv does not have 'halo_id'. Assuming global stats. Appending metadata.")
        # Store global stats in metadata for now, or add as columns with NaN
        # For this implementation, we'll just keep the merged data and note global stats in report
        pass

    return merged

def compute_summary_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute summary statistics for the final report."""
    stats = {}
    
    # Alignment Stats
    angle_cols = [c for c in df.columns if 'angle' in c.lower()]
    for col in angle_cols:
        if col in df.columns:
            non_null = df[col].dropna()
            if len(non_null) > 0:
                stats[f"{col}_mean"] = non_null.mean()
                stats[f"{col}_median"] = non_null.median()
                stats[f"{col}_std"] = non_null.std()
                stats[f"{col}_count"] = len(non_null)
    
    # Shape Stats
    shape_cols = ['triaxiality', 'b_a_ratio', 'c_a_ratio']
    for col in shape_cols:
        if col in df.columns:
            non_null = df[col].dropna()
            if len(non_null) > 0:
                stats[f"shape_{col}_mean"] = non_null.mean()
                stats[f"shape_{col}_std"] = non_null.std()

    return stats

def generate_final_report(
    merged_df: pd.DataFrame,
    summary_stats: Dict[str, Any]
) -> pd.DataFrame:
    """
    Prepare the final dataframe for output.
    Adds metadata columns and ensures flags are present.
    """
    final_df = merged_df.copy()
    
    # Add summary stats as metadata columns (optional, or keep separate)
    # Here we just ensure the dataframe is clean
    
    # Ensure associational_only flag is present if not already
    if 'associational_only' not in final_df.columns:
        final_df['associational_only'] = True
    
    return final_df

def main():
    """Main entry point for T040."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    project_root = get_project_root()
    processed_path = get_data_processed_path()
    output_file = processed_path / "final_report.csv"
    
    logger.info(f"Starting T040: Integrating misalignment results. Output: {output_file}")
    
    try:
        # 1. Load Data
        shapes_df = load_halo_shapes()
        alignment_df = load_alignment_angles()
        stats_df = load_statistical_results()
        
        # 2. Merge
        merged_df = merge_datasets(shapes_df, alignment_df, stats_df)
        
        if merged_df.empty:
            logger.error("Merged dataset is empty. Check input data integrity.")
            sys.exit(1)
        
        # 3. Compute Summaries
        summary_stats = compute_summary_statistics(merged_df)
        
        # 4. Prepare Final Report
        final_df = generate_final_report(merged_df, summary_stats)
        
        # 5. Apply Associational Flag (T026)
        # Ensure the flag is set to true for this dataset
        if 'associational_only' not in final_df.columns:
            final_df['associational_only'] = True
        
        # 6. Save
        logger.info(f"Saving final report to {output_file}")
        final_df.to_csv(output_file, index=False)
        
        # 7. Update Metadata
        metadata_path = project_root / "data" / "metadata.yaml"
        if metadata_path.exists():
            metadata = load_metadata(metadata_path)
            # Add entry for final_report
            if 'datasets' not in metadata:
                metadata['datasets'] = {}
            
            metadata['datasets']['final_report'] = {
                'path': str(output_file.relative_to(project_root)),
                'description': 'Integrated report with halo shapes, alignment angles, and statistical results.',
                'associational_only': True,
                'row_count': len(final_df),
                'summary_stats': summary_stats
            }
            save_metadata(metadata, metadata_path)
            logger.info("Updated metadata.yaml with final_report entry.")
        
        logger.info("T040 completed successfully.")
        
        # Print summary to stdout
        print(f"Final Report Generated: {output_file}")
        print(f"Total Rows: {len(final_df)}")
        print(f"Columns: {list(final_df.columns)}")
        
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during integration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()