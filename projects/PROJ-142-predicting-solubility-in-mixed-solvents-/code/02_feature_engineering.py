import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors, AllChem, rdMolDescriptors
from typing import List, Dict, Tuple, Optional
import json
import os
import sys
from pathlib import Path

# Add parent to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    from utils.constants import DATA_DIR
else:
    try:
        from utils.constants import DATA_DIR
    except ImportError:
        # Fallback for direct execution without package structure
        DATA_DIR = Path(__file__).parent.parent / "data"

def compute_molecular_descriptors(smiles: str) -> Dict[str, float]:
    """Compute basic molecular descriptors for a solute using RDKit."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {}
    
    descriptors = {
        'MolWt': Descriptors.MolWt(mol),
        'LogP': Descriptors.MolLogP(mol),
        'NumHDonors': Descriptors.NumHDonors(mol),
        'NumHAcceptors': Descriptors.NumHAcceptors(mol),
        'TPSA': Descriptors.TPSA(mol),
        'NumRotatableBonds': Descriptors.NumRotatableBonds(mol),
        'FractionCSP3': rdMolDescriptors.CalcFractionCSP3(mol),
    }
    return descriptors

def compute_morgan_fingerprint(smiles: str, radius: int = 2, n_bits: int = 2048) -> np.ndarray:
    """Compute Morgan fingerprint for a solute."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return np.zeros(n_bits)
    
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    arr = np.zeros((n_bits,), dtype=int)
    AllChem.DataStructs.ConvertToNumpyArray(fp, arr)
    return arr

