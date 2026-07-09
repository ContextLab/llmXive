import os
import sys
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import numpy as np
import pandas as pd

from orix.crystal_map import CrystalMap
from orix.quaternion import Orientation
from orix.crystal import cubic
from config import ConfigurationError, get_reductions
from utils.logging import get_logger, configure_lineage
from data.models import EbsdSample, Symmetry

logger = get_logger(__name__)

def load_ebsd_data(file_path: Path) -> Optional[pd.DataFrame]:
    """
    Load EBSD data from a CSV file.
    
    Args:
        file_path: Path to the CSV file containing EBSD data.
        
    Returns:
        DataFrame with EBSD data, or None if file is corrupted or missing.
    """
    try:
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return None
        
        # Attempt to load with pandas, handling potential corruption
        try:
            df = pd.read_csv(file_path)
            if df.empty:
                logger.warning(f"File is empty or contains no valid data: {file_path}")
                return None
            
            # Check for required columns
            required_cols = ['x', 'y', 'euler1', 'euler2', 'euler3', 'confidence']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                logger.warning(f"Missing required columns in {file_path}: {missing_cols}")
                return None
                
            return df
        except Exception as e:
            logger.warning(f"Corrupted file or invalid format in {file_path}: {str(e)}")
            return None
            
    except Exception as e:
        logger.warning(f"Error loading file {file_path}: {str(e)}")
        return None

def filter_by_confidence(df: pd.DataFrame, min_confidence: float = 0.1) -> pd.DataFrame:
    """
    Filter EBSD data by confidence index.
    
    Args:
        df: DataFrame containing EBSD data with a 'confidence' column.
        min_confidence: Minimum confidence index threshold.
        
    Returns:
        Filtered DataFrame.
    """
    if df.empty:
        return df
        
    filtered_df = df[df['confidence'] >= min_confidence].copy()
    filtered_count = len(df) - len(filtered_df)
    if filtered_count > 0:
        logger.info(f"Filtered {filtered_count} points with confidence < {min_confidence}")
    
    return filtered_df

def reindex_to_fcc(df: pd.DataFrame) -> pd.DataFrame:
    """
    Re-index orientations to FCC symmetry using orix.
    
    Args:
        df: DataFrame containing EBSD data with Euler angles.
        
    Returns:
        DataFrame with re-indexed Euler angles.
    """
    if df.empty:
        return df
        
    try:
        # Convert Euler angles to Orix format (degrees to radians)
        euler_rad = np.radians(df[['euler1', 'euler2', 'euler3']].values)
        
        # Create orientation object
        orientations = Orientation.from_euler(euler_rad, symmetry=cubic.OH)
        
        # Re-index to fundamental sector
        reindexed = orientations.fundamental_sector()
        
        # Convert back to Euler angles (radians to degrees)
        new_euler = np.degrees(reindexed.to_euler())
        
        df['euler1'] = new_euler[:, 0]
        df['euler2'] = new_euler[:, 1]
        df['euler3'] = new_euler[:, 2]
        
        logger.info(f"Re-indexed {len(df)} orientations to FCC symmetry")
        return df
    except Exception as e:
        logger.error(f"Error during FCC re-indexing: {str(e)}")
        raise

def process_ebsd_dataset(
    file_path: Path,
    material: str,
    reduction_level: Optional[float] = None
) -> Optional[EbsdSample]:
    """
    Process a single EBSD dataset file.
    
    Args:
        file_path: Path to the EBSD data file.
        material: Material type (e.g., 'Al', 'Cu', 'Ni').
        reduction_level: Cold rolling reduction percentage.
        
    Returns:
        EbsdSample object if successful, None otherwise.
    """
    # Load data with error handling
    df = load_ebsd_data(file_path)
    if df is None:
        logger.warning(f"Skipping file {file_path} due to loading errors")
        return None
    
    # Check for missing reduction level
    if reduction_level is None:
        # Try to infer from filename if possible, otherwise raise error
        logger.warning(f"Missing reduction level for {file_path}. Attempting to infer from filename...")
        try:
            # Look for pattern like "reduction_X%" or "X%" in filename
            import re
            match = re.search(r'(\d+)%', file_path.name)
            if match:
                reduction_level = float(match.group(1))
                logger.info(f"Inferred reduction level {reduction_level}% from filename")
            else:
                logger.error(f"Cannot determine reduction level for {file_path} and none provided")
                return None
        except Exception as e:
            logger.error(f"Error inferring reduction level: {str(e)}")
            return None
    
    # Filter by confidence index
    df = filter_by_confidence(df, min_confidence=0.1)
    
    if df.empty:
        logger.warning(f"All points filtered out for {file_path} due to low confidence")
        return None
    
    # Re-index to FCC symmetry
    try:
        df = reindex_to_fcc(df)
    except Exception as e:
        logger.error(f"Failed to re-index {file_path} to FCC symmetry: {str(e)}")
        return None
    
    # Create EbsdSample object
    try:
        sample = EbsdSample(
            material=material,
            reduction_level=reduction_level,
            data=df.to_dict('records'),
            file_path=str(file_path)
        )
        logger.info(f"Successfully processed {file_path} for {material} at {reduction_level}% reduction")
        return sample
    except Exception as e:
        logger.error(f"Error creating EbsdSample for {file_path}: {str(e)}")
        return None

def main():
    """
    Main entry point for EBSD preprocessing pipeline.
    Processes all EBSD files according to configuration.
    """
    # Setup logging
    configure_lineage("preprocessing")
    
    # Get reduction levels from config
    try:
        reduction_levels = get_reductions()
        if not reduction_levels:
            logger.error("No reduction levels found in configuration. Aborting.")
            sys.exit(1)
        logger.info(f"Processing reduction levels: {reduction_levels}")
    except ConfigurationError as e:
        logger.error(f"Configuration error: {str(e)}")
        sys.exit(1)
    
    # Define data directories
    raw_data_dir = Path("data/raw")
    processed_data_dir = Path("data/processed")
    
    if not raw_data_dir.exists():
        logger.error(f"Raw data directory not found: {raw_data_dir}")
        sys.exit(1)
    
    processed_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Process all EBSD files
    processed_samples = []
    skipped_files = []
    
    for material_dir in raw_data_dir.iterdir():
        if not material_dir.is_dir():
            continue
            
        material = material_dir.name
        logger.info(f"Processing material: {material}")
        
        for file_path in material_dir.glob("*.csv"):
            # Determine reduction level from filename or config
            reduction_level = None
            
            # Try to infer from filename
            try:
                import re
                match = re.search(r'(\d+)%', file_path.name)
                if match:
                    reduction_level = float(match.group(1))
            except:
                pass
            
            # Process the file
            sample = process_ebsd_dataset(file_path, material, reduction_level)
            
            if sample is not None:
                processed_samples.append(sample)
            else:
                skipped_files.append(str(file_path))
    
    # Log summary
    logger.info(f"Successfully processed {len(processed_samples)} samples")
    logger.info(f"Skipped {len(skipped_files)} files due to errors")
    
    if skipped_files:
        logger.warning("Skipped files:")
        for f in skipped_files:
            logger.warning(f"  - {f}")
    
    # Return processed samples for further use
    return processed_samples

if __name__ == "__main__":
    main()