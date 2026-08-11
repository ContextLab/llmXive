"""
Compute crystallographic descriptors for perovskite structures.

Calculates:
- Octahedral tilting angles
- Bond-length variance
- Tolerance factor
- Unit cell volume

This module implements FR-003.
"""
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from pymatgen.core import Structure, Lattice
from pymatgen.analysis.local_env import VoronoiNN
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.validation import setup_logger, handle_error

# Configure logger
logger = setup_logger(__name__, logging.INFO)


def calculate_tolerance_factor(
    structure: Structure,
    tolerance: Optional[str] = "goldschmidt"
) -> float:
    """
    Calculate the Goldschmidt tolerance factor for a perovskite structure.

    For ABX3 perovskites: t = (r_A + r_X) / (sqrt(2) * (r_B + r_X))

    Args:
        structure: pymatgen Structure object
        tolerance: Type of tolerance factor calculation

    Returns:
        float: Tolerance factor value
    """
    try:
        # Get species and their ionic radii
        # For perovskites, we assume standard A, B, X sites
        # We need to identify which species are at which sites
        
        # Get unique species
        species = structure.species
        unique_species = list(set(species))
        
        if len(unique_species) != 3:
            logger.warning(f"Structure has {len(unique_species)} unique species, expected 3 for ABX3")
            return np.nan

        # Calculate ionic radii for each species
        radii = {}
        for sp in unique_species:
            try:
                # Use Shannon radii (default oxidation state)
                radii[str(sp)] = sp.ionic_radius
            except Exception:
                # Fallback to covalent radius if ionic radius not available
                radii[str(sp)] = sp.covalent_radius
                logger.warning(f"Using covalent radius for {sp}")

        # Identify A, B, X sites based on coordination and stoichiometry
        # In ideal perovskite: A is 12-coordinated, B is 6-coordinated, X is 2-6 coordinated
        nn = VoronoiNN()
        
        site_radii = {}
        for site in structure.sites:
            try:
                radius = site.species_string
                if radius not in radii:
                    # Try to get from species
                    radius = str(site.species_string)
                    if radius not in radii:
                        radius = str(site.species)
                
                # Get coordination number
                neighbors = nn.get_nn(site, structure)
                coord_num = len(neighbors)
                
                if radius not in site_radii:
                    site_radii[radius] = []
                site_radii[radius].append((coord_num, radii.get(radius, radii.get(str(site.species), 0))))
            except Exception as e:
                logger.warning(f"Error processing site {site}: {e}")
                continue

        # Classify sites based on coordination
        # A-site: typically 12-coordinated (or highest coordination)
        # B-site: typically 6-coordinated
        # X-site: typically 2-6 coordinated (anion)
        
        if not site_radii:
            return np.nan

        # Find species with highest average coordination (A-site)
        avg_coords = {}
        for sp, coords in site_radii.items():
            if coords:
                avg_coords[sp] = sum(c[0] for c in coords) / len(coords)

        if not avg_coords:
            return np.nan

        sorted_species = sorted(avg_coords.items(), key=lambda x: x[1], reverse=True)
        
        if len(sorted_species) < 3:
            logger.warning("Could not identify all three sites")
            return np.nan

        # Assign sites
        a_species = sorted_species[0][0]
        b_species = sorted_species[1][0]
        x_species = sorted_species[2][0]

        # Get representative radii
        r_a = site_radii[a_species][0][1] if site_radii[a_species] else 0
        r_b = site_radii[b_species][0][1] if site_radii[b_species] else 0
        r_x = site_radii[x_species][0][1] if site_radii[x_species] else 0

        if r_b + r_x == 0:
            return np.nan

        # Goldschmidt tolerance factor
        t = (r_a + r_x) / (np.sqrt(2) * (r_b + r_x))
        return float(t)

    except Exception as e:
        logger.error(f"Error calculating tolerance factor: {e}")
        return np.nan


