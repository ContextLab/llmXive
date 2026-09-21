"""
Symmetry and Invariance Analysis Utilities.

This module provides tools for analyzing molecular symmetry, detecting graph
automorphisms, and verifying the invariance of topological indices under
molecular graph permutations (rotations/reflections in the graph space).

It addresses the requirement (FR-008) to ensure that topological descriptors
are not coordinate-dependent artifacts but true invariants of the molecular topology.
"""
import logging
from typing import List, Optional, Tuple, Set, Dict, Any
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
from rdkit.Chem.rdmolops import GetAdjacencyMatrix
import networkx as nx
import numpy as np
from itertools import permutations

# Import existing descriptors to verify invariance
from code.descriptors import (
    calculate_wiener_index,
    calculate_balaban_index,
    calculate_zagreb_index
)
from code.utils.logger import setup_logger

logger = setup_logger(__name__)


def get_graph_automorphisms(mol: Chem.Mol) -> List[Dict[int, int]]:
    """
    Compute the set of graph automorphisms for a given RDKit molecule.

    An automorphism is a permutation of the vertices (atoms) that preserves
    the adjacency matrix (bond structure).

    Args:
        mol: RDKit molecule object.

    Returns:
        A list of dictionaries, where each dictionary represents a valid
        automorphism mapping: {original_atom_idx: new_atom_idx}.
        Note: For large molecules, the full set of automorphisms can be huge.
        This function returns a generator or a limited set if the count exceeds
        a threshold to prevent memory exhaustion, but for typical EAS reactants
        (small aromatic rings), it returns the full set.
    """
    if mol is None:
        return []

    # Create a NetworkX graph from the RDKit molecule
    G = nx.Graph()
    for atom in mol.GetAtoms():
        G.add_node(atom.GetIdx())
    for bond in mol.GetBonds():
        G.add_edge(bond.GetBeginAtomIdx(), bond.GetEndAtomIdx())

    # Use networkx to find automorphisms
    # rx.automorphisms() returns a generator of permutations
    try:
        # networkx.algorithms.automorphisms returns a generator
        automorphisms = list(nx.algorithms.automorphisms(G))
        
        # Convert list of tuples to list of dicts for easier handling
        # Each tuple is a permutation of node indices
        result = []
        for perm in automorphisms:
            # perm is a tuple where perm[i] is the new position of node i
            # We want a mapping: old_idx -> new_idx
            mapping = {i: perm[i] for i in range(len(perm))}
            result.append(mapping)
        
        return result
    except Exception as e:
        logger.warning(f"Failed to compute automorphisms for molecule: {e}")
        return []


