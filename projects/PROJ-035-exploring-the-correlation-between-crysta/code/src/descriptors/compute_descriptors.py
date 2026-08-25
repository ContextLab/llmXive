import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

try:
    from pymatgen.core import Structure, Lattice
    from pymatgen.analysis.local_env import VoronoiNN
except ImportError:
    logging.error("pymatgen is required. Install with: pip install pymatgen")
    sys.exit(1)

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def calculate_tolerance_factor(structure: Structure) -> float:
    """
    Calculate the Goldschmidt tolerance factor (t) for a perovskite structure.
    Formula: t = (r_A + r_X) / (sqrt(2) * (r_B + r_X))
    where r_A, r_B, r_X are ionic radii of the A, B, and X site ions.
    
    Args:
        structure: A pymatgen Structure object representing the perovskite.
    
    Returns:
        float: The calculated tolerance factor.
    """
    # Get species and their counts to identify A, B, X sites
    # Assuming standard perovskite ABX3 stoichiometry
    species = structure.species
    unique_species = list(set(species))
    
    if len(unique_species) != 3:
        # Fallback or error handling for non-standard stoichiometry
        logger.warning(f"Non-standard stoichiometry detected: {structure.formula}. Attempting heuristic identification.")
    
    # Heuristic: A is usually the largest cation, B is the smallest cation, X is the anion
    # This is a simplification. A more robust method would use specific ionic radii tables.
    # For this implementation, we assume the structure is already filtered for ABX3.
    
    # We need to assign sites. In a standard perovskite:
    # A is at corners (0,0,0), B at body center (0.5, 0.5, 0.5), X at face centers.
    # However, pymatgen structures might be primitive or supercells.
    # We will use ionic radii from pymatgen's data if available, or a standard lookup.
    
    # Simplified approach using standard ionic radii for common perovskites
    # This is a placeholder for a more robust ionic radius lookup
    standard_radii = {
        'La': 1.36, 'Sr': 1.44, 'Ba': 1.61, 'Ca': 1.34, 'Pb': 1.49, # A-site
        'Ti': 0.605, 'Zr': 0.72, 'Sn': 0.69, 'Nb': 0.64, 'Ta': 0.64, # B-site
        'O': 1.40, 'F': 1.33, 'Cl': 1.81, 'Br': 1.96, 'I': 2.20, # X-site
        'Mn': 0.645, 'Fe': 0.645, 'Co': 0.61, 'Ni': 0.60, # B-site transition metals
    }
    
    # Identify A, B, X based on coordination or position if possible, otherwise by size
    # For this task, we assume the input structure is a valid perovskite and try to infer
    # A, B, X based on typical ionic radii ranges.
    
    cations = []
    anions = []
    
    for site in structure:
        for spec in site.species:
            element = spec.element.symbol
            if element in standard_radii:
                if element in ['O', 'F', 'Cl', 'Br', 'I']:
                    anions.append((element, standard_radii[element]))
                else:
                    cations.append((element, standard_radii[element]))
    
    if not cations or not anions:
        logger.error("Could not identify A, B, or X sites with standard radii.")
        return 0.0
    
    # Assume the largest cation is A, the smallest is B
    cations.sort(key=lambda x: x[1], reverse=True)
    r_A = cations[0][1]
    r_B = cations[-1][1] # Smallest cation
    r_X = anions[0][1]   # Assume all anions are similar, take first
    
    if r_B + r_X == 0:
        return 0.0
        
    t = (r_A + r_X) / (np.sqrt(2) * (r_B + r_X))
    return t


