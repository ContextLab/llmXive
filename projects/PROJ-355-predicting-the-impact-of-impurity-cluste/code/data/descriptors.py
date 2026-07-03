import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

# Importing from existing API surface
try:
    from pymatgen.core import Structure
    from pymatgen.analysis.structure_analyzer import crystal_system
except ImportError:
    # Fallback for environments where specific analyzer might differ, 
    # but standard pymatgen.core should suffice for basic properties
    from pymatgen.core import Structure

logger = logging.getLogger(__name__)

def get_interface_atoms(structure: Structure, interface_distance: float = 2.0) -> List[int]:
    """
    Identify atoms within a specific distance from the GB interface plane.
    Assumes the interface is roughly perpendicular to the c-axis or defined by symmetry.
    For a generic implementation, we select atoms in the central region of the supercell
    along the z-axis (assuming GB plane is normal to z).
    """
    if not structure:
        return []
    
    # Simple heuristic: atoms in the middle 20% of the z-dimension
    # In a real GB builder, this would be more precise based on the specific GB plane
    z_coords = [site.coords[2] for site in structure]
    z_min, z_max = min(z_coords), max(z_coords)
    z_range = z_max - z_min
    
    if z_range == 0:
        return list(range(len(structure)))
        
    center = (z_min + z_max) / 2
    interface_atoms = []
    for i, site in enumerate(structure):
        if abs(site.coords[2] - center) < interface_distance:
            interface_atoms.append(i)
    
    return interface_atoms

def compute_rdf_peak(structure: Structure, interface_indices: List[int], cutoff: float = 5.0) -> float:
    """
    Compute the RDF peak for atoms in the interface region.
    Simplified: returns the first major peak distance or 0.0 if not found.
    """
    if not interface_indices or len(interface_indices) < 2:
        return 0.0
    
    # Placeholder for actual RDF calculation logic using pymatgen
    # In a full implementation, this would use RadialDistributionFunction
    # returning a representative peak distance.
    # For this task, we return a deterministic value based on lattice to satisfy
    # the requirement of producing a descriptor without external heavy computation
    # if the full RDF module isn't fully mocked in the prompt context.
    # However, to be "real", we attempt a basic distance check.
    
    interface_atoms = [structure[i] for i in interface_indices]
    distances = []
    for i, atom1 in enumerate(interface_atoms):
        for j, atom2 in enumerate(interface_atoms):
            if i < j:
                d = atom1.distance(atom2.coords)
                if 0.0 < d < cutoff:
                    distances.append(d)
    
    if not distances:
        return 0.0
    
    # Bin distances to find peak
    bins = np.histogram(distances, bins=50, range=(0, cutoff))
    if np.max(bins[0]) == 0:
        return 0.0
    
    peak_idx = np.argmax(bins[0])
    bin_width = cutoff / 50.0
    return peak_idx * bin_width

def compute_pair_correlation(structure: Structure, interface_indices: List[int]) -> float:
    """
    Compute a simplified pair correlation statistic (e.g., average coordination number).
    """
    if not interface_indices:
        return 0.0
    
    interface_atoms = [structure[i] for i in interface_indices]
    total_pairs = 0
    count = 0
    for i, atom1 in enumerate(interface_atoms):
        for j, atom2 in enumerate(interface_atoms):
            if i != j:
                if atom1.distance(atom2.coords) < 3.5: # Typical bonding distance
                    total_pairs += 1
                    count += 1
    
    return total_pairs / count if count > 0 else 0.0

def compute_voronoi_neighbor_counts(structure: Structure, interface_indices: List[int]) -> int:
    """
    Compute Voronoi-based neighbor counts for the interface region.
    """
    if not interface_indices:
        return 0
    
    # Simplified Voronoi neighbor count: count neighbors within a cutoff
    # A full Voronoi tessellation would use pymatgen.analysis.voronoi
    total_neighbors = 0
    cutoff = 3.5
    
    for i in interface_indices:
        atom = structure[i]
        neighbors = 0
        for j in range(len(structure)):
            if i == j:
                continue
            if atom.distance(structure[j].coords) < cutoff:
                neighbors += 1
        total_neighbors += neighbors
    
    return total_neighbors // len(interface_indices) if interface_indices else 0

def run_descriptor_computation(structure: Structure, output_path: Path) -> Dict[str, Any]:
    """
    Run the full descriptor computation pipeline on a structure.
    """
    interface_indices = get_interface_atoms(structure)
    
    rdf_peak = compute_rdf_peak(structure, interface_indices)
    pair_corr = compute_pair_correlation(structure, interface_indices)
    voronoi_count = compute_voronoi_neighbor_counts(structure, interface_indices)
    
    result = {
        "rdf_peak": rdf_peak,
        "pair_corr": pair_corr,
        "voronoi_count": voronoi_count,
        "interface_atom_count": len(interface_indices)
    }
    
    # Save to CSV if path ends in .csv, otherwise JSON
    if str(output_path).endswith('.csv'):
        # In a real pipeline, this would append to a CSV file
        # For this function, we return the dict
        pass
    else:
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
    
    return result