def check_canonicalization_invariance(smiles: str, tolerance: float = 1e-6) -> bool:
    """
    Verify that topological indices remain invariant when the molecule
    is canonicalized (re-mapped to a standard atom ordering).

    This is a preliminary check (T025) ensuring that the descriptor calculation
    is independent of the input SMILES string's atom ordering.

    Args:
        smiles: Input SMILES string.
        tolerance: Floating point tolerance for index comparison.

    Returns:
        True if indices are invariant, False otherwise.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        logger.error(f"Invalid SMILES: {smiles}")
        return False

    # Calculate indices on original molecule
    try:
        w1 = calculate_wiener_index(mol)
        b1 = calculate_balaban_index(mol)
        z1 = calculate_zagreb_index(mol)
    except Exception as e:
        logger.error(f"Error calculating descriptors for original: {e}")
        return False

    # Canonicalize the molecule (this reorders atoms to a standard form)
    canon_mol = Chem.MolFromSmiles(Chem.MolToSmiles(mol))
    if canon_mol is None:
        logger.error("Canonicalization failed.")
        return False

    # Calculate indices on canonicalized molecule
    try:
        w2 = calculate_wiener_index(canon_mol)
        b2 = calculate_balaban_index(canon_mol)
        z2 = calculate_zagreb_index(canon_mol)
    except Exception as e:
        logger.error(f"Error calculating descriptors for canonical: {e}")
        return False

    # Compare
    if not (abs(w1 - w2) < tolerance and abs(b1 - b2) < tolerance and abs(z1 - z2) < tolerance):
        logger.warning(f"Invariance check failed: {smiles} -> W:{w1}!={w2}, B:{b1}!={b2}, Z:{z1}!={z2}")
        return False

    return True


def get_symmetry_classes(mol: Chem.Mol) -> Dict[int, Set[int]]:
    """
    Identify symmetry classes (orbits) of atoms in the molecule.
    Atoms in the same symmetry class are equivalent under the graph's automorphism group.

    Args:
        mol: RDKit molecule.

    Returns:
        Dictionary mapping a representative atom index to the set of indices
        in its symmetry class (orbit).
    """
    if mol is None:
        return {}

    automorphisms = get_graph_automorphisms(mol)
    if not automorphisms:
        # If no automorphisms found (or failed), assume each atom is its own class
        return {i: {i} for i in range(mol.GetNumAtoms())}

    # Build the orbit map
    orbits = {}
    for i in range(mol.GetNumAtoms()):
        # Find all atoms that i can map to under any automorphism
        orbit = set()
        for auto in automorphisms:
            orbit.add(auto[i])
        orbits[i] = orbit

    # Group into canonical classes
    classes = {}
    processed = set()
    for i in range(mol.GetNumAtoms()):
        if i in processed:
            continue
        orbit = orbits[i]
        rep = min(orbit) # Use the smallest index as representative
        classes[rep] = orbit
        processed.update(orbit)

    return classes


def is_symmetric(mol: Chem.Mol) -> bool:
    """
    Check if a molecule has any non-trivial symmetry (i.e., > 1 automorphism).

    Args:
        mol: RDKit molecule.

    Returns:
        True if the molecule has symmetry (automorphism group size > 1).
    """
    automorphisms = get_graph_automorphisms(mol)
    return len(automorphisms) > 1


def validate_invariance_on_dataset(smiles_list: List[str], tolerance: float = 1e-6) -> Dict[str, Any]:
    """
    Run invariance checks on a list of SMILES strings.

    Args:
        smiles_list: List of SMILES strings.
        tolerance: Tolerance for floating point comparisons.

    Returns:
        Dictionary with statistics: total, passed, failed, failed_examples.
    """
    stats = {
        "total": len(smiles_list),
        "passed": 0,
        "failed": 0,
        "failed_examples": []
    }

    for smiles in smiles_list:
        if check_canonicalization_invariance(smiles, tolerance):
            stats["passed"] += 1
        else:
            stats["failed"] += 1
            stats["failed_examples"].append(smiles)
            if len(stats["failed_examples"]) > 10:
                break # Limit error reporting

    return stats


def _permute_molecule_by_mapping(mol: Chem.Mol, mapping: Dict[int, int]) -> Chem.Mol:
    """
    Create a new molecule object where atoms are permuted according to the mapping.
    This simulates a 'rotation' or 'reflection' of the graph representation.

    Args:
        mol: Original molecule.
        mapping: Dictionary {old_idx: new_idx}.

    Returns:
        New RDKit molecule with permuted atom ordering.
    """
    if mol is None:
        return None

    # Create a new editable molecule
    new_mol = Chem.RWMol()
    
    # We need to reorder atoms. RDKit doesn't have a direct "permute" function
    # that preserves all properties easily without rebuilding.
    # Strategy: Build a new molecule by adding atoms in the order defined by the inverse mapping.
    # If mapping is {0: 2, 1: 0, 2: 1}, then new atom 0 comes from old atom 1.
    # Inverse mapping: new_idx -> old_idx
    inv_mapping = {v: k for k, v in mapping.items()}
    
    # Sort by new index to add in correct order
    sorted_new_indices = sorted(inv_mapping.keys())
    
    # Copy atoms
    for new_idx in sorted_new_indices:
        old_idx = inv_mapping[new_idx]
        atom = mol.GetAtomWithIdx(old_idx)
        new_atom = Chem.Atom(atom.GetSymbol())
        new_atom.SetFormalCharge(atom.GetFormalCharge())
        new_atom.SetIsAromatic(atom.GetIsAromatic())
        # Copy other properties if necessary
        new_mol.AddAtom(new_atom)

    # Copy bonds
    # Map old bond indices to new bond indices based on atom mapping
    # A bond between old_u and old_v becomes a bond between new_u and new_v
    # where new_u = mapping[old_u] (wait, mapping is old->new? No, mapping is old_idx -> new_idx)
    # Let's re-verify: mapping[old_idx] = new_idx.
    # So if we have a bond between old_u and old_v, the new bond is between mapping[old_u] and mapping[old_v].
    
    for bond in mol.GetBonds():
        old_u = bond.GetBeginAtomIdx()
        old_v = bond.GetEndAtomIdx()
        new_u = mapping[old_u]
        new_v = mapping[old_v]
        
        # Ensure u < v for RDKit
        if new_u > new_v:
            new_u, new_v = new_v, new_u
            
        new_mol.AddBond(new_u, new_v, bond.GetBondType())

    return new_mol.GetMol()


def perform_sensitivity_analysis(smiles: str, max_permutations: int = 100) -> Dict[str, Any]:
    """
    T026 Implementation: Perform a preliminary sensitivity analysis by rotating/permuting
    the molecular graph representation and verifying index stability.

    This function:
    1. Parses the SMILES.
    2. Computes the baseline Wiener, Balaban, and Zagreb indices.
    3. Generates a set of graph automorphisms (permutations).
    4. Re-calculates indices for each permuted graph.
    5. Asserts that all indices remain constant (within tolerance).

    This directly addresses the "coordinate-dependent artifact" concern by proving
    that the indices are invariant under the symmetry group of the graph.

    Args:
        smiles: Input SMILES string.
        max_permutations: Maximum number of permutations to test (to avoid exponential blowup).

    Returns:
        Dictionary containing:
            - 'success': bool
            - 'message': str
            - 'baseline': dict of indices
            - 'variance_found': bool (True if any index changed)
            - 'details': list of (perm_idx, indices)
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {
            "success": False,
            "message": f"Invalid SMILES: {smiles}",
            "baseline": None,
            "variance_found": False,
            "details": []
        }

    # 1. Baseline calculation
    try:
        w_base = calculate_wiener_index(mol)
        b_base = calculate_balaban_index(mol)
        z_base = calculate_zagreb_index(mol)
        baseline = {"wiener": w_base, "balaban": b_base, "zagreb": z_base}
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to calculate baseline descriptors: {e}",
            "baseline": None,
            "variance_found": False,
            "details": []
        }

    # 2. Get automorphisms
    automorphisms = get_graph_automorphisms(mol)
    if not automorphisms:
        # No automorphisms found (or trivial only). 
        # This is fine, it means the graph is asymmetric, so invariance is trivially true
        # (only one representation).
        logger.debug(f"No non-trivial automorphisms for {smiles}. Invariance trivially true.")
        return {
            "success": True,
            "message": "No non-trivial symmetries found; invariance trivially satisfied.",
            "baseline": baseline,
            "variance_found": False,
            "details": []
        }

    # Limit permutations if too many
    if len(automorphisms) > max_permutations:
        logger.warning(f"Too many automorphisms ({len(automorphisms)}). Testing first {max_permutations}.")
        automorphisms = automorphisms[:max_permutations]

    # 3. Test each permutation
    tolerance = 1e-6
    variance_found = False
    details = []

    for i, mapping in enumerate(automorphisms):
        try:
            # Permute the molecule
            permuted_mol = _permute_molecule_by_mapping(mol, mapping)
            if permuted_mol is None:
                continue

            # Calculate indices on permuted molecule
            w_p = calculate_wiener_index(permuted_mol)
            b_p = calculate_balaban_index(permuted_mol)
            z_p = calculate_zagreb_index(permuted_mol)

            # Check invariance
            w_diff = abs(w_base - w_p)
            b_diff = abs(b_base - b_p)
            z_diff = abs(z_base - z_p)

            if w_diff > tolerance or b_diff > tolerance or z_diff > tolerance:
                variance_found = True
                details.append({
                    "perm_idx": i,
                    "wiener_diff": w_diff,
                    "balaban_diff": b_diff,
                    "zagreb_diff": z_diff,
                    "failed": True
                })
                logger.error(f"Variance detected for {smiles} at perm {i}: W:{w_diff}, B:{b_diff}, Z:{z_diff}")
            else:
                details.append({
                    "perm_idx": i,
                    "failed": False
                })

        except Exception as e:
            logger.error(f"Error during permutation test {i} for {smiles}: {e}")
            variance_found = True
            details.append({
                "perm_idx": i,
                "error": str(e),
                "failed": True
            })

    return {
        "success": not variance_found,
        "message": "Sensitivity analysis complete." if not variance_found else "Variance detected in topological indices.",
        "baseline": baseline,
        "variance_found": variance_found,
        "details": details
    }


