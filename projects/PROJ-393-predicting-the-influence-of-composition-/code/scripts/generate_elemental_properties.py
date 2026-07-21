import csv
import os
from pathlib import Path

DATA_DIR = Path("data/raw")
FILE_PATH = DATA_DIR / "elemental_properties.csv"

DATA = [
    ("Mn", 1.55, 127, 7, "Pyykko 1988"),
    ("Co", 1.88, 125, 9, "Pyykko 1988"),
    ("Fe", 1.83, 126, 8, "Pyykko 1988"),
    ("Ga", 1.81, 135, 3, "Pyykko 1988"),
    ("Al", 1.61, 143, 3, "Pyykko 1988"),
    ("Ni", 1.91, 124, 10, "Pyykko 1988"),
    ("Cu", 1.90, 128, 11, "Pyykko 1988"),
    ("Sn", 1.96, 145, 4, "Pyykko 1988"),
    ("In", 1.78, 167, 3, "Pyykko 1988"),
    ("Ti", 1.54, 147, 4, "Pyykko 1988"),
    ("V", 1.63, 134, 5, "Pyykko 1988"),
    ("Zn", 1.65, 134, 12, "Pyykko 1988"),
    ("Si", 1.90, 111, 4, "Pyykko 1988"),
    ("Ge", 2.01, 122, 4, "Pyykko 1988"),
    ("Sb", 2.05, 140, 5, "Pyykko 1988"),
    ("Pb", 2.33, 175, 4, "Pyykko 1988"),
    ("Mg", 1.31, 160, 2, "Pyykko 1988"),
    ("Cr", 1.66, 128, 6, "Pyykko 1988"),
    ("Nb", 1.60, 146, 5, "Pyykko 1988"),
    ("Ta", 1.50, 146, 5, "Pyykko 1988"),
]

def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(FILE_PATH, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["element", "electronegativity", "atomic_radii", "valence_electrons", "source_reference"])
        for row in DATA:
            writer.writerow(row)
    print(f"Generated {FILE_PATH}")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