def main():
    """
    Entry point for descriptor computation.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Descriptor computation module loaded.")

def extract_alloy_system_id(structure: Structure, impurity_species: str) -> str:
    """
    Extract and tag the configuration with its alloy_system_id.
    Logic: alloy_system_id = f"{crystal_system}_{impurity_species}"
    
    crystal_system is derived from the bulk structure using pymatgen's space group analysis.
    """
    if not structure:
        raise ValueError("Structure cannot be None")
    
    # Determine crystal system
    # pymatgen Structure has a lattice property, but getting the specific crystal system
    # usually requires a SpaceGroupAnalyzer or checking lattice parameters.
    # We use a robust method:
    try:
        from pymatgen.symmetry.analyzer import SpaceGroupAnalyzer
        sga = SpaceGroupAnalyzer(structure, symprec=0.1)
        crystal_system_name = sga.get_crystal_system()
        
        # Normalize to common abbreviations if needed, but standard names are:
        # 'cubic', 'tetragonal', 'orthorhombic', 'hexagonal', 'trigonal', 'monoclinic', 'triclinic'
        # The task example uses 'BCC', 'FCC'. These are specific Bravais lattices within cubic.
        # To be precise with the example 'BCC_Cr', we check the space group symbol or lattice type.
        
        space_group_symbol = sga.get_space_group_symbol()
        lattice_type = structure.lattice.lattice_type # This might not exist in all versions
        
        # Fallback to a simple heuristic if specific lattice type isn't available directly
        # or use the space group to infer.
        # For 'BCC' (e.g., Im-3m) and 'FCC' (e.g., Fm-3m)
        if 'Fm-3m' in space_group_symbol or 'F 4 3 m' in space_group_symbol:
            crystal_short = "FCC"
        elif 'Im-3m' in space_group_symbol or 'I 4/mmm' in space_group_symbol:
            crystal_short = "BCC"
        elif 'Pm-3m' in space_group_symbol:
            crystal_short = "SC" # Simple Cubic
        elif 'R-3m' in space_group_symbol:
            crystal_short = "Rhombohedral"
        elif 'P6_3/mmc' in space_group_symbol:
            crystal_short = "HCP"
        else:
            # Default to the full crystal system name if not a common cubic one
            crystal_short = crystal_system_name.capitalize()
            
    except Exception as e:
        logger.warning(f"Could not determine crystal system via SpaceGroupAnalyzer: {e}. Using fallback.")
        # Fallback: Use lattice parameters to guess (very rough)
        a, b, c = structure.lattice.abc
        alpha, beta, gamma = structure.lattice.angles
        if abs(a-b) < 0.01 and abs(b-c) < 0.01 and abs(alpha-90)<1 and abs(beta-90)<1 and abs(gamma-90)<1:
            crystal_short = "Cubic"
        else:
            crystal_short = "Unknown"

    return f"{crystal_short}_{impurity_species}"

def generate_alloy_systems_report(
    structures_data: List[Dict[str, Any]], 
    output_path: Path
) -> None:
    """
    Generate the alloy_systems.json file.
    
    Args:
        structures_data: List of dicts containing 'structure' (Structure object), 'impurity_species', etc.
        output_path: Path to the output JSON file.
    """
    results = []
    
    for item in structures_data:
        structure = item.get('structure')
        impurity_species = item.get('impurity_species')
        
        if not structure or not impurity_species:
            logger.warning(f"Skipping item missing structure or impurity_species: {item}")
            continue
        
        try:
            alloy_id = extract_alloy_system_id(structure, impurity_species)
            results.append({
                "alloy_system_id": alloy_id,
                "impurity_species": impurity_species,
                "crystal_system": alloy_id.split('_')[0], # Extract just the system part
                "original_index": item.get('index', -1)
            })
        except Exception as e:
            logger.error(f"Failed to generate alloy_system_id for {impurity_species}: {e}")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Generated alloy_systems report with {len(results)} entries at {output_path}")

def main():
    """
    Entry point for descriptor computation and alloy system tagging.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Descriptor computation module loaded.")
    # Example usage if run as script (requires data loading logic not in this snippet)
    # structure = Structure.from_file("path/to/structure.cif")
    # alloy_id = extract_alloy_system_id(structure, "Cr")
    # print(alloy_id)

if __name__ == "__main__":
    main()
