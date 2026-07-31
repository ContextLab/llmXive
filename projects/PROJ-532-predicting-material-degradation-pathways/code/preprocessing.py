import pandas as pd
import numpy as np
import logging
from typing import Tuple, Dict, Any, List
import os
import json
from pathlib import Path

# Import shared utilities from the project's utils module
from utils import ensure_dir, save_json, setup_logging, get_env_var

# Configure logging
logger = setup_logging(__name__)

# Constants
DATA_DIR = Path(get_env_var("DATA_DIR", "data"))
PROCESSED_DIR = DATA_DIR / "processed"
MIN_RECORDS_THRESHOLD = 200

# Alloy Family Classification Rules
# Based on typical elemental composition thresholds found in materials science literature
ALLOY_FAMILY_RULES = {
    "High-Entropy Alloys": {
        "min_elements": 5,
        "max_concentration": 0.35,  # No single element > 35%
        "description": "Multi-principal element alloys with 5+ elements in equimolar or near-equimolar ratios"
    },
    "Stainless Steels": {
        "min_chromium": 0.105,  # >10.5% Cr for passivation
        "max_carbon": 0.02,     # Low carbon for most grades (varies by grade)
        "description": "Iron-based alloys with >10.5% Chromium for corrosion resistance"
    },
    "Carbon Steels": {
        "max_chromium": 0.005,  # <0.5% Cr (essentially no Cr)
        "min_iron": 0.90,       # >90% Fe
        "description": "Iron-carbon alloys with minimal alloying elements"
    },
    "Nickel-Based Superalloys": {
        "min_nickel": 0.50,     # >50% Ni
        "description": "Nickel-rich alloys for high-temperature applications"
    },
    "Titanium Alloys": {
        "min_titanium": 0.50,   # >50% Ti
        "description": "Titanium-based alloys with various alloying elements"
    },
    "Aluminum Alloys": {
        "min_aluminum": 0.85,   # >85% Al
        "description": "Aluminum-based alloys with various alloying elements"
    }
}

def classify_alloy_family(row: pd.Series) -> str:
    """
    Classify a single alloy record into a family based on elemental composition.
    
    Args:
        row: A pandas Series containing elemental weight percentages.
    
    Returns:
        A string label for the alloy family, or "Unknown" if no rules match.
    """
    # Get all elemental columns (columns that look like element symbols)
    element_cols = [col for col in row.index if col.isupper() and len(col) <= 2]
    
    # Calculate number of distinct elements with significant concentration (>0.1%)
    significant_elements = [col for col in element_cols if row[col] > 0.001]
    num_elements = len(significant_elements)
    
    # Check High-Entropy Alloys first (most specific)
    if num_elements >= 5:
        max_conc = max([row[col] for col in significant_elements])
        if max_conc <= 0.35:
            return "High-Entropy Alloys"
    
    # Check other families
    if "Cr" in row.index and row["Cr"] > ALLOY_FAMILY_RULES["Stainless Steels"]["min_chromium"]:
        # Check if it's stainless steel
        if "C" in row.index:
            carbon = row["C"] if pd.notna(row["C"]) else 0.0
            if carbon <= ALLOY_FAMILY_RULES["Stainless Steels"]["max_carbon"]:
                return "Stainless Steels"
        else:
            # If no carbon data, assume stainless if Cr is high
            return "Stainless Steels"
    
    if "Fe" in row.index and row["Fe"] > ALLOY_FAMILY_RULES["Carbon Steels"]["min_iron"]:
        if "Cr" not in row.index or row["Cr"] < ALLOY_FAMILY_RULES["Carbon Steels"]["max_chromium"]:
            return "Carbon Steels"
    
    if "Ni" in row.index and row["Ni"] > ALLOY_FAMILY_RULES["Nickel-Based Superalloys"]["min_nickel"]:
        return "Nickel-Based Superalloys"
    
    if "Ti" in row.index and row["Ti"] > ALLOY_FAMILY_RULES["Titanium Alloys"]["min_titanium"]:
        return "Titanium Alloys"
    
    if "Al" in row.index and row["Al"] > ALLOY_FAMILY_RULES["Aluminum Alloys"]["min_aluminum"]:
        return "Aluminum Alloys"
    
    return "Unknown"

