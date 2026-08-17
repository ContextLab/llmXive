import pandas as pd
import numpy as np
import logging
from typing import Tuple, Dict, Any, List, Optional
import os
import json
from pathlib import Path

from utils import load_json, save_json, ensure_dir, setup_logging

# Configure logging
logger = setup_logging("preprocessing")

# Constants
DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"
CONTRACTS_DIR = DATA_DIR / "contracts"

def classify_alloy_family(row: pd.Series) -> str:
    """
    Classify alloy family based on composition rules.
    Rules:
    - If Fe > 10% AND Cr > 10% THEN 'Stainless Steel'
    - If Fe > 80% AND C < 2% THEN 'Carbon Steel'
    - If 5+ elements > 5% each THEN 'High-Entropy Alloy'
    - Else 'Other'
    """
    fe = row.get('Fe', 0)
    cr = row.get('Cr', 0)
    c = row.get('C', 0)
    
    # Check High-Entropy Alloy first (most specific)
    # Count elements > 5%
    elements_over_5pct = sum(1 for val in row.values if isinstance(val, (int, float)) and val > 5.0)
    if elements_over_5pct >= 5:
        return 'High-Entropy Alloy'
    
    # Check Stainless Steel
    if fe > 10 and cr > 10:
        return 'Stainless Steel'
    
    # Check Carbon Steel
    if fe > 80 and c < 2:
        return 'Carbon Steel'
    
    return 'Other'

def generate_alloy_class_map(df: pd.DataFrame, output_path: Path) -> Dict[str, List[int]]:
    """
    Generate alloy class map based on composition rules.
    Returns a dictionary mapping alloy class to list of indices.
    """
    logger.info("Generating alloy class map...")
    
    # Apply classification
    df['alloy_class'] = df.apply(classify_alloy_family, axis=1)
    
    # Create map
    class_map = {}
    for idx, row in df.iterrows():
        alloy_class = row['alloy_class']
        if alloy_class not in class_map:
            class_map[alloy_class] = []
        class_map[alloy_class].append(idx)
    
    # Save map
    ensure_dir(output_path.parent)
    save_json(class_map, str(output_path))
    logger.info(f"Alloy class map saved to {output_path}")
    
    return class_map

