"""
Microbiome data model for the Gut Microbiome-Cognitive Correlation Study.

Represents taxonomic abundance data and associated metadata for microbiome
samples, including processing status and quality control metrics.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
import pandas as pd
import numpy as np

@dataclass
class MicrobiomeProfile:
    """
    Represents a microbiome sample profile with taxonomic abundances.
    
    Attributes:
        participant_id: Link to the Participant (UK Biobank e.g., 'eid')
        sample_id: Unique sample identifier
        collection_date: Date of sample collection
        sequencing_depth: Total reads/sequences in the sample
        taxonomy_level: Taxonomic level of data (e.g., 'genus', 'species')
        abundances: Dictionary mapping taxon names to abundance values
        zero_replaced: Whether Bayesian multiplicative zero-replacement was applied
        ilr_transformed: Whether Isometric Log-Ratio transformation was applied
        ilr_coordinates: Dictionary of ILR-transformed coordinates
        quality_score: Sample quality metric (e.g., Shannon diversity, read depth)
        contamination_flag: Flag for potential contamination
        batch_id: Sequencing batch identifier
    """
    participant_id: str
    sample_id: str
    collection_date: Optional[str] = None
    sequencing_depth: Optional[int] = None
    taxonomy_level: str = 'genus'
    abundances: Dict[str, float] = field(default_factory=dict)
    zero_replaced: bool = False
    ilr_transformed: bool = False
    ilr_coordinates: Dict[str, float] = field(default_factory=dict)
    quality_score: Optional[float] = None
    contamination_flag: bool = False
    batch_id: Optional[str] = None
    
    def __post_init__(self):
        """Validate microbiome data after initialization."""
        if self.abundances and not self.zero_replaced and not self.ilr_transformed:
            # Check for zeros that might cause log transformation issues
            zero_count = sum(1 for v in self.abundances.values() if v == 0)
            if zero_count > 0:
                # Log warning but don't fail - zero-replacement should handle this
                pass
    
    def get_taxa(self) -> List[str]:
        """Return list of taxon names present in the profile."""
        return list(self.abundances.keys())
    
    def get_abundances_array(self) -> np.ndarray:
        """Return abundances as a numpy array in consistent order."""
        taxa = sorted(self.abundances.keys())
        return np.array([self.abundances[t] for t in taxa])
    
    def get_ilr_array(self) -> np.ndarray:
        """Return ILR coordinates as a numpy array in consistent order."""
        taxa = sorted(self.ilr_coordinates.keys())
        return np.array([self.ilr_coordinates[t] for t in taxa])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary representation."""
        return {
            'participant_id': self.participant_id,
            'sample_id': self.sample_id,
            'collection_date': self.collection_date,
            'sequencing_depth': self.sequencing_depth,
            'taxonomy_level': self.taxonomy_level,
            'abundances': self.abundances,
            'zero_replaced': self.zero_replaced,
            'ilr_transformed': self.ilr_transformed,
            'ilr_coordinates': self.ilr_coordinates,
            'quality_score': self.quality_score,
            'contamination_flag': self.contamination_flag,
            'batch_id': self.batch_id
        }
    
    @classmethod
    def from_row(cls, row: pd.Series) -> 'MicrobiomeProfile':
        """
        Create a MicrobiomeProfile instance from a pandas Series row.
        
        Args:
            row: pandas Series containing microbiome data
            
        Returns:
            MicrobiomeProfile instance
        """
        # Handle abundances which might be stored as a JSON string or dict
        abundances = row.get('abundances', {})
        if isinstance(abundances, str):
            import json
            abundances = json.loads(abundances)
        
        ilr_coords = row.get('ilr_coordinates', {})
        if isinstance(ilr_coords, str):
            import json
            ilr_coords = json.loads(ilr_coords)
        
        return cls(
            participant_id=str(row.get('participant_id', row.get('eid', ''))),
            sample_id=str(row.get('sample_id', '')),
            collection_date=row.get('collection_date', None),
            sequencing_depth=int(row.get('sequencing_depth', None)) if pd.notna(row.get('sequencing_depth', None)) else None,
            taxonomy_level=row.get('taxonomy_level', 'genus'),
            abundances=abundances if abundances else {},
            zero_replaced=bool(row.get('zero_replaced', False)),
            ilr_transformed=bool(row.get('ilr_transformed', False)),
            ilr_coordinates=ilr_coords if ilr_coords else {},
            quality_score=row.get('quality_score', None),
            contamination_flag=bool(row.get('contamination_flag', False)),
            batch_id=row.get('batch_id', None)
        )
    
    @classmethod
    def from_dataframe(cls, df: pd.DataFrame) -> List['MicrobiomeProfile']:
        """
        Create a list of MicrobiomeProfile instances from a DataFrame.
        
        Args:
            df: DataFrame with microbiome data
            
        Returns:
            List of MicrobiomeProfile instances
        """
        return [cls.from_row(row) for _, row in df.iterrows()]

def create_microbiome_dataframe(profiles: List[MicrobiomeProfile]) -> pd.DataFrame:
    """
    Convert a list of MicrobiomeProfile instances to a DataFrame.
    
    Args:
        profiles: List of MicrobiomeProfile instances
        
    Returns:
        DataFrame with microbiome data
    """
    data = []
    for p in profiles:
        row = p.to_dict()
        # Flatten abundances and ilr_coordinates for storage
        for taxon, val in p.abundances.items():
            row[f'abundance_{taxon}'] = val
        for taxon, val in p.ilr_coordinates.items():
            row[f'ilr_{taxon}'] = val
        # Remove nested dicts
        row.pop('abundances')
        row.pop('ilr_coordinates')
        data.append(row)
    return pd.DataFrame(data)
