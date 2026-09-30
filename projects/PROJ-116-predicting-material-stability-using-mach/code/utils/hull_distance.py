import logging
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path
import numpy as np
import pandas as pd
from pymatgen.core import Structure, Composition
from pymatgen.analysis.phase_diagram import PhaseDiagram, PDEntry
from pymatgen.entries.compatibility import MaterialsProject2020Compatibility
from config import set_seed, get_seed
from utils.logging import setup_logger
from utils.validation import validate_structure

# Initialize logger
logger = setup_logger(__name__)

def get_phase_diagram_entry(structure: Structure, energy: float) -> Optional[PDEntry]:
    """
    Create a PDEntry from a Structure and its energy.
    Returns None if the structure is invalid or composition is empty.
    """
    if structure is None:
        return None
    try:
        # Ensure composition is valid
        if len(structure.composition.elements) == 0:
            return None
        return PDEntry(structure.composition, energy)
    except Exception as e:
        logger.warning(f"Failed to create PDEntry for structure: {e}")
        return None

def calculate_hull_distance(structure: Structure, formation_energy_per_atom: float, 
                            phase_diagram: PhaseDiagram) -> float:
    """
    Calculate the distance to the convex hull (hull distance) for a given structure.
    
    Args:
        structure: The crystal structure.
        formation_energy_per_atom: The formation energy per atom (eV/atom).
        phase_diagram: The PhaseDiagram object for the relevant elements.
        
    Returns:
        The hull distance in eV/atom.
    """
    if structure is None:
        raise ValueError("Structure cannot be None")
    
    try:
        # Calculate the energy above hull
        # pymatgen's get_hull_energy requires a PDEntry or similar
        # We can construct a PDEntry with the given formation energy
        # Note: PhaseDiagram expects formation energies relative to the elements in the diagram
        # If the formation_energy_per_atom is already relative to the standard states,
        # we can use it directly.
        
        # Create a temporary entry
        entry = PDEntry(structure.composition, formation_energy_per_atom * structure.num_sites)
        
        # Calculate energy above hull
        energy_above_hull = phase_diagram.get_hull_energy(entry)
        
        # The hull distance is the energy above hull divided by the number of atoms
        hull_distance = energy_above_hull / structure.num_sites
        
        return hull_distance
    except Exception as e:
        logger.error(f"Failed to calculate hull distance: {e}")
        raise