def perform_ood_split(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Perform Out-of-Distribution (OOD) test set split based on alloy class.
    
    This function identifies distinct alloy families in the dataset and holds out
    one full family as the test set. If fewer than 2 distinct families exist,
    it falls back to a stratified random split and flags this condition.
    
    Args:
        df: Input DataFrame with alloy composition data and a 'alloy_family' column.
    
    Returns:
        Tuple containing:
            - train_set: Training set DataFrame
            - test_set: Test set DataFrame (OOD split)
            - split_metadata: Dictionary with split statistics and flags
    """
    logger.info(f"Performing OOD split on {len(df)} records")
    
    # Get unique alloy families
    unique_families = df['alloy_family'].unique()
    family_counts = df['alloy_family'].value_counts().to_dict()
    
    split_metadata = {
        "method": "alloy_family_ood_split",
        "total_records": len(df),
        "unique_families": len(unique_families),
        "family_distribution": family_counts,
        "fallback_used": False,
        "fallback_reason": None,
        "train_records": 0,
        "test_records": 0,
        "train_families": [],
        "test_families": []
    }
    
    if len(unique_families) < 2:
        # Fallback to stratified random split
        logger.warning(f"Only {len(unique_families)} alloy families found. Falling back to stratified random split.")
        split_metadata["fallback_used"] = True
        split_metadata["fallback_reason"] = f"Insufficient alloy families ({len(unique_families)} < 2) for OOD split"
        
        # Stratified random split by degradation pathways (multi-label)
        # Use the first degradation label column for stratification if available
        label_cols = [col for col in df.columns if 'degradation' in col.lower() or col.startswith('label_')]
        
        if label_cols:
            stratify_col = label_cols[0]
            # Simple stratified split using sklearn's train_test_split
            from sklearn.model_selection import train_test_split
            train_df, test_df = train_test_split(
                df, 
                test_size=0.2, 
                random_state=42, 
                stratify=df[stratify_col]
            )
            split_metadata["split_method"] = "stratified_random"
            split_metadata["stratify_column"] = stratify_col
        else:
            # Fallback to simple random split if no labels available
            from sklearn.model_selection import train_test_split
            train_df, test_df = train_test_split(
                df, 
                test_size=0.2, 
                random_state=42
            )
            split_metadata["split_method"] = "random_split"
        
        split_metadata["train_records"] = len(train_df)
        split_metadata["test_records"] = len(test_df)
        split_metadata["train_families"] = list(train_df['alloy_family'].unique())
        split_metadata["test_families"] = list(test_df['alloy_family'].unique())
        
        logger.info(f"Stratified split: {len(train_df)} train, {len(test_df)} test")
    else:
        # Perform OOD split: hold out one full family
        # Choose the smallest family for the test set to maximize training data
        # but ensure it has at least 5 records for meaningful evaluation
        sorted_families = sorted(family_counts.items(), key=lambda x: x[1])
        
        test_family = None
        for family, count in sorted_families:
            if count >= 5:  # Minimum records for test set
                test_family = family
                break
        
        if test_family is None:
            # If no family has >= 5 records, use the smallest family anyway
            test_family = sorted_families[0][0]
            logger.warning(f"Using family '{test_family}' with {family_counts[test_family]} records for test set (less than 5 records)")
        
        # Split data
        test_df = df[df['alloy_family'] == test_family].copy()
        train_df = df[df['alloy_family'] != test_family].copy()
        
        split_metadata["split_method"] = "alloy_family_ood"
        split_metadata["test_family"] = test_family
        split_metadata["train_families"] = [f for f in unique_families if f != test_family]
        split_metadata["test_families"] = [test_family]
        split_metadata["train_records"] = len(train_df)
        split_metadata["test_records"] = len(test_df)
        
        logger.info(f"OOD split: {len(train_df)} train ({len(split_metadata['train_families'])} families), "
                   f"{len(test_df)} test (family: {test_family})")
    
    return train_df, test_df, split_metadata

def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing values in the dataset using median imputation or exclusion.
    
    Args:
        df: Input DataFrame with potential missing values.
    
    Returns:
        DataFrame with missing values handled according to the rules.
    """
    logger.info(f"Handling missing values in {len(df)} records")
    
    # Calculate missing value percentages for each column
    missing_percentages = df.isnull().mean() * 100
    
    # Identify columns to drop (>=5% missing)
    drop_cols = missing_percentages[missing_percentages >= 5].index.tolist()
    logger.info(f"Dropping {len(drop_cols)} columns with >=5% missing values: {drop_cols}")
    
    # Drop columns with high missingness
    df_clean = df.drop(columns=drop_cols)
    
    # Impute remaining missing values with median for numeric columns
    numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if df_clean[col].isnull().any():
            median_val = df_clean[col].median()
            df_clean[col] = df_clean[col].fillna(median_val)
            logger.debug(f"Imputed {col} with median {median_val}")
    
    # Fill categorical columns with 'Unknown'
    categorical_cols = df_clean.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        if df_clean[col].isnull().any():
            df_clean[col] = df_clean[col].fillna('Unknown')
    
    logger.info(f"Final dataset after missing value handling: {len(df_clean)} records, {len(df_clean.columns)} columns")
    return df_clean

def map_elemental_composition_to_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map elemental weight percentages to feature vectors.
    
    Args:
        df: Input DataFrame with elemental composition data.
    
    Returns:
        DataFrame with mapped feature vectors.
    """
    logger.info(f"Mapping elemental composition to features for {len(df)} records")
    
    # Identify elemental columns (columns that look like element symbols)
    element_cols = [col for col in df.columns if col.isupper() and len(col) <= 2]
    
    if not element_cols:
        logger.warning("No elemental columns found in the dataset")
        return df
    
    logger.info(f"Found {len(element_cols)} elemental columns: {element_cols}")
    
    # Ensure all elemental columns are numeric and fill NaN with 0
    for col in element_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # The feature vector is simply the elemental weight percentages
    # Additional derived features can be added here if needed
    feature_df = df[element_cols].copy()
    
    # Add a constant feature for bias term if needed
    feature_df['bias'] = 1.0
    
    logger.info(f"Created feature matrix with {len(feature_df.columns)} features")
    return feature_df

def calculate_derived_atomic_properties(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate derived atomic properties for post-hoc analysis.
    
    Args:
        df: Input DataFrame with elemental composition data.
    
    Returns:
        DataFrame with derived atomic properties (not included in training features).
    """
    logger.info(f"Calculating derived atomic properties for {len(df)} records")
    
    # Electronegativity values (Pauling scale) for common elements
    electronegativity = {
        'H': 2.20, 'He': 0.00, 'Li': 0.98, 'Be': 1.57, 'B': 2.04, 'C': 2.55,
        'N': 3.04, 'O': 3.44, 'F': 3.98, 'Ne': 0.00, 'Na': 0.93, 'Mg': 1.31,
        'Al': 1.61, 'Si': 1.90, 'P': 2.19, 'S': 2.58, 'Cl': 3.16, 'Ar': 0.00,
        'K': 0.82, 'Ca': 1.00, 'Sc': 1.36, 'Ti': 1.54, 'V': 1.63, 'Cr': 1.66,
        'Mn': 1.55, 'Fe': 1.83, 'Co': 1.88, 'Ni': 1.91, 'Cu': 1.90, 'Zn': 1.65,
        'Ga': 1.81, 'Ge': 2.01, 'As': 2.18, 'Se': 2.55, 'Br': 2.96, 'Kr': 0.00,
        'Rb': 0.82, 'Sr': 0.95, 'Y': 1.22, 'Zr': 1.33, 'Nb': 1.60, 'Mo': 2.16,
        'Tc': 1.90, 'Ru': 2.20, 'Rh': 2.28, 'Pd': 2.20, 'Ag': 1.93, 'Cd': 1.69,
        'In': 1.78, 'Sn': 1.96, 'Sb': 2.05, 'Te': 2.10, 'I': 2.66, 'Xe': 0.00,
        'Cs': 0.79, 'Ba': 0.89, 'La': 1.10, 'Ce': 1.12, 'Pr': 1.13, 'Nd': 1.14,
        'Pm': 1.13, 'Sm': 1.17, 'Eu': 1.20, 'Gd': 1.20, 'Tb': 1.20, 'Dy': 1.22,
        'Ho': 1.23, 'Er': 1.24, 'Tm': 1.25, 'Yb': 1.10, 'Lu': 1.27, 'Hf': 1.30,
        'Ta': 1.50, 'W': 2.36, 'Re': 1.90, 'Os': 2.20, 'Ir': 2.20, 'Pt': 2.28,
        'Au': 2.54, 'Hg': 2.00, 'Tl': 1.62, 'Pb': 2.33, 'Bi': 2.02, 'Po': 2.00,
        'At': 2.20, 'Rn': 0.00
    }
    
    # Atomic radii (pm) for common elements
    atomic_radii = {
        'H': 37, 'He': 32, 'Li': 152, 'Be': 112, 'B': 85, 'C': 77,
        'N': 75, 'O': 73, 'F': 72, 'Ne': 71, 'Na': 186, 'Mg': 160,
        'Al': 143, 'Si': 117, 'P': 110, 'S': 104, 'Cl': 99, 'Ar': 97,
        'K': 227, 'Ca': 197, 'Sc': 162, 'Ti': 147, 'V': 134, 'Cr': 128,
        'Mn': 127, 'Fe': 126, 'Co': 125, 'Ni': 124, 'Cu': 128, 'Zn': 134,
        'Ga': 135, 'Ge': 122, 'As': 121, 'Se': 117, 'Br': 114, 'Kr': 110,
        'Rb': 248, 'Sr': 215, 'Y': 180, 'Zr': 160, 'Nb': 146, 'Mo': 139,
        'Tc': 136, 'Ru': 134, 'Rh': 134, 'Pd': 137, 'Ag': 144, 'Cd': 151,
        'In': 167, 'Sn': 140, 'Sb': 140, 'Te': 136, 'I': 133, 'Xe': 130,
        'Cs': 265, 'Ba': 222, 'La': 187, 'Ce': 182, 'Pr': 182, 'Nd': 181,
        'Pm': 183, 'Sm': 180, 'Eu': 199, 'Gd': 180, 'Tb': 177, 'Dy': 178,
        'Ho': 176, 'Er': 176, 'Tm': 176, 'Yb': 194, 'Lu': 174, 'Hf': 159,
        'Ta': 146, 'W': 139, 'Re': 137, 'Os': 135, 'Ir': 136, 'Pt': 139,
        'Au': 144, 'Hg': 151, 'Tl': 171, 'Pb': 175, 'Bi': 156, 'Po': 167,
        'At': 145, 'Rn': 145
    }
    
    # Identify elemental columns
    element_cols = [col for col in df.columns if col.isupper() and len(col) <= 2]
    
    derived_features = {}
    
    # Calculate weighted average electronegativity
    weighted_en = np.zeros(len(df))
    weighted_radius = np.zeros(len(df))
    element_count = np.zeros(len(df))
    
    for element in element_cols:
        if element in electronegativity and element in atomic_radii:
            if element in df.columns:
                weight = df[element].values
                weighted_en += weight * electronegativity[element]
                weighted_radius += weight * atomic_radii[element]
                element_count += weight
    
    # Normalize by total weight (should be ~100 for weight percentages)
    mask = element_count > 0
    derived_features['avg_electronegativity'] = np.where(mask, weighted_en / element_count, 0)
    derived_features['avg_atomic_radius'] = np.where(mask, weighted_radius / element_count, 0)
    
    # Calculate number of distinct elements
    derived_features['num_elements'] = (df[element_cols] > 0.001).sum(axis=1)
    
    # Add derived features to a new DataFrame
    derived_df = pd.DataFrame(derived_features)
    
    logger.info(f"Calculated {len(derived_df.columns)} derived atomic properties")
    return derived_df

def train_test_split(df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Simple train-test split function (wrapper around sklearn for compatibility).
    
    Args:
        df: Input DataFrame.
        test_size: Proportion of data to use for testing.
        random_state: Random seed for reproducibility.
    
    Returns:
        Tuple of (train_df, test_df).
    """
    from sklearn.model_selection import train_test_split as sklearn_split
    return sklearn_split(df, test_size=test_size, random_state=random_state, stratify=None)

def run_preprocessing_pipeline(input_file: str) -> Dict[str, Any]:
    """
    Run the complete preprocessing pipeline.
    
    Args:
        input_file: Path to the cleaned alloys CSV file.
    
    Returns:
        Dictionary with pipeline execution statistics.
    """
    logger.info(f"Starting preprocessing pipeline for {input_file}")
    
    # Ensure output directory exists
    ensure_dir(PROCESSED_DIR)
    
    # Load cleaned data
    df = pd.read_csv(input_file)
    logger.info(f"Loaded {len(df)} records from {input_file}")
    
    # Handle missing values
    df_clean = handle_missing_values(df)
    
    # Classify alloy families
    df_clean['alloy_family'] = df_clean.apply(classify_alloy_family, axis=1)
    logger.info(f"Classified alloy families: {df_clean['alloy_family'].value_counts().to_dict()}")
    
    # Perform OOD split
    train_df, test_df, split_metadata = perform_ood_split(df_clean)
    
    # Save train and test sets
    train_path = PROCESSED_DIR / "train_set.parquet"
    test_path = PROCESSED_DIR / "test_ood_set.parquet"
    
    train_df.to_parquet(train_path, index=False)
    test_df.to_parquet(test_path, index=False)
    
    logger.info(f"Saved train set to {train_path} ({len(train_df)} records)")
    logger.info(f"Saved test set to {test_path} ({len(test_df)} records)")
    
    # Save split metadata
    metadata_path = PROCESSED_DIR / "split_metadata.json"
    save_json(split_metadata, metadata_path)
    logger.info(f"Saved split metadata to {metadata_path}")
    
    # Calculate derived atomic properties (for post-hoc analysis, not training)
    derived_df = calculate_derived_atomic_properties(train_df)
    derived_df.to_csv(PROCESSED_DIR / "derived_atomic_properties.csv", index=False)
    logger.info(f"Saved derived atomic properties to {PROCESSED_DIR / 'derived_atomic_properties.csv'}")
    
    return {
        "status": "success",
        "input_records": len(df),
        "cleaned_records": len(df_clean),
        "train_records": len(train_df),
        "test_records": len(test_df),
        "split_metadata": split_metadata,
        "output_files": [
            str(train_path),
            str(test_path),
            str(metadata_path),
            str(PROCESSED_DIR / "derived_atomic_properties.csv")
        ]
    }

def main():
    """Main entry point for the preprocessing pipeline."""
    # Default input file path
    input_file = os.getenv("CLEANED_ALLOYS_FILE", "data/processed/cleaned_alloys.csv")
    
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please run the ingestion pipeline first to generate the cleaned data.")
        return {"status": "error", "message": f"Input file not found: {input_file}"}
    
    result = run_preprocessing_pipeline(input_file)
    
    if result["status"] == "success":
        logger.info("Preprocessing pipeline completed successfully")
        logger.info(f"Train set: {result['train_records']} records")
        logger.info(f"Test set: {result['test_records']} records")
        if result["split_metadata"]["fallback_used"]:
            logger.warning(f"Fallback used: {result['split_metadata']['fallback_reason']}")
    else:
        logger.error(f"Preprocessing pipeline failed: {result.get('message', 'Unknown error')}")
    
    return result

if __name__ == "__main__":
    main()