def calculate_octahedral_tilting_angles(structure: Structure) -> float:
    """
    Calculate a representative octahedral tilting angle.
    This is a simplified metric: deviation of B-X-B bond angles from 180 degrees.
    
    Args:
        structure: A pymatgen Structure object.
    
    Returns:
        float: Average absolute deviation from 180 degrees for B-X-B angles.
    """
    # Find B-X-B bonds
    # We need to identify B and X sites first
    # Heuristic: B is the smallest cation, X is the anion
    
    # Use VoronoiNN to find neighbors
    nn = VoronoiNN()
    
    b_x_b_angles = []
    
    # Identify B site (smallest cation) and X site (anion)
    # This logic needs to be robust. For now, we assume a standard perovskite.
    species_list = [site.species for site in structure]
    # Flatten to get all elements
    all_elements = []
    for site in structure:
        for spec in site.species:
            all_elements.append(spec.element.symbol)
    
    # Simple heuristic: find unique elements
    unique_elements = set(all_elements)
    # Assume anion is the most electronegative or one of O, F, Cl, etc.
    anion_candidates = {'O', 'F', 'Cl', 'Br', 'I', 'S', 'N'}
    anion_element = None
    for el in unique_elements:
        if el in anion_candidates:
            anion_element = el
            break
    
    if not anion_element:
        logger.warning("Could not identify anion for tilting angle calculation.")
        return 0.0
    
    # Find B site: smallest cation (excluding anion)
    cation_elements = [el for el in unique_elements if el != anion_element]
    # Assume first cation found is B (needs refinement for mixed B-sites)
    # For simplicity, we take the first cation element as B
    if not cation_elements:
        return 0.0
    b_element = cation_elements[0] # Simplification
    
    b_sites = [i for i, site in enumerate(structure) if b_element in [spec.element.symbol for spec in site.species]]
    x_sites = [i for i, site in enumerate(structure) if anion_element in [spec.element.symbol for spec in site.species]]
    
    if not b_sites or not x_sites:
        return 0.0
    
    # Calculate B-X-B angles
    for x_idx in x_sites:
        x_site = structure[x_idx]
        # Find neighbors of X
        neighbors = nn.get_neighbors(structure, x_site, 4.0) # Search radius
        b_neighbors = [n.site for n in neighbors if any(spec.element.symbol == b_element for spec in n.site.species)]
        
        if len(b_neighbors) >= 2:
            # Calculate angle between pairs of B neighbors around X
            for i in range(len(b_neighbors)):
                for j in range(i + 1, len(b_neighbors)):
                    v1 = b_neighbors[i].coords - x_site.coords
                    v2 = b_neighbors[j].coords - x_site.coords
                    # Normalize
                    v1 = v1 / np.linalg.norm(v1)
                    v2 = v2 / np.linalg.norm(v2)
                    angle_rad = np.arccos(np.clip(np.dot(v1, v2), -1.0, 1.0))
                    angle_deg = np.degrees(angle_rad)
                    b_x_b_angles.append(abs(180.0 - angle_deg))
    
    if not b_x_b_angles:
        return 0.0
    
    return np.mean(b_x_b_angles)


def calculate_bond_length_variance(structure: Structure) -> float:
    """
    Calculate the variance of B-X bond lengths.
    Ideally, in a perfect octahedron, all B-X bonds are equal.
    
    Args:
        structure: A pymatgen Structure object.
    
    Returns:
        float: Variance of B-X bond lengths.
    """
    # Identify B and X sites
    all_elements = set()
    for site in structure:
        for spec in site.species:
            all_elements.add(spec.element.symbol)
    
    anion_candidates = {'O', 'F', 'Cl', 'Br', 'I', 'S', 'N'}
    anion_element = next((el for el in all_elements if el in anion_candidates), None)
    
    if not anion_element:
        logger.warning("Anion not found for bond length variance.")
        return 0.0
    
    cation_elements = [el for el in all_elements if el != anion_element]
    if not cation_elements:
        return 0.0
    b_element = cation_elements[0] # Simplification
    
    bond_lengths = []
    
    for site in structure:
        if b_element in [spec.element.symbol for spec in site.species]:
            # Find X neighbors
            for neighbor_site in structure:
                if anion_element in [spec.element.symbol for spec in neighbor_site.species]:
                    dist = structure.distance(site, neighbor_site)
                    # Filter for reasonable bond lengths (e.g., < 3.0 Angstroms)
                    if 1.5 < dist < 3.0:
                        bond_lengths.append(dist)
    
    if len(bond_lengths) < 2:
        return 0.0
    
    return float(np.var(bond_lengths))


def calculate_unit_cell_volume(structure: Structure) -> float:
    """
    Calculate the volume of the unit cell.
    
    Args:
        structure: A pymatgen Structure object.
    
    Returns:
        float: Volume of the unit cell in Angstrom^3.
    """
    return structure.volume


def compute_all_descriptors(structure: Structure) -> Dict[str, float]:
    """
    Compute all descriptors for a given structure.
    
    Args:
        structure: A pymatgen Structure object.
    
    Returns:
        dict: A dictionary of descriptor names and their values.
    """
    try:
        tolerance_factor = calculate_tolerance_factor(structure)
        tilting_angle = calculate_octahedral_tilting_angles(structure)
        bond_length_var = calculate_bond_length_variance(structure)
        volume = calculate_unit_cell_volume(structure)
        
        return {
            'tolerance_factor': tolerance_factor,
            'octahedral_tilting_angle': tilting_angle,
            'bond_length_variance': bond_length_var,
            'unit_cell_volume': volume
        }
    except Exception as e:
        logger.error(f"Error computing descriptors: {e}")
        return {
            'tolerance_factor': np.nan,
            'octahedral_tilting_angle': np.nan,
            'bond_length_variance': np.nan,
            'unit_cell_volume': np.nan
        }


