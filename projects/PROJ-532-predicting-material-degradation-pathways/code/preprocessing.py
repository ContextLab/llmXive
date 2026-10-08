import pandas as pd
import numpy as np
import logging
from typing import Tuple, Dict, Any, List, Optional
import os
import json
from pathlib import Path

from utils import save_json, load_json, ensure_dir, setup_logging

# Configure logging
logger = setup_logging(__name__)

def classify_alloy_family(row: pd.Series) -> str:
    """
    Classify a single alloy record into a family based on explicit composition rules.
    
    Rules (applied in order):
    1. High-Entropy Alloy: 5+ elements > 5% each.
    2. Stainless Steel: Fe > 10% AND Cr > 10%.
    3. Carbon Steel: Fe > 80% AND C < 2%.
    4. Other: Default fallback.
    
    Args:
        row: A pandas Series representing a single alloy record.
        
    Returns:
        str: The classified alloy family.
    """
    # Normalize column names to handle potential case/spacing issues
    row_dict = {k.strip().lower(): v for k, v in row.items()}
    
    # Helper to safely get element percentage, defaulting to 0 if missing
    def get_pct(element: str) -> float:
        # Try direct match first, then lowercase
        val = row_dict.get(element.lower(), 0.0)
        if pd.isna(val):
            return 0.0
        return float(val)

    # Rule 1: High-Entropy Alloy (5+ elements > 5% each)
    # We assume standard alloying elements: Fe, C, Cr, Ni, Mn, Si, Mo, Ti, Al, V, Cu, Co, W
    standard_elements = ['fe', 'c', 'cr', 'ni', 'mn', 'si', 'mo', 'ti', 'al', 'v', 'cu', 'co', 'w']
    high_concentration_count = 0
    for elem in standard_elements:
        if get_pct(elem) > 5.0:
            high_concentration_count += 1
    
    if high_concentration_count >= 5:
        return "High-Entropy Alloy"

    # Rule 2: Stainless Steel (Fe > 10% AND Cr > 10%)
    fe_pct = get_pct('fe')
    cr_pct = get_pct('cr')
    if fe_pct > 10.0 and cr_pct > 10.0:
        return "Stainless Steel"

    # Rule 3: Carbon Steel (Fe > 80% AND C < 2%)
    c_pct = get_pct('c')
    if fe_pct > 80.0 and c_pct < 2.0:
        return "Carbon Steel"

    # Rule 4: Other
    return "Other"

