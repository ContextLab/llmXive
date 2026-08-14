import pandas as pd
import numpy as np
import logging
from typing import Tuple, Dict, Any, List, Optional
import os
import json
import random
from pathlib import Path

# Import shared utilities
from utils import ensure_dir, load_json, save_json, setup_logging, get_env_var

# Configure logging
logger = setup_logging("preprocessing")

# Constants
OOD_SPLIT_REPORT_PATH = "data/processed/ood_split_report.json"
RANDOM_SEED = int(get_env_var("RANDOM_SEED", "42"))
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

# Alloy family classification rules based on typical compositional thresholds
# These rules are heuristic but align with standard metallurgical definitions
ALLOY_FAMILY_RULES = {
    "High-Entropy Alloys": {
        # HEAs typically have 5+ principal elements with concentrations between 5-35 at%
        # We approximate using weight % and number of elements > 5%
        "min_elements_above_5pct": 5,
        "max_element_concentration_pct": 40,  # No single element > 40%
        "description": "High-Entropy Alloys (HEA) - 5+ principal elements"
    },
    "Stainless Steels": {
        # Stainless steels: Fe base, Cr > 10.5%, often Ni present
        "min_chromium_pct": 10.5,
        "max_iron_pct": 85,  # Fe is major but not overwhelming
        "description": "Stainless Steels - Cr > 10.5%"
    },
    "Carbon Steels": {
        # Carbon steels: Fe base, low alloying, C < 2%
        "max_iron_pct": 98,
        "min_iron_pct": 80,
        "max_total_alloying_pct": 5,  # Sum of non-Fe, non-C elements
        "description": "Carbon Steels - High Fe, low alloying"
    },
    "Nickel-Based Superalloys": {
        # Ni > 50%, often with Cr, Co, Mo
        "min_nickel_pct": 50,
        "description": "Nickel-Based Superalloys - Ni > 50%"
    },
    "Titanium Alloys": {
        # Ti > 50%
        "min_titanium_pct": 50,
        "description": "Titanium Alloys - Ti > 50%"
    }
}

def classify_alloy_family(row: pd.Series) -> str:
    """
    Classify a single alloy record into a family based on compositional rules.
    Returns 'Unknown' if no rules match.
    """
    # Convert row to dict for easier access, handling missing values
    composition = row.to_dict()
    
    # Helper to safely get element percentage
    def get_pct(element: str) -> float:
        val = composition.get(element, 0.0)
        return float(val) if pd.notna(val) else 0.0

    # Rule 1: High-Entropy Alloys
    elements_above_5pct = sum(1 for key, val in composition.items() 
                              if pd.notna(val) and float(val) >= 5.0)
    max_concentration = max([get_pct(k) for k in composition.keys() if pd.notna(composition.get(k))], default=0)
    
    if elements_above_5pct >= ALLOY_FAMILY_RULES["High-Entropy Alloys"]["min_elements_above_5pct"] and \
       max_concentration <= ALLOY_FAMILY_RULES["High-Entropy Alloys"]["max_element_concentration_pct"]:
        return "High-Entropy Alloys"

    # Rule 2: Stainless Steels
    cr_pct = get_pct("Cr")
    fe_pct = get_pct("Fe")
    if cr_pct >= ALLOY_FAMILY_RULES["Stainless Steels"]["min_chromium_pct"] and \
       fe_pct <= ALLOY_FAMILY_RULES["Stainless Steels"]["max_iron_pct"]:
        return "Stainless Steels"

    # Rule 3: Carbon Steels
    fe_pct = get_pct("Fe")
    # Estimate total alloying (excluding Fe, C, and common impurities like S, P if not tracked)
    # Assuming main columns are elements
    other_elements = [k for k in composition.keys() if k not in ['Fe', 'C'] and pd.notna(composition.get(k))]
    total_alloying = sum(get_pct(k) for k in other_elements)
    
    if fe_pct >= ALLOY_FAMILY_RULES["Carbon Steels"]["min_iron_pct"] and \
       fe_pct <= ALLOY_FAMILY_RULES["Carbon Steels"]["max_iron_pct"] and \
       total_alloying <= ALLOY_FAMILY_RULES["Carbon Steels"]["max_total_alloying_pct"]:
        return "Carbon Steels"

    # Rule 4: Nickel-Based Superalloys
    ni_pct = get_pct("Ni")
    if ni_pct >= ALLOY_FAMILY_RULES["Nickel-Based Superalloys"]["min_nickel_pct"]:
        return "Nickel-Based Superalloys"

    # Rule 5: Titanium Alloys
    ti_pct = get_pct("Ti")
    if ti_pct >= ALLOY_FAMILY_RULES["Titanium Alloys"]["min_titanium_pct"]:
        return "Titanium Alloys"

    return "Unknown"

