"""
CIF parser for converting CIF files to MaterialGraph objects.

This module implements the parsing logic for converting crystallographic
information files (CIF) into the canonical MaterialGraph data structure.
It relies on pymatgen for structure parsing and feature extraction.

WARNING: This model is a surrogate interpolator trained on pre-computed DFT data.
It does NOT solve the Schrödinger equation or perform first-principles calculations.
"""
from __future__ import annotations

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import asdict

import numpy as np
from pymatgen.io.cif import CifParser
from pymatgen.core import Structure
from pymatgen.analysis.elasticity import ElasticTensor

from data_models.material_graph import MaterialGraph
from ingest.bias_check import ExclusionReason

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Feature dimensions as per spec
NODE_FEATURE_DIM = 128
EDGE_FEATURE_DIM = 64

def get_atomic_properties(structure: Structure) -> Dict[str, Any]:
    """Extract atomic properties from a pymatgen Structure."""
    composition = structure.composition
    elements = composition.elements
    num_atoms = len(structure)
    
    # Basic composition statistics
    element_counts = {str(el): count for el, count in composition.items()}
    
    # Average atomic mass
    total_mass = sum(el.atomic_mass * count for el, count in composition.items())
    avg_mass = total_mass / num_atoms if num_atoms > 0 else 0.0
    
    # Space group info
    sg_info = structure.get_space_group_info()
    space_group = sg_info[0] if sg_info[0] else "Unknown"
    space_group_num = sg_info[1] if sg_info[1] else 0
    
    # Lattice parameters
    lattice = structure.lattice
    lattice_params = {
        "a": lattice.a,
        "b": lattice.b,
        "c": lattice.c,
        "alpha": lattice.alpha,
        "beta": lattice.beta,
        "gamma": lattice.gamma
    }
    
    return {
        "num_atoms": num_atoms,
        "composition": composition.formula,
        "element_counts": element_counts,
        "avg_atomic_mass": avg_mass,
        "space_group_symbol": space_group,
        "space_group_number": space_group_num,
        "lattice_parameters": lattice_params,
        "volume": lattice.volume
    }

def featurize_atoms(structure: Structure) -> np.ndarray:
    """
    Featurize atoms into a fixed-size vector per atom.
    Uses elemental properties from pymatgen.
    """
    features = []
    for site in structure.sites:
        element = site.specie
        
        # Elemental properties
        atomic_number = element.Z
        atomic_mass = element.atomic_mass
        electronegativity = element.X if hasattr(element, 'X') else 0.0
        valence = element.num_valence if hasattr(element, 'num_valence') else 0
        group = element.group_number if hasattr(element, 'group_number') else 0
        period = element.period if hasattr(element, 'period') else 0
        
        # Normalize features
        # Atomic number (max ~118)
        norm_atomic_number = atomic_number / 118.0
        # Atomic mass (max ~294 for Oganesson, but let's use 300)
        norm_atomic_mass = atomic_mass / 300.0
        # Electronegativity (Pauling scale, max ~4)
        norm_electronegativity = electronegativity / 4.0
        # Valence (max ~8 for main group)
        norm_valence = valence / 8.0
        # Group (max 18)
        norm_group = group / 18.0
        # Period (max 7)
        norm_period = period / 7.0
        
        # Create feature vector (pad to NODE_FEATURE_DIM)
        vec = [
            norm_atomic_number,
            norm_atomic_mass,
            norm_electronegativity,
            norm_valence,
            norm_group,
            norm_period
        ]
        
        # Pad with zeros to reach NODE_FEATURE_DIM
        padding = [0.0] * (NODE_FEATURE_DIM - len(vec))
        vec.extend(padding)
        
        features.append(vec)
    
    return np.array(features, dtype=np.float32)

