import logging
import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import get_config
from logging_config import get_logger
from data.clean import validate_raw_record_fields, normalize_raw_data

logger = get_logger(__name__)

def load_raw_data(raw_path: Path) -> List[Dict[str, Any]]:
    """Load raw data from JSON file."""
    with open(raw_path, 'r') as f:
        data = json.load(f)
    
    # Handle different data structures
    if isinstance(data, dict):
        records = data.get("data", [])
        if not records:
            records = data.get("records", [])
        if not records:
            # Assume the whole dict is a list in a single key
            for key, value in data.items():
                if isinstance(value, list):
                    records = value
                    break
    else:
        records = data if isinstance(data, list) else [data]
    
    return records

def apply_schema_validation(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    T010: Apply field validation to raw records.
    
    Validates that all required fields are present and non-null.
    Excludes records that fail validation.
    """
    valid_records = []
    excluded_count = 0
    
    for i, record in enumerate(records):
        try:
            validate_raw_record_fields(record, f"record_{i}")
            valid_records.append(record)
        except ValueError as e:
            excluded_count += 1
            logger.warning(f"Excluded record {i}: {e}")
    
    logger.info(f"Schema validation: {len(valid_records)} valid, {excluded_count} excluded")
    return valid_records

def apply_independence_filter(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    T014: Filter records based on measurement method independence.
    
    Excludes records where measurement_method is missing or doesn't match
    the valid methods regex.
    """
    config = get_config()
    valid_methods = config.VALID_MEASUREMENT_METHODS
    
    valid_records = []
    excluded_count = 0
    
    for i, record in enumerate(records):
        method = record.get("measurement_method", "")
        
        if not method:
            excluded_count += 1
            logger.warning(f"Excluded record {i}: missing measurement_method")
            continue
        
        if not any(valid_method in str(method) for valid_method in valid_methods):
            excluded_count += 1
            logger.warning(f"Excluded record {i}: invalid measurement_method '{method}'")
            continue
        
        valid_records.append(record)
    
    logger.info(f"Independence filter: {len(valid_records)} valid, {excluded_count} excluded")
    return valid_records

def apply_monolithic_filter(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    T011: Filter for monolithic alloys only.
    
    Excludes composites based on alloy_type, is_composite, or composite_fraction.
    """
    valid_records = []
    excluded_count = 0
    
    for i, record in enumerate(records):
        # Priority order: alloy_type -> is_composite -> composite_fraction
        alloy_type = record.get("alloy_type", "")
        is_composite = record.get("is_composite", False)
        composite_fraction = record.get("composite_fraction", 0.0)
        
        # If alloy_type is specified, check it first
        if alloy_type:
            if alloy_type.lower() == "monolithic":
                valid_records.append(record)
                continue
            elif alloy_type.lower() == "composite":
                excluded_count += 1
                continue
        
        # Check is_composite flag
        if is_composite:
            excluded_count += 1
            continue
        
        # Check composite_fraction
        if composite_fraction > 0.0:
            excluded_count += 1
            continue
        
        # If none of the fields exist, exclude (as per spec)
        if not alloy_type and not is_composite and not composite_fraction:
            excluded_count += 1
            continue
        
        valid_records.append(record)
    
    logger.info(f"Monolithic filter: {len(valid_records)} valid, {excluded_count} excluded")
    return valid_records

def normalize_units(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    T012: Normalize units to standard format.
    
    - young_modulus: Convert MPa to GPa (divide by 1000) if needed
    - composition: Convert wt% to at% using atomic weights
    """
    from periodictable import elements

    normalized_records = []
    
    for i, record in enumerate(records):
        new_record = record.copy()
        
        # Normalize Young's modulus to GPa
        young_mod = new_record.get("young_modulus", 0)
        if young_mod > 1000:  # Likely in MPa
            new_record["young_modulus"] = young_mod / 1000.0
            logger.debug(f"Record {i}: Converted young_modulus from MPa to GPa")
        
        # Normalize composition to atomic fraction
        composition = new_record.get("composition", {})
        if composition:
            total_weight = sum(composition.values())
            if total_weight > 0:
                atomic_fractions = {}
                for element, weight_pct in composition.items():
                    if element in ["Al", "Cu", "Mg", "Si", "Zn", "Mn"]:
                        elem_obj = getattr(elements, element, None)
                        if elem_obj:
                            atomic_weight = elem_obj.A
                            atomic_fraction = (weight_pct / atomic_weight) / (total_weight / 100.0)
                            atomic_fractions[element] = atomic_fraction
                
                # Normalize to sum to 1.0
                total_atomic = sum(atomic_fractions.values())
                if total_atomic > 0:
                    for key in atomic_fractions:
                        atomic_fractions[key] /= total_atomic
                
                new_record["composition"] = atomic_fractions
        
        normalized_records.append(new_record)
    
    return normalized_records

def apply_major_element_filter(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    T013: Filter records where major element sum < 0.95.
    
    Calculates sum of Cu, Mg, Si, Zn, Mn atomic fractions.
    Excludes records where sum < 0.95.
    """
    config = get_config()
    major_elements = config.MAJOR_ALLOY_ELEMENTS if hasattr(config, 'MAJOR_ALLOY_ELEMENTS') else ["Cu", "Mg", "Si", "Zn", "Mn"]
    
    valid_records = []
    excluded_count = 0
    
    for i, record in enumerate(records):
        composition = record.get("composition", {})
        
        major_sum = sum(composition.get(elem, 0.0) for elem in major_elements)
        
        if major_sum < 0.95:
            excluded_count += 1
            logger.warning(f"Excluded record {i}: major element sum {major_sum:.4f} < 0.95")
            continue
        
        valid_records.append(record)
    
    logger.info(f"Major element filter: {len(valid_records)} valid, {excluded_count} excluded")
    return valid_records

def apply_ilr_transformation(records: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    T019: Apply ILR transformation to composition data.
    
    Uses fixed order ['Cu', 'Mg', 'Si', 'Zn', 'Mn'] for reproducibility.
    """
    try:
        from compositional import ilr
    except ImportError:
        logger.warning("compositional package not found, skipping ILR transformation")
        return pd.DataFrame(records)
    
    df = pd.DataFrame(records)
    composition_cols = ["Cu", "Mg", "Si", "Zn", "Mn"]
    
    # Extract composition data
    composition_data = df[composition_cols].values
    
    # Apply ILR transformation
    try:
        ilr_data = ilr(composition_data)
        
        # Create ILR feature columns
        for i in range(ilr_data.shape[1]):
            df[f'ilr_{i}'] = ilr_data[:, i]
        
        logger.info("ILR transformation applied successfully")
    except Exception as e:
        logger.warning(f"ILR transformation failed: {e}")
    
    return df

def run_cleaning_pipeline(raw_path: Path, output_path: Path) -> pd.DataFrame:
    """
    Run the full data cleaning pipeline.
    
    Steps:
    1. Load raw data
    2. Apply schema validation (T010)
    3. Apply independence filter (T014)
    4. Apply monolithic filter (T011)
    5. Normalize units (T012)
    6. Apply major element filter (T013)
    7. Apply ILR transformation (T019)
    8. Save to parquet
    """
    logger.info("Starting cleaning pipeline...")
    
    # Step 1: Load raw data
    records = load_raw_data(raw_path)
    logger.info(f"Loaded {len(records)} raw records")
    
    # Step 2: Schema validation (T010)
    records = apply_schema_validation(records)
    
    # Step 3: Independence filter (T014)
    records = apply_independence_filter(records)
    
    # Step 4: Monolithic filter (T011)
    records = apply_monolithic_filter(records)
    
    # Step 5: Normalize units (T012)
    records = normalize_units(records)
    
    # Step 6: Major element filter (T013)
    records = apply_major_element_filter(records)
    
    # Convert to DataFrame
    df = pd.DataFrame(records)
    
    # Step 7: ILR transformation (T019)
    df = apply_ilr_transformation(records)
    
    # Step 8: Save to parquet
    df.to_parquet(output_path, index=False)
    logger.info(f"Pipeline complete. Saved {len(df)} records to {output_path}")
    
    return df

def main():
    """CLI entry point for cleaning pipeline."""
    config = get_config()
    raw_path = Path(config.data_raw_dir) / "openml_aluminum.json"
    output_path = Path(config.data_processed_dir) / "alloys_clean.parquet"
    
    df = run_cleaning_pipeline(raw_path, output_path)
    logger.info(f"Final dataset: {len(df)} records")

if __name__ == "__main__":
    main()
