"""
Synthetic data generator for metallic glass alloy compositions.

This module provides functions to generate valid alloy compositions with
realistic descriptors when the canonical DOI source is unavailable.
It is designed to support reproducibility per plan.md Constitution Check.

IMPORTANT: This is a FALLBACK mechanism ONLY. The primary data source
(Zenodo DOI or Materials Project API) MUST be attempted first.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path
from features.descriptors import compute_all_descriptors

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fixed seed for reproducibility
REPRODUCIBLE_SEED = 42

# Representative alloy systems for metallic glasses
# Format: (base_element, common_alloying_elements, typical_ranges)
ALLOY_SYSTEMS = [
    ("Zr", ["Ti", "Cu", "Ni", "Al", "Be"], [(0.3, 0.7), (0.0, 0.3), (0.0, 0.3), (0.0, 0.2), (0.0, 0.1)]),
    ("Pd", ["Si", "Ge", "Cu", "Ni", "Ag"], [(0.4, 0.8), (0.0, 0.2), (0.0, 0.2), (0.0, 0.2), (0.0, 0.1)]),
    ("La", ["Al", "Ni", "Cu", "Co", "Fe"], [(0.4, 0.8), (0.0, 0.3), (0.0, 0.2), (0.0, 0.2), (0.0, 0.1)]),
    ("Mg", ["Cu", "Zn", "Ni", "Ag", "Y"], [(0.4, 0.8), (0.0, 0.3), (0.0, 0.2), (0.0, 0.2), (0.0, 0.1)]),
    ("Ti", ["Zr", "Cu", "Ni", "Al", "Be"], [(0.3, 0.7), (0.0, 0.3), (0.0, 0.3), (0.0, 0.2), (0.0, 0.1)]),
    ("Fe", ["B", "Si", "C", "Cr", "Ni"], [(0.4, 0.8), (0.0, 0.3), (0.0, 0.2), (0.0, 0.2), (0.0, 0.1)]),
    ("Cu", ["Zr", "Hf", "Ti", "Al", "Ni"], [(0.3, 0.7), (0.0, 0.3), (0.0, 0.3), (0.0, 0.2), (0.0, 0.1)]),
    ("Ni", ["Nb", "Ti", "Zr", "Al", "Cu"], [(0.3, 0.7), (0.0, 0.3), (0.0, 0.3), (0.0, 0.2), (0.0, 0.1)]),
]

# Phase labels for metallic glass datasets
PHASE_LABELS = ["amorphous", "crystalline"]
PHASE_WEIGHTS = [0.4, 0.6]  # Typical distribution in experimental datasets

def generate_composition_from_system(
    system_idx: int,
    rng: np.random.Generator
) -> Dict[str, Any]:
    """
    Generate a single alloy composition from a specified alloy system.

    Args:
        system_idx: Index of the alloy system to use
        rng: NumPy random generator for reproducibility

    Returns:
        Dictionary with 'composition' (string) and 'phase' label
    """
    base_element, alloying_elements, ranges = ALLOY_SYSTEMS[system_idx]

    # Generate random atomic fractions that sum to 1.0
    n_elements = len(alloying_elements) + 1
    fractions = np.zeros(n_elements)

    # Sample from Dirichlet distribution for realistic proportions
    # Adjust concentration to favor base element
    concentration_params = [2.0] + [1.0] * n_elements
    raw_fractions = rng.dirichlet(concentration_params)

    # Normalize to ensure sum is exactly 1.0
    fractions = raw_fractions / raw_fractions.sum()

    # Build composition string
    elements = [base_element] + alloying_elements
    composition_parts = []
    for elem, frac in zip(elements, fractions):
        if frac > 0.01:  # Only include elements with >1% concentration
            composition_parts.append(f"{elem}{frac:.3f}")

    composition_str = "".join(composition_parts)

    # Assign phase label based on weights
    phase = rng.choice(PHASE_LABELS, p=PHASE_WEIGHTS)

    return {
        "composition": composition_str,
        "phase": phase
    }

def generate_synthetic_dataset(
    n_samples: int = 1000,
    seed: int = REPRODUCIBLE_SEED
) -> pd.DataFrame:
    """
    Generate a synthetic dataset of alloy compositions with realistic descriptors.

    This function creates a dataset that mimics the structure and statistical
    properties of real metallic glass datasets, suitable for testing the
    pipeline when canonical data sources are unavailable.

    Args:
        n_samples: Number of compositions to generate (default: 1000)
        seed: Random seed for reproducibility

    Returns:
        pandas DataFrame with compositions, phases, and computed descriptors
    """
    rng = np.random.default_rng(seed)

    logger.info(f"Generating {n_samples} synthetic alloy compositions...")

    # Generate base compositions
    compositions = []
    for i in range(n_samples):
        # Cycle through alloy systems to ensure diversity
        system_idx = i % len(ALLOY_SYSTEMS)
        comp_data = generate_composition_from_system(system_idx, rng)
        compositions.append(comp_data)

    df = pd.DataFrame(compositions)

    logger.info("Computing atomic descriptors for generated compositions...")

    # Compute descriptors using the existing feature engineering pipeline
    # This ensures consistency with the main pipeline
    df_with_descriptors = apply_descriptors_to_dataframe(df)

    logger.info(f"Generated dataset with {len(df_with_descriptors)} samples")
    logger.info(f"Descriptor columns: {list(df_with_descriptors.columns)}")

    return df_with_descriptors

def apply_descriptors_to_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply descriptor computation to a DataFrame of compositions.

    Args:
        df: DataFrame with 'composition' and 'phase' columns

    Returns:
        DataFrame with added descriptor columns
    """
    # Use the existing descriptor computation pipeline
    # This ensures consistency with the main data processing workflow
    df_descriptors = df.copy()

    # Compute all descriptors for each composition
    descriptor_results = []
    for idx, row in df_descriptors.iterrows():
        try:
            descriptors = compute_all_descriptors(row['composition'])
            descriptor_results.append(descriptors)
        except Exception as e:
            logger.warning(f"Failed to compute descriptors for {row['composition']}: {e}")
            # Create default descriptors for failed compositions
            descriptor_results.append({
                'atomic_radius': 0.0,
                'electronegativity': 0.0,
                'valence_electron_concentration': 0.0,
                'atomic_size_mismatch': 0.0,
                'mixing_enthalpy': 0.0,
                'atomic_size_difference': 0.0,
                'valence_electron_size_mismatch': 0.0,
                'electron_atom_ratio': 0.0,
                'miedema_heat_of_formation': 0.0,
                'atomic_packing_factor': 0.0
            })

    descriptors_df = pd.DataFrame(descriptor_results)

    # Combine with original dataframe
    result_df = pd.concat([df_descriptors, descriptors_df], axis=1)

    return result_df

