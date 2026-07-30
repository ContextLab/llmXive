import os
import sys
import logging
import csv
import random
from typing import List, Dict, Any, Tuple, Optional, Union

from data.utils import set_seed, get_seed
from models.polymer_graph import PolymerGraph
from models.permeability_record import PermeabilityRecord

logger = logging.getLogger(__name__)

# Note: This module provides synthetic data generation ONLY for internal testing
# when real data is strictly unavailable. Per project constraints (SC-001),
# real data sources (NIST/PubChem) must be attempted first.
# This module is explicitly designed to be bypassed by the ingestion pipeline
# if real data is found.

def generate_polymer_graphs(
    count: Optional[int] = None,
    seed: Optional[int] = None,
    num_samples: Optional[int] = None
) -> Tuple[List[PolymerGraph], List[PermeabilityRecord]]:
    """
    Generates synthetic polymer graphs for testing purposes ONLY.
    
    This function accepts arguments from multiple call sites:
    - `generate_polymer_graphs(count, seed)` from simulation.py main
    - `generate_polymer_graphs(num_samples=1000)` from ingestion.py fallback
    
    Args:
        count: Number of samples to generate (positional arg from simulation.py)
        seed: Random seed for reproducibility
        num_samples: Number of samples to generate (keyword arg from ingestion.py)
        
    Returns:
        Tuple of (list of PolymerGraph, list of PermeabilityRecord)
        
    Raises:
        ValueError: If neither count nor num_samples is provided
    """
    # Resolve sample count from either positional or keyword argument
    if num_samples is not None:
        actual_count = num_samples
    elif count is not None:
        actual_count = count
    else:
        raise ValueError("generate_polymer_graphs requires either 'count' or 'num_samples' argument")
        
    if seed is not None:
        set_seed(seed)
    else:
        ensure_seed = get_seed()
        if ensure_seed is None:
            set_seed(42)
        
    graphs = []
    records = []
    
    # Simple synthetic generation for testing only
    # In production, this path should never be reached due to real data requirements
    atom_types = ["C", "H", "O", "N", "Cl"]
    bond_types = [1, 2, 3]
    
    for i in range(actual_count):
        # Create a minimal synthetic graph
        num_atoms = random.randint(5, 20)
        nodes = []
        edges = []
        
        for j in range(num_atoms):
            atom = random.choice(atom_types)
            hybridization = random.choice(["sp", "sp2", "sp3"])
            nodes.append({
                "atom_type": atom,
                "hybridization": hybridization,
                "index": j
            })
            
            if j > 0:
                bond = random.choice(bond_types)
                edges.append({
                    "source": j - 1,
                    "target": j,
                    "bond_type": bond
                })
        
        # Create synthetic polymer graph
        graph = PolymerGraph(
            nodes=nodes,
            edges=edges,
            smiles=f"C{num_atoms}H{num_atoms*2}",  # Synthetic SMILES
            mw=float(num_atoms * 12.01 + num_atoms * 2 * 1.008)
        )
        graphs.append(graph)
        
        # Create synthetic permeability record
        log_perm = random.uniform(-10.0, -4.0)
        record = PermeabilityRecord(
            polymer_id=f"synth_{i:04d}",
            smiles=graph.smiles,
            log_permeability=log_perm,
            temperature=298.0,
            source="synthetic"
        )
        records.append(record)
        
    return graphs, records

def save_simulation_data(
    graphs: List[PolymerGraph],
    records: List[PermeabilityRecord],
    output_path: str
) -> None:
    """
    Saves synthetic polymer data to a CSV file for testing.
    
    Args:
        graphs: List of PolymerGraph objects
        records: List of PermeabilityRecord objects
        output_path: Path to save the CSV file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['polymer_id', 'smiles', 'log_permeability', 'temperature', 'source', 'mw'])
        
        for graph, record in zip(graphs, records):
            writer.writerow([
                record.polymer_id,
                graph.smiles,
                record.log_permeability,
                record.temperature,
                record.source,
                graph.mw
            ])
    
    logger.info(f"Saved {len(graphs)} synthetic samples to {output_path}")

def main():
    """Main entry point for standalone simulation data generation."""
    logging.basicConfig(level=logging.INFO)
    
    # Generate test data
    graphs, records = generate_polymer_graphs(count=100, seed=42)
    
    # Save to file
    output_path = "data/raw/synthetic_polymer_data.csv"
    save_simulation_data(graphs, records, output_path)
    
    logger.info("Simulation data generation complete.")

if __name__ == "__main__":
    main()
