import csv
import random
import math
from pathlib import Path
from typing import List, Dict

# Fixed seed for reproducibility
RANDOM_SEED = 42
NUM_ROWS = 500  # Updated to meet task specification

# Simple SMILES templates for synthetic data
SMILES_TEMPLATES = [
    "C", "CC", "CCC", "CCCC", "CCO", "CCCO", "CCCCO", "C(C)O", "CC(C)O",
    "CC=O", "C=O", "CC(=O)O", "C(=O)O", "CC(=O)OC", "C1=CC=CC=C1", "CC1=CC=CC=C1",
    "CC1=CC=CC=C1O", "CC1=CC=CC=C1C(=O)O", "CC1=CC=CC=C1C(=O)OC",
    "C1CCCCC1", "C1CCCCC1O", "C1CCCCC1C(=O)O", "C1=CC=CC=C1C1CCCCC1",
    "CC(C)C", "CC(C)CC", "CC(C)CCC", "CC(C)CCCC", "CC(C)C(C)C",
    "CC(C)C(C)CC", "CC(C)C(C)CCC", "CC(C)C(C)CCCC", "CC(C)C(C)C(C)C"
]

SOLVENTS = [
    {"name": "water", "viscosity": 0.89, "dielectric_constant": 78.4},
    {"name": "ethanol", "viscosity": 1.07, "dielectric_constant": 24.3},
    {"name": "methanol", "viscosity": 0.59, "dielectric_constant": 32.6},
    {"name": "acetone", "viscosity": 0.31, "dielectric_constant": 20.7},
    {"name": "hexane", "viscosity": 0.31, "dielectric_constant": 1.89},
    {"name": "benzene", "viscosity": 0.65, "dielectric_constant": 2.28},
    {"name": "toluene", "viscosity": 0.59, "dielectric_constant": 2.38},
]

def approximate_molecular_weight(smiles: str) -> float:
    """
    Rough approximation of molecular weight based on SMILES length and composition.
    This is a heuristic for synthetic data generation, not a real calculation.
    """
    # Count heavy atoms (non‑hydrogen) in the SMILES string
    count = len([c for c in smiles if c not in ['H', ' ', '(', ')', '[', ']', '=', '#']])
    # Add a small random perturbation for diversity
    return count * 13.5 + random.uniform(-5, 5)

def stokes_einstein_diffusion(mw: float, viscosity: float, temperature: float = 298.15) -> float:
    """
    Approximate diffusion coefficient using the Stokes‑Einstein relation.
    D = kT / (6π η r), with a simplistic radius estimate based on molecular weight.
    """
    k_b = 1.380649e-23  # Boltzmann constant (J·K⁻¹)
    # Very rough radius scaling (meters)
    r = (mw ** (1 / 3)) * 1e-9 * 0.5
    eta = viscosity * 1e-3  # cP → Pa·s
    D = (k_b * temperature) / (6 * math.pi * eta * r)
    # Convert from m²·s⁻¹ to cm²·s⁻¹
    return D * 1e4

def generate_random_smiles() -> str:
    """Select a random SMILES template, occasionally concatenating two."""
    if random.random() < 0.8:
        return random.choice(SMILES_TEMPLATES)
    else:
        # Concatenate two templates to increase variety
        s1 = random.choice(SMILES_TEMPLATES)
        s2 = random.choice(SMILES_TEMPLATES)
        return s1 + s2

def select_random_solvent() -> Dict:
    """Pick a solvent definition at random."""
    return random.choice(SOLVENTS)

def generate_synthetic_dataset(output_path: Path, num_rows: int = NUM_ROWS) -> None:
    """
    Generate a deterministic synthetic diffusion dataset and write it to CSV.

    Parameters
    ----------
    output_path : Path
        Destination CSV file (including filename).
    num_rows : int, optional
        Number of rows to generate; defaults to the module‑level NUM_ROWS (500).
    """
    random.seed(RANDOM_SEED)  # Ensure reproducibility
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows: List[Dict] = []
    for _ in range(num_rows):
        smiles = generate_random_smiles()
        solvent_info = select_random_solvent()
        solvent_name = solvent_info["name"]
        viscosity = float(solvent_info["viscosity"])
        dielectric = float(solvent_info["dielectric_constant"])

        mw = approximate_molecular_weight(smiles)
        diffusion = stokes_einstein_diffusion(mw, viscosity)

        rows.append({
            "smiles": smiles,
            "solvent_type": solvent_name,          # Column name matches schema
            "diffusion_coefficient": diffusion,    # Store as numeric value
            "viscosity": viscosity,
            "dielectric_constant": dielectric
        })

    fieldnames = [
        "smiles",
        "solvent_type",
        "diffusion_coefficient",
        "viscosity",
        "dielectric_constant"
    ]

    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated synthetic dataset with {num_rows} rows at {output_path}")

def main() -> None:
    """
    Entry‑point used by the CI / quick‑start. It resolves the project root,
    ensures the raw data directory exists, and creates ``dataset.csv``.
    """
    # Resolve the project root relative to this file's location
    root = Path(__file__).resolve().parents[2]  # <project>/code/ingestion/..
    raw_dir = root / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    output_file = raw_dir / "dataset.csv"
    generate_synthetic_dataset(output_file)

if __name__ == "__main__":
    main()