"""
Clean and standardize BMG data.

Filters for 'bulk metallic glass' phase and standardizes units (FR-002, FR-003).
Reads from data/processed/raw_with_features.csv (output of ingest/features)
and writes to data/processed/cleaned_bmg.csv.
"""
import os
import sys
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger
from utils.provenance import record_artifact, compute_file_checksum, ensure_state_directory

logger = get_logger(__name__)

# Constants for unit conversion
# Assumed input units from ingest/features: 
# - Composition: at% (atomic percent) - already standardized in features step
# - Shear Modulus: GPa
# - Density: g/cm3
# - Temperature: K
# We ensure these are consistent and filter by phase.

INPUT_FILE = "data/processed/raw_with_features.csv"
OUTPUT_FILE = "data/processed/cleaned_bmg.csv"

# Target phase identifier (case-insensitive matching)
TARGET_PHASE_KEYWORDS = ["bulk metallic glass", "bmg", "metallic glass", "amorphous"]

def is_bmg_phase(phase_description: Optional[str]) -> bool:
    """
    Check if the phase description indicates a bulk metallic glass.
    
    Args:
        phase_description: String describing the material phase.
        
    Returns:
        True if the description matches BMG keywords.
    """
    if not phase_description:
        return False
    
    phase_lower = phase_description.lower()
    return any(keyword in phase_lower for keyword in TARGET_PHASE_KEYWORDS)

def standardize_units(row: Dict[str, str]) -> Dict[str, Any]:
    """
    Standardize units and types for a data row.
    
    Converts string values to appropriate numeric types and ensures
    units are consistent (GPa for modulus, at% for composition, etc.).
    
    Args:
        row: Dictionary representing a single data row.
        
    Returns:
        Dictionary with standardized values.
    """
    cleaned_row = {}
    
    # Copy string fields as-is (IDs, names, etc.)
    for key, value in row.items():
        if key in ["material_id", "formula", "alloy_family", "phase_description"]:
            cleaned_row[key] = value.strip() if isinstance(value, str) else value
        elif key == "shear_modulus_gpa":
            # Ensure shear modulus is float
            try:
                cleaned_row[key] = float(value) if value else None
            except (ValueError, TypeError):
                cleaned_row[key] = None
        elif key == "density_g_cm3":
            # Ensure density is float
            try:
                cleaned_row[key] = float(value) if value else None
            except (ValueError, TypeError):
                cleaned_row[key] = None
        elif key == "glass_transition_temp_k":
            # Ensure temperature is float
            try:
                cleaned_row[key] = float(value) if value else None
            except (ValueError, TypeError):
                cleaned_row[key] = None
        elif key == "melting_temp_k":
            # Ensure temperature is float
            try:
                cleaned_row[key] = float(value) if value else None
            except (ValueError, TypeError):
                cleaned_row[key] = None
        else:
            # Try to convert numeric fields (compositions, features)
            # Composition columns (e.g., "Fe_at_pct", "Zr_at_pct")
            if "_at_pct" in key or "_at%" in key:
                try:
                    cleaned_row[key] = float(value) if value else 0.0
                except (ValueError, TypeError):
                    cleaned_row[key] = 0.0
            # Feature columns (e.g., "delta", "delta_hmix")
            elif key in ["delta", "delta_hmix", "vec", "delta_chi", "vif_score"]:
                try:
                    cleaned_row[key] = float(value) if value else None
                except (ValueError, TypeError):
                    cleaned_row[key] = None
            else:
                # Fallback: keep as string if unknown
                cleaned_row[key] = value
    
    return cleaned_row

def clean_and_filter(input_path: Path, output_path: Path) -> int:
    """
    Read input CSV, filter for BMG phase, standardize units, and write output.
    
    Args:
        input_path: Path to input CSV file.
        output_path: Path to output CSV file.
        
    Returns:
        Number of rows written to output.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Reading input from {input_path}")
    
    rows_written = 0
    filtered_count = 0
    total_count = 0
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(input_path, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        
        if not fieldnames:
            raise ValueError("Input CSV has no headers")
        
        logger.info(f"Input columns: {fieldnames}")
        
        with open(output_path, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in reader:
                total_count += 1
                
                # Filter by phase
                phase_desc = row.get("phase_description", "")
                if not is_bmg_phase(phase_desc):
                    filtered_count += 1
                    continue
                
                # Standardize units
                cleaned_row = standardize_units(row)
                
                # Skip rows with missing target variable (shear_modulus_gpa)
                if cleaned_row.get("shear_modulus_gpa") is None:
                    logger.debug(f"Skipping row with missing shear modulus: {cleaned_row.get('material_id')}")
                    continue
                
                writer.writerow(cleaned_row)
                rows_written += 1
    
    logger.info(f"Processed {total_count} rows: {filtered_count} filtered by phase, {total_count - filtered_count - (total_count - rows_written)} with missing target, {rows_written} written")
    return rows_written

def main():
    """Main entry point for the cleaning pipeline."""
    logger.info("Starting BMG data cleaning pipeline (T017)")
    
    input_path = project_root / INPUT_FILE
    output_path = project_root / OUTPUT_FILE
    
    try:
        rows_written = clean_and_filter(input_path, output_path)
        
        if rows_written == 0:
            logger.warning("No valid rows written to output. Check input data and filters.")
            # Still record the empty artifact for provenance
            record_artifact(
                output_path,
                description="Cleaned BMG dataset (empty)",
                task_id="T017"
            )
            return 1
        
        # Record provenance
        checksum = compute_file_checksum(output_path)
        record_artifact(
            output_path,
            description=f"Cleaned BMG dataset ({rows_written} rows)",
            task_id="T017",
            checksum=checksum
        )
        
        logger.info(f"Successfully cleaned data: {rows_written} rows written to {output_path}")
        return 0
        
    except Exception as e:
        logger.error(f"Error during cleaning pipeline: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())