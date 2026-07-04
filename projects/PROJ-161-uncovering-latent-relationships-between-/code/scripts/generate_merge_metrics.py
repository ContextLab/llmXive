"""
Script to generate merge_metrics.json after the data processing pipeline.

This script loads the processed data (descriptors.csv) and calculates
the merge metrics required by SC-001.

Usage:
    python scripts/generate_merge_metrics.py
"""
import os
import sys
import logging
from pathlib import Path

import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import get_project_root, load_config
from src.data.metrics import generate_merge_metrics_report

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for generating merge metrics."""
    config = load_config()
    project_root = get_project_root()
    
    # Define paths
    processed_dir = Path(project_root) / "data" / "processed"
    descriptors_path = processed_dir / "descriptors.csv"
    
    # Check if descriptors file exists
    if not descriptors_path.exists():
        logger.error(f"Descriptors file not found: {descriptors_path}")
        logger.error("Please run the data processing pipeline first (T014-T015).")
        sys.exit(1)
    
    logger.info(f"Loading descriptors from: {descriptors_path}")
    
    try:
        df = pd.read_csv(descriptors_path)
        logger.info(f"Loaded {len(df)} rows from descriptors file.")
    except Exception as e:
        logger.error(f"Failed to load descriptors: {e}")
        sys.exit(1)
    
    # Determine total requested count
    # This should ideally come from the download step, but we can estimate
    # based on the number of unique InChIKeys requested
    # For now, we'll use the number of rows in the original SMILES file if available
    # or fall back to the merged count if we can't determine it
    
    # Try to find the original SMILES count from the raw data
    raw_dir = Path(project_root) / "data" / "raw"
    chembl_file = raw_dir / "chembl_smiles.csv"
    zinc_file = raw_dir / "zinc15_smiles.csv"
    
    total_requested = 0
    
    if chembl_file.exists():
        try:
            chembl_df = pd.read_csv(chembl_file)
            total_requested += len(chembl_df)
            logger.info(f"ChEMBL SMILES count: {len(chembl_df)}")
        except Exception as e:
            logger.warning(f"Could not read ChEMBL SMILES: {e}")
    
    if zinc_file.exists():
        try:
            zinc_df = pd.read_csv(zinc_file)
            total_requested += len(zinc_df)
            logger.info(f"ZINC15 SMILES count: {len(zinc_df)}")
        except Exception as e:
            logger.warning(f"Could not read ZINC15 SMILES: {e}")
    
    if total_requested == 0:
        # Fallback: use the number of rows in the descriptors file as a lower bound
        # This is not ideal but allows the script to complete
        logger.warning("Could not determine total requested count from raw files. Using descriptors count as fallback.")
        total_requested = len(df)
    
    logger.info(f"Total requested compounds: {total_requested}")
    
    # Generate metrics
    logger.info("Calculating merge metrics...")
    output_path = generate_merge_metrics_report(df, total_requested)
    
    logger.info(f"Merge metrics saved to: {output_path}")
    
    # Log summary
    with open(output_path, 'r') as f:
        import json
        metrics = json.load(f)
    
    logger.info(f"Merge Summary:")
    logger.info(f"  - Total Requested: {metrics['total_requested']}")
    logger.info(f"  - Matches: {metrics['matches']}")
    logger.info(f"  - Fraction: {metrics['fraction']:.4f}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
