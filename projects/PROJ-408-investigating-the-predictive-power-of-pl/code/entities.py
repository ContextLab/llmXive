"""
Base entity dataclasses.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Union
from pathlib import Path
import numpy as np

@dataclass
class PlantSpecies:
    name: str
    taxonomy_id: Optional[str] = None
    common_name: Optional[str] = None

@dataclass
class PhylogeneticTree:
    newick_string: str
    species: List[str]
    root: Optional[str] = None

@dataclass
class MetaboliteProfile:
    species: str
    compounds: Set[str]
    source: str = "KEGG"

@dataclass
class DistanceMatrix:
    species: List[str]
    values: np.ndarray  # Square matrix

    def get_subset_matrix(self, subset_species: List[str]) -> 'DistanceMatrix':
        """Return a new matrix containing only rows/cols for subset_species."""
        # Map species to index
        idx_map = {s: i for i, s in enumerate(self.species)}
        indices = [idx_map[s] for s in subset_species]
        
        new_matrix = self.values[np.ix_(indices, indices)]
        return DistanceMatrix(
            species=subset_species,
            values=new_matrix
        )
