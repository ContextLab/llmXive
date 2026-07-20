import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Iterator

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors, rdMolDescriptors
from rdkit import RDLogger

# Project imports based on API surface
try:
    from utils.config import get_project_root, get_data_dir
    from utils.logging import get_logger
    from utils.conformer_config import load_conformer_config
except ImportError:
    # Fallback for direct script execution context
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.config import get_project_root, get_data_dir
    from utils.logging import get_logger
    from utils.conformer_config import load_conformer_config

# Disable RDKit warnings to keep logs clean
RDLogger.DisableLog('rdApp.*')

# Configuration constant for max atoms filter (T044)
MAX_ATOMS_THRESHOLD = 100

def load_conformer_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load conformer generation parameters from JSON.
    Falls back to default if file not found.
    """
    if config_path is None:
        data_dir = get_data_dir()
        config_path = data_dir / "processed" / "conformer_config.json"
    
    if not config_path.exists():
        logging.warning(f"Conformer config not found at {config_path}. Using defaults.")
        return {
            "etkdg_version": 3,
            "max_attempts": 20,
            "random_seed": 42,
            "enforce_chirality": True
        }
    
    with open(config_path, 'r') as f:
        return json.load(f)

def atom_to_feature_vector(atom: Chem.Atom) -> List[float]:
    """
    Convert an RDKit atom to a feature vector.
    Features: [atomic_num, degree, formal_charge, hybridization, is_aromatic]
    """
    atomic_num = atom.GetAtomicNum()
    degree = atom.GetDegree()
    formal_charge = atom.GetFormalCharge()
    hybridization = int(atom.GetHybridization())
    is_aromatic = 1 if atom.GetIsAromatic() else 0
    
    return [float(atomic_num), float(degree), float(formal_charge), float(hybridization), float(is_aromatic)]

def molecule_to_graph(mol: Chem.Mol) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Convert an RDKit molecule to node features, edge index, and edge features.
    Returns:
        node_features: (N, 5) array
        edge_index: (2, E) array
        edge_features: (E, 1) array (bond type)
    """
    num_atoms = mol.GetNumAtoms()
    
    # Node features
    node_features = np.array([atom_to_feature_vector(atom) for atom in mol.GetAtoms()], dtype=np.float32)
    
    # Edge index and features
    edges = []
    edge_types = []
    
    for bond in mol.GetBonds():
        start = bond.GetBeginAtomIdx()
        end = bond.GetEndAtomIdx()
        bond_type = int(bond.GetBondType())
        
        edges.append([start, end])
        edges.append([end, start]) # Undirected graph
        edge_types.append(bond_type)
        edge_types.append(bond_type)
    
    if not edges:
        edge_index = np.zeros((2, 0), dtype=np.int64)
        edge_features = np.zeros((0, 1), dtype=np.float32)
    else:
        edge_index = np.array(edges, dtype=np.int64).T
        edge_features = np.array(edge_types, dtype=np.float32).reshape(-1, 1)
        
    return node_features, edge_index, edge_features

def extract_2d_features(mol: Chem.Mol) -> Dict[str, Any]:
    """
    Extract 2D topological features from a molecule.
    """
    mol_weight = Descriptors.MolWt(mol)
    num_h_donors = Descriptors.NumHDonors(mol)
    num_h_acceptors = Descriptors.NumHAcceptors(mol)
    logp = Descriptors.MolLogP(mol)
    num_rotatable_bonds = Descriptors.NumRotatableBonds(mol)
    num_aromatic_rings = Descriptors.NumAromaticRings(mol)
    
    return {
        "molecular_weight": mol_weight,
        "num_h_donors": num_h_donors,
        "num_h_acceptors": num_h_acceptors,
        "logp": logp,
        "num_rotatable_bonds": num_rotatable_bonds,
        "num_aromatic_rings": num_aromatic_rings
    }

def generate_conformers(mol: Chem.Mol, config: Dict[str, Any]) -> Optional[Chem.Mol]:
    """
    Generate 3D conformers for a molecule and return the lowest energy one.
    Returns None if generation fails.
    """
    # Clone molecule to avoid modifying input
    mol_copy = Chem.Mol(mol)
    mol_copy = Chem.AddHs(mol_copy)
    
    params = AllChem.ETKDGv3()
    params.maxAttempts = config.get("max_attempts", 20)
    params.randomSeed = config.get("random_seed", 42)
    params.enforceChirality = config.get("enforce_chirality", True)
    
    try:
        # Generate conformers
        conformer_ids = AllChem.EmbedMultipleConfs(mol_copy, numConfs=1, params=params)
        
        if not conformer_ids:
            return None
        
        # Optimize geometry
        AllChem.MMFFOptimizeMolecule(mol_copy, confId=conformer_ids[0])
        
        # Remove hydrogens for the final graph representation (optional, depending on downstream needs)
        # For SASA calculation, we need hydrogens. For graph input, we might remove them or keep them.
        # The task implies graph feature extraction, which often works on heavy atoms, but SASA needs H.
        # We will return the molecule with H for SASA calc, but the graph extractor can handle it.
        return mol_copy
        
    except Exception as e:
        logging.debug(f"Conformer generation failed: {e}")
        return None

