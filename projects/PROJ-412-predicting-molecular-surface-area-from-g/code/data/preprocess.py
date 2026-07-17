import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Iterator

# Local imports matching API surface
from utils.logging import get_logger
from utils.conformer_config import load_conformer_config
from utils.config import get_data_dir

logger = get_logger(__name__)

FAILURE_THRESHOLD_RATE = 0.10  # 10%

def load_conformer_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Loads the conformer generation configuration.
    """
    if config_path is None:
        config_path = get_data_dir() / "conformer_config.json"
    
    if not config_path.exists():
        logger.warning(f"Config not found at {config_path}, using defaults.")
        return {
            "max_conformers": 10,
            "rms_threshold": 0.5,
            "energy_window": 10.0,
            "max_iterations": 200
        }
    
    with open(config_path, 'r') as f:
        return json.load(f)

def atom_to_feature_vector(atom) -> List[float]:
    """
    Converts an RDKit atom to a feature vector.
    """
    try:
        from rdkit import Chem
        # Basic features: atomic number, degree, hybridization, formal charge, aromaticity
        atomic_num = atom.GetAtomicNum()
        degree = atom.GetDegree()
        hybridization = int(atom.GetHybridization())
        formal_charge = atom.GetFormalCharge()
        aromatic = 1 if atom.GetIsAromatic() else 0
        
        # Normalize/Encode (simplified for this example)
        # In production, use one-hot or learned embeddings
        return [float(atomic_num), float(degree), float(hybridization), float(formal_charge), float(aromatic)]
    except Exception as e:
        logger.error(f"Error converting atom to features: {e}")
        return [0.0] * 5

def molecule_to_graph(mol) -> Dict[str, Any]:
    """
    Converts an RDKit molecule to a graph representation (nodes, edges).
    """
    try:
        nodes = []
        for atom in mol.GetAtoms():
            nodes.append(atom_to_feature_vector(atom))
        
        edges = []
        for bond in mol.GetBonds():
            start = bond.GetBeginAtomIdx()
            end = bond.GetEndAtomIdx()
            bond_type = int(bond.GetBondType())
            edges.append([start, end, bond_type])
            edges.append([end, start, bond_type]) # Undirected
        
        return {
            "nodes": nodes,
            "edges": edges,
            "num_atoms": mol.GetNumAtoms()
        }
    except Exception as e:
        logger.error(f"Error converting molecule to graph: {e}")
        return None

def extract_2d_features(smiles: str) -> Optional[Dict[str, Any]]:
    """
    Extracts 2D graph features from a SMILES string.
    """
    try:
        from rdkit import Chem
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        return molecule_to_graph(mol)
    except Exception as e:
        logger.error(f"Error extracting 2D features for {smiles[:20]}...: {e}")
        return None

def generate_conformers(smiles: str, config: Dict[str, Any]) -> Tuple[Optional[float], bool]:
    """
    Generates 3D conformers and calculates SASA.
    
    Returns:
        Tuple of (SASA value or None, success boolean)
    """
    try:
        from rdkit import Chem
        from rdkit.Chem import AllChem, rdMolDescriptors
        
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None, False
        
        # Add hydrogens
        mol_h = Chem.AddHs(mol)
        
        # Embed conformer
        params = AllChem.ETKDGv3()
        params.maxAttempts = config.get("max_iterations", 200)
        
        # Try to generate conformer
        res = AllChem.EmbedMolecule(mol_h, params)
        if res == -1:
            logger.warning(f"Conformer generation failed for {smiles[:20]}... (Embedding)")
            return None, False
        
        # Optimize geometry
        AllChem.MMFFOptimizeMolecule(mol_h, maxIters=config.get("max_iterations", 200))
        
        # Calculate SASA
        sasa = rdMolDescriptors.CalcSASA(mol_h)
        
        return sasa, True
    except Exception as e:
        logger.warning(f"Conformer generation or SASA calculation failed for {smiles[:20]}...: {e}")
        return None, False

def process_molecule_chunk(smiles_list: List[str], config: Dict[str, Any]) -> Tuple[List[Dict], int, int]:
    """
    Processes a chunk of molecules, extracting 2D features and generating 3D SASA.
    
    Returns:
        Tuple of (list of processed records, total processed, failure count)
    """
    processed = []
    total = len(smiles_list)
    failures = 0

    for i, smiles in enumerate(smiles_list):
        # 2D Features
        graph_data = extract_2d_features(smiles)
        if graph_data is None:
            failures += 1
            logger.warning(f"Failed to extract 2D features for: {smiles[:20]}...")
            continue
        
        # 3D SASA
        sasa, success = generate_conformers(smiles, config)
        if not success:
            failures += 1
            logger.warning(f"Failed to generate conformer for: {smiles[:20]}...")
            continue
        
        processed.append({
            "smiles": smiles,
            "graph": graph_data,
            "sasa": sasa
        })
        
        if (i + 1) % 100 == 0:
            logger.info(f"Processed {i+1}/{total} molecules in chunk.")

    return processed, total, failures

def main():
    """
    Main entry point for the preprocessing pipeline with validation and error handling.
    """
    import argparse
    import gzip
    import json

    parser = argparse.ArgumentParser(description="Preprocess SMILES data with 2D/3D features.")
    parser.add_argument("--input", type=str, required=True, help="Input SMILES file (txt or gz)")
    parser.add_argument("--output", type=str, required=True, help="Output JSON/Parquet file")
    parser.add_argument("--chunk-size", type=int, default=100, help="Number of molecules per chunk")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    config = load_conformer_config()
    
    # Load SMILES
    smiles_list = []
    if input_path.suffix == '.gz':
        with gzip.open(input_path, 'rt') as f:
            for line in f:
                s = line.strip().split()[0]
                if s: smiles_list.append(s)
    else:
        with open(input_path, 'r') as f:
            for line in f:
                s = line.strip().split()[0]
                if s: smiles_list.append(s)

    logger.info(f"Loaded {len(smiles_list)} SMILES strings.")

    all_processed = []
    total_processed = 0
    total_failures = 0

    # Process in chunks
    for i in range(0, len(smiles_list), args.chunk_size):
        chunk = smiles_list[i : i + args.chunk_size]
        processed, chunk_total, chunk_failures = process_molecule_chunk(chunk, config)
        all_processed.extend(processed)
        total_processed += chunk_total
        total_failures += chunk_failures

    failure_rate = total_failures / total_processed if total_processed > 0 else 0.0

    logger.info(f"Total processed: {total_processed}, Failures: {total_failures}")
    logger.info(f"Overall failure rate: {failure_rate:.2%}")

    if failure_rate > FAILURE_THRESHOLD_RATE:
        error_msg = f"CRITICAL: Conformer generation failure rate ({failure_rate:.2%}) exceeds threshold ({FAILURE_THRESHOLD_RATE:.2%}). Halting pipeline."
        logger.critical(error_msg)
        raise RuntimeError(error_msg)

    # Save results
    with open(output_path, 'w') as f:
        json.dump(all_processed, f, indent=2)
    
    logger.info(f"Saved {len(all_processed)} processed molecules to {output_path}")

if __name__ == "__main__":
    main()
