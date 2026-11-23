"""
SMILES to RDKit Graph conversion and conformer generation utilities.

Implements FR-001: Convert SMILES strings to graph representations suitable
for the MPNN VAE encoder. Also handles ETKDG conformer generation.
"""
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
from rdkit import Chem
from rdkit.Chem import rdmolops, AllChem
from rdkit import DataStructs

from config import get_paths, get_hyperparams
from utils.logging import get_project_logger
from utils.seeds import set_global_seed

# Logger instance
logger = get_project_logger(__name__)


def smiles_to_graph(smiles: str) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    Convert a SMILES string to a graph representation (node/edge features).

    The graph is represented as a dictionary with:
    - 'nodes': list of node feature dictionaries
    - 'edges': list of edge feature dictionaries (source, target, type)
    - 'num_nodes': int
    - 'num_edges': int

    Node features include:
    - atomic_num (int)
    - degree (int)
    - formal_charge (int)
    - num_hydrogens (int)
    - hybridization (int, mapped from enum)
    - is_aromatic (bool)

    Edge features include:
    - bond_type (int, mapped from enum)
    - is_conjugated (bool)
    - is_in_ring (bool)

    Args:
        smiles: SMILES string of the molecule.

    Returns:
        Tuple of (graph_dict, error_message).
        If successful, error_message is None.
        If failed (invalid SMILES), graph_dict is None and error_message is set.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None, f"Failed to parse SMILES: {smiles}"

        # Add hydrogens explicitly to ensure accurate degree/hydrogen count
        mol = Chem.AddHs(mol)

        num_nodes = mol.GetNumAtoms()
        num_edges = mol.GetNumBonds()

        nodes = []
        for atom in mol.GetAtoms():
            node_feat = {
                "atomic_num": atom.GetAtomicNum(),
                "degree": atom.GetDegree(),
                "formal_charge": atom.GetFormalCharge(),
                "num_hydrogens": atom.GetTotalNumHs(),
                "hybridization": int(atom.GetHybridization()),
                "is_aromatic": atom.GetIsAromatic(),
            }
            nodes.append(node_feat)

        edges = []
        for bond in mol.GetBonds():
            start_idx = bond.GetBeginAtomIdx()
            end_idx = bond.GetEndAtomIdx()
            edge_feat = {
                "source": start_idx,
                "target": end_idx,
                "bond_type": int(bond.GetBondType()),
                "is_conjugated": bond.GetIsConjugated(),
                "is_in_ring": bond.IsInRing(),
            }
            edges.append(edge_feat)

        # RDKit bond types are enums, but we store ints for serialization
        # 1=SINGLE, 2=DOUBLE, 3=TRIPLE, 4=AROMATIC

        graph_dict = {
            "smiles": smiles,
            "nodes": nodes,
            "edges": edges,
            "num_nodes": num_nodes,
            "num_edges": num_edges,
        }

        return graph_dict, None

    except Exception as e:
        logger.error(f"Error converting SMILES to graph: {e}")
        return None, str(e)


