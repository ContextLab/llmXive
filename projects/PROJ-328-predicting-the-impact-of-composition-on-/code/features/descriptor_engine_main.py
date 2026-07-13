"""
Main entry point for descriptor engineering pipeline.

This script orchestrates the computation of compositional descriptors
from validated solder alloy data.
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from seed import init_reproducibility
from features.descriptor_engine import DescriptorEngine
from config import get_data_processed_dir, get_data_outputs_dir

def main():
    """
    Main function to run the descriptor engineering pipeline.
    
    Reads validated data, computes descriptors, and saves results.
    """
    init_reproducibility()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Starting descriptor engineering pipeline")
    
    # Define paths
    processed_dir = get_data_processed_dir()
    input_path = Path(processed_dir) / "solder_hardness_validated.csv"
    output_dir = get_data_outputs_dir()
    output_path = Path(output_dir) / "descriptors.csv"
    
    # Check if input file exists
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please run the ingestion pipeline first to generate validated data.")
        sys.exit(1)
    
    # Load data
    import pandas as pd
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Identify composition columns (all numeric columns except target)
    target_cols = ['hardness_hv', 'sample_id']
    composition_cols = [col for col in df.columns if col not in target_cols and df[col].dtype in ['float64', 'int64', 'float32', 'int32']]
    
    if not composition_cols:
        logger.error("No composition columns found in the data.")
        sys.exit(1)
    
    logger.info(f"Found {len(composition_cols)} composition columns: {composition_cols}")
    
    # Initialize descriptor engine
    engine = DescriptorEngine(elements=composition_cols)
    
    # Compute descriptors
    logger.info("Computing descriptors...")
    descriptors = engine.compute_all_descriptors(df[composition_cols])
    
    # Merge with original data
    result = pd.concat([df, descriptors], axis=1)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save results
    logger.info(f"Saving descriptors to {output_path}")
    result.to_csv(output_path, index=False)
    
    logger.info(f"Descriptor engineering complete. Output saved to {output_path}")
    logger.info(f"Total descriptors computed: {len(descriptors.columns)}")
    logger.info(f"Total samples processed: {len(result)}")

if __name__ == "__main__":
    main()