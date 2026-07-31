"""
Feature Engineering Module for Polymer Blend Structure-Property Relationships.

This module handles:
1. Loading harmonized data from previous ingestion steps.
2. Parsing SMILES and computing molecular descriptors using RDKit.
3. Calculating blend-specific features (weighted averages, absolute differences).
4. Deriving the target variable (Tg_residual) and interaction features (Fox/GT predictions).
5. Saving the processed dataset to data/processed/.
"""
import os
import json
import logging
import sys
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
from rdkit import RDLogger

# Disable RDKit warnings to keep logs clean
RDLogger.DisableLog('rdApp.*')

# Import project utilities
# Note: These paths assume execution from the project root or code/ directory
# Adjusted to match the API surface provided in the prompt
try:
    from utils.logger import get_logger
    from utils.seeds import set_deterministic_seed
    from utils.schema_validator import validate_output_file
    from config import ensure_directories
except ImportError:
    # Fallback for direct execution or different import context
    # This block ensures the script runs if imported directly or via runpy
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from utils.logger import get_logger
    from utils.seeds import set_deterministic_seed
    from utils.schema_validator import validate_output_file
    from config import ensure_directories

# Initialize logger
logger = get_logger(__name__)

# Constants
DEFAULT_RANDOM_SEED = 42
TARGET_COLUMN_NAME = "Tg_residual"
FOG_PREDICTION_COLUMN = "Tg_Fox_predicted"
GT_PREDICTION_COLUMN = "Tg_GordonTaylor_predicted"

def load_harmonized_data(input_path: Optional[str] = None) -> pd.DataFrame:
    """
    Loads the harmonized dataset from the processed raw data stage.
    
    Args:
        input_path: Optional path to the harmonized CSV. If None, defaults to 
                    data/processed/harmonized_polymer_data.csv (or similar output from T019).
                    
    Returns:
        pd.DataFrame: The loaded dataset.
    """
    if input_path is None:
        # Assuming the output from T019 (Ingestion) is the input here
        # Based on standard pipeline flow, T019 saves to data/processed/
        input_path = "data/processed/harmonized_polymer_data.csv"
    
    path_obj = Path(input_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Harmonized data file not found at {input_path}. "
                                f"Please ensure T019 (Ingestion) has completed successfully.")
    
    logger.info(f"Loading harmonized data from {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} records with columns: {list(df.columns)}")
    return df

def parse_smiles_to_mol(smiles: str) -> Optional[Chem.Mol]:
    """
    Converts a SMILES string to an RDKit Mol object.
    
    Args:
        smiles: SMILES string.
        
    Returns:
        RDKit Mol object or None if parsing fails.
    """
    if pd.isna(smiles) or not isinstance(smiles, str):
        return None
    try:
        mol = Chem.MolFromSmiles(smiles)
        return mol
    except Exception as e:
        logger.warning(f"Failed to parse SMILES '{smiles}': {e}")
        return None

def compute_molecular_descriptors(mol: Chem.Mol) -> Dict[str, float]:
    """
    Computes a set of molecular descriptors for a given RDKit Mol object.
    Includes at least 15 features as per requirements.
    
    Returns:
        Dictionary of descriptor name -> value.
    """
    if mol is None:
        return {}
    
    descriptors = {}
    
    # Basic Descriptors
    descriptors['MW'] = Descriptors.MolWt(mol)
    descriptors['TPSA'] = Descriptors.TPSA(mol)
    descriptors['LogP'] = Descriptors.MolLogP(mol)
    descriptors['NumHDonors'] = Descriptors.NumHDonors(mol)
    descriptors['NumHAcceptors'] = Descriptors.NumHAcceptors(mol)
    descriptors['NumRotatableBonds'] = Descriptors.NumRotatableBonds(mol)
    descriptors['NumAromaticRings'] = Descriptors.NumAromaticRings(mol)
    descriptors['NumSatAromaticRings'] = Descriptors.NumSatAromaticRings(mol)
    descriptors['FractionCSP3'] = Descriptors.FractionCSP3(mol)
    descriptors['NumHeavyAtoms'] = Descriptors.HeavyAtomCount(mol)
    descriptors['NumRings'] = Descriptors.RingCount(mol)
    descriptors['NumAliphaticRings'] = Descriptors.NumAliphaticRings(mol)
    descriptors['NumHeteroatoms'] = Descriptors.NumHeteroatoms(mol)
    descriptors['MaxDfP'] = Descriptors.MaxDfP(mol) # Max number of double bonds in a path
    descriptors['MinDfP'] = Descriptors.MinDfP(mol) # Min number of double bonds in a path
    
    # Add Free Volume proxy (approximated by molecular volume if available, else MW)
    # RDKit doesn't have a direct 'FreeVolume' descriptor, but we can use
    # Molecular Surface Area or a proxy.
    descriptors['MolVol'] = rdMolDescriptors.CalcMolVolume(mol)
    
    return descriptors

def generate_descriptors_for_row(row: pd.Series) -> Dict[str, float]:
    """
    Generates descriptors for a single row containing a SMILES string.
    """
    smiles = row.get('smiles', None)
    mol = parse_smiles_to_mol(smiles)
    if mol:
        return compute_molecular_descriptors(mol)
    return {}