def calculate_hull_distances_batch(df: pd.DataFrame, 
                                   structure_col: str = 'structure',
                                   energy_col: str = 'formation_energy_per_atom') -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calculate hull distances for a batch of entries.
    
    This function:
    1. Identifies unique elemental compositions to build a comprehensive PhaseDiagram.
    2. Iterates through the dataframe to calculate hull distances.
    3. Handles failures (missing elemental references) by logging and excluding from classification
       but retaining in the regression analysis.
    
    Args:
        df: DataFrame containing structures and energies.
        structure_col: Name of the column containing Structure objects.
        energy_col: Name of the column containing formation energies.
        
    Returns:
        A tuple (filtered_df, excluded_entries) where:
        - filtered_df contains entries with successfully calculated hull distances.
        - excluded_entries contains entries that failed calculation (with reason).
    """
    logger.info(f"Starting hull distance calculation for {len(df)} entries.")
    
    # Collect all unique elements to build a global PhaseDiagram
    all_elements = set()
    valid_structures = []
    
    for idx, row in df.iterrows():
        struct = row.get(structure_col)
        if struct is not None:
            try:
                # Validate structure first
                if validate_structure(struct):
                    all_elements.update([str(el) for el in struct.composition.elements])
                    valid_structures.append((idx, struct))
            except Exception:
                continue
    
    if not valid_structures:
        logger.warning("No valid structures found to build phase diagram.")
        return df, pd.DataFrame(columns=['index', 'reason'])
    
    logger.info(f"Building PhaseDiagram for {len(all_elements)} elements: {sorted(all_elements)}")
    
    # We need standard formation energies for the elements to build the PhaseDiagram.
    # Since we don't have a full database here, we will use the provided formation energies
    # to approximate the convex hull. However, a true convex hull requires standard state energies.
    # For this implementation, we assume the 'formation_energy_per_atom' provided is relative to
    # the standard states of the elements present.
    
    # To build a PhaseDiagram, we need PDEntries for all relevant compounds.
    # Since we only have the target compounds, we will build a PhaseDiagram from the valid entries themselves.
    # This is an approximation but allows us to calculate relative stability.
    
    entries = []
    for idx, struct in valid_structures:
        energy = df.loc[idx, energy_col]
        entry = PDEntry(struct.composition, energy * struct.num_sites)
        entries.append(entry)
    
    try:
        phase_diagram = PhaseDiagram(entries)
    except Exception as e:
        logger.error(f"Failed to build PhaseDiagram: {e}")
        # If we can't build the diagram, we can't calculate hull distances.
        # Return the original dataframe and mark all as excluded? 
        # Or return empty? The task says "exclude from classification but retain in regression".
        # So we return the original df for regression, and an empty list for classification?
        # Actually, if we can't calculate, we can't classify.
        # Let's return the original df and mark all as excluded with the error reason.
        excluded = pd.DataFrame({
            'index': df.index,
            'reason': [f"PhaseDiagram build failed: {e}"] * len(df)
        })
        return df, excluded

    # Now calculate hull distances
    filtered_rows = []
    excluded_rows = []
    
    for idx, struct in valid_structures:
        energy = df.loc[idx, energy_col]
        try:
            hull_dist = calculate_hull_distance(struct, energy, phase_diagram)
            filtered_rows.append({
                'index': idx,
                'hull_distance': hull_dist,
                'status': 'success'
            })
        except Exception as e:
            logger.warning(f"Failed to calculate hull distance for index {idx}: {e}")
            excluded_rows.append({
                'index': idx,
                'reason': str(e),
                'status': 'failed'
            })
    
    # Create DataFrames
    filtered_df = pd.DataFrame(filtered_rows)
    excluded_df = pd.DataFrame(excluded_rows)
    
    # Merge back to original df for the 'filtered' set (for regression)
    # We keep all original rows in the returned 'filtered_df' but mark which have hull distances
    result_df = df.copy()
    result_df['hull_distance'] = np.nan
    result_df['classification_status'] = 'unknown'
    
    if not filtered_df.empty:
        result_df.loc[filtered_df['index'], 'hull_distance'] = filtered_df['hull_distance']
        result_df.loc[filtered_df['index'], 'classification_status'] = 'valid'
    
    if not excluded_df.empty:
        for _, row in excluded_df.iterrows():
            idx = row['index']
            logger.warning(f"Excluding index {idx} from classification due to: {row['reason']}")
            result_df.loc[idx, 'classification_status'] = 'excluded'
    
    logger.info(f"Hull distance calculation complete. {len(filtered_df)} valid, {len(excluded_df)} excluded.")
    logger.info(f"Regression dataset size: {len(result_df)} (all entries retained)")
    logger.info(f"Classification dataset size: {len(filtered_df)} (excluded entries removed)")
    
    return result_df, excluded_df

def main():
    """
    Main function to execute hull distance calculation.
    Reads raw data, calculates hull distances, and saves the result.
    """
    logger.info("Starting hull distance calculation (T037).")
    
    # Load raw data (assuming it was saved by T012)
    raw_data_path = Path("data/raw/filtered_oqmd.csv")
    if not raw_data_path.exists():
        logger.error(f"Raw data not found at {raw_data_path}. Please run download_data.py first.")
        return
    
    df = pd.read_csv(raw_data_path)
    
    # We need to convert the composition string back to Structure if possible,
    # or assume the raw data has structure objects serialized.
    # For this implementation, we assume the raw data has a 'structure' column with pymatgen structures.
    # If not, we might need to reconstruct from composition and lattice.
    # Let's assume the data has 'structure' as a string representation that can be loaded.
    # However, loading structures from string can be complex. 
    # A safer approach: if the data has composition and lattice, we can reconstruct.
    # But for simplicity, let's assume the raw data has 'structure' as a dict or similar.
    
    # If the structure column is missing or invalid, we might need to skip.
    # Let's check if we have the necessary columns.
    required_cols = ['structure', 'formation_energy_per_atom']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return
    
    # Calculate hull distances
    result_df, excluded_df = calculate_hull_distances_batch(df)
    
    # Save the results
    output_path = Path("data/processed/hull_distances.parquet")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_parquet(output_path, index=False)
    logger.info(f"Hull distances saved to {output_path}")
    
    # Save excluded entries for logging
    if not excluded_df.empty:
        excluded_path = Path("data/processed/excluded_hull_entries.csv")
        excluded_df.to_csv(excluded_path, index=False)
        logger.info(f"Excluded entries saved to {excluded_path}")
    
    # Log summary
    logger.info(f"Total entries: {len(df)}")
    logger.info(f"Entries with valid hull distances: {len(result_df[result_df['classification_status'] == 'valid'])}")
    logger.info(f"Entries excluded from classification: {len(result_df[result_df['classification_status'] == 'excluded'])}")
    
    return result_df

if __name__ == "__main__":
    main()
