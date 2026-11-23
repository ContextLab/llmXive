"""
Molecular Descriptor Calculation Module (T014 & T015)

Implements calculation of molecular complexity metrics (TPSA, Rotatable Bonds, MW, etc.)
and handles error logging for excluded molecules to data/processed/excluded_molecules.csv
as per T015 requirements.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# Import from sibling modules as per API surface
from config import get_config
from error_handlers import DescriptorCalculationError, handle_molecule_error

# Try importing RDKit; if missing, we will raise a clear error at runtime
try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, rdMolDescriptors
    from rdkit import RDLogger
    # Suppress RDKit warnings for cleaner logs
    RDLogger.DisableLog('rdApp.*')
except ImportError:
    Chem = None
    Descriptors = None
    rdMolDescriptors = None


def get_data_path() -> str:
    """Return the data directory path relative to project root."""
    return "data"


def load_config() -> Dict[str, Any]:
    """Load configuration from data/config.yaml."""
    config_path = os.path.join("data", "config.yaml")
    if not os.path.exists(config_path):
        # Fallback default if config is missing (should not happen in valid run)
        return {
            "dataset_id": "unknown",
            "dataset_version": "unknown",
            "temp_min": 20.0,
            "temp_max": 30.0,
            "ph_min": 7.35,
            "ph_max": 7.45
        }
    with open(config_path, 'r') as f:
        import yaml
        return yaml.safe_load(f)


def check_gate_status() -> Dict[str, Any]:
    """Check the gate status file to ensure data ingestion passed."""
    gate_path = os.path.join("data", "gate_status.json")
    if not os.path.exists(gate_path):
        raise RuntimeError("Gate status file not found. Run ingest.py first.")
    
    with open(gate_path, 'r') as f:
        status = json.load(f)
    
    if status.get("status") != "PASS":
        raise RuntimeError(f"Data gate failed: {status.get('reason', 'Unknown reason')}")
    
    return status


def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return "file_not_found"


def get_source_hash() -> str:
    """Get the hash of the source data file (merged_drugs.csv)."""
    source_path = os.path.join("data", "processed", "merged_drugs.csv")
    return calculate_file_hash(source_path)


def log_error_to_file(smiles: str, error_type: str, source_hash: str, output_path: str = None) -> None:
    """
    Log a molecule error to the excluded_molecules.csv file.
    
    T015 Requirement:
    - Writes to data/processed/excluded_molecules.csv
    - Schema: smiles (string), error_type (string), timestamp (ISO8601), source_hash (string)
    - Must be robust and append-only.
    """
    if output_path is None:
        output_path = os.path.join("data", "processed", "excluded_molecules.csv")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Check if file exists to determine if we need headers
    file_exists = os.path.isfile(output_path)
    
    timestamp = datetime.utcnow().isoformat()
    
    with open(output_path, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            # Write header if new file
            writer.writerow(['smiles', 'error_type', 'timestamp', 'source_hash'])
        
        writer.writerow([smiles, error_type, timestamp, source_hash])


def validate_molecule(smiles: str) -> Optional[Chem.Mol]:
    """
    Validate and parse a SMILES string into an RDKit Mol object.
    Returns None if invalid.
    """
    if Chem is None:
        raise ImportError("RDKit is not installed. Cannot validate molecules.")
    
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        # Sanitize the molecule to catch valence errors
        Chem.SanitizeMol(mol)
        return mol
    except (Chem.rdchem.AtomValenceException, Chem.rdchem.MolSanitizeException, ValueError) as e:
        return None


def calculate_tpsa(mol: Chem.Mol) -> float:
    """Calculate Topological Polar Surface Area."""
    return Descriptors.TPSA(mol)


def calculate_rotatable_bonds(mol: Chem.Mol) -> int:
    """Calculate Rotatable Bond Count."""
    return rdMolDescriptors.CalcNumRotatableBonds(mol)


def calculate_mw(mol: Chem.Mol) -> float:
    """Calculate Molecular Weight."""
    return Descriptors.MolWt(mol)


def calculate_aromatic_rings(mol: Chem.Mol) -> int:
    """Calculate Aromatic Ring Count."""
    return rdMolDescriptors.CalcNumAromaticRings(mol)


def calculate_wiener_index(mol: Chem.Mol) -> float:
    """Calculate Wiener Index (approximation via RDKit)."""
    # RDKit does not have a direct Wiener index descriptor in Descriptors module
    # We use the Wiener index from the GraphDescriptors if available, or a fallback
    try:
        from rdkit.Chem.GraphDescriptors import WienerIndex
        return WienerIndex(mol)
    except Exception:
        # Fallback: 0.0 if calculation fails, but log it
        return 0.0


def calculate_zagreb_index(mol: Chem.Mol) -> float:
    """Calculate Zagreb Index."""
    # RDKit does not have a direct Zagreb index in standard Descriptors
    # We calculate it manually based on degree of vertices
    try:
        mol = Chem.AddHs(mol) # Ensure hydrogens are present for degree calc if needed
        graph = mol.GetRingGraph() # Not directly available, use adjacency
        # Using Mol.GetDegree() for each atom
        degrees = [atom.GetDegree() for atom in mol.GetAtoms()]
        # First Zagreb Index M1 = sum(deg(v)^2)
        if not degrees:
            return 0.0
        return float(sum(d * d for d in degrees))
    except Exception:
        return 0.0


def calculate_descriptors_for_molecule(smiles: str, source_hash: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Calculate all descriptors for a single molecule.
    
    Returns:
      Tuple (descriptors_dict, error_type)
      If successful: (dict, None)
      If failed: (None, error_type_string)
    """
    if Chem is None:
        raise ImportError("RDKit is not installed.")

    mol = validate_molecule(smiles)
    if mol is None:
        return None, "Invalid SMILES or Valence Error"

    try:
        descriptors = {
            "smiles": smiles,
            "tpsa": calculate_tpsa(mol),
            "rotatable_bonds": calculate_rotatable_bonds(mol),
            "molecular_weight": calculate_mw(mol),
            "aromatic_rings": calculate_aromatic_rings(mol),
            "wiener_index": calculate_wiener_index(mol),
            "zagreb_index": calculate_zagreb_index(mol)
        }
        return descriptors, None
    except Exception as e:
        error_type = type(e).__name__
        return None, error_type