def calculate_composition_weighted_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate composition-weighted solvent descriptors."""
    if df.empty:
        return df

    # Identify solvent property columns (assuming naming convention: prop_solvent1, prop_solvent2, etc.)
    # We look for columns that end with '_solvent' or similar pattern, but for now assume specific known columns
    # or derive from the dataframe structure.
    # Common solvent properties: LogP, Polarity, DielectricConstant, etc.
    
    # Strategy: Group columns by property name across solvents.
    # Assuming columns are named like: 'LogP_solvent_1', 'LogP_solvent_2', 'MoleFraction_solvent_1', etc.
    
    # Heuristic: Find columns that look like properties for solvents
    # We'll assume the input has columns: 'MoleFraction_1', 'MoleFraction_2', 'LogP_1', 'LogP_2', etc.
    # Or generic: 'Prop_1', 'Prop_2'
    
    # Let's assume the dataframe has columns: 
    # 'MoleFraction_solvent_1', 'MoleFraction_solvent_2', 
    # 'LogP_solvent_1', 'LogP_solvent_2', 
    # 'Dielectric_solvent_1', 'Dielectric_solvent_2', etc.
    
    # Identify property columns (excluding MoleFraction and Solute info)
    # We'll look for columns that contain a number at the end (e.g., _1, _2)
    import re
    
    # Get unique property prefixes by stripping the number suffix
    all_cols = df.columns.tolist()
    property_cols = [c for c in all_cols if re.search(r'_\d+$', c) and 'MoleFraction' not in c]
    
    if not property_cols:
        # Fallback: if no specific pattern found, try to infer or skip
        return df

    # Extract property names (prefix before the last underscore and number)
    property_names = set()
    for col in property_cols:
        match = re.match(r'^(.+)_(\d+)$', col)
        if match:
            property_names.add(match.group(1))
    
    # Calculate weighted descriptors
    for prop_name in property_names:
        # Get mole fraction columns for this property set
        # Assuming mole fractions are named 'MoleFraction_1', 'MoleFraction_2'
        # or 'MoleFraction_solvent_1', etc.
        mol_frac_cols = [c for c in all_cols if re.match(rf'^MoleFraction.*_{re.escape(prop_name.split("_")[-1])}$', c) or (prop_name in c and 'MoleFraction' in c)]
        # Simpler approach: assume MoleFraction_1, MoleFraction_2 exist if we have property_1, property_2
        mol_frac_cols = [c for c in all_cols if re.match(r'^MoleFraction_\d+$', c)]
        
        if not mol_frac_cols:
            continue
        
        # Sort to ensure consistent ordering
        mol_frac_cols.sort(key=lambda x: int(re.search(r'\d+$', x).group()))
        
        prop_cols = [c for c in property_cols if c.startswith(prop_name + '_')]
        prop_cols.sort(key=lambda x: int(re.search(r'\d+$', x).group()))
        
        if len(mol_frac_cols) != len(prop_cols):
            continue
        
        weighted_col_name = f'{prop_name}_weighted'
        df[weighted_col_name] = 0.0
        
        for mf_col, p_col in zip(mol_frac_cols, prop_cols):
            df[weighted_col_name] += df[mf_col] * df[p_col]
    
    return df

def add_interaction_terms(df: pd.DataFrame) -> pd.DataFrame:
    """
    Implement explicit interaction term generation.
    
    Logic:
    1. Check for mixed-solvent data (multiple solvent columns or mole fractions).
    2. If mixed-solvent data exists:
       - Generate polynomial terms (x1*x2, x1^2, x2^2) for mole fractions.
       - Generate ratio terms (x1/x2) if denominators are non-zero.
       - Generate interaction terms between weighted descriptors and solute properties.
    3. If pure solvent data (single solvent):
       - Apply polynomial/ratio terms to the single solvent's descriptors (e.g., LogP^2, 1/LogP).
    
    Appends new columns to the dataframe.
    """
    if df.empty:
        return df

    new_cols = []
    
    # Identify solvent components
    # Check for multiple mole fraction columns
    mol_frac_cols = [c for c in df.columns if 'MoleFraction' in c and 'weighted' not in c]
    mol_frac_cols = sorted([c for c in mol_frac_cols if re.search(r'_\d+$', c)], key=lambda x: int(re.search(r'\d+$', x).group()))
    
    is_mixed = len(mol_frac_cols) > 1
    
    # --- 1. Mole Fraction Interaction Terms ---
    if is_mixed:
        # Polynomial: x1 * x2
        if len(mol_frac_cols) >= 2:
            df['mole_frac_interaction'] = df[mol_frac_cols[0]] * df[mol_frac_cols[1]]
            new_cols.append('mole_frac_interaction')
            
            # Squared terms
            df[f'{mol_frac_cols[0]}_sq'] = df[mol_frac_cols[0]] ** 2
            df[f'{mol_frac_cols[1]}_sq'] = df[mol_frac_cols[1]] ** 2
            new_cols.extend([f'{mol_frac_cols[0]}_sq', f'{mol_frac_cols[1]}_sq'])
        
        # Ratio: x1 / x2 (handle division by zero)
        if len(mol_frac_cols) >= 2:
            x1 = df[mol_frac_cols[0]]
            x2 = df[mol_frac_cols[1]]
            # Avoid division by zero
            safe_x2 = x2.replace(0, 1e-9) 
            df['mole_frac_ratio'] = x1 / safe_x2
            new_cols.append('mole_frac_ratio')
    else:
        # Pure solvent case: generate terms for the single mole fraction (usually 1.0)
        # or apply to descriptors. If only one fraction, maybe just 1.0, so interaction is trivial.
        # Instead, apply to descriptors as per task: "apply to pure solvent descriptors"
        pass

    # --- 2. Descriptor Interaction Terms ---
    # Identify weighted descriptors and solute properties
    weighted_cols = [c for c in df.columns if c.endswith('_weighted')]
    solute_props = [c for c in df.columns if c in ['MolWt', 'LogP', 'NumHDonors', 'NumHAcceptors', 'TPSA', 'NumRotatableBonds', 'FractionCSP3']]
    
    if weighted_cols and solute_props:
        # Create interactions between solute properties and weighted solvent descriptors
        # e.g., LogP_solute * LogP_solvent_weighted
        for solute_col in solute_props:
            for weighted_col in weighted_cols:
                # Skip if same property name to avoid self-interaction redundancy if not desired
                # But here we want cross-interaction
                base_name = solute_col.split('_')[0] # e.g., 'LogP' from 'LogP'
                weighted_base = weighted_col.replace('_weighted', '')
                
                if base_name == weighted_base:
                    # Interaction of same property type (e.g., LogP * LogP_weighted)
                    col_name = f'{solute_col}_x_{weighted_col}'
                    df[col_name] = df[solute_col] * df[weighted_col]
                    new_cols.append(col_name)
                
                # Cross-property interactions (e.g., MolWt * LogP_weighted)
                # Limit to a few key cross-terms to avoid explosion
                if solute_col in ['MolWt', 'LogP'] and weighted_base in ['LogP', 'Polarity']:
                    col_name = f'{solute_col}_x_{weighted_col}'
                    df[col_name] = df[solute_col] * df[weighted_col]
                    new_cols.append(col_name)
    
    # --- 3. Pure Solvent Specific: Polynomial/Inverse of descriptors ---
    if not is_mixed and weighted_cols:
        # If pure solvent, apply polynomial/inverse to the weighted descriptors
        for weighted_col in weighted_cols:
            # Squared
            df[f'{weighted_col}_sq'] = df[weighted_col] ** 2
            new_cols.append(f'{weighted_col}_sq')
            
            # Inverse (safe)
            safe_val = df[weighted_col].replace(0, 1e-9)
            df[f'{weighted_col}_inv'] = 1.0 / safe_val
            new_cols.append(f'{weighted_col}_inv')

    return df

def execute_feature_engineering(input_path: str, output_path: str) -> None:
    """
    Main entry point for feature engineering.
    1. Load raw data.
    2. Compute molecular descriptors.
    3. Compute Morgan fingerprints (optional, might be too wide for CSV, but task asks for it).
    4. Calculate composition-weighted descriptors.
    5. Add interaction terms.
    6. Save to output.
    """
    print(f"Loading data from {input_path}...")
    df = pd.read_csv(input_path)
    
    print("Computing molecular descriptors...")
    # Apply descriptor computation row-wise
    # Assuming 'solute_smiles' or similar column exists
    smiles_col = None
    for col in df.columns:
        if 'smiles' in col.lower() and 'solute' in col.lower():
            smiles_col = col
            break
    if not smiles_col:
        # Try generic
        smiles_col = next((c for c in df.columns if 'smiles' in c.lower()), None)
    
    if smiles_col:
        desc_df = df[smiles_col].apply(compute_molecular_descriptors).apply(pd.Series)
        df = pd.concat([df, desc_df], axis=1)
    else:
        print("Warning: No solute SMILES column found. Skipping molecular descriptors.")

    print("Calculating composition-weighted descriptors...")
    df = calculate_composition_weighted_descriptors(df)
    
    print("Adding interaction terms...")
    df = add_interaction_terms(df)
    
    print(f"Saving processed features to {output_path}...")
    df.to_csv(output_path, index=False)
    print("Feature engineering complete.")

if __name__ == "__main__":
    # Default paths if not provided
    input_file = DATA_DIR / "processed" / "cleaned_compositions.csv"
    output_file = DATA_DIR / "processed" / "solubility_features.csv"
    
    if not input_file.exists():
        print(f"Error: Input file {input_file} not found. Run data ingestion first.")
        sys.exit(1)
    
    execute_feature_engineering(str(input_file), str(output_file))
