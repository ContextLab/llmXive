import csv
import json
import random
import math
from pathlib import Path
from typing import List, Dict, Tuple

# Fixed seed for reproducibility
RANDOM_SEED = 42
NUM_ROWS = 100

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
    # Very rough: count heavy atoms (non-H) and assign average weight ~12-16
    # This is purely for synthetic diversity, not accuracy.
    count = len([c for c in smiles if c not in ['H', ' ', '(', ')', '[', ']', '=', '#']])
    # Add some noise
    return count * 13.5 + random.uniform(-5, 5)

def stokes_einstein_diffusion(mw: float, viscosity: float, temperature: float = 298.15) -> float:
    """
    Calculate diffusion coefficient using Stokes-Einstein equation (approximate).
    D = kT / (6 * pi * eta * r)
    Assume r is proportional to MW^(1/3)
    """
    k_b = 1.380649e-23  # Boltzmann constant
    # Approximate radius in meters (very rough scaling)
    # Assume density ~ 1 g/cm3, volume ~ MW / density, r ~ (3V/4pi)^(1/3)
    # MW in g/mol -> kg/molecule = MW / N_A
    # But for synthetic, we just want a trend.
    # Let's use a simplified scaling: r ~ MW^(1/3) * 1e-9 (nm scale)
    r = (mw ** (1/3)) * 1e-9 * 0.5  # arbitrary scaling factor
    eta = viscosity * 1e-3  # convert cP to Pa.s (approx)
    D = (k_b * temperature) / (6 * math.pi * eta * r)
    # Convert to cm^2/s (common unit)
    D_cm2_s = D * 1e4
    return D_cm2_s

def generate_random_smiles() -> str:
    """Select a random SMILES from templates or combine them."""
    if random.random() < 0.8:
        return random.choice(SMILES_TEMPLATES)
    else:
        # Combine two templates
        s1 = random.choice(SMILES_TEMPLATES)
        s2 = random.choice(SMILES_TEMPLATES)
        return s1 + s2

def select_random_solvent() -> Dict:
    return random.choice(SOLVENTS)

def generate_synthetic_dataset(output_path: Path, num_rows: int = NUM_ROWS) -> None:
    """Generate a deterministic synthetic dataset and save to CSV."""
    random.seed(RANDOM_SEED)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for i in range(num_rows):
        smiles = generate_random_smiles()
        solvent_info = select_random_solvent()
        solvent_name = solvent_info["name"]
        viscosity = solvent_info["viscosity"]
        dielectric = solvent_info["dielectric_constant"]

        mw = approximate_molecular_weight(smiles)
        diffusion = stokes_einstein_diffusion(mw, viscosity)

        rows.append({
            "smiles": smiles,
            "solvent": solvent_name,
            "diffusion_coefficient": f"{diffusion:.6e}",
            "viscosity": viscosity,
            "dielectric_constant": dielectric
        })

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["smiles", "solvent", "diffusion_coefficient", "viscosity", "dielectric_constant"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated synthetic dataset with {num_rows} rows at {output_path}")

def main():
    root = Path(__file__).resolve().parent.parent.parent
    raw_dir = root / "data" / "raw"
    output_file = raw_dir / "dataset.csv"
    generate_synthetic_dataset(output_file)

if __name__ == "__main__":
    main()
