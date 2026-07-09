import pandas as pd
import numpy as np
import logging
from typing import Tuple, Dict, Any, List
import os
import json
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for alloy classification
# These keywords are used to identify alloy families in the 'alloy_type' or 'composition' columns
ALLOY_FAMILIES = {
    "High-Entropy Alloys": ["high entropy", "healoy", "high-entropy", "hea"],
    "Stainless Steels": ["stainless steel", "ss", "austenitic", "ferritic", "martensitic", "duplex"],
    "Carbon Steels": ["carbon steel", "mild steel", "low alloy steel", "hss"],
    "Nickel Alloys": ["nickel alloy", "inconel", "monel", "hastelloy", "nickel-based"],
    "Aluminum Alloys": ["aluminum alloy", "alum alloy", "al alloy"],
    "Titanium Alloys": ["titanium alloy", "ti alloy", "titanium-based"]
}

def handle_missing_values(df: pd.DataFrame, threshold: float = 0.05) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Handle missing values in the dataframe.
    - If a column has < 5% missing values, impute with median.
    - If a column has >= 5% missing values, drop the column.
    
    Args:
        df: Input DataFrame
        threshold: Percentage threshold for dropping columns (default 0.05)
        
    Returns:
        Tuple of (cleaned DataFrame, stats dictionary)
    """
    stats = {
        "total_rows": len(df),
        "dropped_columns": [],
        "imputed_columns": [],
        "missing_stats": {}
    }
    
    # Calculate missing percentages
    missing_pct = df.isnull().mean()
    stats["missing_stats"] = missing_pct.to_dict()
    
    # Identify columns to drop vs impute
    cols_to_drop = missing_pct[missing_pct >= threshold].index.tolist()
    cols_to_impute = missing_pct[(missing_pct > 0) & (missing_pct < threshold)].index.tolist()
    
    # Drop columns with high missingness
    if cols_to_drop:
        logger.info(f"Dropping {len(cols_to_drop)} columns with >= {threshold*100}% missing values: {cols_to_drop}")
        df = df.drop(columns=cols_to_drop)
        stats["dropped_columns"] = cols_to_drop
    
    # Impute remaining missing values with median
    if cols_to_impute:
        logger.info(f"Imputing {len(cols_to_impute)} columns with median values")
        for col in cols_to_impute:
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
        stats["imputed_columns"] = cols_to_impute
        
    stats["remaining_rows"] = len(df)
    return df, stats

def map_elemental_composition_to_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map elemental weight percentages to feature vectors.
    Assumes columns like 'Fe', 'Cr', 'Ni', 'C', etc. exist in the dataframe.
    Non-elemental columns are preserved.
    
    Args:
        df: Input DataFrame with elemental composition columns
        
    Returns:
        DataFrame with feature vectors (numeric columns only, normalized if needed)
    """
    # Identify elemental columns (assuming they are uppercase or mixed case chemical symbols)
    # We'll assume any column that is all letters and has a known atomic mass is an element
    # For simplicity, we'll just take all numeric columns that look like elements
    # In a real scenario, we'd have a predefined list of elements
    element_cols = [col for col in df.columns if col.isalpha() and col.isupper()]
    
    # If no element columns found, try to find columns that might be elements (e.g. 'Fe', 'Cr')
    if not element_cols:
        # Heuristic: columns that are 1-2 letters and appear in a known element list
        known_elements = {'Fe', 'Cr', 'Ni', 'C', 'Mn', 'Si', 'Mo', 'V', 'Ti', 'Al', 'Cu', 'Co', 'W', 'Nb', 'Ta', 'Re', 'Ru', 'Rh', 'Pd', 'Ag', 'Au', 'Pt', 'Ir', 'Os', 'Hf', 'Zr', 'V', 'Nb', 'Ta', 'Mo', 'W', 'Re', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'In', 'Sn', 'Sb', 'Te', 'I', 'Xe', 'Cs', 'Ba', 'La', 'Ce', 'Pr', 'Nd', 'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu', 'Hf', 'Ta', 'W', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg', 'Tl', 'Pb', 'Bi', 'Po', 'At', 'Rn', 'Fr', 'Ra', 'Ac', 'Th', 'Pa', 'U', 'Np', 'Pu', 'Am', 'Cm', 'Bk', 'Cf', 'Es', 'Fm', 'Md', 'No', 'Lr', 'Rf', 'Db', 'Sg', 'Bh', 'Hs', 'Mt', 'Ds', 'Rg', 'Cn', 'Nh', 'Fl', 'Mc', 'Lv', 'Ts', 'Og', 'Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn', 'Ga', 'Ge', 'As', 'Se', 'Br', 'Kr', 'Rb', 'Sr', 'Y', 'Zr', 'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'In', 'Sn', 'Sb', 'Te', 'I', 'Xe', 'Cs', 'Ba', 'La', 'Ce', 'Pr', 'Nd', 'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu', 'Hf', 'Ta', 'W', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg', 'Tl', 'Pb', 'Bi', 'Po', 'At', 'Rn', 'Fr', 'Ra', 'Ac', 'Th', 'Pa', 'U', 'Np', 'Pu', 'Am', 'Cm', 'Bk', 'Cf', 'Es', 'Fm', 'Md', 'No', 'Lr'}
        element_cols = [col for col in df.columns if col in known_elements]
    
    if not element_cols:
        logger.warning("No elemental columns found. Returning original dataframe.")
        return df
    
    # Extract elemental features
    feature_df = df[element_cols].copy()
    
    # Normalize features (optional, but good practice for ML)
    # Here we just ensure they are numeric
    feature_df = feature_df.apply(pd.to_numeric, errors='coerce')
    
    # Preserve non-elemental columns that are useful (e.g., alloy_type, environment, degradation_type)
    non_element_cols = [col for col in df.columns if col not in element_cols]
    metadata_df = df[non_element_cols].copy()
    
    # Combine
    result_df = pd.concat([metadata_df, feature_df], axis=1)
    
    logger.info(f"Extracted {len(element_cols)} elemental features: {element_cols}")
    return result_df

def calculate_derived_atomic_properties(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate derived atomic properties (electronegativity, radius) for post-hoc analysis.
    These are excluded from the training vector but added for analysis.
    
    Args:
        df: Input DataFrame with elemental composition
        
    Returns:
        DataFrame with added derived property columns
    """
    # Placeholder for atomic property data
    # In a real implementation, this would come from a database or external file
    atomic_properties = {
        'Fe': {'electronegativity': 1.83, 'radius': 126},
        'Cr': {'electronegativity': 1.66, 'radius': 128},
        'Ni': {'electronegativity': 1.91, 'radius': 124},
        'C': {'electronegativity': 2.55, 'radius': 77},
        'Mn': {'electronegativity': 1.55, 'radius': 127},
        'Si': {'electronegativity': 1.90, 'radius': 111},
        'Mo': {'electronegativity': 2.16, 'radius': 139},
        'V': {'electronegativity': 1.63, 'radius': 134},
        'Ti': {'electronegativity': 1.54, 'radius': 147},
        'Al': {'electronegativity': 1.61, 'radius': 143},
        'Cu': {'electronegativity': 1.90, 'radius': 128},
        'Co': {'electronegativity': 1.88, 'radius': 125},
        'W': {'electronegativity': 2.36, 'radius': 139},
        'Nb': {'electronegativity': 1.60, 'radius': 146},
        'Ta': {'electronegativity': 1.50, 'radius': 146},
        'Re': {'electronegativity': 1.90, 'radius': 137},
        'Ru': {'electronegativity': 2.20, 'radius': 134},
        'Rh': {'electronegativity': 2.28, 'radius': 134},
        'Pd': {'electronegativity': 2.20, 'radius': 137},
        'Ag': {'electronegativity': 1.93, 'radius': 144},
        'Au': {'electronegativity': 2.54, 'radius': 144},
        'Pt': {'electronegativity': 2.28, 'radius': 139},
        'Ir': {'electronegativity': 2.20, 'radius': 136},
        'Os': {'electronegativity': 2.20, 'radius': 135},
        'Hf': {'electronegativity': 1.30, 'radius': 159},
        'Zr': {'electronegativity': 1.33, 'radius': 160},
        'Sc': {'electronegativity': 1.36, 'radius': 162},
        'Y': {'electronegativity': 1.22, 'radius': 180},
        'La': {'electronegativity': 1.10, 'radius': 187},
        'Ce': {'electronegativity': 1.12, 'radius': 182},
        'Pr': {'electronegativity': 1.13, 'radius': 182},
        'Nd': {'electronegativity': 1.14, 'radius': 181},
        'Sm': {'electronegativity': 1.17, 'radius': 180},
        'Eu': {'electronegativity': 1.20, 'radius': 199},
        'Gd': {'electronegativity': 1.20, 'radius': 179},
        'Tb': {'electronegativity': 1.20, 'radius': 177},
        'Dy': {'electronegativity': 1.22, 'radius': 177},
        'Ho': {'electronegativity': 1.23, 'radius': 176},
        'Er': {'electronegativity': 1.24, 'radius': 176},
        'Tm': {'electronegativity': 1.25, 'radius': 175},
        'Yb': {'electronegativity': 1.10, 'radius': 194},
        'Lu': {'electronegativity': 1.27, 'radius': 174}
    }
    
    # Calculate weighted average properties based on composition
    element_cols = [col for col in df.columns if col in atomic_properties]
    
    if not element_cols:
        logger.warning("No elemental columns found for derived properties calculation.")
        return df
    
    # Initialize new columns
    df['avg_electronegativity'] = 0.0
    df['avg_radius'] = 0.0
    
    for _, row in df.iterrows():
        total_weight = 0.0
        weighted_electronegativity = 0.0
        weighted_radius = 0.0
        
        for elem in element_cols:
            weight = row.get(elem, 0.0)
            if weight > 0 and elem in atomic_properties:
                total_weight += weight
                weighted_electronegativity += weight * atomic_properties[elem]['electronegativity']
                weighted_radius += weight * atomic_properties[elem]['radius']
        
        if total_weight > 0:
            df.loc[row.name, 'avg_electronegativity'] = weighted_electronegativity / total_weight
            df.loc[row.name, 'avg_radius'] = weighted_radius / total_weight
    
    logger.info("Calculated derived atomic properties: avg_electronegativity, avg_radius")
    return df

def classify_alloy_family(row: pd.Series) -> str:
    """
    Classify an alloy row into a family based on its type or composition description.
    
    Args:
        row: A row from the dataframe
        
    Returns:
        String representing the alloy family
    """
    # Check 'alloy_type' or similar column
    alloy_type = str(row.get('alloy_type', row.get('type', row.get('material_type', '')))).lower()
    composition = str(row.get('composition', row.get('description', ''))).lower()
    
    combined_text = f"{alloy_type} {composition}"
    
    for family, keywords in ALLOY_FAMILIES.items():
        for keyword in keywords:
            if keyword in combined_text:
                return family
    
    return "Unknown"

def perform_ood_split(df: pd.DataFrame, output_dir: str = "data/processed", random_seed: int = 42) -> Dict[str, Any]:
    """
    Perform Out-of-Distribution (OOD) test set split based on alloy class.
    
    Identifies distinct alloy families (e.g., High-Entropy Alloys, Stainless Steels, Carbon Steels).
    If <2 classes exist, falls back to a stratified random split and flags this condition.
    Otherwise, holds out one full family as the test set.
    
    Args:
        df: Input DataFrame with alloy data
        output_dir: Directory to save output files
        random_seed: Random seed for reproducibility
        
    Returns:
        Dictionary with split statistics and file paths
    """
    import random
    random.seed(random_seed)
    np.random.seed(random_seed)
    
    logger.info("Starting OOD split based on alloy class...")
    
    # Classify alloy families
    df['alloy_family'] = df.apply(classify_alloy_family, axis=1)
    
    # Count classes
    family_counts = df['alloy_family'].value_counts()
    num_classes = len(family_counts)
    
    logger.info(f"Identified {num_classes} alloy families: {list(family_counts.index)}")
    
    stats = {
        "total_records": len(df),
        "num_alloy_families": num_classes,
        "family_distribution": family_counts.to_dict(),
        "split_method": "alloy_family_holdout",
        "fallback_used": False,
        "train_size": 0,
        "test_size": 0,
        "train_path": "",
        "test_path": ""
    }
    
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    if num_classes < 2:
        logger.warning(f"Only {num_classes} alloy family found. Falling back to stratified random split.")
        stats["split_method"] = "stratified_random_fallback"
        stats["fallback_used"] = True
        
        # Stratified random split (80/20)
        # Assuming 'degradation_type' or similar is the target for stratification
        stratify_col = 'degradation_type' if 'degradation_type' in df.columns else df.columns[0]
        
        train_df, test_df = train_test_split(
            df, 
            test_size=0.2, 
            random_state=random_seed, 
            stratify=df[stratify_col] if stratify_col in df.columns else None
        )
        
        # Remove the temporary 'alloy_family' column from output if it was only for classification
        # But keep it in the data for reference
        train_path = os.path.join(output_dir, "train_set.parquet")
        test_path = os.path.join(output_dir, "test_ood_set.parquet")
        
    else:
        # Select one family to hold out as test set (preferably the largest or a specific one)
        # For this implementation, we'll hold out the family with the most records to ensure a robust test set
        # Or we can hold out a specific "novel" family if known. Here we pick the last one alphabetically or the largest.
        # Let's pick the family with the median size to ensure it's not too small or too large, or just the first one.
        # A common strategy is to hold out a specific "rare" family. Here, we'll hold out the family with the smallest count
        # that still has a reasonable number of samples, or just the first one if all are large.
        # For simplicity, we'll hold out the family with the largest count to simulate a real-world scenario where a major class is held out.
        # Actually, for OOD, it's often better to hold out a distinct class. Let's hold out the "High-Entropy Alloys" if present, else the largest.
        
        holdout_family = None
        if "High-Entropy Alloys" in family_counts.index:
            holdout_family = "High-Entropy Alloys"
        else:
            # Pick the largest family
            holdout_family = family_counts.idxmax()
        
        logger.info(f"Holding out family '{holdout_family}' as test set.")
        
        test_df = df[df['alloy_family'] == holdout_family].copy()
        train_df = df[df['alloy_family'] != holdout_family].copy()
        
        train_path = os.path.join(output_dir, "train_set.parquet")
        test_path = os.path.join(output_dir, "test_ood_set.parquet")
    
    # Save to parquet
    train_df.to_parquet(train_path, index=False)
    test_df.to_parquet(test_path, index=False)
    
    stats["train_size"] = len(train_df)
    stats["test_size"] = len(test_df)
    stats["train_path"] = train_path
    stats["test_path"] = test_path
    
    # Save split report
    report_path = os.path.join(output_dir, "ood_split_report.json")
    with open(report_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"OOD split complete. Train: {len(train_df)}, Test: {len(test_df)}")
    logger.info(f"Report saved to {report_path}")
    
    return stats

def run_preprocessing_pipeline(input_path: str, output_dir: str = "data/processed") -> Dict[str, Any]:
    """
    Run the full preprocessing pipeline:
    1. Load data
    2. Handle missing values
    3. Map elemental composition to features
    4. Calculate derived atomic properties
    5. Perform OOD split
    
    Args:
        input_path: Path to the cleaned CSV from ingestion
        output_dir: Directory to save output files
        
    Returns:
        Dictionary with pipeline statistics
    """
    logger.info(f"Starting preprocessing pipeline from {input_path}")
    
    # Load data
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} records from {input_path}")
    
    # Handle missing values
    df, missing_stats = handle_missing_values(df)
    
    # Map elemental composition to features
    df = map_elemental_composition_to_features(df)
    
    # Calculate derived atomic properties
    df = calculate_derived_atomic_properties(df)
    
    # Perform OOD split
    ood_stats = perform_ood_split(df, output_dir)
    
    # Combine stats
    pipeline_stats = {
        "input_file": input_path,
        "output_dir": output_dir,
        "missing_value_stats": missing_stats,
        "ood_split_stats": ood_stats
    }
    
    # Save pipeline report
    report_path = os.path.join(output_dir, "preprocessing_report.json")
    with open(report_path, 'w') as f:
        json.dump(pipeline_stats, f, indent=2)
    
    logger.info(f"Preprocessing pipeline complete. Report saved to {report_path}")
    
    return pipeline_stats

# Helper function for stratified split (imported from sklearn if available, else implemented manually)
def train_test_split(df, test_size=0.2, random_state=None, stratify=None):
    """
    Simple train/test split implementation.
    If stratify is provided, it performs stratified sampling.
    """
    import random
    if random_state is not None:
        random.seed(random_state)
    
    indices = list(df.index)
    random.shuffle(indices)
    
    if stratify is not None:
        # Stratified split
        stratify_values = stratify.values
        train_indices = []
        test_indices = []
        
        unique_values = list(set(stratify_values))
        for val in unique_values:
            val_indices = [i for i in indices if stratify_values[i] == val]
            num_test = int(len(val_indices) * test_size)
            test_indices.extend(val_indices[:num_test])
            train_indices.extend(val_indices[num_test:])
        
        train_df = df.loc[train_indices]
        test_df = df.loc[test_indices]
    else:
        # Simple split
        num_test = int(len(indices) * test_size)
        test_indices = indices[:num_test]
        train_indices = indices[num_test:]
        
        train_df = df.loc[train_indices]
        test_df = df.loc[test_indices]
    
    return train_df, test_df

# Export public names
__all__ = [
    'handle_missing_values',
    'map_elemental_composition_to_features',
    'calculate_derived_atomic_properties',
    'perform_ood_split',
    'run_preprocessing_pipeline'
]
