import json
import logging
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from config import Config, load_config
from utils.logger import get_logger

# Constants for element properties (simplified subset for synthetic generation)
# In a full implementation, this would be populated from mendeleev or a larger database
ELEMENT_PROPERTIES = {
    "Zr": {"atomic_mass": 91.22, "density": 6.52},
    "Ti": {"atomic_mass": 47.87, "density": 4.51},
    "Cu": {"atomic_mass": 63.55, "density": 8.96},
    "Ni": {"atomic_mass": 58.69, "density": 8.90},
    "Fe": {"atomic_mass": 55.85, "density": 7.87},
    "Al": {"atomic_mass": 26.98, "density": 2.70},
    "Mg": {"atomic_mass": 24.31, "density": 1.74},
    "Be": {"atomic_mass": 9.01, "density": 1.85},
    "La": {"atomic_mass": 138.91, "density": 6.15},
    "Ce": {"atomic_mass": 140.12, "density": 6.77},
    "Y": {"atomic_mass": 88.91, "density": 4.47},
    "Hf": {"atomic_mass": 178.49, "density": 13.31},
    "Nb": {"atomic_mass": 92.91, "density": 8.57},
    "Mo": {"atomic_mass": 95.95, "density": 10.22},
    "Ta": {"atomic_mass": 180.95, "density": 16.65},
    "W": {"atomic_mass": 183.84, "density": 19.25},
    "Ag": {"atomic_mass": 107.87, "density": 10.49},
    "Au": {"atomic_mass": 196.97, "density": 19.30},
    "Pt": {"atomic_mass": 195.08, "density": 21.45},
    "Pd": {"atomic_mass": 106.42, "density": 12.02},
    "Mn": {"atomic_mass": 54.94, "density": 7.21},
    "Cr": {"atomic_mass": 52.00, "density": 7.19},
    "V": {"atomic_mass": 50.94, "density": 6.11},
}

logger = get_logger(__name__)


def get_element_density(element: str) -> float:
    """
    Get the density of a specific element.
    Falls back to a default value if the element is not in the known list.
    """
    if element in ELEMENT_PROPERTIES:
        return ELEMENT_PROPERTIES[element]["density"]
    # Fallback for unknown elements: use a generic metallic density
    logger.warning(f"Density for element {element} not found, using default 7.0 g/cm³")
    return 7.0


def linear_mixing_rule(composition: Dict[str, float]) -> float:
    """
    Calculate the theoretical density using the linear mixing rule.
    ρ_mix = Σ (w_i * ρ_i)
    where w_i is the mass fraction and ρ_i is the density of element i.
    """
    total_density = 0.0
    for element, mass_fraction in composition.items():
        density = get_element_density(element)
        total_density += mass_fraction * density
    return total_density


def generate_composition_from_distribution(
    available_elements: List[str],
    min_elements: int = 3,
    max_elements: int = 6,
) -> Dict[str, float]:
    """
    Generate a random composition mimicking the distribution of available elements.
    If available_elements is empty, uses a uniform distribution over known elements.
    """
    if not available_elements:
        # Uniform distribution over all known elements
        candidates = list(ELEMENT_PROPERTIES.keys())
    else:
        # Use available elements, potentially augmented with common metallic glass formers
        candidates = available_elements + [
            e for e in ELEMENT_PROPERTIES.keys() if e not in available_elements
        ]
        # Remove duplicates while preserving order
        candidates = list(dict.fromkeys(candidates))

    # Randomly select number of elements in the alloy
    num_elements = random.randint(min_elements, max_elements)
    selected_elements = random.sample(candidates, min(num_elements, len(candidates)))

    # Generate random mass fractions that sum to 1
    fractions = np.random.dirichlet(np.ones(len(selected_elements)))
    composition = {elem: float(f) for elem, f in zip(selected_elements, fractions)}

    return composition


