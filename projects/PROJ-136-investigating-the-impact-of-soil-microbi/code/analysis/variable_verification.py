"""
Variable verification module for FR-008 compliance.

Verifies the presence of required variables in sample and disease datasets
and generates a verification log with [MISSING_VARIABLE] markers.
"""
import os
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Set
import csv
from .logging_config import get_logger

logger = get_logger(__name__)

# FR-008 Required Variables
SAMPLE_VARIABLES = [
    'sample_id',
    'plant_species',
    'gps_latitude',
    'gps_longitude',
    'soil_type',
    'sequencing_depth'
]

DISEASE_VARIABLES = [
    'sample_id',
    'disease_type',
    'incidence_rate',
    'measurement_date'
]

def verify_sample_variables(sample_df: pd.DataFrame, sample_path: str) -> List[Dict[str, str]]:
    """
    Verify presence of required variables in sample data.
    
    Args:
        sample_df: DataFrame containing sample data
        sample_path: Path to the sample data file (for logging)
        
    Returns:
        List of verification records with sample_id, variable_name, status
    """
    logger.info(f"Verifying variables in sample data: {sample_path}")
    results = []
    
    if sample_df is None or sample_df.empty:
        logger.error(f"Sample data is empty or None: {sample_path}")
        return results
        
    available_columns = set(sample_df.columns)
    logger.info(f"Available columns in sample data: {available_columns}")
    
    for var in SAMPLE_VARIABLES:
        # Check if variable exists in columns
        if var in available_columns:
            # Check if column has non-null values
            non_null_count = sample_df[var].notna().sum()
            if non_null_count > 0:
                status = "present"
            else:
                status = "missing"
                logger.warning(f"Variable '{var}' exists but has no non-null values")
        else:
            status = "missing"
            logger.warning(f"Variable '{var}' is missing from sample data")
        
        # Add verification record for each sample (using sample_id or index)
        if 'sample_id' in available_columns:
            sample_ids = sample_df['sample_id'].unique()
        else:
            # Use index as fallback if sample_id doesn't exist
            sample_ids = [f"row_{i}" for i in range(len(sample_df))]
            
        for sid in sample_ids:
            results.append({
                'sample_id': str(sid),
                'variable_name': var,
                'status': status
            })
            
    return results

def verify_disease_variables(disease_df: pd.DataFrame, disease_path: str) -> List[Dict[str, str]]:
    """
    Verify presence of required variables in disease incidence data.
    
    Args:
        disease_df: DataFrame containing disease incidence data
        disease_path: Path to the disease data file (for logging)
        
    Returns:
        List of verification records with sample_id, variable_name, status
    """
    logger.info(f"Verifying variables in disease data: {disease_path}")
    results = []
    
    if disease_df is None or disease_df.empty:
        logger.error(f"Disease data is empty or None: {disease_path}")
        return results
        
    available_columns = set(disease_df.columns)
    logger.info(f"Available columns in disease data: {available_columns}")
    
    for var in DISEASE_VARIABLES:
        # Check if variable exists in columns
        if var in available_columns:
            # Check if column has non-null values
            non_null_count = disease_df[var].notna().sum()
            if non_null_count > 0:
                status = "present"
            else:
                status = "missing"
                logger.warning(f"Variable '{var}' exists but has no non-null values")
        else:
            status = "missing"
            logger.warning(f"Variable '{var}' is missing from disease data")
        
        # Add verification record for each sample
        if 'sample_id' in available_columns:
            sample_ids = disease_df['sample_id'].unique()
        else:
            # Use index as fallback if sample_id doesn't exist
            sample_ids = [f"row_{i}" for i in range(len(disease_df))]
            
        for sid in sample_ids:
            results.append({
                'sample_id': str(sid),
                'variable_name': var,
                'status': status
            })
            
    return results

def run_variable_verification(
    sample_path: str = None,
    disease_path: str = None,
    output_path: str = "data/processed/variable_verification_log.csv"
) -> pd.DataFrame:
    """
    Run variable verification on sample and disease datasets.
    
    Args:
        sample_path: Path to sample data CSV (from T013)
        disease_path: Path to disease data CSV (from T014)
        output_path: Path to write the verification log
        
    Returns:
        DataFrame containing the verification results
    """
    logger.info("Starting variable verification pipeline")
    
    # Load sample data if path provided
    sample_df = None
    if sample_path and os.path.exists(sample_path):
        try:
            sample_df = pd.read_csv(sample_path)
            logger.info(f"Loaded sample data from {sample_path} with {len(sample_df)} rows")
        except Exception as e:
            logger.error(f"Failed to load sample data: {e}")
            sample_df = None
    elif sample_path:
        logger.warning(f"Sample path provided but file not found: {sample_path}")
    else:
        logger.warning("No sample path provided, skipping sample verification")
        
    # Load disease data if path provided
    disease_df = None
    if disease_path and os.path.exists(disease_path):
        try:
            disease_df = pd.read_csv(disease_path)
            logger.info(f"Loaded disease data from {disease_path} with {len(disease_df)} rows")
        except Exception as e:
            logger.error(f"Failed to load disease data: {e}")
            disease_df = None
    elif disease_path:
        logger.warning(f"Disease path provided but file not found: {disease_path}")
    else:
        logger.warning("No disease path provided, skipping disease verification")
    
    # Collect all verification results
    all_results = []
    
    if sample_df is not None and not sample_df.empty:
        sample_results = verify_sample_variables(sample_df, sample_path)
        all_results.extend(sample_results)
        
    if disease_df is not None and not disease_df.empty:
        disease_results = verify_disease_variables(disease_df, disease_path)
        all_results.extend(disease_results)
    
    if not all_results:
        logger.warning("No verification results generated - input data may be missing")
    
    # Create DataFrame
    verification_df = pd.DataFrame(all_results)
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write to CSV
    if not verification_df.empty:
        verification_df.to_csv(output_path, index=False)
        logger.info(f"Verification log written to {output_path}")
        
        # Log summary
        present_count = len(verification_df[verification_df['status'] == 'present'])
        missing_count = len(verification_df[verification_df['status'] == 'missing'])
        logger.info(f"Verification summary: {present_count} present, {missing_count} missing")
    else:
        # Create empty file with headers if no data
        verification_df.to_csv(output_path, index=False)
        logger.info(f"Empty verification log written to {output_path}")
    
    return verification_df

def main():
    """Main entry point for variable verification."""
    logger.info("Running variable verification main")
    
    # Default paths based on project structure
    project_root = Path(__file__).parent.parent.parent
    sample_path = project_root / "data" / "raw" / "emp_agricultural_samples.csv"
    disease_path = project_root / "data" / "raw" / "disease_incidence_records.csv"
    output_path = project_root / "data" / "processed" / "variable_verification_log.csv"
    
    # Run verification
    run_variable_verification(
        sample_path=str(sample_path),
        disease_path=str(disease_path),
        output_path=str(output_path)
    )
    
    logger.info("Variable verification completed")

if __name__ == "__main__":
    main()
