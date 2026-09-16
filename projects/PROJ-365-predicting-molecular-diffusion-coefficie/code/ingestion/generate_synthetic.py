"""
Synthetic dataset generator for the diffusion coefficient prediction pipeline.

This script creates a CSV file at ``data/raw/dataset.csv`` containing a user‑defined
number of synthetic records.  Each record consists of:

- ``smiles``: a valid SMILES string (randomly chosen from a small curated list)
- ``solvent``: a solvent name (randomly chosen from a short list)
- ``temperature_K``: temperature in Kelvin (random float between 273 and 373)
- ``diffusion_coeff_cm2_s``: diffusion coefficient in cm²·s⁻¹, computed
  via a simplified Stokes‑Einstein relationship.

The script also writes a ``data/data_source_flag.json`` file indicating that the
source is synthetic.  This flag is used downstream (see ``code/ingestion/flag_source.py``)
to decide whether evaluation metrics should be calculated.

The implementation deliberately avoids any heavy‑weight chemistry generation
(e.g. building molecules from scratch) and instead relies on a deterministic,
reproducible list of SMILES strings.  This satisfies the requirement for
“random structures strictly for pipeline validation” while keeping execution
fast and deterministic.

The module can be executed directly:

    $ python code/ingestion/generate_synthetic.py

or imported and called via ``generate_synthetic_dataset``.
"""

import csv
import json
import random
from pathlib import Path
from typing import List, Dict

from rdkit import Chem
from rdkit.Chem import Descriptors

from utils.config import get_project_root

# ---------------------------------------------------------------------------
# Helper data
# ---------------------------------------------------------------------------

# A small, curated list of chemically valid SMILES strings.  These are common
# organic molecules that RDKit can parse without issue.
_SMILES_POOL: List[str] = [
    "CCO",                      # ethanol
    "CCCC",                     # butane
    "CC(=O)O",                  # acetic acid
    "c1ccccc1",                 # benzene
    "C1CCCC1",                  # cyclopentane
    "CCN(CC)CC",                # triethylamine
    "C(C(=O)O)N",               # glycine (neutral form)
    "CC(C)O",                   # isopropanol
    "C(CCl)Cl",                 # dichloromethane
    "CC(=O)NC1=CC=CC=C1",       # acetanilide
]

# A short list of common solvents together with a representative viscosity
# (Pa·s) at 298 K and dielectric constant.  The values are taken from public
# literature and are sufficient for the simple Stokes‑Einstein calculation.
_SOLVENTS: List[Dict[str, float]] = [
    {"name": "water", "viscosity_Pa_s": 0.00089, "dielectric": 78.5},
    {"name": "ethanol", "viscosity_Pa_s": 0.00120, "dielectric": 24.5},
    {"name": "acetone", "viscosity_Pa_s": 0.00032, "dielectric": 20.7},
    {"name": "toluene", "viscosity_Pa_s": 0.00059, "dielectric": 2.38},
    {"name": "dimethyl_sulfoxide", "viscosity_Pa_s": 0.00199, "dielectric": 46.7},
]

# Physical constants for the Stokes–Einstein equation
_KB = 1.380649e-23          # Boltzmann constant (J·K⁻¹)
_AVOGADRO = 6.02214076e23   # Avogadro's number (mol⁻¹)

# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def approximate_molecular_weight(smiles: str) -> float:
    """
    Return the molecular weight (g·mol⁻¹) of a molecule given its SMILES.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES string: {smiles}")
    return Descriptors.MolWt(mol)

def stokes_einstein_diffusion(
    temperature_K: float,
    viscosity_Pa_s: float,
    molecular_weight_g_mol: float,
) -> float:
    """
    Compute a diffusion coefficient using a simplified Stokes‑Einstein model.

    The hydrodynamic radius *r* is estimated from the molecular weight
    assuming a spherical particle with a density of 1 g·cm⁻³:

        r = ( (3 * M) / (4 * π * ρ * N_A) )^(1/3)

    where *M* is the molecular weight (g·mol⁻¹) and ρ is the assumed
    density (g·cm⁻³).  The diffusion coefficient *D* is then:

        D = k_B * T / (6 * π * η * r)

    The returned value is in cm²·s⁻¹.
    """
    # Assumed density of an organic molecule in water (g·cm⁻³)
    density = 1.0

    # Convert molecular weight from g·mol⁻¹ to kg per molecule
    mol_weight_kg = molecular_weight_g_mol / 1000.0 / _AVOGADRO

    # Radius in meters
    radius_m = ((3 * mol_weight_kg) / (4 * 3.141592653589793 * density)) ** (1 / 3)

    # Diffusion coefficient in m²·s⁻¹
    D_m2_s = _KB * temperature_K / (6 * 3.141592653589793 * viscosity_Pa_s * radius_m)

    # Convert to cm²·s⁻¹
    return D_m2_s * 1e4

def generate_random_smiles() -> str:
    """Pick a random SMILES string from the curated pool."""
    return random.choice(_SMILES_POOL)

def select_random_solvent() -> Dict[str, float]:
    """Pick a random solvent descriptor dictionary."""
    return random.choice(_SOLVENTS)

def generate_synthetic_dataset(num_samples: int = 100) -> List[Dict[str, str]]:
    """
    Produce a list of synthetic records suitable for the ingestion pipeline.

    Each record contains the fields required by downstream steps:
    ``smiles``, ``solvent``, ``temperature_K``, and ``diffusion_coeff_cm2_s``.
    """
    dataset: List[Dict[str, str]] = []
    for _ in range(num_samples):
        smiles = generate_random_smiles()
        solvent_info = select_random_solvent()
        temperature = random.uniform(273.15, 373.15)  # 0 °C to 100 °C

        mw = approximate_molecular_weight(smiles)
        diffusion = stokes_einstein_diffusion(
            temperature_K=temperature,
            viscosity_Pa_s=solvent_info["viscosity_Pa_s"],
            molecular_weight_g_mol=mw,
        )

        record = {
            "smiles": smiles,
            "solvent": solvent_info["name"],
            "temperature_K": f"{temperature:.2f}",
            "diffusion_coeff_cm2_s": f"{diffusion:.6e}",
        }
        dataset.append(record)
    return dataset

# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _write_csv(dataset: List[Dict[str, str]], output_path: Path) -> None:
    """Write the synthetic dataset to a CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["smiles", "solvent", "temperature_K", "diffusion_coeff_cm2_s"]
    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in dataset:
            writer.writerow(row)

def _write_source_flag(flag_path: Path, source: str = "synthetic") -> None:
    """Write a JSON flag indicating the data source."""
    flag_path.parent.mkdir(parents=True, exist_ok=True)
    with flag_path.open("w", encoding="utf-8") as f:
        json.dump({"source": source}, f, indent=2)

def main(num_samples: int = 200) -> None:
    """
    Generate a synthetic diffusion dataset and store it under ``data/raw``.

    Parameters
    ----------
    num_samples:
        Number of synthetic records to create.  The default (200) provides a
        modestly sized dataset that is quick to process while still exercising
        the full pipeline.
    """
    project_root = get_project_root()
    raw_dir = project_root / "data" / "raw"
    csv_path = raw_dir / "dataset.csv"
    flag_path = project_root / "data" / "data_source_flag.json"

    dataset = generate_synthetic_dataset(num_samples=num_samples)
    _write_csv(dataset, csv_path)
    _write_source_flag(flag_path, source="synthetic")

    print(f"Synthetic dataset written to: {csv_path}")
    print(f"Data source flag written to: {flag_path}")

if __name__ == "__main__":
    # Allow an optional integer argument to control the number of records.
    import sys

    if len(sys.argv) > 1:
        try:
            n = int(sys.argv[1])
        except ValueError:
            print(f"Invalid sample count '{sys.argv[1]}', using default.")
            n = 200
    else:
        n = 200
    main(num_samples=n)