def calculate_octahedral_tilting_angles(
    structure: Structure,
    b_species: Optional[str] = None,
    x_species: Optional[str] = None
) -> Dict[str, float]:
    """
    Calculate octahedral tilting angles from the B-X-B bond angles.

    In an ideal perovskite, B-X-B angles are 180°. Tilting reduces this angle.

    Args:
        structure: pymatgen Structure object
        b_species: Name of the B-site species (optional, auto-detected if None)
        x_species: Name of the X-site species (optional, auto-detected if None)

    Returns:
        dict: Dictionary with 'mean_angle', 'std_angle', 'min_angle', 'max_angle'
    """
    try:
        # Auto-detect B and X species if not provided
        if b_species is None or x_species is None:
            # Use coordination analysis to identify sites
            nn = VoronoiNN()
            site_info = {}
            
            for site in structure.sites:
                try:
                    sp_str = str(site.species_string)
                    neighbors = nn.get_nn(site, structure)
                    coord_num = len(neighbors)
                    
                    if sp_str not in site_info:
                        site_info[sp_str] = {'coord_nums': [], 'sites': []}
                    site_info[sp_str]['coord_nums'].append(coord_num)
                    site_info[sp_str]['sites'].append(site)
                except Exception:
                    continue

            # B-site: typically 6-coordinated
            # X-site: typically 2-6 coordinated
            
            b_candidates = []
            x_candidates = []
            
            for sp, info in site_info.items():
                avg_coord = np.mean(info['coord_nums'])
                if 5 <= avg_coord <= 7:
                    b_candidates.append((sp, avg_coord))
                elif 2 <= avg_coord <= 6:
                    x_candidates.append((sp, avg_coord))

            # Sort by coordination number
            b_candidates.sort(key=lambda x: x[1])
            x_candidates.sort(key=lambda x: x[1])

            if b_candidates:
                b_species = b_candidates[0][0]
            if x_candidates:
                x_species = x_candidates[-1][0]  # X-site often has lower coordination

        if not b_species or not x_species:
            logger.warning("Could not identify B and X species")
            return {'mean_angle': np.nan, 'std_angle': np.nan, 'min_angle': np.nan, 'max_angle': np.nan}

        # Find B-X-B angles
        angles = []
        b_sites = [s for s in structure.sites if str(s.species_string) == b_species]
        x_sites = [s for s in structure.sites if str(s.species_string) == x_species]

        nn = VoronoiNN()

        for x_site in x_sites:
            x_neighbors = nn.get_nn(x_site, structure)
            b_neighbors = [n for n in x_neighbors if str(n.species_string) == b_species]
            
            if len(b_neighbors) >= 2:
                # Calculate angles between B-X-B
                for i in range(len(b_neighbors)):
                    for j in range(i + 1, len(b_neighbors)):
                        # Get vectors
                        v1 = b_neighbors[i].coords - x_site.coords
                        v2 = b_neighbors[j].coords - x_site.coords
                        
                        # Calculate angle
                        dot_product = np.dot(v1, v2)
                        norm1 = np.linalg.norm(v1)
                        norm2 = np.linalg.norm(v2)
                        
                        if norm1 > 0 and norm2 > 0:
                            cos_angle = dot_product / (norm1 * norm2)
                            # Clamp to [-1, 1] to avoid numerical issues
                            cos_angle = np.clip(cos_angle, -1.0, 1.0)
                            angle = np.degrees(np.arccos(cos_angle))
                            angles.append(angle)

        if not angles:
            logger.warning("No B-X-B angles found")
            return {'mean_angle': np.nan, 'std_angle': np.nan, 'min_angle': np.nan, 'max_angle': np.nan}

        return {
            'mean_angle': float(np.mean(angles)),
            'std_angle': float(np.std(angles)),
            'min_angle': float(np.min(angles)),
            'max_angle': float(np.max(angles))
        }

    except Exception as e:
        logger.error(f"Error calculating octahedral tilting angles: {e}")
        return {'mean_angle': np.nan, 'std_angle': np.nan, 'min_angle': np.nan, 'max_angle': np.nan}


