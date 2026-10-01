import os
import sys
import logging
import json
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import mean_absolute_error
import yaml
from config.elements import get_abundant_elements_set
from utils.logger import get_logger
from utils.state_manager import update_artifact_hash
from config.env import load_config

logger = get_logger(__name__)

def load_features_data(data_path: str) -> pd.DataFrame:
    """Loads feature data from a CSV file."""
    try:
        df = pd.read_csv(data_path)
        return df
    except FileNotFoundError:
        logger.error(f"Feature data file not found: {data_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading feature data: {e}")
        raise

def load_family_map(config_path: str) -> dict:
    """Loads the element-to-family mapping from a YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Family map file not found: {config_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading family map: {e}")
        raise

def extract_primary_element(composition: str, fractions: pd.Series) -> tuple:
    """
    Extracts the primary element from a composition string based on atomic fractions.
    
    Logic:
    1. Parse composition string to get element symbols.
    2. Identify the element with the highest atomic fraction.
    3. If tied, choose the element with the higher atomic number.
    
    Args:
        composition: String like "Zr50Cu40Al10" or "Zr-Cu-Al"
        fractions: Series of element fractions corresponding to the composition.
                   Column names should match element symbols.
                   
    Returns:
        Tuple (primary_element: str, all_fractions: dict)
    """
    # Handle both "A-B-C" and "A50B40C10" formats if needed, 
    # but assuming standardized format from ingest.py (e.g., "Zr-Cu-Al" with separate fraction cols)
    # The task implies we have fraction columns.
    
    elements = [elem.strip() for elem in composition.split('-')]
    
    # Get fractions for these elements
    current_fractions = {}
    for elem in elements:
        if elem in fractions.index:
            current_fractions[elem] = fractions[elem]
        else:
            # Fallback or error if column missing
            current_fractions[elem] = 0.0

    if not current_fractions:
        return elements[0], {}

    # Find max fraction
    max_frac = max(current_fractions.values())
    
    # Get all elements with max fraction
    candidates = [e for e, f in current_fractions.items() if f == max_frac]
    
    if len(candidates) == 1:
        return candidates[0], current_fractions
    
    # Tie-breaker: Higher atomic number
    # We need atomic numbers. Using a simple map for abundant elements.
    atomic_numbers = {
        'H': 1, 'He': 2, 'Li': 3, 'Be': 4, 'B': 5, 'C': 6, 'N': 7, 'O': 8, 'F': 9, 'Ne': 10,
        'Na': 11, 'Mg': 12, 'Al': 13, 'Si': 14, 'P': 15, 'S': 16, 'Cl': 17, 'Ar': 18,
        'K': 19, 'Ca': 20, 'Cr': 24, 'Mn': 25, 'Fe': 26, 'Ni': 28, 'Cu': 29, 'Zn': 30,
        'Nb': 41, 'Mo': 42, 'Ag': 47, 'Au': 79, 'Pt': 78, 'Ti': 22, 'Zr': 40, 'Hf': 72,
        'Y': 39, 'La': 57, 'Ce': 58, 'Sc': 21, 'Pb': 82, 'Sn': 50, 'V': 23, 'Mg': 12
    }
    
    # Sort candidates by atomic number descending
    candidates.sort(key=lambda e: atomic_numbers.get(e, 0), reverse=True)
    
    return candidates[0], current_fractions

def assign_element_families(df: pd.DataFrame, family_map: dict) -> pd.DataFrame:
    """
    Assigns element families to each composition based on the primary element.
    
    Logic:
    1. Determine primary element (highest fraction, tie-break by atomic number).
    2. Map primary element to family using family_map.
    3. Handle unmapped elements by grouping with periodic table neighbors or "Other".
    """
    # Ensure we have fraction columns. Assuming columns like 'Zr', 'Cu', etc. exist
    # or we parse from composition.
    # For robustness, we assume the input DF has element fraction columns.
    
    primary_elements = []
    families = []
    
    for idx, row in df.iterrows():
        comp_str = row['composition']
        
        # Extract primary element
        primary_elem, _ = extract_primary_element(comp_str, row)
        primary_elements.append(primary_elem)
        
        # Map to family
        if primary_elem in family_map:
            fam = family_map[primary_elem]
        else:
            # Fallback: Try to find neighbor in periodic table (simplified)
            # For this task, we assume family_map covers most, or use "Other"
            fam = "Other" 
            logger.warning(f"Element {primary_elem} not in family_map, assigned to 'Other'")
        
        families.append(fam)
    
    df['primary_element'] = primary_elements
    df['family'] = families
    return df

def perform_loco_cv(X: pd.DataFrame, y: pd.Series, family_column: str) -> float:
    """Performs Leave-One-Cluster-Out cross-validation."""
    unique_families = X[family_column].unique()
    mae_scores = []

    for family in unique_families:
        train_data = X[X[family_column] != family]
        train_labels = y[X[family_column] != family]
        test_data = X[X[family_column] == family]
        test_labels = y[X[family_column] == family]

        if len(test_data) == 0:
            continue

        model = RandomForestRegressor(random_state=42)
        model.fit(train_data, train_labels)
        y_pred = model.predict(test_data)
        mae = mean_absolute_error(test_labels, y_pred)
        mae_scores.append(mae)

    if not mae_scores:
        return 0.0
    
    return np.mean(mae_scores)

def validate_loco_cluster_assignment(df: pd.DataFrame, family_map: dict):
    """
    Unit test / assertion for LOCO cluster assignment logic.
    
    Verifies:
    1. Primary element is the one with highest fraction.
    2. Tie-breaker (highest atomic number) works for equal fractions.
    3. Family mapping is consistent with family_map.yaml.
    
    Creates a synthetic dataset with known outcomes and asserts the logic holds.
    """
    logger.info("Running LOCO cluster assignment validation...")
    
    # Create synthetic test data
    test_data = {
        'composition': ['Zr-Cu-Al', 'Cu-Zr-Al', 'Zr-Zr-Cu', 'Ti-Hf-Zr'],
        # Simulating fraction columns. Note: In real DF, these are numeric columns.
        # We'll inject them for the test.
    }
    
    # Inject fractions for specific test cases
    # Case 1: Zr > Cu > Al -> Primary Zr
    # Case 2: Cu > Zr > Al -> Primary Cu
    # Case 3: Zr == Zr (impossible, but test logic for ties) -> Zr-Cu where Zr fraction > Cu
    # Case 4: Tie between Ti, Hf, Zr? No, let's do a tie between Zr and Hf (Hf=72, Zr=40) -> Hf
    # Let's construct a DF with fraction columns
    
    synthetic_df = pd.DataFrame({
        'composition': ['Zr-Cu-Al', 'Cu-Zr-Al', 'Zr-Hf-Cu', 'Ti-Hf-Zr'],
        'Zr': [0.5, 0.2, 0.3, 0.2],
        'Cu': [0.3, 0.5, 0.3, 0.2],
         'Al': [0.2, 0.3, 0.0, 0.0],
         'Hf': [0.0, 0.0, 0.3, 0.2],
         'Ti': [0.0, 0.0, 0.0, 0.6]
    })
    
    # Expected Primary Elements based on logic:
    # Row 0: Zr(0.5) -> Zr
    # Row 1: Cu(0.5) -> Cu
    # Row 2: Tie Zr(0.3) vs Hf(0.3). Hf(72) > Zr(40) -> Hf
    # Row 3: Ti(0.6) -> Ti
    
    expected_primary = ['Zr', 'Cu', 'Hf', 'Ti']
    
    # Run the assignment logic
    # We need to pass the dataframe to the function that extracts primary
    # We'll simulate the loop in assign_element_families
    
    test_families = {}
    for idx, row in synthetic_df.iterrows():
        comp_str = row['composition']
        primary, _ = extract_primary_element(comp_str, row)
        test_families[idx] = primary
    
    actual_primary = [test_families[i] for i in range(len(expected_primary))]
    
    # Assertions
    assert actual_primary == expected_primary, f"Primary element extraction failed. Expected {expected_primary}, got {actual_primary}"
    
    # Verify Family Mapping
    # Map expected primary to family
    expected_families = [family_map.get(e, "Other") for e in expected_primary]
    
    # Run the full assignment
    full_df = assign_element_families(synthetic_df, family_map)
    actual_families = full_df['family'].tolist()
    
    assert actual_families == expected_families, f"Family mapping failed. Expected {expected_families}, got {actual_families}"
    
    logger.info("LOCO cluster assignment validation PASSED.")
    return True

def train_models(X: pd.DataFrame, y: pd.Series, family_column: str) -> tuple:
    """Trains RandomForestRegressor and GradientBoostingRegressor."""
    # Create a pipeline with scaling
    rf_pipeline = make_pipeline(StandardScaler(), RandomForestRegressor(random_state=42))
    gb_pipeline = make_pipeline(StandardScaler(), RandomForestRegressor(random_state=42))

    rf_pipeline.fit(X, y)
    gb_pipeline.fit(X, y)
    
    loco_mae_rf = perform_loco_cv(X, y, family_column)
    #loco_mae_gb = perform_loco_cv(X, y, family_column)

    return rf_pipeline, gb_pipeline, loco_mae_rf

def main():
    """Main function to load data, train models, and save results."""
    try:
        config = load_config()
        data_path = config["data_path"]
        family_map_path = config.get("family_map_path", "data/config/family_map.yaml")
        
        df = load_features_data(data_path)
        
        # Load family map
        family_map = load_family_map(family_map_path)
        
        # Validate logic before assignment
        validate_loco_cluster_assignment(df, family_map)
        
        df = assign_element_families(df, family_map)
        
        # Ensure feature columns exist
        feature_cols = [c for c in df.columns if c not in ['composition', 'log10_Rc', 'family', 'primary_element']]
        if not feature_cols:
            raise ValueError("No feature columns found in dataframe.")
        
        X = df[feature_cols]
        y = df['log10_Rc']

        rf_model, gb_model, loco_mae = train_models(X, y, 'family')

        logger.info(f"LOCO MAE (RandomForest): {loco_mae}")
        
        # Save the best model
        with open("best_model.pkl", "wb") as f:
            import pickle
            pickle.dump(rf_model, f)

        update_artifact_hash("best_model.pkl")
    except Exception as e:
        logger.error(f"An error occurred during training: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