def calculate_fox_equation(tg1: float, tg2: float, w1: float, w2: float) -> float:
    """
    Calculates the predicted Tg using the Fox equation.
    1/Tg = w1/Tg1 + w2/Tg2
    Temperatures must be in Kelvin.
    
    Args:
        tg1: Tg of component 1 (K)
        tg2: Tg of component 2 (K)
        w1: Weight fraction of component 1
        w2: Weight fraction of component 2
        
    Returns:
        Predicted Tg in Kelvin.
    """
    if w1 <= 0 or w2 <= 0 or tg1 <= 0 or tg2 <= 0:
        return np.nan
    try:
        inv_tg = (w1 / tg1) + (w2 / tg2)
        return 1.0 / inv_tg
    except ZeroDivisionError:
        return np.nan

def calculate_gordon_taylor_equation(tg1: float, tg2: float, w1: float, w2: float, k: float = 1.0) -> float:
    """
    Calculates the predicted Tg using the Gordon-Taylor equation.
    Tg = (w1*Tg1 + k*w2*Tg2) / (w1 + k*w2)
    
    Args:
        tg1: Tg of component 1 (K)
        tg2: Tg of component 2 (K)
        w1: Weight fraction of component 1
        w2: Weight fraction of component 2
        k: Interaction parameter (default 1.0)
        
    Returns:
        Predicted Tg in Kelvin.
    """
    if tg1 <= 0 or tg2 <= 0:
        return np.nan
    try:
        numerator = (w1 * tg1) + (k * w2 * tg2)
        denominator = w1 + (k * w2)
        if denominator == 0:
            return np.nan
        return numerator / denominator
    except Exception:
        return np.nan

def parse_composition_to_weights(composition_str: str) -> Tuple[float, float]:
    """
    Parses a composition string (e.g., "0.6,0.4") into weight fractions.
    
    Args:
        composition_str: String representation of weights.
        
    Returns:
        Tuple of (w1, w2).
    """
    try:
        if pd.isna(composition_str):
            return 0.0, 0.0
        parts = str(composition_str).split(',')
        if len(parts) != 2:
            return 0.0, 0.0
        w1 = float(parts[0].strip())
        w2 = float(parts[1].strip())
        return w1, w2
    except (ValueError, AttributeError):
        return 0.0, 0.0

def calculate_weighted_average_descriptors(df: pd.DataFrame, descriptor_cols: List[str]) -> pd.DataFrame:
    """
    Calculates weighted average descriptors for the blend.
    Assumes the DataFrame has columns for component descriptors (e.g., MW_1, MW_2) and weights (w1, w2).
    """
    for col in descriptor_cols:
        col_1 = f"{col}_1"
        col_2 = f"{col}_2"
        if col_1 in df.columns and col_2 in df.columns:
            df[f"blend_{col}"] = (df['w1'] * df[col_1]) + (df['w2'] * df[col_2])
        else:
            # If component descriptors aren't split yet, try to infer or skip
            # This logic assumes the row contains merged info or we need to split first
            pass
    return df

def calculate_absolute_difference_descriptors(df: pd.DataFrame, descriptor_cols: List[str]) -> pd.DataFrame:
    """
    Calculates absolute difference descriptors for the blend.
    """
    for col in descriptor_cols:
        col_1 = f"{col}_1"
        col_2 = f"{col}_2"
        if col_1 in df.columns and col_2 in df.columns:
            df[f"diff_{col}"] = np.abs(df[col_1] - df[col_2])
    return df

