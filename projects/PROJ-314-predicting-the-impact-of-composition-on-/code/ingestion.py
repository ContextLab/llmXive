"""
Data ingestion module for ceramic data.
Handles fetching, cleaning, and descriptor computation.
"""
import os
import sys
import json
import logging
import re
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import memory monitor for wrapping ingestion tasks
from .memory_monitor import check_memory_limit, force_garbage_collection, log_memory_usage, HAS_PSUTIL

# Import config
from .config import get_int_config, get_float_config, get_config_value

# Import descriptors
from .descriptors import compute_descriptors

# Import logger
from . import logger

# Ensure logs directory exists
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

def derive_primary_anion_cation_group(composition: str) -> str:
    """
    Derive the primary anion-cation group from a composition string.
    
    Args:
        composition: Chemical composition string (e.g., "Al2O3").
    
    Returns:
        A string representing the primary anion-cation group (e.g., "O-Al").
    """
    # Basic parsing logic - in a real implementation, this would use chemparse
    # For now, we assume a simple format and extract elements
    elements = re.findall(r'([A-Z][a-z]?)(\d*)', composition)
    if not elements:
        return "Unknown"
    
    # Simple heuristic: first element is cation, last is anion (for oxides)
    # This is a placeholder; real logic would be more sophisticated
    cation = elements[0][0]
    anion = elements[-1][0]
    
    return f"{anion}-{cation}"

def apply_primary_anion_cation_group(df: Any) -> Any:
    """
    Apply the primary anion-cation group derivation to a DataFrame.
    
    Args:
        df: A pandas DataFrame with a 'composition' column.
    
    Returns:
        The DataFrame with a new 'primary_anion_cation_group' column.
    """
    df['primary_anion_cation_group'] = df['composition'].apply(derive_primary_anion_cation_group)
    return df

def clean_data_pipeline(df: Any) -> Any:
    """
    Run the full data cleaning pipeline.
    
    Args:
        df: Raw DataFrame.
    
    Returns:
        Cleaned DataFrame.
    """
    # Placeholder for cleaning steps
    # In a real implementation, this would include:
    # - Handling missing values
    # - Filtering invalid stoichiometry
    # - Imputing missing parameters
    return df

def generate_data_availability_report(total_rows: int, valid_rows: int, source_counts: Dict[str, int]) -> Dict[str, Any]:
    """
    Generate a data availability report.
    
    Args:
        total_rows: Total number of rows fetched.
        valid_rows: Number of valid rows after cleaning.
        source_counts: Dictionary of source names to row counts.
    
    Returns:
        A dictionary representing the report.
    """
    report = {
        "total_rows": total_rows,
        "valid_rows": valid_rows,
        "source_counts": source_counts,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "PASS" if valid_rows >= 30 else "FAIL"
    }
    return report

def validate_data_gap(df: Any) -> None:
    """
    Validate data gap and generate report if insufficient data.
    
    Args:
        df: Cleaned DataFrame.
    
    Raises:
        SystemExit: If valid rows < 30.
    """
    total_rows = len(df)
    valid_rows = total_rows  # Assuming df is already cleaned
    
    # Generate source counts (placeholder)
    source_counts = {"total": total_rows}
    
    report = generate_data_availability_report(total_rows, valid_rows, source_counts)
    
    # Ensure reports directory exists
    REPORTS_DIR = Path("data/reports")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    report_path = REPORTS_DIR / "data_availability_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Data availability report generated: {report_path}")
    
    if valid_rows < 30:
        logger.error(f"Insufficient data: {valid_rows} valid rows < 30 required.")
        print("Power Limitation: Insufficient data (N < 30)", file=sys.stderr)
        sys.exit(1)

def main() -> None:
    """
    Main entry point for data ingestion.
    Wraps the ingestion process with memory monitoring.
    """
    logger.info("Starting data ingestion pipeline.")
    log_memory_usage("Ingestion Start")
    
    # Check memory limit before starting (if psutil is available)
    if HAS_PSUTIL:
        try:
            check_memory_limit()
        except MemoryError as e:
            logger.error(f"Memory limit exceeded before ingestion: {e}")
            sys.exit(1)
    
    try:
        # Placeholder for actual ingestion logic
        # In a real implementation, this would:
        # 1. Fetch data from various sources (MP, NIST, arXiv)
        # 2. Clean and process the data
        # 3. Compute descriptors
        # 4. Validate data gap
        
        # For now, we create a dummy DataFrame to demonstrate the flow
        import pandas as pd
        df = pd.DataFrame({
            "composition": ["Al2O3", "SiO2", "ZrO2"],
            "weibull_modulus": [10.5, 8.2, 12.1],
            "sample_count": [50, 30, 45]
        })
        
        # Apply cleaning and descriptor computation
        df = apply_primary_anion_cation_group(df)
        df = clean_data_pipeline(df)
        
        # Validate data gap
        validate_data_gap(df)
        
        # Compute descriptors
        df = compute_descriptors(df)
        
        # Save processed data
        PROCESSED_DIR = Path("data/processed")
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        output_path = PROCESSED_DIR / "step4_final.csv"
        df.to_csv(output_path, index=False)
        logger.info(f"Processed data saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Error during ingestion: {e}", exc_info=True)
        sys.exit(1)
    finally:
        log_memory_usage("Ingestion End")
        if HAS_PSUTIL:
            force_garbage_collection()

if __name__ == "__main__":
    main()
