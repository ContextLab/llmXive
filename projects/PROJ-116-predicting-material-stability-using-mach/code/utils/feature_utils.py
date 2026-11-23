import logging
from typing import List

def identify_local_features(feature_names: List[str]) -> List[str]:
    """
    Identify features that represent local coordination environments.

    Args:
        feature_names: List of all feature names

    Returns:
        List of local coordination feature names
    """
    local_feature_keywords = [
        'coordination', 'voronoi', 'bond_length', 'solid_angle',
        'face_area', 'nearest_neighbor', 'local'
    ]

    local_features = []
    for name in feature_names:
        if any(keyword in name.lower() for keyword in local_feature_keywords):
            local_features.append(name)

    return local_features