def featurize_bonds(structure: Structure) -> np.ndarray:
    """
    Featurize bonds (edges) into a fixed-size vector per bond.
    Uses distance and coordination information.
    """
    # Get bonding structure using pymatgen's bond valence sum or distance-based
    # For simplicity, we'll use distance-based bonding
    bonds = []
    
    # Calculate all pairwise distances and find bonds within cutoff
    # A simple heuristic: bonds exist if distance < sum of covalent radii * factor
    covalent_radii = {site.specie: site.specie.covalent_radius for site in structure.sites}
    
    # Build adjacency list based on distance
    adjacency = {i: [] for i in range(len(structure))}
    
    for i, site1 in enumerate(structure.sites):
        for j, site2 in enumerate(structure.sites):
            if i >= j:
                continue
            
            dist = structure.get_distance(i, j)
            
            # Estimate bond cutoff
            r1 = covalent_radii.get(site1.specie, 1.0)
            r2 = covalent_radii.get(site2.specie, 1.0)
            cutoff = (r1 + r2) * 1.3  # 30% tolerance
            
            if dist < cutoff:
                adjacency[i].append(j)
                adjacency[j].append(i)
                bonds.append((i, j, dist))
    
    # Featurize each bond
    edge_features = []
    for i, j, dist in bonds:
        site1 = structure.sites[i]
        site2 = structure.sites[j]
        
        # Bond features
        element1 = site1.specie
        element2 = site2.specie
        
        # Normalized distance (typical bond lengths ~1-3 Angstrom)
        norm_dist = min(dist / 3.0, 1.0)
        
        # Element properties difference
        en_diff = abs(element1.X - element2.X) if hasattr(element1, 'X') and hasattr(element2, 'X') else 0.0
        norm_en_diff = en_diff / 4.0  # Pauling scale max ~4
        
        # Atomic number difference
        zn_diff = abs(element1.Z - element2.Z)
        norm_zn_diff = min(zn_diff / 118.0, 1.0)
        
        # Bond order estimate (simplified: 1 for single, could be higher)
        bond_order = 1.0
        
        # Coordination numbers
        coord_i = len(adjacency[i])
        coord_j = len(adjacency[j])
        norm_coord_i = min(coord_i / 12.0, 1.0)  # Max coordination ~12
        norm_coord_j = min(coord_j / 12.0, 1.0)
        
        vec = [
            norm_dist,
            norm_en_diff,
            norm_zn_diff,
            bond_order / 4.0,  # Normalize by max typical bond order
            norm_coord_i,
            norm_coord_j
        ]
        
        # Pad to EDGE_FEATURE_DIM
        padding = [0.0] * (EDGE_FEATURE_DIM - len(vec))
        vec.extend(padding)
        
        edge_features.append(vec)
    
    if not edge_features:
        # Return empty array if no bonds found
        return np.array([], dtype=np.float32).reshape(0, EDGE_FEATURE_DIM)
    
    return np.array(edge_features, dtype=np.float32)

def parse_cif_file(cif_path: Path) -> Tuple[Optional[MaterialGraph], Optional[ExclusionReason]]:
    """Parse a single CIF file into a MaterialGraph."""
    try:
        parser = CifParser(str(cif_path))
        structures = parser.parse_structures()
        
        if not structures:
            return None, ExclusionReason(
                material_id=cif_path.stem,
                reason="No structure found in CIF",
                category="parse"
            )
        
        # Take the first structure (or could handle multiple)
        structure = structures[0]
        
        # Validate structure
        if len(structure) == 0:
            return None, ExclusionReason(
                material_id=cif_path.stem,
                reason="Empty structure",
                category="validation"
            )
        
        # Extract atomic properties
        structure_summary = get_atomic_properties(structure)
        
        # Featurize atoms (nodes)
        node_features = featurize_atoms(structure)
        
        # Featurize bonds (edges)
        edge_features = featurize_bonds(structure)
        
        # Target moduli - we'll use placeholder here
        # The actual elastic tensor should come from the data source metadata
        # For now, set to zeros and let the filter step validate
        target_moduli = [0.0] * 6  # Placeholder for 6 independent components
        
        # Determine family_id based on space group
        sg_info = structure.get_space_group_info()
        family_id = sg_info[0] if sg_info[0] else "Unknown"
        
        graph = MaterialGraph(
            node_features=node_features,
            edge_features=edge_features,
            target_moduli=target_moduli,
            family_id=family_id,
            material_id=cif_path.stem,
            structure_summary=structure_summary
        )
        
        return graph, None

    except Exception as e:
        logger.error(f"Error parsing CIF {cif_path}: {e}")
        return None, ExclusionReason(
            material_id=cif_path.stem,
            reason=f"Parsing error: {str(e)}",
            category="parse"
        )

def parse_cif_directory(cif_dir: Path) -> Tuple[List[MaterialGraph], List[ExclusionReason]]:
    """Parse all CIF files in a directory."""
    graphs = []
    exclusions = []

    cif_files = list(cif_dir.glob("*.cif"))
    logger.info(f"Found {len(cif_files)} CIF files in {cif_dir}")

    for cif_file in cif_files:
        graph, exclusion = parse_cif_file(cif_file)
        if graph:
            graphs.append(graph)
        if exclusion:
            exclusions.append(exclusion)
    
    logger.info(f"Parsed {len(graphs)} graphs, excluded {len(exclusions)}.")
    return graphs, exclusions

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Parse CIF files to MaterialGraph.")
    parser.add_argument("--input", type=str, required=True, help="Input directory or file")
    parser.add_argument("--output", type=str, required=True, help="Output JSON file for graphs")
    
    args = parser.parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    if input_path.is_dir():
        graphs, exclusions = parse_cif_directory(input_path)
    else:
        graph, exclusion = parse_cif_file(input_path)
        graphs = [graph] if graph else []
        exclusions = [exclusion] if exclusion else []

    # Save results to JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        "graphs": [
            {
                "node_features": g.node_features.tolist() if hasattr(g.node_features, 'tolist') else list(g.node_features),
                "edge_features": g.edge_features.tolist() if hasattr(g.edge_features, 'tolist') else list(g.edge_features),
                "target_moduli": g.target_moduli.tolist() if hasattr(g.target_moduli, 'tolist') else list(g.target_moduli),
                "family_id": g.family_id,
                "material_id": g.material_id,
                "structure_summary": g.structure_summary
            }
            for g in graphs
        ],
        "exclusions": [asdict(e) for e in exclusions]
    }
    
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    logger.info(f"Total graphs: {len(graphs)}, Exclusions: {len(exclusions)}")

if __name__ == "__main__":
    main()