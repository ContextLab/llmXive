"""
Synthetic data generator for alloy compositions.

This module generates valid alloy compositions with realistic descriptors
to serve as a fallback when the canonical Zenodo DOI source is unavailable.
It ensures reproducibility per plan.md Constitution Check.

The generator creates compositions based on known glass-forming alloy systems
(e.g., Zr-based, Ti-based, Pd-based) and computes descriptors using the
established features pipeline.
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

# Import from local project modules
from features.descriptors import compute_all_descriptors
from config import ensure_data_directories, get_data_path

# Set up logging
logger = logging.getLogger(__name__)

# Define common glass-forming alloy systems with base elements and typical ranges
# Based on literature: Zr-based, Ti-based, Pd-based, Mg-based, La-based, Fe-based
GLASS_FORMING_SYSTEMS = [
    {
        "name": "Zr-based",
        "base_elements": ["Zr", "Cu", "Ni", "Al", "Ti", "Be"],
        "element_frequencies": {"Zr": 0.4, "Cu": 0.25, "Ni": 0.15, "Al": 0.1, "Ti": 0.07, "Be": 0.03},
        "atomic_fraction_range": (0.1, 0.6),
        "num_elements_range": (3, 5),
        "phase_label": "amorphous"
    },
    {
        "name": "Ti-based",
        "base_elements": ["Ti", "Cu", "Ni", "Zr", "Be", "Al"],
        "element_frequencies": {"Ti": 0.45, "Cu": 0.2, "Ni": 0.15, "Zr": 0.1, "Be": 0.05, "Al": 0.05},
        "atomic_fraction_range": (0.1, 0.55),
        "num_elements_range": (3, 5),
        "phase_label": "amorphous"
    },
    {
        "name": "Pd-based",
        "base_elements": ["Pd", "Cu", "Ni", "P", "Si", "Ge"],
        "element_frequencies": {"Pd": 0.4, "Cu": 0.25, "Ni": 0.15, "P": 0.1, "Si": 0.07, "Ge": 0.03},
        "atomic_fraction_range": (0.1, 0.5),
        "num_elements_range": (3, 5),
        "phase_label": "amorphous"
    },
    {
        "name": "Mg-based",
        "base_elements": ["Mg", "Cu", "Ni", "Zn", "Y", "Gd"],
        "element_frequencies": {"Mg": 0.5, "Cu": 0.2, "Ni": 0.15, "Zn": 0.08, "Y": 0.04, "Gd": 0.03},
        "atomic_fraction_range": (0.15, 0.6),
        "num_elements_range": (3, 4),
        "phase_label": "amorphous"
    },
    {
        "name": "La-based",
        "base_elements": ["La", "Al", "Ni", "Cu", "Co", "Fe"],
        "element_frequencies": {"La": 0.45, "Al": 0.2, "Ni": 0.15, "Cu": 0.1, "Co": 0.06, "Fe": 0.04},
        "atomic_fraction_range": (0.15, 0.55),
        "num_elements_range": (3, 5),
        "phase_label": "amorphous"
    },
    {
        "name": "Fe-based",
        "base_elements": ["Fe", "B", "Si", "P", "C", "Cr", "Mo"],
        "element_frequencies": {"Fe": 0.6, "B": 0.15, "Si": 0.1, "P": 0.08, "C": 0.04, "Cr": 0.02, "Mo": 0.01},
        "atomic_fraction_range": (0.05, 0.7),
        "num_elements_range": (3, 6),
        "phase_label": "amorphous"
    }
]

# Additional crystalline phase samples for balanced dataset
CRYSTALLINE_SYSTEMS = [
    {
        "name": "Simple_Alloys",
        "base_elements": ["Fe", "Cu", "Al", "Ni", "Zn", "Pb"],
        "element_frequencies": {"Fe": 0.3, "Cu": 0.25, "Al": 0.2, "Ni": 0.15, "Zn": 0.07, "Pb": 0.03},
        "atomic_fraction_range": (0.2, 0.8),
        "num_elements_range": (2, 4),
        "phase_label": "crystalline"
    }
]

def generate_composition_from_system(system_config: Dict[str, Any], 
                                    rng: np.random.Generator) -> Dict[str, Any]:
    """
    Generate a single alloy composition from a system configuration.
    
    Args:
        system_config: Dictionary containing system parameters
        rng: NumPy random generator for reproducibility
        
    Returns:
        Dictionary with composition string, atomic fractions, and phase label
    """
    # Select number of elements
    num_elements = rng.integers(
        system_config["num_elements_range"][0], 
        system_config["num_elements_range"][1] + 1
    )
    
    # Select elements based on frequencies
    elements = []
    weights = []
    for elem in system_config["base_elements"]:
        if elem in system_config["element_frequencies"]:
            elements.append(elem)
            weights.append(system_config["element_frequencies"][elem])
    
    # Normalize weights
    weights = np.array(weights) / np.sum(weights)
    
    # Sample unique elements
    selected_elements = rng.choice(
        elements, 
        size=min(num_elements, len(elements)), 
        replace=False, 
        p=weights
    )
    
    # Generate atomic fractions that sum to 1
    num_selected = len(selected_elements)
    raw_fractions = rng.uniform(
        system_config["atomic_fraction_range"][0],
        system_config["atomic_fraction_range"][1],
        size=num_selected
    )
    
    # Normalize to sum to 1
    atomic_fractions = raw_fractions / np.sum(raw_fractions)
    
    # Round to 2 decimal places and renormalize
    atomic_fractions = np.round(atomic_fractions, 2)
    atomic_fractions = atomic_fractions / np.sum(atomic_fractions)
    
    # Build composition string (e.g., "Zr50Cu30Ni20")
    composition_parts = []
    for elem, frac in zip(selected_elements, atomic_fractions):
        count = int(round(frac * 100))
        if count > 0:
            composition_parts.append(f"{elem}{count}")
    
    composition_str = "".join(composition_parts)
    
    # Create element-fraction mapping
    element_map = {elem: float(frac) for elem, frac in zip(selected_elements, atomic_fractions)}
    
    return {
        "composition": composition_str,
        "element_fractions": element_map,
        "phase": system_config["phase_label"],
        "system": system_config["name"]
    }

def generate_synthetic_dataset(
    num_samples: int = 1000,
    amorphous_ratio: float = 0.7,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate a synthetic dataset of alloy compositions with realistic properties.
    
    Args:
        num_samples: Total number of samples to generate
        amorphous_ratio: Proportion of amorphous (glass) samples
        seed: Random seed for reproducibility
        
    Returns:
        DataFrame with compositions and pre-computed descriptors
    """
    rng = np.random.default_rng(seed)
    
    # Calculate sample counts
    num_amorphous = int(num_samples * amorphous_ratio)
    num_crystalline = num_samples - num_amorphous
    
    all_samples = []
    
    # Generate amorphous samples
    logger.info(f"Generating {num_amorphous} amorphous samples...")
    for _ in range(num_amorphous):
        # Randomly select a glass-forming system
        system = rng.choice(GLASS_FORMING_SYSTEMS)
        sample = generate_composition_from_system(system, rng)
        all_samples.append(sample)
    
    # Generate crystalline samples
    logger.info(f"Generating {num_crystalline} crystalline samples...")
    for _ in range(num_crystalline):
        # Randomly select a crystalline system
        system = rng.choice(CRYSTALLINE_SYSTEMS)
        sample = generate_composition_from_system(system, rng)
        all_samples.append(sample)
    
    # Convert to DataFrame
    df = pd.DataFrame(all_samples)
    
    # Compute descriptors
    logger.info("Computing atomic descriptors...")
    df = compute_all_descriptors(df)
    
    # Add metadata
    df["source"] = "synthetic"
    df["generation_seed"] = seed
    df["timestamp"] = pd.Timestamp.now().isoformat()
    
    logger.info(f"Generated {len(df)} samples with {len(df.columns)} columns")
    
    return df

