import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors, AllChem, rdMolDescriptors
from typing import List, Dict, Tuple, Optional
import json
import os
import sys
from pathlib import Path

# Constants and paths
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
PROCESSED_DIR = DATA_DIR / "processed"
ARTIFACTS_DIR = DATA_DIR / "artifacts"

# Ensure directories exist
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

def compute_molecular_descriptors(smiles: str) -> Dict[str, float]:
    """Compute basic molecular descriptors for a single SMILES string."""
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return {}
        
        descriptors = {
            'mw': Descriptors.MolWt(mol),
            'logp': Descriptors.MolLogP(mol),
            'hbd': Descriptors.NumHDonors(mol),
            'hba': Descriptors.NumHAcceptors(mol),
            'tpsa': Descriptors.TPSA(mol),
            'rotatable_bonds': Descriptors.NumRotatableBonds(mol),
            'aromatic_rings': rdMolDescriptors.CalcNumAromaticRings(mol),
            'rings': rdMolDescriptors.CalcNumRings(mol),
        }
        return descriptors
    except Exception as e:
        print(f"Error computing descriptors for {smiles}: {e}", file=sys.stderr)
        return {}

def compute_morgan_fingerprint(smiles: str, radius: int = 2, n_bits: int = 2048) -> np.ndarray:
    """Compute Morgan fingerprint for a single SMILES string."""
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return np.zeros(n_bits, dtype=np.int8)
        
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
        arr = np.zeros(n_bits, dtype=np.int8)
        for idx in fp.GetOnBits():
            arr[idx] = 1
        return arr
    except Exception as e:
        print(f"Error computing fingerprint for {smiles}: {e}", file=sys.stderr)
        return np.zeros(n_bits, dtype=np.int8)

def calculate_composition_weighted_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate composition-weighted solvent descriptors."""
    # Assuming columns: 'solvent_desc_1', 'solvent_desc_2', ... and 'mole_frac_1', 'mole_frac_2', ...
    # This is a simplified version; actual implementation depends on data structure
    descriptor_cols = [col for col in df.columns if col.startswith('solvent_desc_')]
    if not descriptor_cols:
        return df
    
    # Get corresponding mole fraction columns
    frac_cols = [col.replace('solvent_desc_', 'mole_frac_') for col in descriptor_cols]
    frac_cols = [col for col in frac_cols if col in df.columns]
    
    if len(frac_cols) != len(descriptor_cols):
        print("Warning: Mismatch between descriptor and mole fraction columns", file=sys.stderr)
        return df
    
    weighted_desc = np.zeros(len(df))
    for desc_col, frac_col in zip(descriptor_cols, frac_cols):
        weighted_desc += df[desc_col].values * df[frac_col].values
    
    df['weighted_solvent_desc'] = weighted_desc
    return df

def add_interaction_terms(df: pd.DataFrame, pivot_status: str) -> pd.DataFrame:
    """Add interaction terms based on pivot status."""
    if pivot_status == "pivoted":
        # Generate interaction terms for pure solvents
        # Example: polynomial terms of weighted descriptors
        if 'weighted_solvent_desc' in df.columns:
            df['interaction_term_1'] = df['weighted_solvent_desc'] ** 2
            df['interaction_term_2'] = df['weighted_solvent_desc'] * df['weighted_solvent_desc']
    else:
        # Generate interaction terms for mixed solvents
        # Example: ratio of solvent properties
        if 'weighted_solvent_desc' in df.columns and 'mw' in df.columns:
            df['interaction_term_1'] = df['weighted_solvent_desc'] / (df['mw'] + 1e-6)
            df['interaction_term_2'] = df['weighted_solvent_desc'] * df['mw']
    
    return df

def execute_feature_engineering(input_path: str, output_path: str) -> pd.DataFrame:
    """Main function to execute feature engineering pipeline."""
    print(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Compute molecular descriptors for solutes
    print("Computing molecular descriptors...")
    desc_list = df['solute_smiles'].apply(compute_molecular_descriptors).apply(pd.Series)
    df = pd.concat([df, desc_list], axis=1)
    
    # Compute Morgan fingerprints (simplified for demo, typically done in batches)
    print("Computing Morgan fingerprints...")
    fps = df['solute_smiles'].apply(lambda x: compute_morgan_fingerprint(x))
    # Store as string representation for CSV compatibility
    df['solute_fp'] = [fp.tobytes().hex() for fp in fps]
    
    # Calculate composition-weighted descriptors
    print("Calculating composition-weighted descriptors...")
    df = calculate_composition_weighted_descriptors(df)
    
    # Count mixed-solvent entries for pivot logic
    mixed_count = len(df[df['is_mixed_solvent'] == True]) if 'is_mixed_solvent' in df.columns else 0
    print(f"Mixed-solvent entries: {mixed_count}")
    
    # Determine pivot status and save decision
    pivot_status = "pivoted" if mixed_count < 100 else "normal"
    pivot_decision = {
        "status": pivot_status,
        "mixed_solvent_count": mixed_count,
        "reason": f"Insufficient mixed solvent data (< 100 rows). Non-linear mixing hypothesis dropped. Interaction terms will be generated for pure solvents." if pivot_status == "pivoted" else "Sufficient mixed solvent data available."
    }
    
    pivot_path = ARTIFACTS_DIR / "pivot_decision.json"
    with open(pivot_path, 'w') as f:
        json.dump(pivot_decision, f, indent=2)
    print(f"Pivot decision saved to {pivot_path}")
    
    # Add interaction terms based on pivot status
    print("Adding interaction terms...")
    df = add_interaction_terms(df, pivot_status)
    
    # Save final dataset
    print(f"Saving processed data to {output_path}")
    df.to_csv(output_path, index=False)
    
    return df

def main():
    """Main entry point."""
    input_file = PROCESSED_DIR / "imputed_data.csv"
    output_file = PROCESSED_DIR / "solubility_features.csv"
    
    if not input_file.exists():
        print(f"Error: Input file {input_file} does not exist.", file=sys.stderr)
        sys.exit(1)
    
    df = execute_feature_engineering(str(input_file), str(output_file))
    print(f"Feature engineering complete. Output saved to {output_file}")

if __name__ == "__main__":
    main()