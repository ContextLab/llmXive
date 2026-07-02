import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import rdPartialCharges, Descriptors

def compute_gasteiger_charges(mol: Chem.Mol) -> List[float]:
    """Compute Gasteiger partial charges for a molecule."""
    if mol is None:
        return []
    try:
        rdPartialCharges.ComputeGasteigerCharges(mol)
        charges = [float(atom.GetProp('_GasteigerCharge')) for atom in mol.GetAtoms()]
        return charges
    except:
        return []

def compute_topological_indices(mol: Chem.Mol) -> List[float]:
    """Compute topological indices for a molecule."""
    if mol is None:
        return []
    indices = []
    try:
        indices.append(Descriptors.MolWt(mol))
        indices.append(Descriptors.MolLogP(mol))
        indices.append(Descriptors.NumRotatableBonds(mol))
        indices.append(Descriptors.TPSA(mol))
        indices.append(Descriptors.NumHDonors(mol))
        indices.append(Descriptors.NumHAcceptors(mol))
    except:
        pass
    return indices

def process_single_row(row: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
    """Process a single row to compute descriptors."""
    smiles = row.get("smiles", "")
    if not smiles:
        return row, "missing_smiles"

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return row, "invalid_mol"

    charges = compute_gasteiger_charges(mol)
    indices = compute_topological_indices(mol)

    row["gasteiger_charges"] = charges
    row["topological_indices"] = indices
    return row, None

def compute_descriptors_for_dataset(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """Compute descriptors for the entire dataset."""
    exclusions = []
    processed_rows = []

    for idx, row in df.iterrows():
        processed_row, error = process_single_row(row.to_dict())
        if error:
            exclusions.append({
                "row_index": idx,
                "reason": error,
                "original_smiles": row.get("smiles", "")
            })
        else:
            processed_rows.append(processed_row)

    return pd.DataFrame(processed_rows), exclusions

def main():
    """Main entry point for descriptor computation."""
    base_dir = Path(__file__).parent.parent.parent
    processed_dir = base_dir / "data" / "processed"

    input_path = processed_dir / "cleaned_sn1_step1.csv"
    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        sys.exit(1)

    df = pd.read_csv(input_path)
    processed_df, exclusions = compute_descriptors_for_dataset(df)

    output_path = processed_dir / "cleaned_sn1.csv"
    processed_df.to_csv(output_path, index=False)

    exclusion_path = processed_dir / "exclusion_report.csv"
    pd.DataFrame(exclusions).to_csv(exclusion_path, index=False)

    print(f"Descriptors computed. Saved to {output_path}")

if __name__ == "__main__":
    main()