def calculate_bond_length_variance(
    structure: Structure,
    b_species: Optional[str] = None,
    x_species: Optional[str] = None
) -> Dict[str, float]:
    """
    Calculate the variance of B-X bond lengths.

    In an ideal perovskite, all B-X bonds are equal. Variance indicates distortion.

    Args:
        structure: pymatgen Structure object
        b_species: Name of the B-site species (optional)
        x_species: Name of the X-site species (optional)

    Returns:
        dict: Dictionary with 'mean_length', 'std_length', 'variance', 'min_length', 'max_length'
    """
    try:
        # Auto-detect if not provided
        if b_species is None or x_species is None:
            nn = VoronoiNN()
            site_info = {}
            
            for site in structure.sites:
                try:
                    sp_str = str(site.species_string)
                    neighbors = nn.get_nn(site, structure)
                    coord_num = len(neighbors)
                    
                    if sp_str not in site_info:
                        site_info[sp_str] = {'coord_nums': [], 'sites': []}
                    site_info[sp_str]['coord_nums'].append(coord_num)
                    site_info[sp_str]['sites'].append(site)
                except Exception:
                    continue

            b_candidates = []
            x_candidates = []
            
            for sp, info in site_info.items():
                avg_coord = np.mean(info['coord_nums'])
                if 5 <= avg_coord <= 7:
                    b_candidates.append((sp, avg_coord))
                elif 2 <= avg_coord <= 6:
                    x_candidates.append((sp, avg_coord))

            b_candidates.sort(key=lambda x: x[1])
            x_candidates.sort(key=lambda x: x[1])

            if b_candidates:
                b_species = b_candidates[0][0]
            if x_candidates:
                x_species = x_candidates[-1][0]

        if not b_species or not x_species:
            logger.warning("Could not identify B and X species")
            return {'mean_length': np.nan, 'std_length': np.nan, 'variance': np.nan, 'min_length': np.nan, 'max_length': np.nan}

        # Find all B-X bond lengths
        bond_lengths = []
        b_sites = [s for s in structure.sites if str(s.species_string) == b_species]
        
        nn = VoronoiNN()

        for b_site in b_sites:
            neighbors = nn.get_nn(b_site, structure)
            for neighbor in neighbors:
                if str(neighbor.species_string) == x_species:
                    distance = b_site.distance(neighbor)
                    bond_lengths.append(distance)

        if not bond_lengths:
            logger.warning("No B-X bonds found")
            return {'mean_length': np.nan, 'std_length': np.nan, 'variance': np.nan, 'min_length': np.nan, 'max_length': np.nan}

        mean_length = np.mean(bond_lengths)
        variance = np.var(bond_lengths)
        std_length = np.sqrt(variance)

        return {
            'mean_length': float(mean_length),
            'std_length': float(std_length),
            'variance': float(variance),
            'min_length': float(np.min(bond_lengths)),
            'max_length': float(np.max(bond_lengths))
        }

    except Exception as e:
        logger.error(f"Error calculating bond length variance: {e}")
        return {'mean_length': np.nan, 'std_length': np.nan, 'variance': np.nan, 'min_length': np.nan, 'max_length': np.nan}


def calculate_unit_cell_volume(structure: Structure) -> float:
    """
    Calculate the unit cell volume.

    Args:
        structure: pymatgen Structure object

    Returns:
        float: Unit cell volume in Angstrom^3
    """
    try:
        return float(structure.volume)
    except Exception as e:
        logger.error(f"Error calculating unit cell volume: {e}")
        return np.nan


