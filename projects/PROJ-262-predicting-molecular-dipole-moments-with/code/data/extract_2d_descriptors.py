from __future__ import annotations

import numpy as np
import pandas as pd
from typing import List, Dict, Any
import sys
from pathlib import Path
import rdkit
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors
from rdkit import RDLogger

# Suppress RDKit warnings for cleaner output
RDLogger.DisableLog('rdApp.*')

def extract_2d_features(input_path: Path, output_path: Path):
    """
    Extracts 2D molecular descriptors (Morgan fingerprints, simple descriptors)
    from a CSV file containing molecular data (SMILES or InChI).
    
    Input CSV expected columns: molecule_id, smiles (or similar)
    Output: Parquet file with molecule_id and feature vectors.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    print(f"Loading data from {input_path}...")
    df = pd.read_csv(input_path)
    
    # Identify SMILES column (common names)
    smiles_col = None
    for col in ['smiles', 'SMILES', 'smi', 'mol_smiles']:
        if col in df.columns:
            smiles_col = col
            break
    
    if smiles_col is None:
        # Fallback: assume first string column is SMILES
        str_cols = df.select_dtypes(include=['object']).columns
        if len(str_cols) > 0:
            smiles_col = str_cols[0]
            print(f"WARNING: No standard SMILES column found. Using '{smiles_col}' as SMILES.")
        else:
            raise ValueError("Could not identify SMILES column in input data.")
    
    print(f"Using column '{smiles_col}' for 2D feature extraction.")
    
    fingerprints = []
    molecule_ids = []
    descriptor_values = []
    
    print("Generating 2D features (Morgan fingerprints + Descriptors)...")
    for idx, row in df.iterrows():
        mol_id = row['molecule_id']
        smiles = row[smiles_col]
        
        if pd.isna(smiles):
            continue
            
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                continue
            
            # Morgan Fingerprint (radius=2, nBits=2048)
            fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=2048)
            fp_arr = np.zeros((2048,), dtype=np.int8)
            fp_arr = np.array(fp, dtype=np.int8)
            
            # Simple Descriptors
            desc = [
                Descriptors.MolWt(mol),
                Descriptors.MolLogP(mol),
                Descriptors.NumHDonors(mol),
                Descriptors.NumHAcceptors(mol),
                Descriptors.TPSA(mol),
                Descriptors.NumRotatableBonds(mol),
                Descriptors.NumAromaticRings(mol),
                Descriptors.FractionCSP3(mol)
            ]
            
            # Combine features: [Fingerprint (2048), Descriptors (8)]
            # Note: For memory efficiency, we might store separately, but task asks for one file
            # We will create a row with the fingerprint as a list/array and descriptors as columns
            # Or flatten everything. Let's store as a list for the fingerprint to keep it compact in parquet
            # Actually, Parquet handles lists well.
            
            fingerprints.append(list(fp_arr))
            descriptor_values.append(desc)
            molecule_ids.append(mol_id)
            
        except Exception as e:
            # Log but continue
            print(f"Warning: Failed to process {mol_id}: {e}", file=sys.stderr)
            continue

    if len(molecule_ids) == 0:
        raise RuntimeError("No valid molecules processed. Check input data format.")
    
    # Create DataFrame
    # We'll store the fingerprint as a list column and descriptors as separate columns
    # to make it easier to query later.
    result_df = pd.DataFrame({
        'molecule_id': molecule_ids,
        'fingerprint': fingerprints,
        'mol_wt': [v[0] for v in descriptor_values],
        'mol_logp': [v[1] for v in descriptor_values],
        'num_h_donors': [v[2] for v in descriptor_values],
        'num_h_acceptors': [v[3] for v in descriptor_values],
        'tpsa': [v[4] for v in descriptor_values],
        'num_rotatable_bonds': [v[5] for v in descriptor_values],
        'num_aromatic_rings': [v[6] for v in descriptor_values],
        'fraction_csp3': [v[7] for v in descriptor_values],
    })
    
    print(f"Writing 2D features to {output_path}...")
    result_df.to_parquet(output_path, index=False)
    print(f"Successfully wrote {len(result_df)} molecules to {output_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    args = parser.parse_args()
    extract_2d_features(Path(args.input), Path(args.output))