def generate_synthetic_data(
    num_rows: int = 100,
    seed: int = 42,
    existing_data_path: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Generate synthetic metallic glass data.

    Logic:
    1. If existing_data_path is provided and contains data, extract the 'dominant_element'
       distribution from the 'clean' real data to mimic the composition.
    2. If no real data exists, use a uniform distribution over known elements.
    3. Generate compositions using the selected distribution.
    4. Calculate density using the linear mixing rule + Gaussian noise (σ=0.05).

    Args:
        num_rows: Number of rows to generate.
        seed: Random seed for reproducibility.
        existing_data_path: Path to existing real data to derive distribution from.

    Returns:
        pd.DataFrame with columns 'composition' (dict) and 'density' (float).
    """
    random.seed(seed)
    np.random.seed(seed)

    available_elements = []
    if existing_data_path and existing_data_path.exists():
        logger.info(f"Reading existing data from {existing_data_path} to derive element distribution.")
        try:
            # Try to read as JSON or CSV depending on format
            if existing_data_path.suffix == ".csv":
                df_real = pd.read_csv(existing_data_path)
            elif existing_data_path.suffix == ".json":
                with open(existing_data_path, "r") as f:
                    data = json.load(f)
                    # Handle if it's a list of dicts or a dict with a key
                    if isinstance(data, list):
                        df_real = pd.DataFrame(data)
                    else:
                        # Assume key is 'data' or similar
                        df_real = pd.DataFrame(data.get("data", []))

            # Extract dominant element if column exists, otherwise parse composition
            if "dominant_element" in df_real.columns:
                available_elements = df_real["dominant_element"].dropna().unique().tolist()
            elif "composition" in df_real.columns:
                # Parse composition strings/dicts to find elements
                elements_found = set()
                for comp in df_real["composition"]:
                    if isinstance(comp, str):
                        # Simple parsing for "Element1:0.5,Element2:0.5"
                        parts = comp.split(",")
                        for part in parts:
                            if ":" in part:
                                elem = part.split(":")[0].strip()
                                elements_found.add(elem)
                    elif isinstance(comp, dict):
                        elements_found.update(comp.keys())
                available_elements = list(elements_found)

            logger.info(f"Derived {len(available_elements)} unique elements from real data.")
        except Exception as e:
            logger.warning(f"Failed to parse existing data for distribution: {e}. Using uniform distribution.")
            available_elements = []

    rows = []
    for _ in range(num_rows):
        composition = generate_composition_from_distribution(available_elements)

        # Calculate baseline density
        baseline_density = linear_mixing_rule(composition)

        # Add Gaussian noise (σ=0.05 relative to baseline? or absolute? Spec says σ=0.05)
        # Assuming absolute noise for simplicity, or relative if densities are small.
        # Given typical densities (2-20), 0.05 absolute is very small.
        # Let's assume 0.05 * baseline to make it proportional, or just 0.05 absolute as per strict spec.
        # Spec: "Gaussian noise (σ=0.05)". Usually implies absolute unless specified "relative".
        noise = np.random.normal(0, 0.05)
        density = baseline_density + noise

        rows.append({
            "composition": json.dumps(composition), # Store as JSON string for CSV compatibility
            "density": float(density)
        })

    df_synthetic = pd.DataFrame(rows)
    logger.info(f"Generated {len(df_synthetic)} rows of synthetic data.")
    return df_synthetic


def save_synthetic_data(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the synthetic data DataFrame to a CSV file.
    """
    df.to_csv(output_path, index=False)
    logger.info(f"Synthetic data saved to {output_path}")


def check_and_fallback(
    clean_data_path: Path,
    min_rows: int = 50,
    synthetic_rows: int = 100,
    seed: int = 42,
) -> bool:
    """
    Check if the clean data has enough rows. If not, generate synthetic data.

    Args:
        clean_data_path: Path to the cleaned real data (or where it should be).
        min_rows: Minimum required rows.
        synthetic_rows: Number of synthetic rows to generate if fallback is needed.
        seed: Random seed.

    Returns:
        True if fallback was triggered and synthetic data generated, False otherwise.
    """
    if not clean_data_path.exists():
        logger.warning(f"Clean data file {clean_data_path} not found. Triggering fallback.")
        df_synthetic = generate_synthetic_data(
            num_rows=synthetic_rows,
            seed=seed,
            existing_data_path=None
        )
        save_synthetic_data(df_synthetic, clean_data_path.with_name("synthetic_data.csv"))
        return True

    try:
        df = pd.read_csv(clean_data_path)
        # Check if composition is a string that needs parsing or already a dict representation
        # For counting rows, we just need the length.
        row_count = len(df)
    except Exception as e:
        logger.error(f"Error reading clean data for row count check: {e}")
        row_count = 0

    if row_count < min_rows:
        logger.warning(
            f"Clean data has {row_count} rows, which is less than the required {min_rows}. "
            f"Triggering synthetic data generation."
        )
        # Use the existing clean_data_path as the source to derive distribution if possible
        # even if it's small, to mimic the "dominant element" distribution.
        df_synthetic = generate_synthetic_data(
            num_rows=synthetic_rows,
            seed=seed,
            existing_data_path=clean_data_path
        )
        # Save to synthetic_data.csv as per task description
        output_path = clean_data_path.with_name("synthetic_data.csv")
        save_synthetic_data(df_synthetic, output_path)
        return True

    logger.info(f"Clean data has {row_count} rows. No fallback needed.")
    return False


def main():
    """
    Main entry point for the download module.
    This function is primarily responsible for triggering the fallback logic
    if the preprocessing step (T014) results in insufficient data.
    """
    config = load_config()
    clean_data_path = config.data_dir / "clean_data.csv"

    logger.info("Running download.py fallback check...")
    triggered = check_and_fallback(
        clean_data_path=clean_data_path,
        min_rows=50,
        synthetic_rows=100,
        seed=42
    )

    if triggered:
        logger.info("Synthetic data generation completed successfully.")
    else:
        logger.info("Real data is sufficient; synthetic data generation not triggered.")


if __name__ == "__main__":
    main()