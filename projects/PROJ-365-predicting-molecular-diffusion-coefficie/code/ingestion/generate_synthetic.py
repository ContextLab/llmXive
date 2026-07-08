"""
Synthetic dataset generator for the molecular diffusion coefficient pipeline.

This script creates a CSV file ``data/raw/dataset.csv`` containing a set of
molecule–solvent pairs together with an estimated diffusion coefficient
calculated via the Stokes‑Einstein relation.  The generated data is meant
solely for pipeline validation when real experimental data cannot be
obtained.

The output schema matches the expectations of downstream ingestion code:

    molecule_id               : unique integer identifier
    smiles                    : SMILES string of the solute molecule
    solvent                   : name of the solvent
    temperature_K             : temperature at which D is evaluated (K)
    viscosity_Pas             : dynamic viscosity of the solvent (Pa·s)
    dielectric_constant       : relative permittivity of the solvent
    diffusion_cm2_per_s       : estimated diffusion coefficient (cm²·s⁻¹)

The script can be invoked directly:

    python code/ingestion/generate_synthetic.py

It will create the ``data/raw`` directory if missing and write the CSV.
"""

import csv
import math
import random
from pathlib import Path
from typing import List, Tuple

from utils.config import get_project_root

# -------------------------------------------------------------------------
# Physical constants
# -------------------------------------------------------------------------
K_B = 1.380649e-23           # Boltzmann constant (J·K⁻¹)
AVOGADRO = 6.02214076e23     # Avogadro's number (mol⁻¹)
TEMPERATURE = 298.15         # Standard temperature (K)
DENSITY_SOLUTE = 0.8         # Approx. density of organic solutes (g·cm⁻³)

# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------
def approximate_molecular_weight(smiles: str) -> float:
    """
    Very rough molecular‑weight estimator for aliphatic SMILES consisting
    only of carbon atoms (e.g., C, CC, CCC...).  Hydrogen count is inferred
    from the alkane formula CnH2n+2.

    Parameters
    ----------
    smiles: str
        SMILES string (expected to contain only carbon atoms).

    Returns
    -------
    float
        Molecular weight in grams per mole (g·mol⁻¹).
    """
    n_c = smiles.count('C')
    # Alkane formula: CnH2n+2
    n_h = 2 * n_c + 2
    mw = n_c * 12.01 + n_h * 1.008
    return mw

def stokes_einstein_diffusion(
    mw_g_mol: float,
    viscosity_pas: float,
    temperature_k: float = TEMPERATURE,
    density_g_cm3: float = DENSITY_SOLUTE,
) -> float:
    """
    Compute diffusion coefficient using the Stokes‑Einstein equation.

    Parameters
    ----------
    mw_g_mol: float
        Molecular weight (g·mol⁻¹).
    viscosity_pas: float
        Dynamic viscosity of the solvent (Pa·s).
    temperature_k: float
        Absolute temperature (K). Default 298.15 K.
    density_g_cm3: float
        Approximate density of the solute (g·cm⁻³). Default 0.8 g·cm⁻³.

    Returns
    -------
    float
        Diffusion coefficient in cm²·s⁻¹.
    """
    # Convert molecular weight to kg·mol⁻¹
    mw_kg_mol = mw_g_mol / 1000.0

    # Convert density to kg·m⁻³ (1 g·cm⁻³ = 1000 kg·m⁻³)
    density_kg_m3 = density_g_cm3 * 1000.0

    # Estimate hydrodynamic radius (m) from volume of a sphere:
    #   V = MW / (N_A * density)
    #   r = (3V / (4π))^(1/3)
    volume_m3 = mw_kg_mol / (AVOGADRO * density_kg_m3)
    radius_m = ((3.0 * volume_m3) / (4.0 * math.pi)) ** (1.0 / 3.0)

    # Stokes‑Einstein equation (m²·s⁻¹)
    d_m2_s = K_B * temperature_k / (6.0 * math.pi * viscosity_pas * radius_m)

    # Convert to cm²·s⁻¹ (1 m² = 1e4 cm²)
    return d_m2_s * 1e4

def generate_random_smiles(min_c: int = 1, max_c: int = 10) -> str:
    """
    Produce a simple alkane SMILES with a random number of carbon atoms.
    """
    n_c = random.randint(min_c, max_c)
    return "C" * n_c

def select_random_solvent() -> Tuple[str, float, float]:
    """
    Choose a solvent and return its name, viscosity (Pa·s) and dielectric constant.
    The values are typical at 298 K.
    """
    solvents = [
        ("water", 0.001, 78.5),
        ("ethanol", 0.001095, 24.5),
        ("benzene", 0.000652, 2.28),
        ("acetone", 0.000316, 20.7),
        ("toluene", 0.000590, 2.38),
    ]
    return random.choice(solvents)

def generate_synthetic_dataset(
    num_samples: int = 200,
    output_path: Path = None,
) -> Path:
    """
    Generate a synthetic CSV dataset.

    Parameters
    ----------
    num_samples: int
        Number of rows to generate.
    output_path: Path | None
        Destination CSV file.  If ``None`` the file will be placed at
        ``data/raw/dataset.csv`` relative to the project root.

    Returns
    -------
    Path
        Path to the written CSV file.
    """
    if output_path is None:
        project_root = get_project_root()
        output_path = project_root / "data" / "raw" / "dataset.csv"

    # Ensure the parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "molecule_id",
        "smiles",
        "solvent",
        "temperature_K",
        "viscosity_Pas",
        "dielectric_constant",
        "diffusion_cm2_per_s",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for idx in range(1, num_samples + 1):
            smiles = generate_random_smiles()
            mw = approximate_molecular_weight(smiles)

            solvent, viscosity, dielectric = select_random_solvent()
            diffusion = stokes_einstein_diffusion(
                mw_g_mol=mw,
                viscosity_pas=viscosity,
                temperature_k=TEMPERATURE,
            )

            writer.writerow(
                {
                    "molecule_id": idx,
                    "smiles": smiles,
                    "solvent": solvent,
                    "temperature_K": f"{TEMPERATURE:.2f}",
                    "viscosity_Pas": f"{viscosity:.6f}",
                    "dielectric_constant": f"{dielectric:.2f}",
                    "diffusion_cm2_per_s": f"{diffusion:.6e}",
                }
            )

    return output_path

# -------------------------------------------------------------------------
# CLI entry point
# -------------------------------------------------------------------------
def main() -> None:
    """
    Generate a default synthetic dataset (200 samples) and write it to
    ``data/raw/dataset.csv``.  The function prints the location of the
    created file for user convenience.
    """
    output_file = generate_synthetic_dataset()
    print(f"Synthetic diffusion dataset written to: {output_file}")

if __name__ == "__main__":
    main()