"""
Synthetic Data Generator for Metallic Glass Alloy Compositions.

This module generates valid alloy compositions with realistic descriptors
for local testing and reproducibility verification when the canonical
DOI is inaccessible.

IMPORTANT: This is a testing utility ONLY. It is NOT a fallback for the
main ingestion pipeline (T010). The main pipeline MUST fail loudly if
real data sources are unavailable.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
import logging
from pathlib import Path
from features.descriptors import compute_all_descriptors

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Real elemental properties based on standard periodic table data
# Sources: WebElements, Materials Project, and standard thermodynamic tables
ELEMENT_PROPERTIES = {
    # Atomic Radius (pm), Electronegativity (Pauling), Valence Electrons
    'Zr': {'radius': 160, 'electronegativity': 1.33, 'valence': 4},
    'Ti': {'radius': 147, 'electronegativity': 1.54, 'valence': 4},
    'Hf': {'radius': 159, 'electronegativity': 1.30, 'valence': 4},
    'Cu': {'radius': 128, 'electronegativity': 1.90, 'valence': 1},
    'Zn': {'radius': 134, 'electronegativity': 1.65, 'valence': 2},
    'Ni': {'radius': 124, 'electronegativity': 1.91, 'valence': 2},
    'Al': {'radius': 143, 'electronegativity': 1.61, 'valence': 3},
    'Be': {'radius': 112, 'electronegativity': 1.57, 'valence': 2},
    'Mg': {'radius': 160, 'electronegativity': 1.31, 'valence': 2},
    'La': {'radius': 187, 'electronegativity': 1.10, 'valence': 3},
    'Ce': {'radius': 182, 'electronegativity': 1.12, 'valence': 3},
    'Pd': {'radius': 137, 'electronegativity': 2.20, 'valence': 2},
    'Pt': {'radius': 139, 'electronegativity': 2.28, 'valence': 2},
    'Ag': {'radius': 144, 'electronegativity': 1.93, 'valence': 1},
    'Au': {'radius': 144, 'electronegativity': 2.54, 'valence': 1},
    'Fe': {'radius': 126, 'electronegativity': 1.83, 'valence': 2},
    'Co': {'radius': 125, 'electronegativity': 1.88, 'valence': 2},
    'Y': {'radius': 180, 'electronegativity': 1.22, 'valence': 3},
    'Nb': {'radius': 146, 'electronegativity': 1.60, 'valence': 5},
    'Mo': {'radius': 139, 'electronegativity': 2.16, 'valence': 6},
    'Ta': {'radius': 146, 'electronegativity': 1.50, 'valence': 5},
    'W': {'radius': 139, 'electronegativity': 2.36, 'valence': 6},
    'Sn': {'radius': 145, 'electronegativity': 1.96, 'valence': 4},
    'In': {'radius': 167, 'electronegativity': 1.78, 'valence': 3},
    'Ga': {'radius': 135, 'electronegativity': 1.81, 'valence': 3},
    'Si': {'radius': 118, 'electronegativity': 1.90, 'valence': 4},
    'B': {'radius': 85, 'electronegativity': 2.04, 'valence': 3},
    'C': {'radius': 77, 'electronegativity': 2.55, 'valence': 4},
    'P': {'radius': 110, 'electronegativity': 2.19, 'valence': 5},
    'S': {'radius': 103, 'electronegativity': 2.58, 'valence': 6},
}

# Common metallic glass forming systems with typical composition ranges
GLASS_FORMING_SYSTEMS = [
    # Zr-based systems (most common)
    {'base': 'Zr', 'elements': ['Cu', 'Ni', 'Al', 'Be'], 'ranges': [(30, 70), (5, 35), (5, 30), (0, 20)]},
    {'base': 'Zr', 'elements': ['Cu', 'Ni', 'Ti', 'Al'], 'ranges': [(30, 65), (10, 35), (5, 25), (5, 20)]},
    {'base': 'Zr', 'elements': ['Cu', 'Al', 'Ni', 'Be'], 'ranges': [(35, 60), (10, 25), (5, 20), (0, 15)]},
    # Ti-based systems
    {'base': 'Ti', 'elements': ['Cu', 'Ni', 'Zr', 'Al'], 'ranges': [(25, 60), (10, 35), (10, 40), (5, 25)]},
    {'base': 'Ti', 'elements': ['Cu', 'Zr', 'Ni', 'Be'], 'ranges': [(30, 55), (15, 40), (5, 25), (0, 15)]},
    # Pd-based systems
    {'base': 'Pd', 'elements': ['Cu', 'Ni', 'P', 'Si'], 'ranges': [(35, 65), (10, 35), (10, 30), (0, 15)]},
    {'base': 'Pd', 'elements': ['Ag', 'Cu', 'P', 'Si'], 'ranges': [(30, 55), (10, 30), (10, 35), (5, 20)]},
    # La-based systems
    {'base': 'La', 'elements': ['Al', 'Cu', 'Ni', 'Be'], 'ranges': [(20, 50), (15, 40), (10, 35), (0, 20)]},
    # Mg-based systems
    {'base': 'Mg', 'elements': ['Cu', 'Zn', 'Ni', 'Al'], 'ranges': [(30, 60), (10, 35), (5, 25), (5, 20)]},
    # Y-based systems
    {'base': 'Y', 'elements': ['Al', 'Cu', 'Ni', 'Co'], 'ranges': [(25, 50), (15, 40), (10, 35), (5, 25)]},
    # Fe-based systems
    {'base': 'Fe', 'elements': ['B', 'Si', 'P', 'C'], 'ranges': [(60, 85), (5, 20), (5, 20), (0, 15)]},
    # Nb-based systems
    {'base': 'Nb', 'elements': ['Cu', 'Al', 'Ni', 'Si'], 'ranges': [(25, 55), (10, 35), (10, 30), (5, 20)]},
]

# Phase labels with realistic distribution (amorphous vs crystalline)
PHASE_LABELS = ['amorphous', 'crystalline']
AMORPHOUS_PROBABILITY = 0.65  # Slight bias towards amorphous for glass-forming region study

def generate_composition_from_system(system_idx: int, rng: np.random.Generator) -> Tuple[str, float]:
    """
    Generate a random composition from a specific glass-forming system.

    Args:
        system_idx: Index of the glass-forming system to use
        rng: NumPy random generator for reproducibility

    Returns:
        Tuple of (composition_string, phase_label)
    """
    system = GLASS_FORMING_SYSTEMS[system_idx]
    elements = system['elements']
    ranges = system['ranges']

    # Generate random percentages that sum to 100
    n_elements = len(elements)
    raw_values = [rng.uniform(ranges[i][0], ranges[i][1]) for i in range(n_elements)]

    # Normalize to sum to 100
    total = sum(raw_values)
    percentages = [v / total * 100 for v in raw_values]

    # Round to 1 decimal place and adjust to ensure sum is exactly 100
    rounded = [round(p, 1) for p in percentages]
    diff = 100 - sum(rounded)
    if diff != 0:
        rounded[0] += diff

    # Build composition string in Hill system format (base element first for clarity)
    # For alloys, we'll use a simplified format: Element1x1+Element2x2+...
    composition_parts = []
    for elem, pct in zip(elements, rounded):
        if pct > 0.1:  # Only include elements with significant percentage
            composition_parts.append(f"{elem}{pct:.1f}")

    composition_str = "+".join(composition_parts)

    # Determine phase label with realistic probability
    is_amorphous = rng.random() < AMORPHOUS_PROBABILITY
    phase_label = 'amorphous' if is_amorphous else 'crystalline'

    return composition_str, phase_label

def generate_synthetic_dataset(
    n_samples: int = 1000,
    seed: Optional[int] = 42,
    systems_to_include: Optional[List[int]] = None
) -> pd.DataFrame:
    """
    Generate a synthetic dataset of alloy compositions with realistic descriptors.

    Args:
        n_samples: Number of samples to generate
        seed: Random seed for reproducibility
        systems_to_include: List of system indices to include (None = all systems)

    Returns:
        DataFrame with compositions, phase labels, and computed descriptors
    """
    if seed is not None:
        rng = np.random.default_rng(seed)
    else:
        rng = np.random.default_rng()

    if systems_to_include is None:
        systems_to_include = list(range(len(GLASS_FORMING_SYSTEMS)))

    if not systems_to_include:
        raise ValueError("At least one glass-forming system must be specified")

    data = []
    samples_per_system = n_samples // len(systems_to_include)
    remainder = n_samples % len(systems_to_include)

    for i, system_idx in enumerate(systems_to_include):
        n_for_system = samples_per_system + (1 if i < remainder else 0)
        for _ in range(n_for_system):
            composition_str, phase_label = generate_composition_from_system(system_idx, rng)
            data.append({
                'composition': composition_str,
                'phase': phase_label,
                'source': 'synthetic'
            })

    df = pd.DataFrame(data)

    # Apply descriptor computation
    logger.info(f"Computing descriptors for {len(df)} synthetic compositions...")
    df_with_descriptors = apply_descriptors_to_dataframe(df)

    # Verify descriptor completeness
    required_descriptors = [
        'atomic_size_mismatch', 'electronegativity_difference', 'mixing_enthalpy',
        'atomic_radius', 'valence_electron_concentration', 'atomic_size_difference',
        'valence_electron_size_mismatch', 'electron_atom_ratio', 'miedema_heat_of_formation',
        'atomic_packing_factor'
    ]

    missing_cols = [col for col in required_descriptors if col not in df_with_descriptors.columns]
    if missing_cols:
        logger.warning(f"Missing descriptors: {missing_cols}")
    else:
        logger.info("All required descriptors computed successfully")

    # Add metadata
    df_with_descriptors['is_synthetic'] = True
    df_with_descriptors['generation_seed'] = seed
    df_with_descriptors['generation_timestamp'] = pd.Timestamp.now().isoformat()

    return df_with_descriptors

def apply_descriptors_to_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply descriptor computation to a DataFrame of compositions.

    Args:
        df: DataFrame with 'composition' column

    Returns:
        DataFrame with added descriptor columns
    """
    # Use the existing compute_all_descriptors function from features.descriptors
    # This ensures consistency with the main pipeline
    try:
        result_df = compute_all_descriptors(df)
        return result_df
    except Exception as e:
        logger.error(f"Error computing descriptors: {e}")
        raise