def compute_all_descriptors(structure: Structure) -> Dict[str, float]:
    """
    Compute all descriptors for a single structure.

    Args:
        structure: pymatgen Structure object

    Returns:
        dict: Dictionary with all computed descriptors
    """
    descriptors = {}

    # Tolerance factor
    descriptors['tolerance_factor'] = calculate_tolerance_factor(structure)

    # Octahedral tilting angles
    tilting = calculate_octahedral_tilting_angles(structure)
    descriptors['tilting_mean_angle'] = tilting['mean_angle']
    descriptors['tilting_std_angle'] = tilting['std_angle']
    descriptors['tilting_min_angle'] = tilting['min_angle']
    descriptors['tilting_max_angle'] = tilting['max_angle']

    # Bond length variance
    bond_var = calculate_bond_length_variance(structure)
    descriptors['bond_length_mean'] = bond_var['mean_length']
    descriptors['bond_length_std'] = bond_var['std_length']
    descriptors['bond_length_variance'] = bond_var['variance']
    descriptors['bond_length_min'] = bond_var['min_length']
    descriptors['bond_length_max'] = bond_var['max_length']

    # Unit cell volume
    descriptors['unit_cell_volume'] = calculate_unit_cell_volume(structure)

    return descriptors


def process_dataframe(
    df: pd.DataFrame,
    structure_column: str = 'structure',
    output_path: Optional[Union[str, Path]] = None
) -> pd.DataFrame:
    """
    Process a DataFrame of structures and compute descriptors.

    Args:
        df: DataFrame with a column containing pymatgen Structure objects or JSON strings
        structure_column: Name of the column containing structures
        output_path: Optional path to save the results

    Returns:
        pd.DataFrame: Original DataFrame with added descriptor columns
    """
    logger.info(f"Processing {len(df)} structures for descriptor calculation")

    descriptors_list = []
    failed_count = 0

    for idx, row in df.iterrows():
        try:
            structure_data = row[structure_column]
            
            # Handle different input formats
            if isinstance(structure_data, Structure):
                structure = structure_data
            elif isinstance(structure_data, str):
                # Try to parse as JSON
                try:
                    structure = Structure.from_str(structure_data, fmt='json')
                except Exception:
                    logger.warning(f"Failed to parse structure at index {idx} as JSON")
                    descriptors_list.append({})
                    failed_count += 1
                    continue
            else:
                logger.warning(f"Unknown structure format at index {idx}")
                descriptors_list.append({})
                failed_count += 1
                continue

            # Compute descriptors
            descriptors = compute_all_descriptors(structure)
            descriptors_list.append(descriptors)

        except Exception as e:
            logger.warning(f"Error processing structure at index {idx}: {e}")
            descriptors_list.append({})
            failed_count += 1

    # Create DataFrame of descriptors
    desc_df = pd.DataFrame(descriptors_list)

    # Merge with original DataFrame
    result_df = pd.concat([df.reset_index(drop=True), desc_df], axis=1)

    logger.info(f"Successfully computed descriptors for {len(df) - failed_count} structures")
    logger.info(f"Failed to compute descriptors for {failed_count} structures")

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result_df.to_csv(output_path, index=False)
        logger.info(f"Saved descriptors to {output_path}")

    return result_df


def main():
    """
    Main entry point for descriptor computation.
    """
    import argparse

    parser = argparse.ArgumentParser(description='Compute crystallographic descriptors for perovskites')
    parser.add_argument('--input', type=str, required=True, help='Input CSV file with structures')
    parser.add_argument('--output', type=str, required=True, help='Output CSV file for descriptors')
    parser.add_argument('--structure-column', type=str, default='structure', help='Name of structure column')
    parser.add_argument('--log-level', type=str, default='INFO', help='Logging level')

    args = parser.parse_args()

    # Set logging level
    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    setup_logger(__name__, log_level)

    # Load input data
    logger.info(f"Loading data from {args.input}")
    try:
        df = pd.read_csv(args.input)
    except Exception as e:
        handle_error(f"Failed to load input file: {e}", "CRITICAL")
        sys.exit(1)

    # Check for structure column
    if args.structure_column not in df.columns:
        handle_error(f"Structure column '{args.structure_column}' not found in input file", "CRITICAL")
        sys.exit(1)

    # Compute descriptors
    result_df = process_dataframe(
        df,
        structure_column=args.structure_column,
        output_path=args.output
    )

    logger.info("Descriptor computation completed successfully")


if __name__ == '__main__':
    main()
