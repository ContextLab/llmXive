import os
import sys
import logging
import json
import math
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from existing API surface
from utils.exceptions import DataError
from utils.logger import get_memory_usage_mb

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_CURATED_DIR = PROJECT_ROOT / "data" / "curated"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Ensure directories exist
DATA_CURATED_DIR.mkdir(parents=True, exist_ok=True)

def load_cleaned_data(input_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load the cleaned data from the output of code/data/clean.py.
    If input_path is None, it defaults to the standard path for cleaned data.
    
    Returns a list of dictionaries, each representing a row with polymer/filler SMILES and adhesion energy.
    """
    if input_path is None:
        # Assuming clean.py outputs to a standard location or we need to find the latest
        # For this implementation, we assume clean.py writes to data/raw/cleaned_data.csv
        # or the task T014 produces a file that we read here.
        # Based on typical pipeline: download -> clean -> curated.
        # Let's assume clean.py writes to data/raw/cleaned_data.csv as an intermediate step
        # or we read directly from the raw download if clean.py modified it in place.
        # Given T014 description, it flags missing values. Let's assume it writes to data/raw/cleaned_data.csv
        input_path = DATA_RAW_DIR / "cleaned_data.csv"
    
    if not input_path.exists():
        raise DataError(f"Cleaned data file not found at {input_path}. "
                        "Run T014 (clean.py) first.")
    
    data = []
    with open(input_path, 'r', encoding='utf-8') as f:
        header = f.readline().strip().split(',')
        for line in f:
            values = line.strip().split(',')
            if len(values) != len(header):
                logger.warning(f"Skipping malformed row: {line}")
                continue
            row = dict(zip(header, values))
            data.append(row)
    
    logger.info(f"Loaded {len(data)} rows from {input_path}")
    return data

def compute_graph_properties(smiles: str) -> Dict[str, Any]:
    """
    Compute basic graph properties for a given SMILES string.
    Since we are generating the curated dataset, we need to represent the molecular graph.
    We will store the SMILES and basic counts (nodes, edges) as proxies for graph structure
    until T022 converts them to PyG graphs.
    
    Returns a dict with node_count, edge_count, and the original SMILES.
    """
    try:
        from rdkit import Chem
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return {"node_count": 0, "edge_count": 0, "valid": False}
        
        num_atoms = mol.GetNumAtoms()
        num_bonds = mol.GetNumBonds()
        return {
            "node_count": num_atoms,
            "edge_count": num_bonds,
            "valid": True
        }
    except Exception as e:
        logger.warning(f"RDKit failed to parse SMILES '{smiles}': {e}")
        return {"node_count": 0, "edge_count": 0, "valid": False}

def generate_curated_dataset(
    raw_data: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Generates the final curated dataset CSV.
    
    This function:
    1. Iterates through the cleaned data.
    2. Validates that adhesion energy is present and numeric.
    3. Computes graph properties for polymer and filler.
    4. Writes the enriched rows to the output CSV.
    
    The output CSV will have columns:
    polymer_smiles, filler_smiles, adhesion_energy, 
    polymer_nodes, polymer_edges, filler_nodes, filler_edges, is_valid
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    headers = [
        "polymer_smiles", "filler_smiles", "adhesion_energy",
        "polymer_nodes", "polymer_edges", "filler_nodes", "filler_edges",
        "is_valid"
    ]
    
    valid_count = 0
    invalid_count = 0
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(','.join(headers) + '\n')
        
        for row in raw_data:
            polymer_smiles = row.get('polymer_smiles', '').strip()
            filler_smiles = row.get('filler_smiles', '').strip()
            adhesion_str = row.get('adhesion_energy', '').strip()
            
            # Validate adhesion energy
            if not adhesion_str:
                logger.warning(f"Missing adhesion energy for row. Skipping.")
                invalid_count += 1
                continue
            
            try:
                adhesion_val = float(adhesion_str)
            except ValueError:
                logger.warning(f"Invalid adhesion energy '{adhesion_str}'. Skipping.")
                invalid_count += 1
                continue
            
            # Compute graph properties
            poly_props = compute_graph_properties(polymer_smiles)
            fill_props = compute_graph_properties(filler_smiles)
            
            is_valid = poly_props['valid'] and fill_props['valid']
            
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
            
            # Write row
            out_row = [
                polymer_smiles,
                filler_smiles,
                f"{adhesion_val}",
                str(poly_props['node_count']),
                str(poly_props['edge_count']),
                str(fill_props['node_count']),
                str(fill_props['edge_count']),
                str(is_valid)
            ]
            f.write(','.join(out_row) + '\n')
    
    logger.info(f"Curated dataset written to {output_path}")
    logger.info(f"Valid rows: {valid_count}, Invalid rows (skipped): {invalid_count}")
    
    if valid_count == 0:
        raise DataError("E-DATA-001: No valid rows generated in curated dataset.")
    
    # Log memory usage as per requirements
    mem_mb = get_memory_usage_mb()
    logger.info(f"Memory usage after generation: {mem_mb:.2f} MB")

def main():
    """
    Main entry point for generating the curated dataset.
    """
    logger.info("Starting curated dataset generation (T016)...")
    
    # Determine input path
    # T014 (clean.py) should have produced a cleaned file.
    # Let's assume the standard output of clean.py is data/raw/cleaned_data.csv
    input_path = DATA_RAW_DIR / "cleaned_data.csv"
    output_path = DATA_CURATED_DIR / "curated_dataset.csv"
    
    if not input_path.exists():
        # Fallback: check if raw download exists and try to clean on the fly?
        # No, T014 is a separate task. We must fail if T014 hasn't run.
        raise DataError(f"Input file {input_path} not found. "
                        "Ensure T014 (clean.py) has been executed successfully.")
    
    try:
        raw_data = load_cleaned_data(input_path)
        generate_curated_dataset(raw_data, output_path)
        logger.info("T016 completed successfully.")
    except DataError as e:
        logger.error(f"DataError: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
