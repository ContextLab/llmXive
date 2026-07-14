"""
Synthetic Data Generator for Adsorption Isotherm Parameters.

Generates N=5000 synthetic records linking molecular descriptors to isotherm parameters
with realistic noise and random correlations to validate the data pipeline.

Output: data/raw/synthetic_adsorption_data.csv
"""
import os
import numpy as np
import pandas as pd
from pathlib import Path

# Ensure output directory exists
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "synthetic_adsorption_data.csv"
N_SAMPLES = 5000

# Set seed for reproducibility
np.random.seed(42)

def generate_synthetic_data(n: int = N_SAMPLES) -> pd.DataFrame:
    """
    Generate synthetic adsorption dataset.

    Creates molecular descriptors and corresponding isotherm parameters
    with physically plausible ranges and correlations.

    Args:
        n: Number of samples to generate.

    Returns:
        DataFrame with synthetic adsorption data.
    """
    # Molecular Descriptors (Input Features)
    # Molecular Weight (MW): 16 - 300 g/mol (typical small molecules)
    mw = np.random.uniform(16, 300, n)

    # Polar Surface Area (PSA): 0 - 150 Å²
    psa = np.random.uniform(0, 150, n)

    # Polarizability (α): 1 - 30 Å³
    polarizability = np.random.uniform(1, 30, n)

    # H-Bond Donors: 0 - 5
    hbd = np.random.randint(0, 6, n)

    # H-Bond Acceptors: 0 - 8
    hba = np.random.randint(0, 9, n)

    # Van der Waals Volume (V_vdw): 10 - 200 Å³
    v_vdw = np.random.uniform(10, 200, n)

    # Kinetic Diameter (d_kin): 3 - 10 Å
    kinetic_diameter = np.random.uniform(3, 10, n)

    # Adsorbent Properties
    # Surface Area: 500 - 3000 m²/g
    surface_area = np.random.uniform(500, 3000, n)

    # Pore Volume: 0.2 - 2.0 cm³/g
    pore_volume = np.random.uniform(0.2, 2.0, n)

    # Generate Target Variables (Isotherm Parameters)
    # Langmuir Capacity (q_max): Correlated with surface area and polarizability
    # Base relation: q_max ∝ surface_area * polarizability
    noise_q = np.random.normal(0, 0.1 * np.mean(surface_area) * np.mean(polarizability), n)
    langmuir_capacity = (
        0.0001 * surface_area * polarizability
        + 0.05 * mw
        - 0.02 * kinetic_diameter * 100
        + noise_q
    )
    langmuir_capacity = np.maximum(langmuir_capacity, 0.1)  # Ensure positive

    # Henry Constant (K_H): Correlated with polarizability and H-bond capacity
    # Base relation: K_H ∝ polarizability * (1 + hbd + hba)
    noise_k = np.random.normal(0, 0.1 * np.mean(polarizability) * 10, n)
    henry_constant = (
        0.5 * polarizability * (1 + hbd + hba)
        + 0.01 * v_vdw
        - 0.1 * kinetic_diameter
        + noise_k
    )
    henry_constant = np.maximum(henry_constant, 0.01)  # Ensure positive

    # Material IDs (unique per row for synthetic purposes)
    material_ids = [f"SYNTH_{i:05d}" for i in range(n)]

    # Construct DataFrame
    df = pd.DataFrame({
        "material_id": material_ids,
        "molecular_weight": mw,
        "polar_surface_area": psa,
        "polarizability": polarizability,
        "h_bond_donors": hbd,
        "h_bond_acceptors": hba,
        "van_der_waals_volume": v_vdw,
        "kinetic_diameter": kinetic_diameter,
        "surface_area": surface_area,
        "pore_volume": pore_volume,
        "langmuir_capacity": langmuir_capacity,
        "henry_constant": henry_constant
    })

    return df

def main():
    """Generate and save synthetic data to disk."""
    print(f"Generating {N_SAMPLES} synthetic samples...")
    df = generate_synthetic_data(N_SAMPLES)

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Save to CSV
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Successfully wrote {len(df)} rows to {OUTPUT_FILE}")
    print(f"Columns: {list(df.columns)}")

if __name__ == "__main__":
    main()