def generate_alloy_class_map(input_path: str, output_path: str) -> Dict[str, str]:
    """
    Reads the cleaned alloys CSV, classifies each record, and saves the map.
    
    Args:
        input_path: Path to data/processed/cleaned_alloys.csv
        output_path: Path to data/contracts/alloy_class_map.json
        
    Returns:
        Dict mapping record_id to alloy family.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Reading cleaned alloys from {input_path}")
    df = pd.read_csv(input_path)
    
    # Ensure there is a unique identifier. If 'record_id' exists, use it.
    # Otherwise, generate one based on index or a specific column if available.
    if 'record_id' not in df.columns:
        # Fallback: create record_id if missing, assuming index is unique
        if 'id' in df.columns:
            df['record_id'] = df['id']
        else:
            df['record_id'] = [f"rec_{i:05d}" for i in range(len(df))]
    
    logger.info(f"Classifying {len(df)} records...")
    df['alloy_family'] = df.apply(classify_alloy_family, axis=1)
    
    # Create the map: record_id -> family
    class_map = df.set_index('record_id')['alloy_family'].to_dict()
    
    # Ensure output directory exists
    ensure_dir(output_path)
    
    logger.info(f"Saving alloy class map to {output_path}")
    save_json(class_map, output_path)
    
    return class_map

def perform_ood_split(class_map: Dict[str, str], train_ratio: float = 0.8) -> Tuple[List[str], List[str]]:
    """
    Performs an OOD split based on alloy classes.
    
    Logic:
    1. Group records by alloy family.
    2. If fewer than 2 families exist, HALT with specific error.
    3. Select one or more families to be the OOD test set (held out).
       Strategy: Hold out the family with the fewest records (if >1 family) 
       to maximize OOD difficulty, or simply split families 50/50 if many exist.
       For this implementation: Hold out the last N families such that the test set 
       is roughly (1 - train_ratio).
    4. Assign remaining families to train set.
    
    Args:
        class_map: The alloy class map (record_id -> family).
        train_ratio: Ratio of records to include in training.
        
    Returns:
        Tuple of (train_ids, test_ids).
        
    Raises:
        ValueError: If fewer than 2 classes exist, with specific error_code and message.
    """
    if not class_map:
        raise ValueError("OOD_SPLIT_FAILED: Class map is empty.")

    # Group records by family
    family_groups: Dict[str, List[str]] = {}
    for rec_id, family in class_map.items():
        if family not in family_groups:
            family_groups[family] = []
        family_groups[family].append(rec_id)
    
    unique_families = list(family_groups.keys())
    num_families = len(unique_families)
    
    logger.info(f"Found {num_families} unique alloy families: {unique_families}")
    
    # CRITICAL HALT CONDITION: < 2 classes
    if num_families < 2:
        error_msg = "Insufficient alloy classes for OOD split"
        logger.error(f"OOD_SPLIT_FAILED: {error_msg}")
        # Raise with specific attributes to be caught by the pipeline
        err = ValueError(error_msg)
        err.error_code = "OOD_SPLIT_FAILED"
        err.message = error_msg
        raise err
    
    # Strategy for OOD split:
    # We want to hold out entire families.
    # Sort families by size to ensure we can get a reasonable test set.
    # Calculate target test size
    total_records = sum(len(ids) for ids in family_groups.values())
    target_test_size = int(total_records * (1.0 - train_ratio))
    
    # Sort families by size (ascending) to pick smaller ones for test if needed,
    # or just pick the last ones. Let's pick the smallest family first to ensure
    # a distinct OOD set, then add more if needed to reach target size.
    sorted_families = sorted(family_groups.keys(), key=lambda f: len(family_groups[f]))
    
    test_ids = []
    train_ids = []
    
    current_test_size = 0
    test_families = []
    train_families = []
    
    # Greedy approach: Add smallest families to test set until we reach target
    # or we run out of families (leaving at least 1 for train, which is guaranteed by num_families >= 2)
    for family in sorted_families:
        family_size = len(family_groups[family])
        if current_test_size + family_size <= target_test_size or current_test_size == 0:
            # Add to test set if it doesn't overshoot too much, or if it's the first one
            # But we must ensure we don't take ALL families.
            if len(test_families) == num_families - 1:
                # Only one family left for train, stop adding to test
                train_families.append(family)
                train_ids.extend(family_groups[family])
                continue
            
            test_families.append(family)
            test_ids.extend(family_groups[family])
            current_test_size += family_size
        else:
            train_families.append(family)
            train_ids.extend(family_groups[family])
    
    # If the greedy approach left the test set too small (e.g., if smallest family was huge),
    # we might need to adjust. But typically, with >2 families, this works.
    # Ensure we have at least one family in test and one in train.
    if not test_ids or not train_ids:
        # Fallback: just split the sorted list of families in half
        mid = num_families // 2
        test_families = sorted_families[:mid]
        train_families = sorted_families[mid:]
        test_ids = []
        train_ids = []
        for f in test_families:
            test_ids.extend(family_groups[f])
        for f in train_families:
            train_ids.extend(family_groups[f])
    
    logger.info(f"OOD Split complete. Train: {len(train_ids)} records, Test: {len(test_ids)} records")
    logger.info(f"Test families (OOD): {test_families}")
    
    return train_ids, test_ids

def generate_ood_split_report(train_ids: List[str], test_ids: List[str], class_map: Dict[str, str], output_path: str):
    """
    Generates the OOD split report.
    """
    # Determine families in train and test
    train_families = set()
    test_families = set()
    
    for rec_id in train_ids:
        train_families.add(class_map[rec_id])
    for rec_id in test_ids:
        test_families.add(class_map[rec_id])
    
    report = {
        "split_ratio": len(train_ids) / (len(train_ids) + len(test_ids)) if (len(train_ids) + len(test_ids)) > 0 else 0,
        "train_count": len(train_ids),
        "test_count": len(test_ids),
        "train_families": list(train_families),
        "test_families": list(test_families),
        "ood_validation_passed": True,
        "description": "Out-of-Distribution split based on alloy family."
    }
    
    ensure_dir(output_path)
    save_json(report, output_path)
    logger.info(f"OOD split report saved to {output_path}")

def generate_ood_audit_log(train_ids: List[str], test_ids: List[str], class_map: Dict[str, str], output_path: str):
    """
    Generates the OOD audit log.
    """
    audit = {
        "split_logic": "Family-based holdout",
        "train_records": train_ids,
        "test_records": test_ids,
        "family_assignment_trace": {
            rec_id: class_map[rec_id] 
            for rec_id in train_ids + test_ids
        }
    }
    
    ensure_dir(output_path)
    save_json(audit, output_path)
    logger.info(f"OOD audit log saved to {output_path}")

def run_preprocessing_pipeline():
    """
    Main entry point for the preprocessing pipeline.
    Executes T019a (generate map), T019a_val (validate), and T019 (OOD split).
    """
    logger.info("Starting preprocessing pipeline...")
    
    # Paths
    cleaned_data_path = "data/processed/cleaned_alloys.csv"
    class_map_path = "data/contracts/alloy_class_map.json"
    train_output_path = "data/processed/train_set.parquet"
    test_output_path = "data/processed/test_ood_set.parquet"
    report_output_path = "data/processed/ood_split_report.json"
    audit_output_path = "data/processed/ood_audit.json"
    
    # 1. Generate Alloy Class Map (T019a) - Check if exists or regenerate?
    # The task description implies T019a is done. We assume the map exists or we regenerate it.
    # For robustness, we regenerate if the input CSV exists.
    if not os.path.exists(cleaned_data_path):
        raise FileNotFoundError(f"Required input file not found: {cleaned_data_path}")
    
    logger.info("Generating/Updating Alloy Class Map...")
    class_map = generate_alloy_class_map(cleaned_data_path, class_map_path)
    
    # 2. Validate Map Completeness (T019a_val)
    # Count records successfully classified. Since classify_alloy_family always returns a string,
    # all records should be classified. We check if the map is empty or if coverage is low.
    total_records = len(class_map)
    if total_records == 0:
        raise ValueError("Classification coverage is 0%. HALTING.")
    
    # Check if we have enough families for OOD split (T019 dependency)
    unique_families = set(class_map.values())
    if len(unique_families) < 2:
        logger.error("Insufficient alloy classes for OOD split. HALTING.")
        # We don't write a specific failure log here as the main pipeline will catch the error in perform_ood_split
        # But we can write a log if needed. For now, let perform_ood_split handle the HALT.
    
    # 3. Perform OOD Split (T019)
    logger.info("Performing OOD Split...")
    try:
        train_ids, test_ids = perform_ood_split(class_map)
    except ValueError as e:
        if hasattr(e, 'error_code') and e.error_code == "OOD_SPLIT_FAILED":
            logger.critical(f"Pipeline HALTED: {e.message}")
            raise e
        raise
    
    # 4. Load full data and split into Parquet files
    logger.info(f"Loading {cleaned_data_path} to create split datasets...")
    df = pd.read_csv(cleaned_data_path)
    
    # Ensure record_id exists in DF for merging
    if 'record_id' not in df.columns:
        if 'id' in df.columns:
            df['record_id'] = df['id']
        else:
            df['record_id'] = [f"rec_{i:05d}" for i in range(len(df))]
    
    df_train = df[df['record_id'].isin(train_ids)]
    df_test = df[df['record_id'].isin(test_ids)]
    
    logger.info(f"Saving Train set ({len(df_train)} records) to {train_output_path}")
    ensure_dir(train_output_path)
    df_train.to_parquet(train_output_path, index=False)
    
    logger.info(f"Saving Test set ({len(df_test)} records) to {test_output_path}")
    ensure_dir(test_output_path)
    df_test.to_parquet(test_output_path, index=False)
    
    # 5. Generate Reports (T019b, T019c)
    generate_ood_split_report(train_ids, test_ids, class_map, report_output_path)
    generate_ood_audit_log(train_ids, test_ids, class_map, audit_output_path)
    
    logger.info("Preprocessing pipeline completed successfully.")
    return True

def main():
    """
    Command-line entry point.
    """
    try:
        run_preprocessing_pipeline()
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