def save_synthetic_dataset(
    df: pd.DataFrame,
    output_path: str,
    provenance_info: Optional[Dict[str, Any]] = None
) -> None:
    """
    Save synthetic dataset to CSV with provenance information.

    Args:
        df: DataFrame to save
        output_path: Path to save the CSV file
        provenance_info: Optional dictionary with provenance metadata
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Add provenance metadata to the CSV as comments if available
    df.to_csv(output_file, index=False)

    logger.info(f"Saved synthetic dataset to {output_file} with {len(df)} samples")

    if provenance_info:
        provenance_file = output_file.with_suffix('.json')
        import json
        with open(provenance_file, 'w') as f:
            json.dump(provenance_info, f, indent=2)
        logger.info(f"Saved provenance information to {provenance_file}")

def main():
    """Main entry point for generating synthetic dataset."""
    import argparse

    parser = argparse.ArgumentParser(description='Generate synthetic alloy dataset')
    parser.add_argument('--n-samples', type=int, default=1000, help='Number of samples to generate')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    parser.add_argument('--output', type=str, default='data/processed/synthetic_dataset.csv',
                      help='Output file path')
    parser.add_argument('--systems', type=str, default=None,
                      help='Comma-separated list of system indices to include')

    args = parser.parse_args()

    # Parse systems if provided
    systems_to_include = None
    if args.systems:
        systems_to_include = [int(x.strip()) for x in args.systems.split(',')]

    logger.info(f"Generating {args.n_samples} synthetic samples with seed {args.seed}")
    df = generate_synthetic_dataset(
        n_samples=args.n_samples,
        seed=args.seed,
        systems_to_include=systems_to_include
    )

    # Prepare provenance information
    provenance_info = {
        'source': 'synthetic_generator',
        'task_id': 'T011',
        'seed': args.seed,
        'n_samples': args.n_samples,
        'systems_included': systems_to_include if systems_to_include else list(range(len(GLASS_FORMING_SYSTEMS))),
        'generation_timestamp': pd.Timestamp.now().isoformat(),
        'note': 'This is synthetic data for testing only. Not for production use.'
    }

    save_synthetic_dataset(df, args.output, provenance_info)
    logger.info("Synthetic dataset generation complete")

if __name__ == '__main__':
    main()