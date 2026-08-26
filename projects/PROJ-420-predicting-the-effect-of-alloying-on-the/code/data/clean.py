"""
Data cleaning pipeline for alloy data.
Implements T010-T016: Validation, filtering, normalization, and logging.
"""
import sys
import logging
import argparse
import json
import re
import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import from sibling modules
from config import get_config
from logging_config import get_logger, log_operation
from schemas.alloy_record import AlloyRecord

logger = get_logger(__name__)

def log_exclusion(step: str, count: int, reason: str):
    """Log exclusion records to data/logs/exclusion_log.txt."""
    config = get_config()
    log_path = config.data_logs_dir / "exclusion_log.txt"
    
    # Ensure logs directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Append to log file in CSV format
    with open(log_path, 'a') as f:
        f.write(f"{step},{count},{reason}\n")
    
    logger.info(f"Logged exclusion: step={step}, count={count}, reason={reason}")

def validate_raw_record_fields(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    T010: Validate raw data contains required fields at schema level.
    Required fields: poisson_ratio, young_modulus, composition (Cu, Mg, Si, Zn, Mn), measurement_method
    """
    log_operation("validate_raw_record_fields", status="started")
    
    required_fields = ['poisson_ratio', 'young_modulus', 'composition']
    composition_elements = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
    
    valid_records = []
    excluded_count = 0
    
    for record in records:
        # Check top-level required fields
        missing_top_level = [f for f in required_fields if f not in record or record[f] is None]
        
        if missing_top_level:
            excluded_count += 1
            continue
        
        # Check composition elements
        composition = record.get('composition', {})
        missing_elements = [elem for elem in composition_elements if elem not in composition or composition[elem] is None]
        
        if missing_elements:
            excluded_count += 1
            continue
        
        valid_records.append(record)
    
    if excluded_count > 0:
        log_exclusion("T010_schema_validation", excluded_count, "missing_required_fields")
    
    log_operation("validate_raw_record_fields", status="completed", valid_count=len(valid_records))
    return valid_records

def apply_independence_filter(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    T014: Independence verification - attempt inference of measurement_method.
    If measurement_method is missing, try to infer from source metadata.
    If inference fails, exclude the record.
    """
    log_operation("apply_independence_filter", status="started")
    
    inference_keywords = ['Ultrasonic', 'Direct', 'Resonant', 'Impulse']
    
    valid_records = []
    excluded_missing = 0
    excluded_inference_failed = 0
    
    for record in records:
        measurement_method = record.get('measurement_method')
        
        if measurement_method is not None and measurement_method != '':
            valid_records.append(record)
            continue
        
        # Attempt inference from source metadata
        source_metadata = record.get('source_metadata', {})
        inferred = False
        
        for keyword in inference_keywords:
            # Check various metadata fields for keywords
            for field in ['method', 'technique', 'measurement_type', 'description']:
                field_value = source_metadata.get(field, '')
                if isinstance(field_value, str) and keyword in field_value:
                    record['measurement_method'] = keyword
                    record['measurement_method_inferred'] = True
                    valid_records.append(record)
                    inferred = True
                    break
            if inferred:
                break
        
        if not inferred:
            # Check if there's any other indication in the record
            excluded_missing += 1
    
    if excluded_missing > 0:
        log_exclusion("T014_independence_filter", excluded_missing, "missing_measurement_method")
    
    log_operation("apply_independence_filter", status="completed", valid_count=len(valid_records))
    return valid_records

def apply_monolithic_filter(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    T011: Filter for monolithic alloys only.
    Definition: alloy_type == 'monolithic' OR is_composite == False OR composite_fraction == 0.0
    """
    log_operation("apply_monolithic_filter", status="started")
    
    valid_records = []
    excluded_count = 0
    
    for record in records:
        # Priority: alloy_type -> is_composite -> composite_fraction
        alloy_type = record.get('alloy_type')
        is_composite = record.get('is_composite')
        composite_fraction = record.get('composite_fraction')
        
        is_monolithic = False
        
        if alloy_type is not None and alloy_type == 'monolithic':
            is_monolithic = True
        elif is_composite is not None and is_composite == False:
            is_monolithic = True
        elif composite_fraction is not None and composite_fraction == 0.0:
            is_monolithic = True
        
        if is_monolithic:
            valid_records.append(record)
        else:
            excluded_count += 1
    
    if excluded_count > 0:
        log_exclusion("T011_monolithic_filter", excluded_count, "non_monolithic_alloy")
    
    log_operation("apply_monolithic_filter", status="completed", valid_count=len(valid_records))
    return valid_records

def normalize_units(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    T012: Unit normalization.
    - Convert composition from wt% to at% if needed
    - Convert young_modulus from MPa to GPa if needed
    """
    log_operation("normalize_units", status="started")
    
    from periodictable import elements
    
    valid_records = []
    
    for record in records:
        composition = record.get('composition', {})
        unit = record.get('composition_unit', 'at%')
        
        if unit == 'wt%':
            # Convert wt% to at%
            atomic_weights = {elem: elements.__dict__[elem].mass for elem in composition.keys()}
            total_wt = sum(composition.values())
            
            # Calculate atomic fractions
            at_fractions = {}
            for elem, wt_frac in composition.items():
                at_frac = (wt_frac / atomic_weights[elem]) / sum(w / atomic_weights[e] for e, w in composition.items())
                at_fractions[elem] = at_frac
            
            record['composition'] = at_fractions
            record['composition_unit'] = 'at%'
        
        # Convert young_modulus to GPa
        young_modulus = record.get('young_modulus')
        young_unit = record.get('young_modulus_unit', 'GPa')
        
        if young_unit == 'MPa':
            record['young_modulus'] = young_modulus / 1000.0
            record['young_modulus_unit'] = 'GPa'
        
        valid_records.append(record)
    
    log_operation("normalize_units", status="completed", count=len(valid_records))
    return valid_records

def apply_major_element_filter(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    T013: Exclude entries where major element sum < 0.95.
    Major elements: Cu, Mg, Si, Zn, Mn
    """
    log_operation("apply_major_element_filter", status="started")
    
    major_elements = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
    
    valid_records = []
    excluded_count = 0
    
    for record in records:
        composition = record.get('composition', {})
        major_sum = sum(composition.get(elem, 0) for elem in major_elements)
        
        if major_sum >= 0.95:
            valid_records.append(record)
        else:
            excluded_count += 1
    
    if excluded_count > 0:
        log_exclusion("T013_major_element_filter", excluded_count, "major_element_sum_lt_0.95")
    
    log_operation("apply_major_element_filter", status="completed", valid_count=len(valid_records))
    return valid_records

def run_cleaning_pipeline():
    """
    T015: Orchestrate the full cleaning pipeline.
    Steps:
    1. Load raw data
    2. Apply schema validation (T010)
    3. Apply independence filter (T014) - MUST run before others
    4. Apply monolithic filter (T011)
    5. Normalize units (T012)
    6. Apply major element filter (T013)
    7. Log exclusions (T016)
    8. Validate final count and save parquet
    """
    log_operation("run_cleaning_pipeline", status="started")
    
    config = get_config()
    
    # Load raw data from both sources
    raw_data_path = config.data_raw_dir / "merged_raw_data.json"
    
    if not raw_data_path.exists():
        logger.error(f"Raw data file not found: {raw_data_path}")
        sys.exit(1)
    
    with open(raw_data_path, 'r') as f:
        records = json.load(f)
    
    logger.info(f"Loaded {len(records)} raw records")
    
    # Initialize exclusion log
    log_path = config.data_logs_dir / "exclusion_log.txt"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    # Clear previous log
    with open(log_path, 'w') as f:
        f.write("step,count,reason\n")
    
    # Step 1: Schema validation (T010)
    records = validate_raw_record_fields(records)
    
    # Step 2: Independence filter (T014) - MUST run before others
    records = apply_independence_filter(records)
    
    # Step 3: Monolithic filter (T011)
    records = apply_monolithic_filter(records)
    
    # Step 4: Normalize units (T012)
    records = normalize_units(records)
    
    # Step 5: Major element filter (T013)
    records = apply_major_element_filter(records)
    
    # Step 6: Ensure all exclusions are logged (T016)
    # Already logged in each step above
    
    # Step 7: Validate final count
    final_count = len(records)
    logger.info(f"Final record count after filtering: {final_count}")
    
    if final_count < 50:
        logger.error(f"Insufficient data after filtering ({final_count} entries). Minimum required: 50")
        sys.exit(1)
    
    # Step 8: Save cleaned dataset to parquet
    output_path = config.data_processed_dir / "alloys_clean.parquet"
    
    # Convert to DataFrame
    df = pd.DataFrame(records)
    
    # Save to parquet
    df.to_parquet(output_path, index=False)
    
    logger.info(f"Saved cleaned dataset to {output_path}")
    
    log_operation("run_cleaning_pipeline", status="completed", final_count=final_count)
    
    return df

def main():
    """Entry point for data cleaning."""
    run_cleaning_pipeline()

if __name__ == "__main__":
    main()