def generate_etkdg_conformers(
    smiles: str,
    num_confs: int = 10,
    seed: Optional[int] = None
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Generate an initial ensemble of conformers using ETKDG algorithm.

    Args:
        smiles: SMILES string of the molecule.
        num_confs: Number of conformers to generate.
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (conformer_list, error_message).
        conformer_list is a list of dictionaries containing:
            - 'conformer_id': int
            - 'rdkit_mol': RDKit Mol object (not JSON serializable, handled separately)
            - 'positions': numpy array of shape (N_atoms, 3)
        If failed, returns ([], error_message).
    """
    try:
        if seed is not None:
            set_global_seed(seed)

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return [], f"Failed to parse SMILES: {smiles}"

        # Add hydrogens for conformer generation
        mol = Chem.AddHs(mol)

        # Generate conformers
        params = AllChem.ETKDGv3()
        if seed is not None:
            params.randomSeed = seed

        conf_ids = AllChem.EmbedMultipleConfs(mol, numConfs=num_confs, params=params)

        if len(conf_ids) == 0:
            logger.warning(f"ETKDG failed to generate any conformers for {smiles}")
            return [], f"ETKDG failed to generate conformers for {smiles}"

        conformers = []
        for conf_id in conf_ids:
            conf = mol.GetConformer(conf_id)
            positions = conf.GetPositions()
            conformers.append({
                "conformer_id": conf_id,
                "positions": positions,  # numpy array
                "num_atoms": mol.GetNumAtoms(),
            })

        logger.info(f"Generated {len(conformers)} conformers for {smiles}")
        return conformers, None

    except Exception as e:
        logger.error(f"Error generating conformers for {smiles}: {e}")
        return [], str(e)


def process_dataset(
    input_path: str,
    output_graphs_path: str,
    output_conformers_path: Optional[str] = None,
    max_molecules: Optional[int] = None,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Process a dataset file (JSONL or CSV) containing SMILES strings.

    Args:
        input_path: Path to input file (JSONL with 'smiles' column).
        output_graphs_path: Path to save processed graph data (JSONL).
        output_conformers_path: Optional path to save conformer data.
        max_molecules: Optional limit on number of molecules to process.
        seed: Random seed for conformer generation.

    Returns:
        Summary statistics of the processing run.
    """
    paths = get_paths()
    hyperparams = get_hyperparams()

    if seed is None:
        seed = hyperparams.seed

    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    total_processed = 0
    successful_graphs = 0
    failed_graphs = 0
    successful_conformers = 0
    failed_conformers = 0

    graphs_output = []
    conformers_output = [] if output_conformers_path else None

    logger.info(f"Starting dataset processing from {input_path}")

    with open(input_file, 'r') as f:
        for line in f:
            if max_molecules and total_processed >= max_molecules:
                break

            try:
                data = json.loads(line.strip())
                smiles = data.get('smiles')
                if not smiles:
                    logger.warning(f"Skipping line without SMILES: {line[:50]}...")
                    continue

                # Convert to graph
                graph_dict, err = smiles_to_graph(smiles)
                if graph_dict:
                    graphs_output.append(graph_dict)
                    successful_graphs += 1
                else:
                    failed_graphs += 1
                    logger.warning(f"Graph conversion failed for {smiles}: {err}")

                # Generate conformers if requested
                if output_conformers_path:
                    confs, conf_err = generate_etkdg_conformers(smiles, seed=seed)
                    if confs:
                        for conf in confs:
                            # Store molecule SMILES and conformer data together
                            conformers_output.append({
                                "smiles": smiles,
                                "conformer": conf,
                            })
                        successful_conformers += 1
                    else:
                        failed_conformers += 1
                        logger.warning(f"Conformer generation failed for {smiles}: {conf_err}")

                total_processed += 1

                if total_processed % 100 == 0:
                    logger.info(f"Processed {total_processed} molecules...")

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON line: {line[:50]}...")
                continue
            except Exception as e:
                logger.error(f"Unexpected error processing line: {e}")
                continue

    # Write outputs
    graphs_path = Path(output_graphs_path)
    graphs_path.parent.mkdir(parents=True, exist_ok=True)

    with open(graphs_path, 'w') as f:
        for graph in graphs_output:
            f.write(json.dumps(graph) + '\n')

    logger.info(f"Saved {len(graphs_output)} graphs to {output_graphs_path}")

    if output_conformers_path and conformers_output:
        confs_path = Path(output_conformers_path)
        confs_path.parent.mkdir(parents=True, exist_ok=True)

        with open(confs_path, 'w') as f:
            for item in conformers_output:
                # Convert numpy arrays to lists for JSON serialization
                item['conformer']['positions'] = item['conformer']['positions'].tolist()
                f.write(json.dumps(item) + '\n')

        logger.info(f"Saved {len(conformers_output)} conformer entries to {output_conformers_path}")

    summary = {
        "total_processed": total_processed,
        "successful_graphs": successful_graphs,
        "failed_graphs": failed_graphs,
        "successful_conformers": successful_conformers,
        "failed_conformers": failed_conformers,
        "output_graphs_path": str(graphs_path),
        "output_conformers_path": str(confs_path) if output_conformers_path else None,
    }

    logger.info(f"Processing complete: {summary}")
    return summary


def main():
    """
    Entry point for standalone execution.
    Processes the ZINC15 dataset (if downloaded) and saves graph representations.
    """
    paths = get_paths()
    hyperparams = get_hyperparams()

    # Default input: ZINC15 processed file if it exists
    zinc_input = paths.data_raw / "zinc15_processed.jsonl"
    if not zinc_input.exists():
        logger.error(f"ZINC15 data not found at {zinc_input}. Run download_zinc.py first.")
        return

    graphs_output = paths.data_processed / "zinc15_graphs.jsonl"
    conformers_output = paths.data_processed / "zinc15_conformers.jsonl"

    summary = process_dataset(
        input_path=str(zinc_input),
        output_graphs_path=str(graphs_output),
        output_conformers_path=str(conformers_output),
        max_molecules=hyperparams.max_molecules,
        seed=hyperparams.seed
    )

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()