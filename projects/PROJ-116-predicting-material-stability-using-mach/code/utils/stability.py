"""
Utilities for calculating convex hull distances and stability metrics using pymatgen.

This module implements the logic for User Story 3: Metastable Phase Classification.
"""
import logging
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path

import numpy as np
from pymatgen.core import Structure, Composition
from pymatgen.analysis.phase_diagram import PhaseDiagram, PDEntry
from pymatgen.ext.matproj import MPRester
from pymatgen.analysis.stability import StabilityAnalysis

# Import config for API keys if needed, or use environment variables
from config import get_seed

logger = logging.getLogger(__name__)

def get_phase_diagram_entries(composition: Composition, api_key: Optional[str] = None) -> List[PDEntry]:
    """
    Fetches elemental entries and relevant phase diagram data for a given composition.
    
    Args:
        composition: The chemical composition of the material.
        api_key: MP API key. If None, it attempts to use the environment variable MP_API_KEY.
                
    Returns:
        A list of PDEntry objects required to construct the PhaseDiagram.
        
    Raises:
        ValueError: If the composition contains elements not found in the database.
    """
    elements = composition.elements
    element_compositions = [Composition(el.symbol) for el in elements]
    
    # Try to get entries from MPRester
    # Note: In a real pipeline, we might cache these or use a local database
    # to avoid repeated API calls. For this implementation, we fetch on demand.
    try:
        # If api_key is not provided, MPRester will look for MP_API_KEY env var
        # and fail if not found.
        mpr = MPRester(api_key)
        
        # Get all entries for the elements involved
        # We need the elemental energies to form the hull
        entries = []
        for elem_comp in element_compositions:
            # Fetch entries for this element
            elem_entries = mpr.get_entries_in_chemsys([elem_comp.reduced_formula])
            # Filter for the pure element entry (energy per atom is usually lowest for pure element)
            # Actually, we just need the elemental reference energy.
            # MPRester returns a list of entries. We look for the one with composition == element.
            for entry in elem_entries:
                if entry.composition.reduced_formula == elem_comp.reduced_formula:
                    entries.append(entry)
                    break
            
        # Also fetch entries for known stable compounds in the system to build the hull
        # This is tricky without knowing the system. 
        # A robust approach is to use the full chemical system of the composition.
        chemsys = "-".join(sorted([el.symbol for el in elements]))
        all_entries = mpr.get_entries_in_chemsys(chemsys)
        
        # We only need the entries that are relevant to the hull. 
        # The PhaseDiagram constructor handles this, but we need to pass the entries.
        # However, fetching ALL entries for a complex system can be huge.
        # For the purpose of this task, we will assume we are fetching the minimal set
        # or using a pre-computed PhaseDiagram if available.
        # Given the constraints, we will fetch the full system entries.
        
        return all_entries
        
    except Exception as e:
        logger.error(f"Failed to fetch phase diagram entries for {composition}: {e}")
        raise ValueError(f"Could not retrieve phase diagram data for {composition}. "
                         "Ensure MP_API_KEY is set or the element is in the database.")

def calculate_hull_distance(
    structure: Structure, 
    api_key: Optional[str] = None,
    use_cached: bool = True
) -> Optional[float]:
    """
    Calculates the energy above the convex hull (eV/atom) for a given structure.
    
    This function handles cases where pymatgen fails due to missing elemental references
    by returning None and logging the reason.
    
    Args:
        structure: The pymatgen Structure object.
        api_key: MP API key.
        use_cached: Whether to use a cached PhaseDiagram if available (future enhancement).
                    
    Returns:
        The energy above the hull in eV/atom, or None if calculation failed.
    """
    try:
        # Get composition
        comp = structure.composition
        
        # Fetch entries
        entries = get_phase_diagram_entries(comp, api_key)
        
        if not entries:
            logger.warning(f"No entries found for composition {comp}. Skipping hull distance calculation.")
            return None
        
        # Construct PhaseDiagram
        pd = PhaseDiagram(entries)
        
        # Calculate energy above hull
        # get_e_above_hull returns the energy above the hull in eV/atom
        e_above_hull = pd.get_e_above_hull(comp)
        
        return float(e_above_hull)
        
    except Exception as e:
        # Log the specific error and return None
        logger.warning(f"Failed to calculate hull distance for {structure.composition}: {e}")
        return None

def classify_stability(
    hull_distance: float, 
    threshold: float = 0.05
) -> str:
    """
    Classifies a material as 'stable' or 'metastable' based on its hull distance.
    
    Args:
        hull_distance: Energy above hull in eV/atom.
        threshold: The cutoff for metastability (default 0.05 eV/atom).
        
    Returns:
        'stable' if distance <= 0.00
        'metastable' if 0.00 < distance <= threshold
        'unstable' if distance > threshold
    """
    if hull_distance <= 0.0:
        return "stable"
    elif hull_distance <= threshold:
        return "metastable"
    else:
        return "unstable"

def calculate_hull_distances_batch(
    structures: List[Structure],
    api_key: Optional[str] = None
) -> Tuple[List[Optional[float]], int]:
    """
    Calculates hull distances for a list of structures.
    
    Args:
        structures: List of pymatgen Structure objects.
        api_key: MP API key.
        
    Returns:
        A tuple containing:
            - List of hull distances (None for failed entries)
            - Count of skipped entries
    """
    distances = []
    skipped_count = 0
    
    for struct in structures:
        dist = calculate_hull_distance(struct, api_key)
        if dist is None:
            skipped_count += 1
        distances.append(dist)
        
    return distances, skipped_count
