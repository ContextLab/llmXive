"""
Utility functions for feature engineering and analysis.
"""
import logging
from typing import List

logger = logging.getLogger(__name__)

def identify_local_features(feature_names: List[str]) -> List[str]:
    """
    Identify columns that correspond to local coordination features.
    Based on T020, these are Voronoi stats and bond-length histograms.
    """
    local_keywords = [
        'voronoi', 'coordination', 'face_area', 'solid_angle',
        'bond_length', 'histogram', 'local'
    ]
    local_features = []
    for col in feature_names:
        if any(kw in col.lower() for kw in local_keywords):
            local_features.append(col)
    return local_features