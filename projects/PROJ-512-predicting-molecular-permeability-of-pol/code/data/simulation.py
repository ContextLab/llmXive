import os
import sys
import logging
import csv
import random
from typing import List, Dict, Any, Tuple
import json
import hashlib
from data.utils import set_seed, ensure_seed_initialized, setup_logging

# Allowed features per FR-001
ATOMS = ['C', 'H', 'O', 'N', 'S', 'F', 'Cl']
HYBRIDS = ['SP', 'SP2', 'SP3']
BOND_TYPES = ['SINGLE', 'DOUBLE', 'TRIPLE']

# Atomic weights for MW calculation
ATOM_WEIGHTS = {
    'C': 12.01,
    'H': 1.008,
    'O': 16.00,
    'N': 14.01,
    'S': 32.06,
    'F': 19.00,
    'Cl': 35.45
}

def _generate_valid_smiles(nodes: List[Dict]) -> str:
    """
    Constructs a simplified SMILES string from node list.
    Uses a basic chain representation to ensure RDKit compatibility.
    """
    if not nodes:
        return ""
    
    # Map atom types to simple SMILES characters
    # For simulation purposes, we assume a linear chain of these atoms
    # This is a simplified representation for the synthetic dataset
    char_map = {
        'C': 'C',
        'H': 'C', # H usually implicit, using C to maintain chain length for MW correlation
        'O': 'O',
        'N': 'N',
        'S': 'S',
        'F': 'F',
        'Cl': 'Cl'
    }
    
    chars = []
    for node in nodes:
        atom = node['atom_type']
        chars.append(char_map.get(atom, 'C'))
    
    return "".join(chars)

def generate_polymer_graphs(count: int = 1000, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Generates synthetic polymer graphs with associated log-permeability values.
    Uses ONLY node/edge features defined in FR-001 (atom type, hybridization, bond type)
    and basic molecular weight (derived from atom count/type).
    
    Constraint: No physics-based features like 'free-volume' or 'chain dynamics' are included.
    The log-permeability is a heuristic derived from the graph topology (size/composition)
    to provide a target for the model, strictly adhering to the simulation requirement.
    """
    set_seed(seed)
    ensure_seed_initialized()
    logging.info(f"Generating {count} synthetic polymer graphs with seed {seed}...")
    
    graphs = []
    
    for i in range(count):
        # Generate a random repeat unit structure (simplified)
        # Molecular weight is derived from the atoms used
        num_atoms = random.randint(10, 50)
        nodes = []
        total_mw = 0.0
        
        for _ in range(num_atoms):
            atom = random.choice(ATOMS)
            node = {
                "atom_type": atom,
                "hybridization": random.choice(HYBRIDS)
            }
            nodes.append(node)
            total_mw += ATOM_WEIGHTS[atom]
        
        edges = []
        # Create a simple chain-like connectivity to ensure a valid graph structure
        # This mimics a polymer backbone
        for j in range(num_atoms - 1):
            edge = {
                "bond_type": random.choice(BOND_TYPES)
            }
            edges.append(edge)
        
        # Generate a simplified SMILES string for validity checks in ingestion
        smiles = _generate_valid_smiles(nodes)
        
        # Calculate a pseudo-log-permeability based on size and composition
        # Heuristic: Larger molecules generally have lower permeability (negative correlation)
        # but specific functional groups (O, N) might increase it slightly in this simulation context.
        # This is a synthetic target for the model to learn, not a physical law.
        # Formula: Base + Size factor + Composition factor + Noise
        base = -6.0
        size_factor = -0.05 * num_atoms
        comp_factor = 0.1 * (total_mw / 100.0) # Normalize MW contribution
        noise = random.uniform(-0.5, 0.5)
        
        log_perm = base + size_factor + comp_factor + noise
        
        graphs.append({
            "id": i,
            "smiles": smiles,
            "nodes": nodes,
            "edges": edges,
            "molecular_weight": total_mw,
            "log_permeability": log_perm
        })
            
    return graphs

def save_simulation_data(filepath: str, count: int = 1000, seed: int = 42):
    """
    Saves generated simulation data to a CSV file.
    The CSV contains flattened data suitable for ingestion.
    Columns: id, smiles, num_atoms, num_edges, molecular_weight, log_permeability
    """
    graphs = generate_polymer_graphs(count, seed)
    
    rows = []
    for g in graphs:
        rows.append({
            "id": g["id"],
            "smiles": g["smiles"],
            "num_atoms": len(g["nodes"]),
            "num_edges": len(g["edges"]),
            "molecular_weight": round(g["molecular_weight"], 2),
            "log_permeability": round(g["log_permeability"], 4)
        })
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w', newline='') as csvfile:
        fieldnames = ["id", "smiles", "num_atoms", "num_edges", "molecular_weight", "log_permeability"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(rows)
    
    logging.info(f"Simulation data saved to {filepath}")

def main():
    """Main entry point for simulation generation."""
    output_path = "projects/PROJ-512-predicting-molecular-permeability-of-pol/code/data/raw/simulation_data.csv"
    save_simulation_data(output_path, count=1000, seed=42)

if __name__ == "__main__":
    setup_logging()
    main()