def perform_ood_split(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Perform Out-of-Distribution (OOD) test set split based on alloy class.
    
    Logic:
    1. Classify each row into an alloy family.
    2. Count unique families.
    3. If >= 2 families: Hold out one full family (the smallest valid one) as test set.
       This ensures the model is tested on a completely unseen distribution (OOD).
    4. If < 2 families: Fallback to stratified random split and flag the condition.
    
    Returns:
        train_set: DataFrame for training
        test_set: DataFrame for testing
        report: Dictionary containing split details and flags
    """
    logger.info("Starting OOD split based on alloy family classification...")
    
    # Apply classification
    df = df.copy()
    df['alloy_family'] = df.apply(classify_alloy_family, axis=1)
    
    family_counts = df['alloy_family'].value_counts()
    unique_families = family_counts.index.tolist()
    num_families = len(unique_families)
    
    report = {
        "total_records": len(df),
        "unique_families": unique_families,
        "family_counts": family_counts.to_dict(),
        "split_method": None,
        "fallback_triggered": False,
        "held_out_family": None,
        "train_count": 0,
        "test_count": 0,
        "note": ""
    }
    
    if num_families >= 2:
        # OOD Split: Hold out the smallest family (excluding 'Unknown' if it's too small or dominant)
        # We prefer to hold out a known, distinct family. If 'Unknown' is the smallest, we might still use it
        # but ideally we want a defined family. Let's filter out 'Unknown' for the selection if possible.
        known_families = [f for f in unique_families if f != "Unknown"]
        
        if len(known_families) >= 2:
            # Select the smallest known family to hold out
            # Sort known families by count
            known_families_sorted = sorted(known_families, key=lambda f: family_counts[f])
            held_out_family = known_families_sorted[0]
        elif len(known_families) == 1 and "Unknown" in unique_families:
            # Only one known family, hold out 'Unknown' if it exists and is significant
            if family_counts.get("Unknown", 0) > 0:
                held_out_family = "Unknown"
            else:
                # Fallback if we can't form a proper OOD set
                logger.warning("Could not form a proper OOD split with known families. Falling back to stratified.")
                report["fallback_triggered"] = True
                report["split_method"] = "stratified_random"
                report["note"] = "Insufficient distinct families for OOD split."
                # Perform stratified split on the only available label (or random if single label)
                # Since we need a split, we do a random stratified split based on the single family
                # But if there's only 1 family, stratification is trivial. We'll just do a random split.
                split_ratio = 0.2
                train_df, test_df = _perform_stratified_random_split(df, split_ratio=split_ratio, seed=RANDOM_SEED)
                report["train_count"] = len(train_df)
                report["test_count"] = len(test_df)
                return train_df, test_df, report
        else:
            # Fallback
            logger.warning("Insufficient families for OOD split. Falling back to stratified.")
            report["fallback_triggered"] = True
            report["split_method"] = "stratified_random"
            report["note"] = "Less than 2 distinct families found."
            split_ratio = 0.2
            train_df, test_df = _perform_stratified_random_split(df, split_ratio=split_ratio, seed=RANDOM_SEED)
            report["train_count"] = len(train_df)
            report["test_count"] = len(test_df)
            return train_df, test_df, report

        # Perform the OOD split
        test_df = df[df['alloy_family'] == held_out_family]
        train_df = df[df['alloy_family'] != held_out_family]
        
        report["split_method"] = "alloy_family_ood"
        report["held_out_family"] = held_out_family
        report["train_count"] = len(train_df)
        report["test_count"] = len(test_df)
        report["note"] = f"Held out family '{held_out_family}' for OOD testing."
        
        logger.info(f"OOD Split successful: {len(train_df)} train, {len(test_df)} test (Family: {held_out_family})")
    else:
        # Fallback: Less than 2 families
        logger.warning(f"Only {num_families} family found. Falling back to stratified random split.")
        report["fallback_triggered"] = True
        report["split_method"] = "stratified_random"
        report["note"] = "Less than 2 distinct families found. Fallback to stratified random split."
        
        split_ratio = 0.2
        train_df, test_df = _perform_stratified_random_split(df, split_ratio=split_ratio, seed=RANDOM_SEED)
        
        report["train_count"] = len(train_df)
        report["test_count"] = len(test_df)
        
    return train_df, test_df, report

def _perform_stratified_random_split(df: pd.DataFrame, split_ratio: float, seed: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform a stratified random split.
    If the stratification column has only one unique value, it falls back to a simple random split.
    """
    # Determine stratification column: prefer 'alloy_family' if it exists, else use a synthetic label if available
    strat_col = 'alloy_family' if 'alloy_family' in df.columns else None
    
    if strat_col and df[strat_col].nunique() > 1:
        train_df, test_df = train_test_split_stratified(df, stratify_col=strat_col, test_size=split_ratio, random_state=seed)
    else:
        # Simple random split
        train_df, test_df = train_test_split_random(df, test_size=split_ratio, random_state=seed)
        
    return train_df, test_df

def train_test_split_random(df: pd.DataFrame, test_size: float, random_state: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Simple random split."""
    df_shuffled = df.sample(frac=1, random_state=random_state).reset_index(drop=True)
    split_idx = int(len(df_shuffled) * (1 - test_size))
    return df_shuffled.iloc[:split_idx], df_shuffled.iloc[split_idx:]

def train_test_split_stratified(df: pd.DataFrame, stratify_col: str, test_size: float, random_state: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Stratified split preserving class distribution."""
    # Group by stratify_col and sample proportionally
    train_parts = []
    test_parts = []
    
    # Get unique classes
    classes = df[stratify_col].unique()
    for cls in classes:
        cls_df = df[df[stratify_col] == cls].sample(frac=1, random_state=random_state)
        n_test = int(len(cls_df) * test_size)
        if n_test == 0 and len(cls_df) > 0:
            n_test = 1  # Ensure at least one sample if possible
        
        test_parts.append(cls_df.iloc[:n_test])
        train_parts.append(cls_df.iloc[n_test:])
        
    train_df = pd.concat(train_parts, ignore_index=True).sample(frac=1, random_state=random_state)
    test_df = pd.concat(test_parts, ignore_index=True).sample(frac=1, random_state=random_state)
    
    return train_df, test_df

def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing values: median imputation for <5% missing, drop rows for >=5%.
    (Re-implemented here to ensure consistency with T015 logic if needed, 
     though T015 likely already handled this in ingestion. 
     This ensures the data is clean before splitting.)
    """
    logger.info("Handling missing values in preprocessing...")
    df = df.copy()
    
    # Identify numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    for col in numeric_cols:
        missing_pct = df[col].isna().sum() / len(df)
        if missing_pct >= 0.05:
            logger.warning(f"Dropping column {col} due to >5% missing values ({missing_pct:.2%})")
            # In a real pipeline, we might drop the column or the rows. 
            # For this task, we assume rows with missing critical features are dropped or imputed.
            # Let's drop rows with missing values in critical columns for simplicity in this step,
            # assuming T015 did the heavy lifting.
            df = df.dropna(subset=[col])
        else:
            # Impute with median
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            
    return df

def map_elemental_composition_to_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map elemental weight percentages to feature vectors.
    (Placeholder for T016 logic - ensures the function exists for the pipeline)
    """
    # This function is expected to exist per the API surface.
    # Implementation details are in T016.
    return df

def calculate_derived_atomic_properties(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate derived atomic properties.
    (Placeholder for T017 logic)
    """
    return df

def run_preprocessing_pipeline(input_path: str, output_train_path: str, output_test_path: str) -> None:
    """
    Main pipeline function to load, clean, classify, and split data.
    """
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Clean missing values (ensure data is ready for split)
    df = handle_missing_values(df)
    
    # Perform OOD split
    train_df, test_df, report = perform_ood_split(df)
    
    # Ensure output directories exist
    ensure_dir(os.path.dirname(output_train_path))
    ensure_dir(os.path.dirname(output_test_path))
    
    # Save outputs
    logger.info(f"Saving train set to {output_train_path}")
    train_df.to_parquet(output_train_path, index=False)
    
    logger.info(f"Saving test set to {output_test_path}")
    test_df.to_parquet(output_test_path, index=False)
    
    # Save report
    report_path = OOD_SPLIT_REPORT_PATH
    ensure_dir(os.path.dirname(report_path))
    save_json(report, report_path)
    
    logger.info(f"OOD Split Report saved to {report_path}")
    logger.info(f"Report summary: {report['note']}")

def main():
    """Entry point for the preprocessing script."""
    input_file = "data/processed/cleaned_alloys.csv"
    train_output = "data/processed/train_set.parquet"
    test_output = "data/processed/test_ood_set.parquet"
    
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}. Please run ingestion first.")
        return
        
    run_preprocessing_pipeline(input_file, train_output, test_output)

if __name__ == "__main__":
    main()