def save_synthetic_dataset(
    df: pd.DataFrame,
    output_path: str,
    provenance_info: Optional[Dict[str, Any]] = None
) -> Path:
    """
    Save the synthetic dataset to a CSV file with provenance information.

    Args:
        df: DataFrame containing the synthetic dataset
        output_path: Path to save the CSV file
        provenance_info: Optional dictionary with provenance metadata

    Returns:
        Path object of the saved file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_path, index=False)

    logger.info(f"Saved synthetic dataset to {output_path}")

    # Save provenance information if provided
    if provenance_info:
        provenance_path = output_path.with_suffix('.json')
        with open(provenance_path, 'w') as f:
            import json
            json.dump(provenance_info, f, indent=2)
        logger.info(f"Saved provenance information to {provenance_path}")

    return output_path

def main():
    """
    Main entry point for generating synthetic dataset.

    This function is designed to be called from the command line or
    as part of the main ingestion pipeline when canonical data sources fail.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate synthetic metallic glass alloy dataset"
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=1000,
        help="Number of synthetic samples to generate"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/synthetic_dataset.csv",
        help="Output path for the synthetic dataset"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=REPRODUCIBLE_SEED,
        help="Random seed for reproducibility"
    )

    args = parser.parse_args()

    # Generate the dataset
    df = generate_synthetic_dataset(
        n_samples=args.n_samples,
        seed=args.seed
    )

    # Prepare provenance information
    provenance_info = {
        "source": "synthetic_generator",
        "seed": args.seed,
        "n_samples": args.n_samples,
        "timestamp": pd.Timestamp.now().isoformat(),
        "note": "This is synthetic data for testing when canonical sources are unavailable"
    }

    # Save the dataset
    save_synthetic_dataset(
        df,
        args.output,
        provenance_info=provenance_info
    )

    logger.info("Synthetic dataset generation completed successfully")

if __name__ == "__main__":
    main()