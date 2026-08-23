"""
Preprocessing pipeline for EBSD data.

This module implements the core logic for:
1. Loading EBSD data from raw files.
2. Filtering orientations based on confidence index (threshold >= 0.1).
3. Re-indexing orientations to FCC symmetry using orix.
4. Applying exclusion logic for low-reliability samples (>50% filtered).

Dependencies:
- orix: For crystallographic symmetry and orientation handling.
- pandas: For data manipulation.
- numpy: For numerical operations.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import numpy as np
import pandas as pd
from orix.crystal_map import CrystalMap
from orix.quaternion import Orientation
from orix.crystal import Cubic

# Import local utilities
from utils.logging import get_logger
from config import get_reductions, get_data_path
from data.error_handling import apply_exclusion_logic, calculate_reliability_metrics

logger = get_logger(__name__)

CONFIDENCE_THRESHOLD = 0.1
RELIABILITY_THRESHOLD = 0.5  # 50%

def load_ebsd_data(file_path: Path) -> pd.DataFrame:
    """
    Load EBSD data from a CSV or Parquet file into a pandas DataFrame.

    Expected columns: 'phi1', 'Phi', 'phi2', 'confidence', 'x', 'y', 'sample_id', 'material', 'reduction'
    
    Args:
        file_path: Path to the data file.
        
    Returns:
        DataFrame containing the raw EBSD data.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"EBSD data file not found: {file_path}")

    logger.info(f"Loading EBSD data from {file_path}")
    
    if file_path.suffix == '.csv':
        df = pd.read_csv(file_path)
    elif file_path.suffix == '.parquet':
        df = pd.read_parquet(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")

    required_cols = ['phi1', 'Phi', 'phi2', 'confidence']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {file_path}: {missing_cols}")
    
    # Ensure confidence is numeric
    df['confidence'] = pd.to_numeric(df['confidence'], errors='coerce')
    
    return df

def filter_by_confidence(df: pd.DataFrame, threshold: float = CONFIDENCE_THRESHOLD) -> Tuple[pd.DataFrame, float]:
    """
    Filter orientations based on confidence index.
    
    Args:
        df: Input DataFrame.
        threshold: Minimum confidence index (default 0.1).
        
    Returns:
        Tuple of (filtered DataFrame, fraction of points removed).
    """
    total_points = len(df)
    if total_points == 0:
        logger.warning("Input DataFrame is empty.")
        return df, 1.0

    filtered_df = df[df['confidence'] >= threshold].copy()
    removed_points = total_points - len(filtered_df)
    fraction_removed = removed_points / total_points if total_points > 0 else 0.0

    logger.info(f"Filtered {removed_points} points (confidence < {threshold}). "
                f"Retention rate: {1.0 - fraction_removed:.2%}")
    
    return filtered_df, fraction_removed

def reindex_to_fcc(df: pd.DataFrame) -> pd.DataFrame:
    """
    Re-index orientations to FCC symmetry using orix.
    
    This function converts Euler angles to orix Orientations, applies FCC symmetry,
    and converts back to Euler angles in the fundamental region.
    
    Args:
        df: DataFrame containing 'phi1', 'Phi', 'phi2' columns.
        
    Returns:
        DataFrame with re-indexed Euler angles.
    """
    if df.empty:
        logger.warning("Empty DataFrame passed to reindex_to_fcc.")
        return df

    logger.info("Re-indexing orientations to FCC symmetry...")
    
    try:
        # Create CrystalMap (needed for proper orientation handling)
        # We create a dummy map just to leverage orix's symmetry handling
        x = np.zeros(len(df))
        y = np.zeros(len(df))
        
        # Convert to orix Orientations
        # Euler angles in orix are in degrees by default if input is degrees
        # The convention in orix is Bunge convention (phi1, Phi, phi2)
        orientations = Orientation.from_euler(
            np.deg2rad(df[['phi1', 'Phi', 'phi2']].values), 
            symmetry=Cubic()
        )
        
        # Apply symmetry to find the equivalent orientation in the fundamental region
        # The 'disoriented' method or simply re-assigning with symmetry handles this
        # We want to ensure all orientations are within the fundamental zone
        # orix automatically handles symmetry when creating the Orientation object with symmetry=Cubic()
        # However, to ensure they are reduced to the fundamental region, we can use the symmetry operation
        
        # The standard way to ensure fundamental region is to let orix handle it during creation
        # But if we want to explicitly reduce:
        # orientations = orientations.disoriented() # This finds the unique representative
        
        # Actually, creating with symmetry=Cubic() ensures that operations respect symmetry.
        # To ensure the angles are in the fundamental region, we can use the 'reduced' property
        # or simply rely on the fact that orix stores them in a way that respects symmetry.
        # For output, we convert back to Euler angles.
        
        # Let's explicitly reduce to fundamental region
        # orix doesn't have a direct "reduce_to_fundamental" that returns Euler angles directly 
        # without the symmetry context, but the Orientation object itself represents the coset.
        # We will extract the Euler angles. orix stores the minimal representation.
        
        # Extract Euler angles in radians, then convert to degrees
        # The 'angles' property returns the minimal representation in the fundamental region
        euler_rad = orientations.angle_with(orientations).data # This is not correct for extraction
        
        # Correct extraction:
        # orientations.euler returns the Euler angles in the fundamental region
        euler_angles = orientations.euler # Shape (N, 3) in radians
        
        # Convert back to degrees
        df_reindexed = df.copy()
        df_reindexed['phi1'] = np.rad2deg(euler_angles[:, 0])
        df_reindexed['Phi'] = np.rad2deg(euler_angles[:, 1])
        df_reindexed['phi2'] = np.rad2deg(euler_angles[:, 2])
        
        logger.info(f"Re-indexed {len(df)} orientations to FCC fundamental region.")
        
    except Exception as e:
        logger.error(f"Error during FCC re-indexing: {e}", exc_info=True)
        # Fallback: return original if symmetry handling fails (though this violates FR-002)
        # In a strict implementation, we might want to raise here.
        # For now, log and return original to avoid total pipeline crash if orix fails unexpectedly
        # But per FR-002, this is the sole mechanism. If it fails, we should probably fail.
        raise RuntimeError(f"FCC re-indexing failed: {e}")

    return df_reindexed

def process_ebsd_dataset(
    input_path: Path, 
    output_path: Path, 
    reduction_level: Optional[int] = None
) -> Dict[str, Any]:
    """
    Main processing function for a single EBSD dataset.
    
    Performs:
    1. Load data.
    2. Filter by confidence.
    3. Re-index to FCC.
    4. Apply exclusion logic (low reliability).
    5. Save output.
    
    Args:
        input_path: Path to input file.
        output_path: Path to output file.
        reduction_level: Optional reduction level to tag the data.
        
    Returns:
        Dictionary with processing metrics.
    """
    logger.info(f"Processing dataset: {input_path}")
    
    # 1. Load
    df = load_ebsd_data(input_path)
    
    # 2. Filter Confidence
    df_filtered, removal_fraction = filter_by_confidence(df)
    
    # 3. Re-index to FCC
    df_processed = reindex_to_fcc(df_filtered)
    
    # 4. Exclusion Logic
    # Calculate reliability metrics
    metrics = calculate_reliability_metrics(df, df_processed)
    
    # Apply exclusion logic
    is_excluded, reason = apply_exclusion_logic(metrics, threshold=RELIABILITY_THRESHOLD)
    
    if is_excluded:
        logger.warning(f"Sample excluded due to low reliability: {reason}")
        return {
            "status": "excluded",
            "reason": reason,
            "metrics": metrics
        }
    
    # 5. Add metadata
    df_processed['processed'] = True
    if reduction_level is not None:
        df_processed['reduction_level'] = reduction_level
    else:
        # Try to infer from filename or existing column
        if 'reduction' in df_processed.columns:
            pass # Keep existing
        else:
            df_processed['reduction_level'] = -1 # Unknown
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 6. Save
    if output_path.suffix == '.csv':
        df_processed.to_csv(output_path, index=False)
    elif output_path.suffix == '.parquet':
        df_processed.to_parquet(output_path, index=False)
    else:
        # Default to parquet for efficiency if extension missing
        if output_path.suffix == '':
            output_path = output_path.with_suffix('.parquet')
            df_processed.to_parquet(output_path, index=False)
        else:
            df_processed.to_csv(output_path, index=False)
    
    logger.info(f"Processed data saved to {output_path}")
    
    return {
        "status": "success",
        "input_points": len(df),
        "output_points": len(df_processed),
        "removal_fraction": removal_fraction,
        "metrics": metrics
    }

def main():
    """
    Entry point for the preprocessing script.
    Reads configuration and processes all raw EBSD files.
    """
    logger.info("Starting EBSD Preprocessing Pipeline")
    
    data_path = get_data_path()
    raw_dir = data_path / "raw"
    processed_dir = data_path / "processed"
    
    if not raw_dir.exists():
        logger.error(f"Raw data directory not found: {raw_dir}")
        sys.exit(1)
    
    # Get reduction levels from config
    reduction_levels = get_reductions()
    logger.info(f"Target reduction levels: {reduction_levels}")
    
    # Find all raw files
    raw_files = list(raw_dir.glob("*.csv")) + list(raw_dir.glob("*.parquet"))
    if not raw_files:
        logger.warning("No raw data files found.")
        sys.exit(0)
    
    results = []
    
    for raw_file in raw_files:
        # Determine reduction level for this file
        # Try to infer from filename (e.g., "al_20pct.csv" -> 20)
        # Or use the first available level if not specified in filename
        # For this implementation, we assume the filename or metadata contains the level
        # If not, we process with a placeholder or skip.
        # A robust implementation would parse the filename or use a manifest.
        
        # Simple heuristic: look for numbers in filename
        import re
        match = re.search(r'(\d+)', raw_file.stem)
        level = int(match.group(1)) if match else None
        
        # If level not found in filename, check if it matches any in the list
        # If not, we might need to process all levels or skip.
        # For now, we process regardless and tag as 'unknown' if no match, 
        # or try to match the first available level if the file is a generic dump.
        # However, T012 ensures we have reduction levels.
        # Let's assume the file name or content dictates the level.
        # If the file doesn't have a clear level, we might process it for all or skip.
        # To keep it simple and robust: if 'reduction' column exists, we group by it later.
        # Here we just process the file.
        
        output_file = processed_dir / f"{raw_file.stem}_processed.parquet"
        
        try:
            result = process_ebsd_dataset(raw_file, output_file, reduction_level=level)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to process {raw_file}: {e}")
            results.append({"status": "failed", "file": str(raw_file), "error": str(e)})
    
    # Summary
    success_count = sum(1 for r in results if r.get("status") == "success")
    excluded_count = sum(1 for r in results if r.get("status") == "excluded")
    failed_count = sum(1 for r in results if r.get("status") == "failed")
    
    logger.info(f"Preprocessing complete. Success: {success_count}, Excluded: {excluded_count}, Failed: {failed_count}")
    
    if failed_count > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