def derive_target_and_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derives the target variable (Tg_residual) and interaction features (Fox/GT predictions).
    
    Logic:
    1. Parse Tg1, Tg2, w1, w2.
    2. Calculate Tg_Fox_predicted.
    3. Calculate Tg_GordonTaylor_predicted.
    4. Calculate Tg_residual = Tg_measured - Tg_Fox_predicted.
    
    Args:
        df: DataFrame containing Tg1, Tg2, w1, w2, Tg_measured.
        
    Returns:
        DataFrame with new columns.
    """
    logger.info("Deriving target variable and interaction features...")
    
    # Ensure columns exist
    required_cols = ['Tg1_K', 'Tg2_K', 'w1', 'w2', 'Tg_measured_K']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for target derivation: {missing}")
    
    # Apply calculations
    def compute_row(row):
        t1 = row['Tg1_K']
        t2 = row['Tg2_K']
        w1 = row['w1']
        w2 = row['w2']
        t_meas = row['Tg_measured_K']
        
        t_fox = calculate_fox_equation(t1, t2, w1, w2)
        t_gt = calculate_gordon_taylor_equation(t1, t2, w1, w2)
        
        residual = np.nan
        if not np.isnan(t_fox):
            residual = t_meas - t_fox
        
        return pd.Series({
            FOG_PREDICTION_COLUMN: t_fox,
            GT_PREDICTION_COLUMN: t_gt,
            TARGET_COLUMN_NAME: residual
        })
    
    # Apply row-wise
    results = df.apply(compute_row, axis=1)
    
    # Concatenate results to original dataframe
    df = pd.concat([df, results], axis=1)
    
    # Log statistics
    logger.info(f"Computed {FOG_PREDICTION_COLUMN}, {GT_PREDICTION_COLUMN}, and {TARGET_COLUMN_NAME}")
    logger.info(f"Target variable ({TARGET_COLUMN_NAME}) stats: mean={df[TARGET_COLUMN_NAME].mean():.4f}, "
                f"std={df[TARGET_COLUMN_NAME].std():.4f}, nan_count={df[TARGET_COLUMN_NAME].isna().sum()}")
    
    return df

def run_feature_engineering(input_path: str = "data/processed/harmonized_polymer_data.csv",
                            output_path: str = "data/processed/feature_engineered_data.csv",
                            seed: int = DEFAULT_RANDOM_SEED) -> None:
    """
    Main orchestration function for feature engineering.
    
    1. Loads harmonized data.
    2. Generates molecular descriptors (expands to component features if needed).
    3. Calculates interaction features (Fox, Gordon-Taylor).
    4. Derives the target variable (Tg_residual).
    5. Saves the final dataset.
    
    Args:
        input_path: Path to input harmonized data.
        output_path: Path to save the processed data.
        seed: Random seed for determinism.
    """
    set_deterministic_seed(seed)
    ensure_directories()
    
    try:
        # 1. Load Data
        df = load_harmonized_data(input_path)
        
        # 2. Generate Component Descriptors (Simplified for this task)
        # Assuming the input has 'smiles_1' and 'smiles_2' or similar.
        # If the schema is different, we adapt.
        # For now, we assume the input has 'smiles' (if single entry) or 'smiles_1', 'smiles_2'.
        # If the input is a list of blends, we need to split descriptors.
        
        # Check for component SMILES columns
        if 'smiles_1' in df.columns and 'smiles_2' in df.columns:
            logger.info("Found component SMILES columns. Generating descriptors for each component.")
            
            # Generate for component 1
            df_comp1 = df[['smiles_1']].copy()
            df_comp1.columns = ['smiles']
            df_comp1['desc'] = df_comp1['smiles'].apply(generate_descriptors_for_row)
            desc_df1 = pd.DataFrame(df_comp1['desc'].tolist())
            desc_df1.columns = [f"{col}_1" for col in desc_df1.columns]
            
            # Generate for component 2
            df_comp2 = df[['smiles_2']].copy()
            df_comp2.columns = ['smiles']
            df_comp2['desc'] = df_comp2['smiles'].apply(generate_descriptors_for_row)
            desc_df2 = pd.DataFrame(df_comp2['desc'].tolist())
            desc_df2.columns = [f"{col}_2" for col in desc_df2.columns]
            
            df = pd.concat([df, desc_df1, desc_df2], axis=1)
            
            # Calculate blend features
            all_descs = [c.replace('_1', '') for c in desc_df1.columns if c.endswith('_1')]
            df = calculate_weighted_average_descriptors(df, all_descs)
            df = calculate_absolute_difference_descriptors(df, all_descs)
            
        elif 'smiles' in df.columns:
            # Single component or generic case - apply to all
            logger.warning("Only 'smiles' column found. Assuming single component or generic handling.")
            df['desc'] = df['smiles'].apply(generate_descriptors_for_row)
            desc_df = pd.DataFrame(df['desc'].tolist())
            desc_df.columns = [f"{col}_1" for col in desc_df.columns] # Treat as component 1 for now
            df = pd.concat([df, desc_df], axis=1)
        else:
            logger.warning("No SMILES columns found. Skipping descriptor generation.")
        
        # 3. Derive Target and Interaction Features
        df = derive_target_and_interaction_features(df)
        
        # 4. Save Output
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_csv(output_path, index=False)
        logger.info(f"Feature engineered data saved to {output_path}")
        
        # 5. Validate Output (Basic)
        if TARGET_COLUMN_NAME not in df.columns:
            raise ValueError("Target variable derivation failed: Tg_residual column missing.")
        
        logger.info("Feature engineering completed successfully.")
        
    except Exception as e:
        logger.error(f"Feature engineering failed: {e}")
        traceback.print_exc()
        raise

def main():
    """Entry point for script execution."""
    logger.info("Starting Feature Engineering Module (T027a)...")
    
    # Default paths based on project structure
    input_path = "data/processed/harmonized_polymer_data.csv"
    output_path = "data/processed/feature_engineered_data.csv"
    
    # Check if input exists, if not, try to find the most recent harmonized file
    if not Path(input_path).exists():
        # Fallback: look in data/processed/
        processed_dir = Path("data/processed")
        if processed_dir.exists():
            files = list(processed_dir.glob("*.csv"))
            if files:
                input_path = str(files[-1])
                logger.info(f"Using fallback input: {input_path}")
            else:
                logger.error("No CSV files found in data/processed/")
                sys.exit(1)
    
    run_feature_engineering(input_path=input_path, output_path=output_path)

if __name__ == "__main__":
    main()