def perform_ood_split(df: pd.DataFrame, class_map: Dict[str, List[int]], seed: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform OOD split based on alloy class.
    Holds out entire alloy classes for the test set.
    """
    logger.info("Performing OOD split...")
    
    # Filter classes with at least 1 record
    valid_classes = [cls for cls, indices in class_map.items() if len(indices) > 0]
    
    if len(valid_classes) < 2:
        raise ValueError(f"Insufficient alloy classes for OOD split. Found {len(valid_classes)} class(es).")
    
    # Sort classes for deterministic split
    valid_classes.sort()
    
    # Hold out the last class (or last 2 if more than 4 classes) for OOD test
    # This ensures the test set contains entirely unseen alloy families
    if len(valid_classes) > 4:
        test_classes = valid_classes[-2:]
    else:
        test_classes = [valid_classes[-1]]
    
    train_classes = [cls for cls in valid_classes if cls not in test_classes]
    
    # Collect indices
    train_indices = []
    test_indices = []
    
    for cls in train_classes:
        train_indices.extend(class_map[cls])
    for cls in test_classes:
        test_indices.extend(class_map[cls])
    
    # Split data
    train_df = df.iloc[train_indices].reset_index(drop=True)
    test_df = df.iloc[test_indices].reset_index(drop=True)
    
    logger.info(f"OOD Split complete: {len(train_indices)} train, {len(test_indices)} test")
    logger.info(f"Train classes: {train_classes}")
    logger.info(f"Test classes (OOD): {test_classes}")
    
    return train_df, test_df

def load_json(file_path: str) -> Any:
    """Load JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def generate_ood_split_report(
    train_df: pd.DataFrame, 
    test_df: pd.DataFrame, 
    class_map: Dict[str, List[int]],
    ood_classes: List[str],
    output_path: Path
) -> Dict[str, Any]:
    """
    Generate OOD split report with statistics.
    """
    logger.info("Generating OOD split report...")
    
    # Calculate statistics
    train_classes = [cls for cls in class_map.keys() if cls not in ood_classes]
    
    report = {
        "split_ratio": len(test_df) / (len(train_df) + len(test_df)),
        "train_size": len(train_df),
        "test_size": len(test_df),
        "train_classes": train_classes,
        "test_classes": ood_classes,
        "ood_validation_passed": len(ood_classes) > 0 and len(train_classes) > 0,
        "total_classes": len(class_map)
    }
    
    # Save report
    ensure_dir(output_path.parent)
    save_json(report, str(output_path))
    logger.info(f"OOD split report saved to {output_path}")
    
    return report

def generate_ood_audit_log(
    df: pd.DataFrame,
    class_map: Dict[str, List[int]],
    train_indices: List[int],
    test_indices: List[int],
    ood_classes: List[str],
    output_path: Path
) -> Dict[str, Any]:
    """
    Generate OOD audit log containing the raw logic trace of the split decision.
    This includes the classification rules applied, the class distribution,
    and the exact indices assigned to train/test sets.
    """
    logger.info("Generating OOD audit log...")
    
    audit = {
        "task_id": "T019c",
        "description": "OOD Audit Log - Raw logic trace of split decision",
        "classification_rules": {
            "stainless_steel": "Fe > 10% AND Cr > 10%",
            "carbon_steel": "Fe > 80% AND C < 2%",
            "high_entropy_alloy": "5+ elements > 5% each",
            "other": "Default"
        },
        "class_distribution": {
            cls: len(indices) for cls, indices in class_map.items()
        },
        "split_logic": {
            "total_classes": len(class_map),
            "train_classes": [cls for cls in class_map.keys() if cls not in ood_classes],
            "test_classes": ood_classes,
            "selection_rule": "Hold out last class(es) for OOD test set",
            "train_count": len(train_indices),
            "test_count": len(test_indices)
        },
        "raw_indices": {
            "train_indices": train_indices,
            "test_indices": test_indices
        },
        "validation": {
            "ood_classes_exist": len(ood_classes) > 0,
            "train_classes_exist": len([cls for cls in class_map.keys() if cls not in ood_classes]) > 0,
            "no_overlap": set(train_indices).isdisjoint(set(test_indices))
        }
    }
    
    # Save audit log
    ensure_dir(output_path.parent)
    save_json(audit, str(output_path))
    logger.info(f"OOD audit log saved to {output_path}")
    
    return audit

def run_preprocessing_pipeline() -> None:
    """
    Run the full preprocessing pipeline:
    1. Load cleaned alloys
    2. Generate alloy class map
    3. Perform OOD split
    4. Generate OOD split report
    5. Generate OOD audit log
    """
    logger.info("Starting preprocessing pipeline...")
    
    # Paths
    cleaned_alloys_path = PROCESSED_DIR / "cleaned_alloys.csv"
    class_map_path = CONTRACTS_DIR / "alloy_class_map.json"
    train_set_path = PROCESSED_DIR / "train_set.parquet"
    test_ood_set_path = PROCESSED_DIR / "test_ood_set.parquet"
    ood_split_report_path = PROCESSED_DIR / "ood_split_report.json"
    ood_audit_path = PROCESSED_DIR / "ood_audit.json"
    
    # Load cleaned data
    logger.info(f"Loading cleaned alloys from {cleaned_alloys_path}")
    if not cleaned_alloys_path.exists():
        raise FileNotFoundError(f"Cleaned alloys file not found: {cleaned_alloys_path}")
    
    df = pd.read_csv(cleaned_alloys_path)
    logger.info(f"Loaded {len(df)} records")
    
    # Generate alloy class map
    class_map = generate_alloy_class_map(df, class_map_path)
    
    # Validate class map
    valid_classes = [cls for cls, indices in class_map.items() if len(indices) > 0]
    if len(valid_classes) < 2:
        raise ValueError(f"Insufficient alloy classes for OOD split. Found {len(valid_classes)} class(es).")
    
    # Perform OOD split
    train_df, test_df = perform_ood_split(df, class_map)
    
    # Determine OOD classes (test classes)
    ood_classes = list(set(train_df['alloy_class'].unique()) ^ set(df['alloy_class'].unique()))
    if not ood_classes:
        # If no unique classes in test, infer from the split logic
        # This happens if the test set contains classes not in train
        train_classes_set = set(train_df['alloy_class'].unique())
        all_classes_set = set(df['alloy_class'].unique())
        ood_classes = list(all_classes_set - train_classes_set)
    
    # Save train and test sets
    train_df.to_parquet(train_set_path, index=False)
    test_df.to_parquet(test_ood_set_path, index=False)
    logger.info(f"Saved train set to {train_set_path} ({len(train_df)} records)")
    logger.info(f"Saved test set to {test_ood_set_path} ({len(test_df)} records)")
    
    # Generate OOD split report
    generate_ood_split_report(train_df, test_df, class_map, ood_classes, ood_split_report_path)
    
    # Generate OOD audit log
    train_indices = train_df.index.tolist()
    test_indices = test_df.index.tolist()
    generate_ood_audit_log(
        df, class_map, train_indices, test_indices, ood_classes, ood_audit_path
    )
    
    logger.info("Preprocessing pipeline completed successfully")

def main():
    """Main entry point."""
    run_preprocessing_pipeline()

if __name__ == "__main__":
    main()