#!/usr/bin/env python3
"""
Generate synthetic alloy data for glass-forming region prediction.

This script deterministically generates a CSV with synthetic alloy compositions
balanced between glass and crystalline structures, using a fixed random seed
for reproducibility.

Random seed: 42

Output: data/samples/synthetic_alloys.csv
"""

import os
import numpy as np
import pandas as pd

# Fixed random seed for reproducibility
RANDOM_SEED = 42

# Output path (relative to project root)
OUTPUT_PATH = "data/samples/synthetic_alloys.csv"

# Number of samples to generate
NUM_SAMPLES = 1000

# Number of elements per alloy (2-5 components)
MIN_COMPONENTS = 2
MAX_COMPONENTS = 5

# Common metallic elements for synthetic alloys
ELEMENTS = ['Cu', 'Zr', 'Ti', 'Ni', 'Al', 'Fe', 'Co', 'Ag', 'Pd', 'Pt',
            'Mg', 'Ca', 'Be', 'Y', 'La', 'Ce', 'Hf', 'Nb', 'Ta', 'Mo',
            'W', 'Cr', 'Mn', 'V', 'Sn', 'Pb', 'Bi', 'In', 'Ga', 'Ge']

# Periodic table properties for realistic descriptor simulation
# (atomic_radius in pm, electronegativity on Pauling scale)
ELEMENT_PROPERTIES = {
    'Cu': {'radius': 128, 'en': 1.90},
    'Zr': {'radius': 160, 'en': 1.33},
    'Ti': {'radius': 147, 'en': 1.54},
    'Ni': {'radius': 124, 'en': 1.91},
    'Al': {'radius': 143, 'en': 1.61},
    'Fe': {'radius': 126, 'en': 1.83},
    'Co': {'radius': 125, 'en': 1.88},
    'Ag': {'radius': 144, 'en': 1.93},
    'Pd': {'radius': 137, 'en': 2.20},
    'Pt': {'radius': 139, 'en': 2.28},
    'Mg': {'radius': 160, 'en': 1.31},
    'Ca': {'radius': 197, 'en': 1.00},
    'Be': {'radius': 112, 'en': 1.57},
    'Y': {'radius': 180, 'en': 1.22},
    'La': {'radius': 187, 'en': 1.10},
    'Ce': {'radius': 182, 'en': 1.12},
    'Hf': {'radius': 159, 'en': 1.30},
    'Nb': {'radius': 146, 'en': 1.60},
    'Ta': {'radius': 146, 'en': 1.50},
    'Mo': {'radius': 139, 'en': 2.16},
    'W': {'radius': 139, 'en': 2.36},
    'Cr': {'radius': 128, 'en': 1.66},
    'Mn': {'radius': 127, 'en': 1.55},
    'V': {'radius': 134, 'en': 1.63},
    'Sn': {'radius': 140, 'en': 1.96},
    'Pb': {'radius': 175, 'en': 2.33},
    'Bi': {'radius': 156, 'en': 2.02},
    'In': {'radius': 166, 'en': 1.78},
    'Ga': {'radius': 135, 'en': 1.81},
    'Ge': {'radius': 122, 'en': 2.01},
}


def compute_atomic_size_mismatch(composition):
    """
    Compute atomic size mismatch (delta) from composition.

    delta = sqrt(sum(c_i * (1 - r_i / r_avg)^2))
    where c_i is concentration, r_i is atomic radius, r_avg is average radius.
    """
    radii = []
    concentrations = []

    for elem, conc in composition.items():
        if elem in ELEMENT_PROPERTIES:
            radii.append(ELEMENT_PROPERTIES[elem]['radius'])
            concentrations.append(conc)

    if not radii:
        return 0.0

    r_avg = np.sum(np.array(radii) * np.array(concentrations))
    if r_avg == 0:
        return 0.0

    delta = np.sqrt(np.sum(np.array(concentrations) *
                            ((1 - np.array(radii) / r_avg) ** 2)))
    return delta