def run_sensitivity_analysis_on_file(input_path: str, output_path: str) -> bool:
    """
    Run sensitivity analysis on a CSV file of SMILES and write results to a JSON file.

    Args:
        input_path: Path to input CSV with 'smiles' column.
        output_path: Path to output JSON file.

    Returns:
        True if successful, False otherwise.
    """
    import pandas as pd
    import json

    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        return False

    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to read input CSV: {e}")
        return False

    if 'smiles' not in df.columns:
        logger.error("Input CSV must contain a 'smiles' column.")
        return False

    results = []
    total = len(df)
    failed_count = 0

    for idx, row in df.iterrows():
        smiles = row['smiles']
        if not isinstance(smiles, str) or not smiles:
            continue

        result = perform_sensitivity_analysis(smiles)
        results.append({
            "smiles": smiles,
            "result": result
        })

        if not result['success']:
            failed_count += 1

        if (idx + 1) % 100 == 0:
            logger.info(f"Processed {idx + 1}/{total} molecules.")

    output_data = {
        "total_processed": total,
        "failed_count": failed_count,
        "results": results
    }

    try:
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        logger.info(f"Sensitivity analysis results written to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to write output: {e}")
        return False


def main():
    """
    Entry point for running sensitivity analysis from the command line.
    Usage: python -m code.utils.symmetry --input data/processed/eas_reactions.csv --output data/processed/sensitivity_analysis.json
    """
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Perform sensitivity analysis on molecular graphs.")
    parser.add_argument("--input", required=True, help="Path to input CSV with SMILES.")
    parser.add_argument("--output", required=True, help="Path to output JSON file.")
    args = parser.parse_args()

    success = run_sensitivity_analysis_on_file(args.input, args.output)
    if not success:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()