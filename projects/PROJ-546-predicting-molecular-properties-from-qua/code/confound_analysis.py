"""
Confound Analysis Module (T011b)

Implements FR-008: Calculate Molecular Weight, Atom Count, and functional group
enumeration for all molecules using RDKit.

Output: data/confounds.csv with columns:
  - molecule_id (str)
  - mw (float)
  - atom_count (int)
  - functional_groups (str, pipe-separated)
"""

import csv
import os
import sys
from pathlib import Path
from typing import List, Set, Dict, Any, Optional

# RDKit imports
try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, Lipinski
    from rdkit import RDLogger
except ImportError:
    raise ImportError(
        "RDKit is required for confound analysis. "
        "Install via: pip install rdkit"
    )

# Disable RDKit warnings for cleaner logs
RDLogger.DisableLog('rdApp.*')


def load_molecules_from_csv(input_path: str) -> List[Dict[str, Any]]:
    """
    Load molecules from a CSV file containing SMILES strings.
    Expected columns: 'molecule_id' (or 'id') and 'smiles'.
    """
    molecules = []
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # Normalize header keys to lowercase
        headers = [h.lower().strip() for h in reader.fieldnames]
        
        # Determine column names
        smiles_col = None
        id_col = None
        
        if 'smiles' in headers:
            smiles_col = 'smiles'
        elif 'smile' in headers:
            smiles_col = 'smile'
        
        if 'molecule_id' in headers:
            id_col = 'molecule_id'
        elif 'id' in headers:
            id_col = 'id'
        
        if not smiles_col:
            raise ValueError("CSV must contain a 'smiles' or 'smile' column.")
        if not id_col:
            raise ValueError("CSV must contain an 'molecule_id' or 'id' column.")

        for row in reader:
            # Access row with original keys but match via lowercase logic if needed
            # DictReader preserves original keys, so we map back
            row_lower = {k.lower(): v for k, v in row.items()}
            smiles = row_lower.get(smiles_col)
            mol_id = row_lower.get(id_col)
            
            if not smiles:
                continue
                
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                # Log warning but skip invalid molecules
                print(f"Warning: Invalid SMILES for {mol_id}, skipping.", file=sys.stderr)
                continue
            
            molecules.append({
                'id': mol_id,
                'smiles': smiles,
                'mol': mol
            })
    
    if not molecules:
        raise ValueError("No valid molecules found in the input file.")
        
    return molecules


def parse_functional_groups(mol: Chem.Mol) -> List[str]:
    """
    Enumerate functional groups using RDKit's Lipinski and standard patterns.
    Returns a list of group names (e.g., 'amide', 'aromatic', 'hydroxyl').
    """
    groups = []
    
    # 1. Aromatic rings
    if mol.GetNumRingInfo().NumRings() > 0:
        # Check for aromaticity in the molecule
        if any(atom.GetIsAromatic() for atom in mol.GetAtoms()):
            groups.append('aromatic')
    
    # 2. Hydroxyl groups (-OH)
    # Pattern: Oxygen with 1 neighbor (excluding H) and 1 H, or Oxygen with 1 neighbor and 1 H count
    # Simpler: Check for O with exactly 1 heavy neighbor and 1 H
    has_hydroxyl = False
    for atom in mol.GetAtoms():
        if atom.GetAtomicNum() == 8: # Oxygen
            heavy_neighbors = [a for a in atom.GetNeighbors() if a.GetAtomicNum() != 1]
            if len(heavy_neighbors) == 1 and atom.GetTotalNumHs() >= 1:
                has_hydroxyl = True
                break
    if has_hydroxyl:
        groups.append('hydroxyl')
        
    # 3. Carbonyls (C=O) - generic
    has_carbonyl = False
    for atom in mol.GetAtoms():
        if atom.GetAtomicNum() == 6: # Carbon
            neighbors = atom.GetNeighbors()
            # Check for double bond to Oxygen
            for bond in atom.GetBonds():
                if bond.GetBondType() == Chem.BondType.DOUBLE:
                    other = bond.GetOtherAtom(atom)
                    if other.GetAtomicNum() == 8:
                        has_carbonyl = True
                        break
            if has_carbonyl: break
    if has_carbonyl:
        groups.append('carbonyl')
        
    # 4. Amides (N-C=O)
    # Pattern: Nitrogen connected to a Carbon that is double bonded to Oxygen
    has_amide = False
    for atom in mol.GetAtoms():
        if atom.GetAtomicNum() == 7: # Nitrogen
            for neighbor in atom.GetNeighbors():
                if neighbor.GetAtomicNum() == 6: # Carbon
                    # Check if this carbon has a double bond to Oxygen
                    for bond in neighbor.GetBonds():
                        if bond.GetBondType() == Chem.BondType.DOUBLE:
                            other = bond.GetOtherAtom(neighbor)
                            if other.GetAtomicNum() == 8:
                                has_amide = True
                                break
                if has_amide: break
        if has_amide: break
    if has_amide:
        groups.append('amide')
        
    # 5. Amines (aliphatic N with H, not amide)
    # Re-use amide check to exclude
    has_amine = False
    for atom in mol.GetAtoms():
        if atom.GetAtomicNum() == 7:
            # Check if it's part of an amide (already detected)
            is_amide_n = False
            for neighbor in atom.GetNeighbors():
                if neighbor.GetAtomicNum() == 6:
                    for bond in neighbor.GetBonds():
                        if bond.GetBondType() == Chem.BondType.DOUBLE:
                            other = bond.GetOtherAtom(neighbor)
                            if other.GetAtomicNum() == 8:
                                is_amide_n = True
                                break
            if not is_amide_n and atom.GetTotalNumHs() > 0:
                has_amine = True
                break
    if has_amine:
        groups.append('amine')
        
    # 6. Carboxylic Acids (C(=O)O)
    has_carboxylic = False
    for atom in mol.GetAtoms():
        if atom.GetAtomicNum() == 6:
            has_double_o = False
            has_single_o = False
            for bond in atom.GetBonds():
                other = bond.GetOtherAtom(atom)
                if other.GetAtomicNum() == 8:
                    if bond.GetBondType() == Chem.BondType.DOUBLE:
                        has_double_o = True
                    elif bond.GetBondType() == Chem.BondType.SINGLE:
                        has_single_o = True
            if has_double_o and has_single_o:
                has_carboxylic = True
                break
    if has_carboxylic:
        groups.append('carboxylic_acid')
        
    # 7. Halogens
    halogens = [9, 17, 35, 53] # F, Cl, Br, I
    has_halogen = any(atom.GetAtomicNum() in halogens for atom in mol.GetAtoms())
    if has_halogen:
        groups.append('halogen')
        
    # 8. Sulfur containing (Thiols, etc)
    has_sulfur = any(atom.GetAtomicNum() == 16 for atom in mol.GetAtoms())
    if has_sulfur:
        groups.append('sulfur')

    # 9. Phosphorus
    has_phosphorus = any(atom.GetAtomicNum() == 15 for atom in mol.GetAtoms())
    if has_phosphorus:
        groups.append('phosphorus')

    # 10. Nitro group (N(=O)=O)
    has_nitro = False
    for atom in mol.GetAtoms():
        if atom.GetAtomicNum() == 7:
            o_count = 0
            for bond in atom.GetBonds():
                other = bond.GetOtherAtom(atom)
                if other.GetAtomicNum() == 8:
                    o_count += 1
            if o_count == 2:
                has_nitro = True
                break
    if has_nitro:
        groups.append('nitro')

    return groups