def compute_mixing_enthalpy(composition):
    """
    Compute approximate mixing enthalpy from composition.

    Uses a simplified model based on elemental electronegativity differences
    and size mismatch.
    """
    if len(composition) < 2:
        return 0.0

    elements = list(composition.keys())
    concentrations = [composition[e] for e in elements]

    # Simplified enthalpy based on EN differences
    enthalpy = 0.0
    for i, e1 in enumerate(elements):
        for e2 in elements[i+1:]:
            if e1 in ELEMENT_PROPERTIES and e2 in ELEMENT_PROPERTIES:
                en_diff = abs(ELEMENT_PROPERTIES[e1]['en'] -
                             ELEMENT_PROPERTIES[e2]['en'])
                size_diff = abs(ELEMENT_PROPERTIES[e1]['radius'] -
                               ELEMENT_PROPERTIES[e2]['radius']) / 150.0
                enthalpy += concentrations[i] * concentrations[elements.index(e2)] * \
                           (-10 * en_diff - 5 * size_diff)

    return enthalpy


def compute_electronegativity_variance(composition):
    """
    Compute electronegativity variance from composition.
    """
    ens = []
    concentrations = []

    for elem, conc in composition.items():
        if elem in ELEMENT_PROPERTIES:
            ens.append(ELEMENT_PROPERTIES[elem]['en'])
            concentrations.append(conc)

    if not ens:
        return 0.0

    en_avg = np.sum(np.array(ens) * np.array(concentrations))
    variance = np.sum(np.array(concentrations) *
                     ((np.array(ens) - en_avg) ** 2))
    return variance


def generate_composition():
    """Generate a random alloy composition with 2-5 elements."""
    num_elements = np.random.randint(MIN_COMPONENTS, MAX_COMPONENTS + 1)
    selected_elements = np.random.choice(ELEMENTS, num_elements, replace=False)

    # Generate random concentrations that sum to 1
    concentrations = np.random.random(num_elements)
    concentrations = concentrations / np.sum(concentrations)

    composition = {elem: round(conc, 4)
                  for elem, conc in zip(selected_elements, concentrations)}
    return composition


def generate_synthetic_alloys():
    """Generate synthetic alloy data with balanced class distribution."""
    np.random.seed(RANDOM_SEED)

    # Half glass-forming, half crystalline for balance
    half_samples = NUM_SAMPLES // 2

    data = {
        'sample_id': [],
        'composition': [],
        'atomic_size_mismatch': [],
        'mixing_enthalpy': [],
        'electronegativity_variance': [],
        'phase_label': [],
        'source': [],
    }

    # Generate glass-forming alloys (higher delta, more negative enthalpy)
    for i in range(half_samples):
        comp = generate_composition()
        delta = compute_atomic_size_mismatch(comp)
        enthalpy = compute_mixing_enthalpy(comp)
        en_var = compute_electronegativity_variance(comp)

        # Adjust to favor glass formation characteristics
        delta = delta + np.random.uniform(0.02, 0.08)
        enthalpy = enthalpy - np.random.uniform(5, 15)

        data['sample_id'].append(f'GLASS_{i:04d}')
        data['composition'].append(str(comp))
        data['atomic_size_mismatch'].append(round(delta, 6))
        data['mixing_enthalpy'].append(round(enthalpy, 4))
        data['electronegativity_variance'].append(round(en_var, 6))
        data['phase_label'].append('glass')
        data['source'].append('synthetic')

    # Generate crystalline alloys (lower delta, less negative enthalpy)
    for i in range(half_samples):
        comp = generate_composition()
        delta = compute_atomic_size_mismatch(comp)
        enthalpy = compute_mixing_enthalpy(comp)
        en_var = compute_electronegativity_variance(comp)

        # Adjust to favor crystalline characteristics
        delta = delta - np.random.uniform(0.0, 0.03)
        enthalpy = enthalpy + np.random.uniform(0, 10)

        data['sample_id'].append(f'CRYST_{i:04d}')
        data['composition'].append(str(comp))
        data['atomic_size_mismatch'].append(round(delta, 6))
        data['mixing_enthalpy'].append(round(enthalpy, 4))
        data['electronegativity_variance'].append(round(en_var, 6))
        data['phase_label'].append('crystalline')
        data['source'].append('synthetic')

    return pd.DataFrame(data)


def main():
    """Main entry point."""
    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    # Generate synthetic data
    df = generate_synthetic_alloys()

    # Write to CSV
    df.to_csv(OUTPUT_PATH, index=False)

    # Print summary
    print(f"Generated {len(df)} synthetic alloy samples")
    print(f"Output saved to: {OUTPUT_PATH}")
    print(f"Class distribution:")
    print(df['phase_label'].value_counts())


if __name__ == "__main__":
    main()