"""
Script to generate the initial elemental_properties.csv file.
This script creates the fixed periodic table data required for the project.
"""

import csv
import os
from pathlib import Path

# Data source: Pyykko 1988 and standard values for the required elements
# Elements: Mn, Co, Fe, Ga, Al, Ni, Cu, Sn, In, Ti, V
ELEMENTAL_DATA = [
    # element, electronegativity (Pauling), atomic_radii (pm), valence_electrons
    {"element": "Mn", "electronegativity": 1.55, "atomic_radii": 127, "valence_electrons": 7},
    {"element": "Co", "electronegativity": 1.88, "atomic_radii": 125, "valence_electrons": 9},
    {"element": "Fe", "electronegativity": 1.83, "atomic_radii": 126, "valence_electrons": 8},
    {"element": "Ga", "electronegativity": 1.81, "atomic_radii": 135, "valence_electrons": 3},
    {"element": "Al", "electronegativity": 1.61, "atomic_radii": 143, "valence_electrons": 3},
    {"element": "Ni", "electronegativity": 1.91, "atomic_radii": 124, "valence_electrons": 10},
    {"element": "Cu", "electronegativity": 1.90, "atomic_radii": 128, "valence_electrons": 11}, # Often treated as 1 or 11 depending on context, using group valence for consistency with simple models
    {"element": "Sn", "electronegativity": 1.96, "atomic_radii": 140, "valence_electrons": 4},
    {"element": "In", "electronegativity": 1.78, "atomic_radii": 155, "valence_electrons": 3},
    {"element": "Ti", "electronegativity": 1.54, "atomic_radii": 147, "valence_electrons": 4},
    {"element": "V", "electronegativity": 1.63, "atomic_radii": 134, "valence_electrons": 5},
]

def main():
    # Determine output path relative to project root
    # This script is in code/scripts/, so root is code/
    base_dir = Path(__file__).resolve().parent.parent
    output_dir = base_dir / "data" / "raw"
    output_file = output_dir / "elemental_properties.csv"

    # Create directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating {output_file}...")

    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['element', 'electronegativity', 'atomic_radii', 'valence_electrons']
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()
            for row in ELEMENTAL_DATA:
                writer.writerow(row)

        print(f"Successfully wrote {len(ELEMENTAL_DATA)} elements to {output_file}")
    except IOError as e:
        print(f"Error writing file: {e}")
        raise

if __name__ == "__main__":
    main()