def calculate_molecular_properties(mol: Chem.Mol) -> Dict[str, float]:
    """
    Calculate standard molecular properties using RDKit Descriptors.
    Returns: {'mw': float, 'atom_count': int, ...}
    """
    # Molecular Weight
    mw = Descriptors.MolWt(mol)
    
    # Atom Count
    atom_count = mol.GetNumAtoms()
    
    return {
        'mw': float(mw),
        'atom_count': int(atom_count)
    }


def process_molecule(mol_entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single molecule entry to extract confounds.
    """
    mol = mol_entry['mol']
    mol_id = mol_entry['id']
    
    props = calculate_molecular_properties(mol)
    groups = parse_functional_groups(mol)
    
    # Format groups as pipe-separated string
    groups_str = '|'.join(sorted(groups)) if groups else ''
    
    return {
        'molecule_id': mol_id,
        'mw': props['mw'],
        'atom_count': props['atom_count'],
        'functional_groups': groups_str
    }


def write_confounds_csv(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Write the confound analysis results to a CSV file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    fieldnames = ['molecule_id', 'mw', 'atom_count', 'functional_groups']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def main():
    """
    Main entry point for T011b.
    Reads data/raw/barrier_data.csv (or similar) and writes data/confounds.csv.
    """
    # Determine input path: Look for the downloaded dataset
    # Based on T004, the data is likely in data/raw/
    input_file = Path("data/raw/barrier_data.csv")
    
    # Fallback if the specific name isn't known, try to find any CSV in raw
    if not input_file.exists():
        raw_dir = Path("data/raw")
        if raw_dir.exists():
            csv_files = list(raw_dir.glob("*.csv"))
            if csv_files:
                input_file = csv_files[0]
            else:
                print("Error: No CSV files found in data/raw/", file=sys.stderr)
                sys.exit(1)
        else:
            print("Error: data/raw/ directory not found.", file=sys.stderr)
            sys.exit(1)
    
    output_file = Path("data/confounds.csv")
    
    print(f"Loading molecules from: {input_file}")
    molecules = load_molecules_from_csv(str(input_file))
    print(f"Loaded {len(molecules)} valid molecules.")
    
    print("Calculating confounds...")
    results = []
    for mol_entry in molecules:
        try:
            result = process_molecule(mol_entry)
            results.append(result)
        except Exception as e:
            print(f"Error processing {mol_entry['id']}: {e}", file=sys.stderr)
            continue
    
    print(f"Writing results to: {output_file}")
    write_confounds_csv(results, str(output_file))
    
    print(f"Successfully wrote {len(results)} records to {output_file}")


if __name__ == "__main__":
    main()
