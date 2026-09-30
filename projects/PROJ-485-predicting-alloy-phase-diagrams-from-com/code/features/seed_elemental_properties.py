"""
Seeds the elemental properties CSV file with known values for Cu, Al, Zn, Fe, C.
This is required for T007 and used by T017/T020.
"""
import os
import sys
import csv
from utils.logging import get_logger, log_info, log_error

logger = get_logger(__name__)

ELEMENTAL_PROPERTIES = [
    {"element": "Cu", "atomic_radius_angstrom": 1.28, "electronegativity_pauling": 1.90, "valence_electrons": 1},
    {"element": "Al", "atomic_radius_angstrom": 1.43, "electronegativity_pauling": 1.61, "valence_electrons": 3},
    {"element": "Zn", "atomic_radius_angstrom": 1.34, "electronegativity_pauling": 1.65, "valence_electrons": 2},
    {"element": "Fe", "atomic_radius_angstrom": 1.26, "electronegativity_pauling": 1.83, "valence_electrons": 2},
    {"element": "C",  "atomic_radius_angstrom": 0.77, "electronegativity_pauling": 2.55, "valence_electrons": 4},
]

def main():
    output_path = "data/raw/elemental_properties.csv"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if os.path.exists(output_path):
        log_info(f"File {output_path} already exists. Skipping seed.")
        return

    log_info(f"Seeding elemental properties to {output_path}")
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["element", "atomic_radius_angstrom", "electronegativity_pauling", "valence_electrons"])
            writer.writeheader()
            writer.writerows(ELEMENTAL_PROPERTIES)
        log_info("Successfully seeded elemental properties.")
    except Exception as e:
        log_error("Failed to seed elemental properties", str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