def save_synthetic_dataset(
    df: pd.DataFrame,
    output_path: Optional[str] = None
) -> Path:
    """
    Save the synthetic dataset to a CSV file.
    
    Args:
        df: DataFrame containing the synthetic dataset
        output_path: Optional custom output path
        
    Returns:
        Path to the saved file
    """
    if output_path is None:
        ensure_data_directories()
        data_path = get_data_path()
        output_path = str(Path(data_path) / "processed" / "synthetic_dataset.csv")
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Saved synthetic dataset to {output_path}")
    
    return Path(output_path)

def main():
    """Main entry point for synthetic data generation."""
    logging.basicConfig(level=logging.INFO)
    
    logger.info("Starting synthetic data generation...")
    
    # Generate dataset
    df = generate_synthetic_dataset(
        num_samples=1500,
        amorphous_ratio=0.7,
        seed=42
    )
    
    # Save dataset
    output_path = save_synthetic_dataset(df)
    
    # Print summary
    print(f"\nSynthetic Dataset Summary:")
    print(f"  Total samples: {len(df)}")
    print(f"  Amorphous: {sum(df['phase'] == 'amorphous')}")
    print(f"  Crystalline: {sum(df['phase'] == 'crystalline')}")
    print(f"  Features: {len(df.columns)}")
    print(f"  Output: {output_path}")
    
    return df

if __name__ == "__main__":
    main()
