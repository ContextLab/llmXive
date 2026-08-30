"""
Preprocessing pipeline for EBSD data:
1. Filter by confidence index (>= 0.1)
2. Re-index orientations to FCC symmetry using orix
3. Apply exclusion logic for low-reliability samples (>50% filtered)
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import numpy as np
import pandas as pd
from orix.crystal_map import CrystalMap, Orientation
from orix.quaternion.rotation import Rotation
from orix.crystal import Cubic
from orix.io import load as orix_load

# Import from project modules
from config import get_reductions, get_seed
from utils.logging import get_logger
from data.error_handling import apply_exclusion_logic, calculate_reliability_metrics
from data.models import EbsdSample, Symmetry, MaterialType

logger = get_logger(__name__)

CONFIDENCE_THRESHOLD = 0.1
RELIABILITY_THRESHOLD = 0.5  # 50% filtered points trigger exclusion

def load_ebsd_data(file_path: str) -> pd.DataFrame:
    """
    Load EBSD data from various formats (CSV, Parquet).
    
    Args:
        file_path: Path to the data file
        
    Returns:
        DataFrame with EBSD data
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    if path.suffix == '.parquet':
        df = pd.read_parquet(path)
    elif path.suffix == '.csv':
        df = pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")
    
    logger.info(f"Loaded {len(df)} rows from {file_path}")
    return df

def filter_by_confidence(df: pd.DataFrame, threshold: float = CONFIDENCE_THRESHOLD) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Filter orientations based on confidence index.
    
    Args:
        df: Input DataFrame with 'confidence' column
        threshold: Minimum confidence index (default: 0.1)
        
    Returns:
        Tuple of (filtered_df, excluded_df)
    """
    if 'confidence' not in df.columns:
        logger.warning("No 'confidence' column found. Skipping confidence filter.")
        return df, pd.DataFrame()
    
    filtered = df[df['confidence'] >= threshold].copy()
    excluded = df[df['confidence'] < threshold].copy()
    
    logger.info(f"Filtered {len(excluded)} rows with confidence < {threshold}")
    logger.info(f"Retained {len(filtered)} rows")
    
    return filtered, excluded

def reindex_to_fcc(df: pd.DataFrame) -> pd.DataFrame:
    """
    Re-index orientations to FCC symmetry using orix.
    
    This function:
    1. Converts Euler angles to orix Orientation objects
    2. Applies FCC symmetry operations
    3. Returns the re-indexed orientations
    
    Args:
        df: DataFrame with Euler angles (phi1, Phi, phi2)
        
    Returns:
        DataFrame with re-indexed orientations
    """
    required_cols = ['phi1', 'Phi', 'phi2']
    if not all(col in df.columns for col in required_cols):
        logger.error(f"Missing required Euler angle columns: {required_cols}")
        return df
    
    try:
        # Create Orientation objects from Euler angles (in degrees)
        # orix expects radians, so convert
        phi1_rad = np.radians(df['phi1'].values)
        Phi_rad = np.radians(df['Phi'].values)
        phi2_rad = np.radians(df['phi2'].values)
        
        # Create Rotation from Euler angles (Bunge convention)
        rotation = Rotation.from_euler(
            np.column_stack([phi1_rad, Phi_rad, phi2_rad]),
            degrees=False
        )
        
        # Apply FCC symmetry
        fcc_symmetry = Cubic()
        aligned_rotation = rotation.align_symmetry(fcc_symmetry)
        
        # Convert back to Euler angles (degrees)
        euler_aligned = np.degrees(aligned_rotation.to_euler())
        
        # Update DataFrame
        df_out = df.copy()
        df_out['phi1'] = euler_aligned[:, 0]
        df_out['Phi'] = euler_aligned[:, 1]
        df_out['phi2'] = euler_aligned[:, 2]
        
        logger.info(f"Re-indexed {len(df_out)} orientations to FCC symmetry")
        return df_out
        
    except Exception as e:
        logger.error(f"Failed to re-index orientations: {e}")
        return df

def process_ebsd_dataset(
    input_path: str,
    output_path: str,
    reduction_levels: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Main preprocessing function that orchestrates the pipeline.
    
    Args:
        input_path: Path to input EBSD data
        output_path: Path for processed output
        reduction_levels: Optional list of reduction levels to filter
        
    Returns:
        Dictionary with processing statistics
    """
    stats = {
        'input_rows': 0,
        'filtered_by_confidence': 0,
        'excluded_samples': 0,
        'final_rows': 0,
        'output_path': output_path
    }
    
    # Load data
    df = load_ebsd_data(input_path)
    stats['input_rows'] = len(df)
    
    # Filter by confidence
    df_filtered, df_excluded_conf = filter_by_confidence(df)
    stats['filtered_by_confidence'] = len(df_excluded_conf)
    
    # Re-index to FCC symmetry
    df_processed = reindex_to_fcc(df_filtered)
    
    # Apply exclusion logic for low-reliability samples
    # Group by sample ID and check reliability
    if 'sample_id' in df_processed.columns:
        reliability_metrics = calculate_reliability_metrics(df_processed)
        df_processed, excluded_samples = apply_exclusion_logic(
            df_processed, 
            reliability_metrics,
            threshold=RELIABILITY_THRESHOLD
        )
        stats['excluded_samples'] = len(excluded_samples)
    else:
        logger.warning("No 'sample_id' column found. Skipping sample exclusion logic.")
    
    # Filter by reduction levels if specified
    if reduction_levels is not None and 'reduction' in df_processed.columns:
        df_processed = df_processed[df_processed['reduction'].isin(reduction_levels)]
        logger.info(f"Filtered to reduction levels: {reduction_levels}")
    
    stats['final_rows'] = len(df_processed)
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save processed data
    if output_path.endswith('.parquet'):
        df_processed.to_parquet(output_path, index=False)
    elif output_path.endswith('.csv'):
        df_processed.to_csv(output_path, index=False)
    else:
        raise ValueError(f"Unsupported output format: {output_path}")
    
    logger.info(f"Processed data saved to {output_path}")
    logger.info(f"Final dataset: {stats['final_rows']} rows")
    
    return stats

def main():
    """
    CLI entry point for preprocessing.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Preprocess EBSD data')
    parser.add_argument('--input', required=True, help='Input data file path')
    parser.add_argument('--output', required=True, help='Output file path')
    parser.add_argument('--reductions', type=int, nargs='+', help='Reduction levels to include')
    
    args = parser.parse_args()
    
    # Get reduction levels from config if not provided
    reduction_levels = args.reductions
    if reduction_levels is None:
        try:
            reduction_levels = get_reductions()
            logger.info(f"Using reduction levels from config: {reduction_levels}")
        except Exception as e:
            logger.warning(f"Could not get reduction levels from config: {e}")
            reduction_levels = None
    
    # Run preprocessing
    stats = process_ebsd_dataset(
        args.input,
        args.output,
        reduction_levels
    )
    
    # Print summary
    print("\n=== Preprocessing Summary ===")
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