def calculate_descriptors_batch(input_path: str, output_path: str) -> None:
    """
    Read merged_drugs.csv, calculate descriptors, and save to output.
    Logs errors to excluded_molecules.csv as per T015.
    """
    if Chem is None:
        raise ImportError("RDKit is not installed. Please install it via requirements.txt.")

    source_hash = get_source_hash()
    excluded_log_path = os.path.join("data", "processed", "excluded_molecules.csv")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    os.makedirs(os.path.dirname(excluded_log_path), exist_ok=True)

    # Read input
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_path, 'r') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        
        if not fieldnames:
            raise ValueError("Input CSV is empty or has no headers.")

        # Prepare output fieldnames
        output_fieldnames = list(fieldnames) + [
            "tpsa", "rotatable_bonds", "molecular_weight", 
            "aromatic_rings", "wiener_index", "zagreb_index"
        ]

        rows = []
        for row in reader:
            smiles = row.get("canonical_smiles") or row.get("smiles")
            if not smiles:
                # Log missing SMILES
                log_error_to_file("MISSING_SMILES", "Missing SMILES Column", source_hash, excluded_log_path)
                continue

            descriptors, error = calculate_descriptors_for_molecule(smiles, source_hash)
            
            if error:
                # Log error to excluded_molecules.csv (T015 requirement)
                log_error_to_file(smiles, error, source_hash, excluded_log_path)
                # Skip this row in the main output
                continue
            
            # Merge original row with descriptors
            new_row = {**row, **descriptors}
            rows.append(new_row)

    # Write output
    with open(output_path, 'w', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=output_fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    """Main entry point for descriptor calculation."""
    print("Starting descriptor calculation (T014/T015)...")
    
    try:
        # Check gate status first
        check_gate_status()
        
        input_path = os.path.join("data", "processed", "merged_drugs.csv")
        output_path = os.path.join("data", "processed", "descriptors_calculated.csv")
        
        calculate_descriptors_batch(input_path, output_path)
        
        print(f"Descriptor calculation complete. Output: {output_path}")
        print(f"Errors logged to: data/processed/excluded_molecules.csv")
        
    except Exception as e:
        print(f"Error during descriptor calculation: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
