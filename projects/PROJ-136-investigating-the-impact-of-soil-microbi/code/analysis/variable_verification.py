"""
Variable Verification Module (T015)

Implements FR-008: Verifies presence of required variables in downloaded datasets.
Required variables:
  - OTU/ASV tables (handled via sample ID linkage)
  - plant_species
  - gps (latitude/longitude)
  - soil_type
  - sequencing_depth
  - sample_id
  - disease_type
  - incidence_rate
  - measurement_date

Output: data/processed/variable_verification_log.csv
Columns: sample_id, variable_name, status (present/missing)
"""
import os
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Set
import csv

# Import from existing API surface
from .logging_config import get_logger

logger = get_logger(__name__)

# FR-008 Required Variables
REQUIRED_VARIABLES = [
    "sample_id",
    "plant_species",
    "latitude",
    "longitude",
    "soil_type",
    "sequencing_depth",
    "disease_type",
    "incidence_rate",
    "measurement_date"
]

# Mapping of expected column names in raw files to canonical variable names
# This handles potential naming variations in source data
COLUMN_MAPPINGS = {
    "sample_id": ["sample_id", "sample_id", "SampleID", "Sample_ID", "id"],
    "plant_species": ["plant_species", "plant_species", "PlantSpecies", "HostSpecies", "crop"],
    "latitude": ["latitude", "lat", "Latitude", "GPS_Lat", "lat"],
    "longitude": ["longitude", "lon", "Longitude", "GPS_Lon", "lon"],
    "soil_type": ["soil_type", "soil_type", "SoilType", "soil_class"],
    "sequencing_depth": ["sequencing_depth", "sequencing_depth", "read_count", "total_reads", "depth"],
    "disease_type": ["disease_type", "disease_type", "DiseaseType", "disease", "pathogen"],
    "incidence_rate": ["incidence_rate", "incidence_rate", "IncidenceRate", "disease_rate", "rate"],
    "measurement_date": ["measurement_date", "measurement_date", "MeasurementDate", "date", "collection_date", "date"]
}

def _normalize_column_name(col_name: str) -> str:
    """Normalize column name for comparison."""
    return col_name.lower().strip().replace(" ", "_").replace("-", "_")

def _find_column_mapping(df: pd.DataFrame, variable_name: str) -> bool:
    """
    Check if any column in the dataframe matches the expected variable.
    Returns True if found, False otherwise.
    """
    if variable_name not in COLUMN_MAPPINGS:
        return False

    expected_patterns = COLUMN_MAPPINGS[variable_name]
    df_columns = [str(c) for c in df.columns]
    
    for col in df_columns:
        normalized_col = _normalize_column_name(col)
        for pattern in expected_patterns:
            if normalized_col == _normalize_column_name(pattern):
                return True
    return False

def verify_sample_variables(
    sample_file: Path, 
    variable_name: str, 
    results: List[Dict[str, Any]]
) -> None:
    """
    Verify presence of a variable in sample data file.
    Appends results to the provided list.
    """
    try:
        df = pd.read_csv(sample_file)
        found = _find_column_mapping(df, variable_name)
        
        # Get sample IDs if available
        sample_ids = []
        if "sample_id" in df.columns:
            sample_ids = df["sample_id"].tolist()
        elif "SampleID" in df.columns:
            sample_ids = df["SampleID"].tolist()
        else:
            # Fallback: use index if no ID column
            sample_ids = [f"sample_{i}" for i in range(len(df))]
        
        status = "present" if found else "missing"
        for sid in sample_ids:
            results.append({
                "sample_id": sid,
                "variable_name": variable_name,
                "status": status
            })
        
        logger.info(f"Sample file: {variable_name} -> {status}")
        
    except Exception as e:
        logger.error(f"Error processing sample file {sample_file}: {e}")
        # Mark all samples as missing if file can't be read
        sample_ids = [f"sample_{i}" for i in range(10)]  # Default fallback
        for sid in sample_ids:
            results.append({
                "sample_id": sid,
                "variable_name": variable_name,
                "status": "missing"
            })

def verify_disease_variables(
    disease_file: Path, 
    variable_name: str, 
    results: List[Dict[str, Any]]
) -> None:
    """
    Verify presence of a variable in disease incidence data file.
    Appends results to the provided list.
    """
    try:
        df = pd.read_csv(disease_file)
        found = _find_column_mapping(df, variable_name)
        
        # Get sample IDs if available
        sample_ids = []
        if "sample_id" in df.columns:
            sample_ids = df["sample_id"].tolist()
        elif "SampleID" in df.columns:
            sample_ids = df["SampleID"].tolist()
        else:
            # Fallback: use index if no ID column
            sample_ids = [f"disease_sample_{i}" for i in range(len(df))]
        
        status = "present" if found else "missing"
        for sid in sample_ids:
            results.append({
                "sample_id": sid,
                "variable_name": variable_name,
                "status": status
            })
        
        logger.info(f"Disease file: {variable_name} -> {status}")
        
    except Exception as e:
        logger.error(f"Error processing disease file {disease_file}: {e}")
        sample_ids = [f"disease_sample_{i}" for i in range(10)]
        for sid in sample_ids:
            results.append({
                "sample_id": sid,
                "variable_name": variable_name,
                "status": "missing"
            })

def run_variable_verification(
    sample_file: Path,
    disease_file: Path,
    output_file: Path
) -> None:
    """
    Main function to run variable verification across all required variables.
    
    Args:
        sample_file: Path to EMP/MG-RAST sample data
        disease_file: Path to disease incidence records
        output_file: Path to output verification log
    """
    logger.info("Starting variable verification (FR-008)")
    
    results = []
    
    # Verify each required variable in both datasets
    for var in REQUIRED_VARIABLES:
        # Check sample data
        verify_sample_variables(sample_file, var, results)
        
        # Check disease data
        verify_disease_variables(disease_file, var, results)
    
    # Create output directory if it doesn't exist
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write results to CSV
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['sample_id', 'variable_name', 'status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for result in results:
            writer.writerow(result)
    
    # Log summary
    present_count = sum(1 for r in results if r['status'] == 'present')
    missing_count = sum(1 for r in results if r['status'] == 'missing')
    total_count = len(results)
    
    logger.info(f"Verification complete: {present_count}/{total_count} variables present")
    logger.info(f"Missing variables: {missing_count}")
    
    # Log specific missing variables
    missing_vars = set(r['variable_name'] for r in results if r['status'] == 'missing')
    if missing_vars:
        logger.warning(f"Missing variables detected: {', '.join(sorted(missing_vars))}")
    
    logger.info(f"Results written to: {output_file}")

def main():
    """Entry point for variable verification task."""
    # Define paths based on project structure
    project_root = Path(__file__).parent.parent.parent
    data_raw_dir = project_root / "data" / "raw"
    data_processed_dir = project_root / "data" / "processed"
    
    # Identify input files (from T013/T014 outputs)
    sample_files = list(data_raw_dir.glob("emp_*.csv")) + list(data_raw_dir.glob("mg_*.csv"))
    disease_files = list(data_raw_dir.glob("disease_*.csv"))
    
    if not sample_files:
        logger.error("No sample data files found in data/raw/")
        return
    
    if not disease_files:
        logger.error("No disease incidence data files found in data/raw/")
        return
    
    # Use first found files (typically only one of each)
    sample_file = sample_files[0]
    disease_file = disease_files[0]
    
    output_file = data_processed_dir / "variable_verification_log.csv"
    
    run_variable_verification(sample_file, disease_file, output_file)

if __name__ == "__main__":
    main()
