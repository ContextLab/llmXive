"""
Atlas loading and mapping utilities.
Handles Schaefer atlas and Yeo network parcellation.
"""
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
from pathlib import Path
import requests
from io import StringIO

# URL for Schaefer-400 atlas (400 ROIs, 7 networks)
# Using the Schaefer2018_400Parcels_7Networks_N1000.txt from the Schaefer atlas repository
SCHAEFER_ATLAS_URL = (
    "https://raw.githubusercontent.com/ThomasYeoLab/CBIG/v0.14.3/stable_projects/brain_parcellation/"
    "Schaefer2018_LocalGlobal/Parcels/MNI/Schaefer2018_400Parcels_7Networks_order_FSLMNI152_2mm.txt"
)
# URL for Yeo 7-network labels
YEO_7_NETWORKS_URL = (
    "https://raw.githubusercontent.com/ThomasYeoLab/CBIG/v0.14.3/stable_projects/brain_parcellation/"
    "Schaefer2018_LocalGlobal/Parcels/MNI/Schaefer2018_400Parcels_7Networks_order_FSLMNI152_2mm.txt"
)

# Mapping of network IDs to network names based on Yeo 7-network parcellation
# The Schaefer atlas uses the following network order:
# 1: Visual, 2: SomatoMotor, 3: Dorsal Attention, 4: Salience/Ventral Attention,
# 5: Limbic, 6: Frontoparietal, 7: Default Mode
# We map these to the specific networks of interest:
# DMN (Default Mode Network) -> 7
# Auditory (often part of Salience or SomatoMotor, but we map to Salience/Ventral Attention for this study) -> 4
# Salience -> 4 (Salience/Ventral Attention)
# Note: The prompt specifies Auditory=4, Salience=2. We will adjust the mapping to match the prompt's specific requirements
# if the standard mapping doesn't align, or we will assume the prompt's mapping is the ground truth for this project.
# Standard Yeo 7-network mapping:
# 1: Visual, 2: SomatoMotor, 3: Dorsal Attention, 4: Ventral Attention (Salience), 5: Limbic, 6: Frontoparietal, 7: Default Mode
# The prompt asks for: DMN=7, Auditory=4, Salience=2.
# This implies a specific mapping where:
# 7 -> DMN
# 4 -> Auditory (Note: In standard Yeo, 4 is Salience/Ventral Attention. We will follow the prompt's explicit mapping).
# 2 -> Salience (Note: In standard Yeo, 2 is SomatoMotor. We will follow the prompt's explicit mapping).
# We will create a custom mapping function to satisfy the task's explicit requirement.

def load_atlas() -> pd.DataFrame:
    """
    Loads the Schaefer-400 atlas and returns a DataFrame with ROI IDs and network labels.

    Returns:
        pd.DataFrame: DataFrame with columns ['roi_id', 'network_id', 'network_name']
    """
    try:
        response = requests.get(SCHAEFER_ATLAS_URL, timeout=30)
        response.raise_for_status()
        # The file contains ROI IDs and network labels
        # We parse it manually or use pandas if structured
        content = response.text
        lines = content.strip().split('\n')
        
        data = []
        for i, line in enumerate(lines):
            if line.startswith('#') or not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 2:
                roi_id = f"roi_{i+1:04d}"
                network_id = int(parts[1]) if len(parts) > 1 else 0
                data.append({'roi_id': roi_id, 'network_id': network_id})
        
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        # Fallback to a generated atlas if download fails (for testing purposes only, 
        # but in real execution this should fail loudly as per constraints)
        # For the purpose of this task, we assume the download works or we use a local file if available.
        # Since we cannot guarantee external access in all environments, we will try to load from a local file first.
        local_path = Path("data/raw/schaefer_atlas.txt")
        if local_path.exists():
            df = pd.read_csv(local_path, delim_whitespace=True, header=None, names=['roi_id', 'network_id'])
            df['roi_id'] = [f"roi_{i+1:04d}" for i in range(len(df))]
            return df
        else:
            raise RuntimeError(f"Could not load atlas from URL or local file: {e}")

def map_to_yeo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Maps the atlas network IDs to the Yeo 7-network parcellation names.
    Specifically maps to the networks of interest: DMN, Auditory, Salience.
    
    The mapping is defined as:
    - Network 7 -> DMN
    - Network 4 -> Auditory (as per task requirement)
    - Network 2 -> Salience (as per task requirement)
    
    Args:
        df: DataFrame from load_atlas()
        
    Returns:
        pd.DataFrame: DataFrame with an additional 'network_name' column
    """
    # Define the mapping based on the task requirements
    network_mapping = {
        7: "DMN",
        4: "Auditory",
        2: "Salience",
        # Map other networks to a generic name or keep as is if needed
        1: "Visual",
        3: "Dorsal Attention",
        5: "Limbic",
        6: "Frontoparietal"
    }
    
    df['network_name'] = df['network_id'].map(network_mapping)
    return df

def get_roi_networks() -> Dict[str, str]:
    """
    Returns a dictionary mapping ROI IDs to their network names.
    
    Returns:
        Dict[str, str]: Mapping of roi_id -> network_name
    """
    atlas_df = load_atlas()
    atlas_df = map_to_yeo(atlas_df)
    return dict(zip(atlas_df['roi_id'], atlas_df['network_name']))
