"""
Data loading and verification utilities for GTEx data analysis.

This module handles the loading of GTEx v8 expression and phenotype data,
including verification gates for required clinical variables.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import numpy as np

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from utils.logging import get_logger
from utils.config import get_project_paths

logger = get_logger(__name__)

# Required clinical variables for metabolic syndrome analysis (ATP-III criteria)
REQUIRED_CLINICAL_COLUMNS = [
    "BMI",
    "Glucose",
    "BP_Systolic",  # Systolic Blood Pressure
    "BP_Diastolic", # Diastolic Blood Pressure (often combined or used separately)
    "Triglycerides", # TG
    "HDL_Cholesterol" # HDL
]

# Mapping from task description abbreviations to actual column names expected
# The task mentions: BMI, Glucose, BP, TG, HDL
# We map these to the standard GTEx/clinical column names we expect
COLUMN_MAPPING = {
    "BMI": "BMI",
    "Glucose": "Glucose",
    "BP": ["BP_Systolic", "BP_Diastolic"], # BP usually implies both or a composite
    "TG": "Triglycerides",
    "HDL": "HDL_Cholesterol"
}

def verify_clinical_columns(phenotype_df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Verify that all required clinical columns are present in the phenotype dataframe.
    
    Args:
        phenotype_df: DataFrame containing phenotype data.
        
    Returns:
        Tuple of (is_valid, list_of_missing_columns).
    """
    missing_columns = []
    
    # Check for BMI
    if "BMI" not in phenotype_df.columns:
        missing_columns.append("BMI")
        
    # Check for Glucose
    if "Glucose" not in phenotype_df.columns:
        missing_columns.append("Glucose")
        
    # Check for Blood Pressure (at least one of systolic or diastolic, or a specific BP column)
    # Based on the task description "BP", we expect a BP column or both systolic/diastolic
    # Let's check for a generic "BP" or the specific ones
    has_bp = False
    if "BP" in phenotype_df.columns or "BP_Systolic" in phenotype_df.columns or "BP_Diastolic" in phenotype_df.columns:
        has_bp = True
    if not has_bp:
        missing_columns.append("BP")
        
    # Check for Triglycerides (TG)
    if "Triglycerides" not in phenotype_df.columns:
        missing_columns.append("Triglycerides")
        
    # Check for HDL
    if "HDL_Cholesterol" not in phenotype_df.columns:
        missing_columns.append("HDL_Cholesterol")
        
    return len(missing_columns) == 0, missing_columns

def run_data_availability_gate(phenotype_df: pd.DataFrame, output_dir: Path) -> bool:
    """
    Run the column verification gate.
    
    Checks for required clinical variables (BMI, Glucose, BP, TG, HDL).
    If any are missing:
        1. Log fatal error.
        2. Write data_availability_gate.json with status="Exploratory - Insufficient Phenotype Data".
        3. Halt pipeline execution (exit code 1).
    If all present:
        1. Log success.
        2. Return True to proceed.
        
    Args:
        phenotype_df: DataFrame with phenotype data.
        output_dir: Directory to write the gate status file.
        
    Returns:
        True if gate passes, False (and exits) if it fails.
    """
    logger.info("Running data availability gate for clinical variables...")
    
    is_valid, missing_columns = verify_clinical_columns(phenotype_df)
    
    if not is_valid:
        error_msg = f"Critical missing clinical variables: {', '.join(missing_columns)}"
        logger.error(error_msg)
        logger.error("Pipeline cannot proceed without complete phenotype data for MetS classification.")
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        gate_status_file = output_dir / "data_availability_gate.json"
        gate_data = {
            "status": "Exploratory - Insufficient Phenotype Data",
            "missing_columns": missing_columns,
            "message": error_msg,
            "required_columns": ["BMI", "Glucose", "BP", "Triglycerides", "HDL_Cholesterol"]
        }
        
        with open(gate_status_file, "w") as f:
            json.dump(gate_data, f, indent=2)
        
        logger.info(f"Wrote gate status to {gate_status_file}")
        
        # Halt pipeline execution
        sys.exit(1)
    
    logger.info("Data availability gate PASSED. All required clinical variables present.")
    return True

def load_gtex_phenotype_data(data_path: Path) -> pd.DataFrame:
    """
    Load GTEx phenotype data from a CSV or TSV file.
    
    Args:
        data_path: Path to the phenotype data file.
        
    Returns:
        DataFrame with phenotype data.
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Phenotype data file not found: {data_path}")
    
    logger.info(f"Loading phenotype data from {data_path}")
    
    # Try to infer delimiter
    with open(data_path, 'r') as f:
        first_line = f.readline()
        if '\t' in first_line:
            delimiter = '\t'
        else:
            delimiter = ','
    
    df = pd.read_csv(data_path, delimiter=delimiter)
    logger.info(f"Loaded {len(df)} samples with {len(df.columns)} columns")
    return df

# Example usage / entry point for testing
if __name__ == "__main__":
    # This block is for manual testing of the gate logic
    # In the real pipeline, this would be called from a main script
    paths = get_project_paths()
    data_dir = paths["data_raw"]
    
    # Mock data for testing the gate logic without real files
    # In a real scenario, this would load from data_dir
    mock_data = {
        "SampleID": ["S1", "S2", "S3"],
        "BMI": [25.0, 30.0, 28.0],
        "Glucose": [90.0, 110.0, 95.0],
        "BP_Systolic": [120.0, 140.0, 125.0],
        "BP_Diastolic": [80.0, 90.0, 82.0],
        "Triglycerides": [150.0, 200.0, 160.0],
        "HDL_Cholesterol": [50.0, 35.0, 55.0]
    }
    
    test_df = pd.DataFrame(mock_data)
    
    # Run the gate
    run_data_availability_gate(test_df, paths["data_processed"])
    print("Gate passed successfully.")
