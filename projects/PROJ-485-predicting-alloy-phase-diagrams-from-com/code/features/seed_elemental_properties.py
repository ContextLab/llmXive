import os
import sys
import csv
from utils.logging import get_logger, log_info, log_error

logger = get_logger(__name__)

# Seed data as per T007
ELEMENTAL_DATA = [
    {"element": "Cu", "atomic_radius_angstrom": 1.28, "electronegativity_pauling": 1.90, "valence_electrons": 1},
    {"element": "Al", "atomic_radius_angstrom": 1.43, "electronegativity_pauling": 1.61, "valence_electrons": 3},
    {"element": "Zn", "atomic_radius_angstrom": 1.34, "electronegativity_pauling": 1.65, "valence_electrons": 2},
    {"element": "Fe", "atomic_radius_angstrom": 1.24, "electronegativity_pauling": 1.83, "valence_electrons": 2},
    {"element": "C",  "atomic_radius_angstrom": 0.77, "electronegativity_pauling": 2.55, "valence_electrons": 4},
]

def main():
    output_path = "data/raw/elemental_properties.csv"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if os.path.exists(output_path):
        logger.info(f"File {output_path} already exists. Skipping generation.")
        return

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["element", "atomic_radius_angstrom", "electronegativity_pauling", "valence_electrons"])
        writer.writeheader()
        for row in ELEMENTAL_DATA:
            writer.writerow(row)
    
    log_info(f"Elemental properties seeded to {output_path}")

if __name__ == "__main__":
    main()
