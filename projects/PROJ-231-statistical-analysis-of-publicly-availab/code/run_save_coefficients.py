import os
import sys
import json
import logging
import pickle
from pathlib import Path

from basis import expand_ensemble_to_b_spline, reconstruct_and_verify
from ingestion import download_cmip6_data, apply_imputation_to_dataset, standardize_ensemble
from config import get_project_root, get_data_dir
from logging_config import setup_logging, get_logger
from update_state import update_state, compute_directory_hash

logger = get_logger(__name__)

def save_b_spline_coefficients(ensemble_data: dict, basis_info: dict, output_dir: Path):
    """
    Save processed B-spline coefficients and metadata to disk.
    
    Args:
        ensemble_data: Dictionary containing processed ensemble data
        basis_info: Dictionary containing basis dimension K and other metadata
        output_dir: Directory path where coefficients will be saved
    
    Returns:
        Path to the saved coefficients file
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    coefficients_file = output_dir / "b_spline_coefficients.pkl"
    metadata_file = output_dir / "basis_metadata.json"
    
    # Save coefficients using pickle for complex data structures
    with open(coefficients_file, 'wb') as f:
        pickle.dump(ensemble_data, f)
    
    # Save metadata as JSON
    with open(metadata_file, 'w') as f:
        json.dump(basis_info, f, indent=2)
    
    logger.info(f"Saved B-spline coefficients to {coefficients_file}")
    logger.info(f"Saved basis metadata to {metadata_file}")
    
    return coefficients_file

def main():
    """
    Main entry point for saving B-spline coefficients.
    This script:
    1. Downloads and processes CMIP6 data (if not already done)
    2. Applies imputation and standardization
    3. Performs B-spline basis expansion
    4. Saves coefficients to data/processed/
    5. Updates the project state hash
    """
    # Setup logging
    setup_logging(level=logging.INFO)
    
    project_root = get_project_root()
    data_dir = get_data_dir()
    processed_dir = data_dir / "processed"
    
    logger.info("Starting B-spline coefficient saving pipeline")
    
    try:
        # Step 1: Download and preprocess data
        logger.info("Downloading CMIP6 data...")
        raw_data = download_cmip6_data()
        
        # Step 2: Apply imputation for missing values
        logger.info("Applying spline-based imputation...")
        imputed_data = apply_imputation_to_dataset(raw_data)
        
        # Step 3: Standardize ensemble across spatial grids
        logger.info("Standardizing ensemble...")
        standardized_data = standardize_ensemble(imputed_data)
        
        # Step 4: Perform B-spline basis expansion
        logger.info("Performing B-spline basis expansion...")
        # We need to determine optimal basis dimension first
        from basis import select_optimal_basis_dimension, pilot_basis_selection
        
        # Use pilot selection to determine K
        K = pilot_basis_selection(standardized_data)
        logger.info(f"Selected optimal basis dimension K={K}")
        
        # Expand to B-spline representation
        coefficients, basis_info = expand_ensemble_to_b_spline(standardized_data, K)
        
        # Step 5: Verify reconstruction quality
        logger.info("Verifying reconstruction quality...")
        mse = reconstruct_and_verify(standardized_data, coefficients, basis_info)
        logger.info(f"Reconstruction MSE: {mse:.6f}")
        
        if mse > 0.01:
            logger.warning(f"MSE {mse:.6f} exceeds threshold 0.01, but continuing...")
        
        # Step 6: Save coefficients to disk
        logger.info("Saving coefficients to processed directory...")
        saved_file = save_b_spline_coefficients(
            coefficients, 
            {
                "basis_dimension": K,
                "mse": float(mse),
                "num_ensemble_members": len(standardized_data),
                "processed_timestamp": str(datetime.now(timezone.utc))
            },
            processed_dir
        )
        
        # Step 7: Update state hash
        logger.info("Updating project state hash...")
        update_state(project_root)
        
        logger.info("B-spline coefficient saving pipeline completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed with error: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
