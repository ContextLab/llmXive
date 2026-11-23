"""
Texture Descriptor Calculation Module

Calculates Texture Index and volume fractions of major FCC rolling texture components
(Brass, Copper, S, Goss) using MTEX-style search algorithms with defined Euler ranges.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
import pandas as pd

# Import from project API surface
from code.utils.logging import get_logger
from code.data.models import TextureDescriptor, MaterialType
from code.features.symmetry import align_orientations_to_fcc

logger = get_logger(__name__)

# Define Euler angle ranges (phi1, Phi, phi2) in degrees
# Format: (center_phi1, center_Phi, center_phi2, window_size)
# Window size defines the ± range around the center
COMPONENT_RANGES = {
    "Brass": {
        "center": (40.0, 60.0, 45.0),
        "window": 5.0,
        "description": "Approximate Brass component (phi1=35-45, Phi=55-65, phi2=0-90)"
    },
    "Copper": {
        "center": (39.0, 39.0, 0.0),
        "window": 5.0,
        "description": "Approximate Copper component (phi1=39, Phi=39, phi2=0)"
    },
    "S": {
        "center": (59.0, 37.0, 63.0),
        "window": 5.0,
        "description": "Approximate S component (phi1=59, Phi=37, phi2=63)"
    },
    "Goss": {
        "center": (0.0, 45.0, 90.0),
        "window": 5.0,
        "description": "Approximate Goss component (phi1=0, Phi=45, phi2=90)"
    }
}

def calculate_orientation_distance(
    o1: Tuple[float, float, float],
    o2: Tuple[float, float, float],
    metric: str = "euclidean"
) -> float:
    """
    Calculate the angular distance between two orientations in Euler space.

    Args:
        o1: First orientation as (phi1, Phi, phi2) in degrees.
        o2: Second orientation as (phi1, Phi, phi2) in degrees.
        metric: Distance metric ('euclidean' or 'max').

    Returns:
        Angular distance in degrees.
    """
    phi1_diff = abs(o1[0] - o2[0])
    Phi_diff = abs(o1[1] - o2[1])
    phi2_diff = abs(o1[2] - o2[2])

    # Handle periodicity for phi1 and phi2 (0-360)
    phi1_diff = min(phi1_diff, 360 - phi1_diff)
    phi2_diff = min(phi2_diff, 360 - phi2_diff)

    if metric == "euclidean":
        return np.sqrt(phi1_diff**2 + Phi_diff**2 + phi2_diff**2)
    elif metric == "max":
        return max(phi1_diff, Phi_diff, phi2_diff)
    else:
        raise ValueError(f"Unknown metric: {metric}")

def classify_orientation_to_component(
    orientation: Tuple[float, float, float],
    tolerance: float = 5.0
) -> Tuple[Optional[str], float]:
    """
    Classify an orientation to the closest texture component within a tolerance.

    Args:
        orientation: Euler angles (phi1, Phi, phi2) in degrees.
        tolerance: Maximum angular distance to consider a match (degrees).

    Returns:
        Tuple of (component_name, distance) or (None, infinity) if no match.
    """
    min_distance = float('inf')
    best_component = None

    for component_name, params in COMPONENT_RANGES.items():
        center = params["center"]
        window = params["window"]
        
        # Use the specific window for this component if provided, else default
        comp_tolerance = window

        distance = calculate_orientation_distance(orientation, center)
        
        if distance <= comp_tolerance:
            if distance < min_distance:
                min_distance = distance
                best_component = component_name

    return best_component, min_distance

def calculate_component_volume_fractions(
    orientations: pd.DataFrame
) -> Dict[str, float]:
    """
    Calculate volume fractions of major texture components.

    Args:
        orientations: DataFrame with columns 'phi1', 'Phi', 'phi2' (in degrees).
                     Must be pre-filtered and re-indexed to FCC symmetry.

    Returns:
        Dictionary mapping component names to their volume fractions.
    """
    if orientations.empty:
        return {k: 0.0 for k in COMPONENT_RANGES.keys()}

    total_points = len(orientations)
    component_counts = {k: 0 for k in COMPONENT_RANGES.keys()}
    
    # Count points belonging to each component
    for idx, row in orientations.iterrows():
        orientation = (row['phi1'], row['Phi'], row['phi2'])
        component, _ = classify_orientation_to_component(orientation)
        
        if component:
            component_counts[component] += 1

    # Convert counts to fractions
    fractions = {}
    for component, count in component_counts.items():
        fractions[component] = count / total_points

    return fractions

def calculate_texture_index(
    fractions: Dict[str, float]
) -> float:
    """
    Calculate the Texture Index as the sum of squared volume fractions.
    
    This metric indicates the degree of texture development (1.0 = perfect 
    single component, lower values = more random).

    Args:
        fractions: Dictionary of volume fractions for major components.

    Returns:
        Scalar texture index value.
    """
    # Sum of squares of fractions
    # Note: This is a simplified index. In rigorous ODF analysis, 
    # this involves integration over the orientation space.
    return sum(f**2 for f in fractions.values())

def calculate_descriptors(
    input_data: pd.DataFrame,
    sample_id: Optional[str] = None
) -> TextureDescriptor:
    """
    Main entry point to calculate all texture descriptors for a dataset.

    Args:
        input_data: DataFrame containing orientation data with columns:
                   'phi1', 'Phi', 'phi2' (in degrees), and optionally 
                   'sample_id', 'material', 'reduction'.
        sample_id: Optional sample identifier for the descriptor.

    Returns:
        TextureDescriptor Pydantic model instance.
    """
    logger.info(f"Calculating descriptors for {len(input_data)} orientations")

    # Ensure symmetry alignment (re-index to FCC)
    # Note: In a real pipeline, this might be done in preprocess.py
    # Here we assume the data is already aligned or we perform a quick check
    # For this implementation, we proceed with the data as is, assuming
    # it has been processed by T014 (reindex_to_fcc)
    
    # Calculate volume fractions
    fractions = calculate_component_volume_fractions(input_data)
    
    # Calculate random fraction (1 - sum of major components)
    sum_major = sum(fractions.values())
    random_fraction = max(0.0, 1.0 - sum_major)
    
    # Calculate texture index
    texture_index = calculate_texture_index(fractions)
    
    # Construct the descriptor
    descriptor = TextureDescriptor(
        sample_id=sample_id or "unknown",
        brass_fraction=fractions["Brass"],
        copper_fraction=fractions["Copper"],
        s_fraction=fractions["S"],
        goss_fraction=fractions["Goss"],
        random_fraction=random_fraction,
        texture_index=texture_index
    )
    
    logger.info(f"Descriptors calculated: Texture Index = {texture_index:.4f}")
    return descriptor

def main():
    """
    Main execution function for standalone testing or CLI usage.
    Loads processed EBSD data and calculates descriptors.
    """
    # Define paths
    processed_data_path = Path("data/processed/cleaned_ebsd.parquet")
    output_path = Path("data/processed/descriptors.csv")
    
    if not processed_data_path.exists():
        logger.error(f"Processed data not found at {processed_data_path}")
        logger.error("Please run the data pipeline (T012-T015) first.")
        sys.exit(1)
    
    logger.info(f"Loading data from {processed_data_path}")
    df = pd.read_parquet(processed_data_path)
    
    # Validate required columns
    required_cols = ['phi1', 'Phi', 'phi2']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        sys.exit(1)
    
    # Group by sample_id if available, otherwise process as one block
    if 'sample_id' in df.columns:
        groups = df.groupby('sample_id')
        descriptors = []
        
        for sample_id, group_df in groups:
            desc = calculate_descriptors(group_df, sample_id=sample_id)
            descriptors.append(desc.model_dump())
            logger.info(f"Processed sample {sample_id}: Texture Index = {desc.texture_index:.4f}")
    else:
        # Process entire dataset as one sample
        desc = calculate_descriptors(df, sample_id="full_dataset")
        descriptors = [desc.model_dump()]
    
    # Export to CSV
    output_df = pd.DataFrame(descriptors)
    output_df.to_csv(output_path, index=False)
    logger.info(f"Descriptors exported to {output_path}")
    
    return output_path

if __name__ == "__main__":
    main()