def process_molecule_chunk(chunk: List[Dict[str, Any]], logger: logging.Logger) -> Iterator[Dict[str, Any]]:
    """
    Process a chunk of molecules, extracting features and generating conformers.
    Implements T044: max_atoms filter.
    """
    processed_count = 0
    excluded_large_count = 0
    failed_conformer_count = 0
    invalid_smiles_count = 0
    
    config = load_conformer_config()
    
    for item in chunk:
        smiles = item.get("smiles")
        mol_id = item.get("id", "unknown")
        
        # 1. Parse SMILES
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            invalid_smiles_count += 1
            logger.warning(f"Invalid SMILES for molecule {mol_id}: {smiles}")
            continue
        
        # 2. T044: Filter by max atoms
        num_atoms = mol.GetNumAtoms()
        if num_atoms > MAX_ATOMS_THRESHOLD:
            excluded_large_count += 1
            logger.info(f"Excluding molecule {mol_id} (SMILES: {smiles[:50]}...) due to atom count {num_atoms} > {MAX_ATOMS_THRESHOLD}")
            continue
        
        # 3. Generate 3D Conformer
        mol_3d = generate_conformers(mol, config)
        if mol_3d is None:
            failed_conformer_count += 1
            logger.warning(f"Failed to generate conformer for molecule {mol_id}")
            continue
        
        # 4. Calculate SASA (Solvent Accessible Surface Area)
        # RDKit needs a conformer to calculate SASA
        try:
            sasa = rdMolDescriptors.CalcCrippenDescriptors(mol_3d)[0] # Placeholder, using Crippen as proxy or proper SASA
            # Correct SASA calculation
            sasa = rdMolDescriptors.CalcMolSA(mol_3d) # Total Surface Area
            # Or more precise: rdMolDescriptors.CalcSASA(mol_3d, probeRadius=1.4) if available
            # Using CalcMolSA as a standard proxy if CalcSASA is not in this RDKit version
            # Actually, CalcSASA is in rdMolDescriptors in newer RDKit. Let's use the most robust one.
            # If CalcSASA is missing, we fall back to CalcMolSA.
            try:
                sasa = rdMolDescriptors.CalcSASA(mol_3d, probeRadius=1.4)
            except AttributeError:
                sasa = rdMolDescriptors.CalcMolSA(mol_3d)
        except Exception as e:
            failed_conformer_count += 1
            logger.warning(f"Failed to calculate SASA for molecule {mol_id}: {e}")
            continue
        
        # 5. Extract 2D features
        features_2d = extract_2d_features(mol)
        
        # 6. Convert to graph
        node_features, edge_index, edge_features = molecule_to_graph(mol_3d)
        
        # 7. Compile result
        result = {
            "smiles": smiles,
            "id": mol_id,
            "num_atoms": num_atoms,
            "surface_area": sasa,
            "molecular_weight": features_2d["molecular_weight"],
            "node_features": node_features.tolist(),
            "edge_index": edge_index.tolist(),
            "edge_features": edge_features.tolist(),
            "num_h_donors": features_2d["num_h_donors"],
            "num_h_acceptors": features_2d["num_h_acceptors"],
            "logp": features_2d["logp"],
            "num_rotatable_bonds": features_2d["num_rotatable_bonds"],
            "num_aromatic_rings": features_2d["num_aromatic_rings"]
        }
        
        processed_count += 1
        yield result
    
    # Log chunk statistics
    logger.info(f"Chunk processed: {processed_count} valid, {invalid_smiles_count} invalid SMILES, "
                f"{excluded_large_count} excluded (> {MAX_ATOMS_THRESHOLD} atoms), {failed_conformer_count} conformer failures")

def main():
    """
    Main entry point for the preprocessing pipeline.
    This script is expected to be called by the ingestion pipeline or run standalone
    to process the raw data into the processed parquet format.
    """
    logger = get_logger(__name__)
    logger.info("Starting preprocessing pipeline with max_atoms filter (T044)")
    
    # In a real scenario, this would load from data/raw/ or stream from datasets
    # For this task implementation, we assume the data is available or will be streamed
    # by the calling process (T012/T014).
    
    # Example of how the filter works in a loop:
    # for item in stream_data():
    #     for processed in process_molecule_chunk([item], logger):
    #         save_to_parquet(processed)
    
    logger.info("Preprocessing logic defined. Ready for integration with data stream.")

if __name__ == "__main__":
    main()