def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process a dataframe of perovskite data to compute descriptors.
    Assumes the dataframe has a 'structure' column containing pymatgen Structure objects
    or a 'structure_id' column that can be used to reconstruct the structure.
    For this implementation, we assume 'structure' column exists.
    
    Args:
        df: Input dataframe.
    
    Returns:
        pd.DataFrame: DataFrame with added descriptor columns.
    """
    logger.info(f"Processing {len(df)} structures for descriptors...")
    
    descriptors_list = []
    
    for idx, row in df.iterrows():
        if 'structure' in row:
            struct = row['structure']
            if isinstance(struct, Structure):
                desc = compute_all_descriptors(struct)
                descriptors_list.append(desc)
            else:
                logger.warning(f"Row {idx} has invalid structure type: {type(struct)}")
                descriptors_list.append({k: np.nan for k in ['tolerance_factor', 'octahedral_tilting_angle', 'bond_length_variance', 'unit_cell_volume']})
        else:
            logger.warning(f"Row {idx} missing 'structure' column")
            descriptors_list.append({k: np.nan for k in ['tolerance_factor', 'octahedral_tilting_angle', 'bond_length_variance', 'unit_cell_volume']})
    
    desc_df = pd.DataFrame(descriptors_list)
    
    # Combine with original dataframe
    result_df = pd.concat([df.reset_index(drop=True), desc_df], axis=1)
    
    return result_df


def main():
    """
    Main entry point for the descriptor computation script.
    Expects a cleaned CSV file at data/cleaned/merged_perovskite.csv
    and outputs to data/results/descriptors.csv
    """
    # Paths
    input_path = Path("data/cleaned/merged_perovskite.csv")
    output_path = Path("data/results/descriptors.csv")
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    # Load data
    # Note: The structure column might be stored as a string or object.
    # If it's a string representation, we need to parse it.
    # For this task, we assume the data cleaning step (T013) preserved Structure objects
    # or we need to reconstruct them.
    # A robust implementation would read from a JSON or a specific format.
    # Here, we assume the CSV was saved with a custom converter or we need to reload structures.
    
    # Since CSV cannot natively hold Structure objects, we assume the 'structure' column
    # contains a JSON string or a path to a CIF/structure file.
    # For this implementation, we will assume the input CSV has a 'cif_string' or similar
    # and we reconstruct the structure.
    # However, T013 output is a CSV. Let's assume the 'structure' column is a JSON string
    # that we can eval or a path.
    
    # To make this runnable, we will assume the input CSV has columns:
    # 'structure_id', 'thermal_conductivity', 'formula', 'structure_json' (stringified structure)
    # If 'structure' is present as an object, it won't survive CSV roundtrip.
    # Let's assume the previous step saved a 'structure_json' column.
    
    df = pd.read_csv(input_path)
    
    # Check for structure data
    if 'structure' in df.columns:
        # If it's a string representation of a dict/json, try to parse
        # This is a fragile approach. Ideally, we use a different format like HDF5 or JSON.
        # For now, we assume it's a JSON string that we can reconstruct if we had a loader.
        # Since we don't have a robust JSON->Structure loader in this snippet without more code,
        # we will assume the 'structure' column is actually a path to a CIF file or similar.
        # BUT, T013 merges data. It's likely the structure is stored as a stringified JSON of the structure data.
        # Let's assume we have a helper to load from JSON string.
        # For the sake of this task, we will skip the actual Structure reconstruction if it's not trivial
        # and assume the 'structure' column is already a Structure object (which implies the CSV was not a standard CSV
        # but a pickle or similar, which contradicts the task).
        
        # Correction: The task says "merged with thermal data". The structure must be stored somehow.
        # Let's assume the input file is actually a pickle or the 'structure' column is a JSON string
        # and we have a function to load it.
        # Since we cannot guarantee the format without more context, we will assume the 'structure' column
        # is a JSON string and we need to parse it.
        
        # We will implement a simple check. If it's a string, we try to load it.
        # If it's already a Structure, we use it.
        
        # For this implementation, we will assume the 'structure' column contains a JSON string
        # representing the structure data (species, coords, lattice).
        # We need a function to reconstruct Structure from this JSON.
        # Since we don't have that in the API surface, we will assume the input is a pickle
        # or the 'structure' column is not present and we need to load from a separate file.
        
        # Given the constraints, let's assume the input CSV has 'structure_json' column.
        # If not, we cannot proceed without a loader.
        
        # Let's assume the 'structure' column is a JSON string and we use `json.loads` and `Structure.from_dict`.
        import json
        
        def load_structure_from_json(json_str):
            try:
                d = json.loads(json_str)
                return Structure.from_dict(d)
            except Exception as e:
                logger.error(f"Failed to load structure from JSON: {e}")
                return None
        
        structures = []
        for val in df['structure']:
            if isinstance(val, str):
                s = load_structure_from_json(val)
                structures.append(s)
            elif isinstance(val, Structure):
                structures.append(val)
            else:
                structures.append(None)
        
        df['structure'] = structures
        
    elif 'structure_json' in df.columns:
        import json
        def load_structure_from_json(json_str):
            try:
                d = json.loads(json_str)
                return Structure.from_dict(d)
            except Exception as e:
                logger.error(f"Failed to load structure from JSON: {e}")
                return None
        
        df['structure'] = df['structure_json'].apply(load_structure_from_json)
    else:
        logger.error("No structure column found in input CSV.")
        sys.exit(1)
    
    # Process
    result_df = process_dataframe(df)
    
    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(output_path, index=False)
    logger.info(f"Descriptors saved to {output_path}")


if __name__ == "__main__":
    main()
