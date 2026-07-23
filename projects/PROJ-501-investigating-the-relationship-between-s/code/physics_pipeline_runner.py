"""
T025 Implementation: Physics Pipeline Runner

Reads data/processed/merged_filtered.csv, applies physics models (T021-T023),
applies unphysical filters (T024a-T024b), and writes the clean result to
data/processed/derived_physics.csv.

Columns in output: cumulative_flux, mass_loss_rate, retention_fraction, is_valid
"""
import logging
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from physics import (
    calculate_quiescent_xuv,
    calculate_cumulative_flux,
    calculate_retention_fraction,
    calculate_unphysical_flag,
    apply_unphysical_filter,
    run_physics_pipeline
)
from utils import log_api_provenance

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for T025: Run physics models on merged data and save results.
    """
    input_path = Path("data/processed/merged_filtered.csv")
    output_path = Path("data/processed/derived_physics.csv")
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Required input file {input_path} does not exist. "
                              "Run T017 (data ingestion) first.")

    logger.info(f"Reading input data from {input_path}")
    df = pd.read_csv(input_path)
    
    logger.info(f"Loaded {len(df)} records from {input_path}")
    logger.info(f"Columns: {list(df.columns)}")

    # Apply physics models
    logger.info("Applying physics models...")
    
    # Step 1: Calculate quiescent XUV
    # T021: calculate_quiescent_xuv expects a DataFrame and returns a DataFrame with 'quiescent_xuv'
    try:
        df = calculate_quiescent_xuv(df)
        logger.info("Quiescent XUV calculation complete.")
    except Exception as e:
        logger.error(f"Error in quiescent XUV calculation: {e}")
        raise

    # Step 2: Calculate cumulative flux
    # T022: calculate_cumulative_flux expects a DataFrame and returns a DataFrame with 'cumulative_flux'
    try:
        df = calculate_cumulative_flux(df)
        logger.info("Cumulative flux calculation complete.")
    except Exception as e:
        logger.error(f"Error in cumulative flux calculation: {e}")
        raise

    # Step 3: Calculate retention fraction
    # T023: calculate_retention_fraction expects a DataFrame and returns a DataFrame with 'retention_fraction' and 'mass_loss_rate'
    try:
        df = calculate_retention_fraction(df)
        logger.info("Retention fraction calculation complete.")
    except Exception as e:
        logger.error(f"Error in retention fraction calculation: {e}")
        raise

    # Step 4: Calculate unphysical flag
    # T024a: calculate_unphysical_flag expects a DataFrame and returns a boolean Series or DataFrame with 'is_unphysical'
    try:
        df = calculate_unphysical_flag(df)
        logger.info("Unphysical flag calculation complete.")
    except Exception as e:
        logger.error(f"Error in unphysical flag calculation: {e}")
        raise

    # Step 5: Apply unphysical filter
    # T024b: apply_unphysical_filter expects a DataFrame and returns a filtered DataFrame with 'is_valid'
    try:
        df = apply_unphysical_filter(df)
        logger.info("Unphysical filter applied.")
    except Exception as e:
        logger.error(f"Error applying unphysical filter: {e}")
        raise

    # Verify required columns exist
    required_columns = ['cumulative_flux', 'mass_loss_rate', 'retention_fraction', 'is_valid']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns in output: {missing_cols}")
        raise ValueError(f"Physics pipeline did not produce expected columns: {missing_cols}")

    # Log statistics
    logger.info(f"Output statistics:")
    logger.info(f"  Total records: {len(df)}")
    logger.info(f"  Valid records: {df['is_valid'].sum()}")
    logger.info(f"  Invalid records: {(~df['is_valid']).sum()}")
    logger.info(f"  Cumulative flux range: [{df['cumulative_flux'].min():.2e}, {df['cumulative_flux'].max():.2e}]")
    logger.info(f"  Retention fraction range: [{df['retention_fraction'].min():.2f}, {df['retention_fraction'].max():.2f}]")

    # Save output
    logger.info(f"Saving results to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    
    logger.info(f"Successfully wrote {len(df)} records to {output_path}")
    
    # Log provenance
    log_api_provenance(
        operation="physics_pipeline",
        input_file=str(input_path),
        output_file=str(output_path),
        record_count=len(df),
        valid_count=int(df['is_valid'].sum())
    )

    return output_path

if __name__ == "__main__":
    main()
