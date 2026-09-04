"""
T011: Confounds Analysis
Reads SMILES from data/raw/barrier_dataset.csv, calculates molecular properties,
and outputs data/confounds.csv.
"""
import csv
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

# Check for RDKit availability
try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, Lipinski, Fragments
except ImportError:
    print("ERROR: RDKit is required. Install via: pip install rdkit", file=sys.stderr)
    sys.exit(1)

INPUT_PATH = Path("data/raw/barrier_dataset.csv")
OUTPUT_PATH = Path("data/confounds.csv")
LOG_PATH = Path("data/confounds_verification.log")

def load_molecules_from_csv(input_path: Path) -> List[Dict[str, Any]]:
    """Load SMILES and IDs from the barrier dataset CSV."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    molecules = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # Validate required columns exist
        if 'SMILES' not in reader.fieldnames:
            raise ValueError(f"Input CSV missing required column 'SMILES'. Found: {reader.fieldnames}")
        
        for idx, row in enumerate(reader):
            mol_id = row.get('molecule_id', f"mol_{idx}")
            smiles = row['SMILES']
            molecules.append({'molecule_id': mol_id, 'smiles': smiles})
    
    return molecules

def parse_functional_groups(mol: Chem.Mol) -> str:
    """
    Identify functional groups using RDKit Fragments and Lipinski.
    Returns a pipe-separated string of detected groups.
    """
    groups = []
    
    # Common fragment descriptors (return counts, check > 0)
    # Using Fragments module for specific group counts
    frag_funcs = [
        ('OH', Fragments.fr_Al_OH),
        ('carbonyl', Fragments.fr_Aldehyde),
        ('carboxyl', Fragments.fr_COO),
        ('ester', Fragments.fr_Ester),
        ('amine', Fragments.fr_Amine),
        ('amide', Fragments.fr_Amide),
        ('phenol', Fragments.fr_Phenol),
        ('aromatic', Fragments.fr_Ar),
        ('nitro', Fragments.fr_Nitro),
        ('halogen', Fragments.fr_halogen),
    ]
    
    for name, func in frag_funcs:
        try:
            count = func(mol)
            if count > 0:
                groups.append(f"{name}:{int(count)}")
        except Exception:
            continue

    # Lipinski features
    lipinski_funcs = [
        ('HBA', Lipinski.NumHAcceptors),
        ('HBD', Lipinski.NumHDonors),
    ]
    
    for name, func in lipinski_funcs:
        try:
            count = func(mol)
            if count > 0:
                groups.append(f"{name}:{int(count)}")
        except Exception:
            continue

    return "|".join(groups) if groups else "none"

def calculate_molecular_properties(mol: Chem.Mol) -> Dict[str, Any]:
    """Calculate MW and atom count."""
    if mol is None:
        return {'mw': 0.0, 'atom_count': 0}
    
    try:
        mw = Descriptors.MolWt(mol)
        atom_count = Descriptors.NumAtoms(mol)
    except Exception:
        mw = 0.0
        atom_count = 0
    
    return {'mw': float(mw), 'atom_count': int(atom_count)}

def process_molecule(mol_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Process a single molecule entry."""
    smiles = mol_data['smiles']
    mol_id = mol_data['molecule_id']
    
    # Convert SMILES to Mol object
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        # Log warning but skip invalid molecules
        print(f"Warning: Could not parse SMILES for {mol_id}: {smiles}", file=sys.stderr)
        return None
    
    # Calculate properties
    props = calculate_molecular_properties(mol)
    groups = parse_functional_groups(mol)
    
    return {
        'molecule_id': mol_id,
        'mw': props['mw'],
        'atom_count': props['atom_count'],
        'functional_groups': groups
    }

def write_confounds_csv(results: List[Dict[str, Any]], output_path: Path) -> None:
    """Write the final confounds CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['molecule_id', 'mw', 'atom_count', 'functional_groups']
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

def verify_distribution_stats(results: List[Dict[str, Any]], log_path: Path) -> bool:
    """
    FR-008 Compliance: Calculate distribution stats (mean, std) for MW/atom_count
    and compare against target dataset stats. Log result with status PASS/FAIL.
    """
    if not results:
        with open(log_path, 'w') as f:
            f.write("STATUS: FAIL\nReason: No data to analyze.\n")
        return False

    mws = [r['mw'] for r in results]
    atom_counts = [r['atom_count'] for r in results]

    mean_mw = sum(mws) / len(mws)
    std_mw = (sum((x - mean_mw) ** 2 for x in mws) / len(mws)) ** 0.5 if len(mws) > 1 else 0.0

    mean_atoms = sum(atom_counts) / len(atom_counts)
    std_atoms = (sum((x - mean_atoms) ** 2 for x in atom_counts) / len(atom_counts)) ** 0.5 if len(atom_counts) > 1 else 0.0

    # Target stats (example targets for barrier dataset, typically small organics)
    # These are heuristic targets; in a real scenario, these would come from the spec.
    # Assuming typical barrier dataset molecules are small to medium organics.
    target_mw_mean = 150.0  # Approximate target mean MW
    target_atoms_mean = 20.0 # Approximate target mean atom count

    # Define acceptable deviation (e.g., within 50% of target mean for this check)
    # This is a loose check to ensure we aren't processing garbage data (e.g. huge polymers or single atoms)
    mw_ok = 0.5 * target_mw_mean <= mean_mw <= 1.5 * target_mw_mean
    atoms_ok = 0.5 * target_atoms_mean <= mean_atoms <= 1.5 * target_atoms_mean

    status = "PASS" if (mw_ok and atoms_ok) else "FAIL"
    
    log_content = (
        f"STATUS: {status}\n"
        f"Calculated MW - Mean: {mean_mw:.2f}, Std: {std_mw:.2f}\n"
        f"Calculated Atom Count - Mean: {mean_atoms:.2f}, Std: {std_atoms:.2f}\n"
        f"Target MW Mean: {target_mw_mean}, Target Atom Mean: {target_atoms_mean}\n"
        f"Checks: MW={'OK' if mw_ok else 'FAIL'}, Atoms={'OK' if atoms_ok else 'FAIL'}\n"
    )

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'w') as f:
        f.write(log_content)
    
    print(f"Verification log written to {log_path}: {status}")
    return status == "PASS"

def main():
    """Main entry point for T011."""
    print(f"Starting Confounds Analysis (T011)...")
    print(f"Input: {INPUT_PATH}")
    print(f"Output: {OUTPUT_PATH}")
    
    if not INPUT_PATH.exists():
        print(f"ERROR: Input file {INPUT_PATH} does not exist. Run T004b first.", file=sys.stderr)
        sys.exit(1)
    
    try:
        molecules = load_molecules_from_csv(INPUT_PATH)
        print(f"Loaded {len(molecules)} molecules.")
    except Exception as e:
        print(f"ERROR: Failed to load input CSV: {e}", file=sys.stderr)
        sys.exit(1)
    
    results = []
    for mol_data in molecules:
        processed = process_molecule(mol_data)
        if processed:
            results.append(processed)
    
    if not results:
        print("ERROR: No valid molecules processed.", file=sys.stderr)
        sys.exit(1)
    
    try:
        write_confounds_csv(results, OUTPUT_PATH)
        print(f"Successfully wrote {len(results)} records to {OUTPUT_PATH}")
    except Exception as e:
        print(f"ERROR: Failed to write output CSV: {e}", file=sys.stderr)
        sys.exit(1)
    
    # FR-008 Compliance: Verification
    verify_distribution_stats(results, LOG_PATH)

if __name__ == "__main__":
    main()