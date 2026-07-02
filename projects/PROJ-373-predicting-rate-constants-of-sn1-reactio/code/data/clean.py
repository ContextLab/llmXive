import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors

def calculate_steric_index(mol: Chem.Mol) -> float:
    """Calculate steric index for a molecule."""
    if mol is None:
        return float('inf')
    rotatable = rdMolDescriptors.CalcNumRotatableBonds(mol)
    # Crippen descriptor for steric component (approximation)
    try:
        crippen = Descriptors.MolLogP(mol)  # Using LogP as proxy for steric
    except:
        crippen = 0.0
    return rotatable + abs(crippen)

def canonicalize_smiles(smiles: str) -> Optional[str]:
    """Canonicalize a SMILES string."""
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol:
            return Chem.MolToSmiles(mol, isomericSmiles=True)
        return None
    except:
        return None

def is_primary_substrate(mol: Chem.Mol) -> bool:
    """Check if molecule is a primary alkyl halide."""
    if mol is None:
        return False
    # Simple heuristic: count heavy atoms attached to halogen
    for atom in mol.GetAtoms():
        if atom.GetAtomicNum() in [9, 17, 35, 53]:  # F, Cl, Br, I
            neighbors = atom.GetNeighbors()
            if len(neighbors) == 1 and neighbors[0].GetAtomicNum() == 6:
                # Check if that carbon is attached to only 1 other carbon
                carbon = neighbors[0]
                carbon_neighbors = [n for n in carbon.GetNeighbors() if n.GetAtomicNum() == 6]
                if len(carbon_neighbors) == 0:
                    return True
    return False

def clean_and_filter_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """Clean SMILES and filter primary alkyl halides."""
    exclusions = []
    cleaned_rows = []

    for idx, row in df.iterrows():
        smiles = row.get("smiles", "")
        if not smiles:
            exclusions.append({"row_index": idx, "reason": "parsing_error", "original_smiles": ""})
            continue

        canonical = canonicalize_smiles(smiles)
        if canonical is None:
            exclusions.append({"row_index": idx, "reason": "parsing_error", "original_smiles": smiles})
            continue

        mol = Chem.MolFromSmiles(canonical)
        if mol is None:
            exclusions.append({"row_index": idx, "reason": "parsing_error", "original_smiles": smiles})
            continue

        # Check substrate class
        substrate_class = row.get("substrate_class", "").lower()
        if substrate_class == "primary":
            exclusions.append({"row_index": idx, "reason": "invalid_substrate", "original_smiles": smiles})
            continue

        # Calculate steric index
        steric = calculate_steric_index(mol)
        if steric > 2.0:
            exclusions.append({"row_index": idx, "reason": "invalid_substrate", "original_smiles": smiles})
            continue

        row["smiles"] = canonical
        cleaned_rows.append(row)

    cleaned_df = pd.DataFrame(cleaned_rows)
    return cleaned_df, exclusions

def main():
    """Main entry point for data cleaning."""
    base_dir = Path(__file__).parent.parent.parent
    data_dir = base_dir / "data" / "raw"
    processed_dir = base_dir / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    input_path = data_dir / "raw_sn1_data.csv"
    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        sys.exit(1)

    df = pd.read_csv(input_path)
    cleaned_df, exclusions = clean_and_filter_data(df)

    output_path = processed_dir / "cleaned_sn1_step1.csv"
    cleaned_df.to_csv(output_path, index=False)

    exclusion_path = processed_dir / "exclusion_report_step1.csv"
    pd.DataFrame(exclusions).to_csv(exclusion_path, index=False)

    print(f"Cleaned data saved to {output_path}")
    print(f"Exclusions saved to {exclusion_path}")

if __name__ == "__main__":
    main()
