import json
import logging
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import load_config
from utils.logger import get_logger
from data.preprocess import generate_synthetic_data as preprocess_generate_synthetic

# Constants
MIN_REAL_ROWS = 50
SYNTHETIC_MIN_ROWS = 100
DEFAULT_SEED = 42

logger = get_logger(__name__)

def get_element_density(element_symbol: str) -> Optional[float]:
    """
    Placeholder for fetching element density.
    In a real implementation, this would query a database or API.
    """
    # Mock data for demonstration if real source is unavailable
    mock_densities = {
        "Zr": 6.52, "Cu": 8.96, "Ni": 8.90, "Al": 2.70,
        "Fe": 7.87, "Ti": 4.51, "Pd": 12.02, "Pt": 21.45,
        "La": 6.15, "Ce": 6.77, "Mg": 1.74, "Ca": 1.55
    }
    return mock_densities.get(element_symbol)

def linear_mixing_rule(composition: Dict[str, float], element_densities: Dict[str, float]) -> float:
    """
    Calculates the linear mixing rule density: ρ = Σ(w_i * ρ_i)
    """
    total_density = 0.0
    for element, weight in composition.items():
        density = element_densities.get(element)
        if density is None:
            raise ValueError(f"Unknown element: {element}")
        total_density += weight * density
    return total_density

def generate_composition_from_distribution(elements: List[str], num_elements: int = 3) -> Dict[str, float]:
    """
    Generates a random composition dict with weights summing to 1.0.
    Mimics 'dominant element' distribution if real data exists, else uniform.
    """
    if not elements:
        elements = ["Zr", "Cu", "Ni", "Al", "Fe", "Ti"]

    selected = random.sample(elements, min(num_elements, len(elements)))
    weights = [random.random() for _ in selected]
    total = sum(weights)
    return {elem: w / total for elem, w in zip(selected, weights)}

def generate_synthetic_data(num_rows: int = SYNTHETIC_MIN_ROWS, seed: int = DEFAULT_SEED) -> List[Dict[str, Any]]:
    """
    Generates synthetic metallic glass data.
    Uses linear mixing rule + Gaussian noise.
    """
    random.seed(seed)
    np.random.seed(seed)
    import numpy as np

    elements = ["Zr", "Cu", "Ni", "Al", "Fe", "Ti", "Pd", "Pt", "La", "Ce", "Mg", "Ca"]
    mock_densities = {
        "Zr": 6.52, "Cu": 8.96, "Ni": 8.90, "Al": 2.70,
        "Fe": 7.87, "Ti": 4.51, "Pd": 12.02, "Pt": 21.45,
        "La": 6.15, "Ce": 6.77, "Mg": 1.74, "Ca": 1.55
    }

    data = []
    for _ in range(num_rows):
        comp = generate_composition_from_distribution(elements)
        # Calculate baseline density
        baseline = sum(w * mock_densities[e] for e, w in comp.items())
        # Add Gaussian noise (sigma=0.05 relative to baseline? or absolute? Spec says sigma=0.05)
        # Assuming absolute noise for simplicity, or small relative. Let's do absolute 0.05.
        noise = np.random.normal(0, 0.05)
        density = baseline + noise
        data.append({
            "composition": comp,
            "density": float(density)
        })
    return data

def save_synthetic_data(data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Saves synthetic data to a CSV file.
    """
    import pandas as pd
    rows = []
    for item in data:
        rows.append({
            "composition": json.dumps(item["composition"]),
            "density": item["density"]
        })
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved synthetic data to {output_path} with {len(rows)} rows.")

def check_and_fallback(real_data_path: Path, synthetic_output_path: Path) -> bool:
    """
    Checks if real data exists and has sufficient rows.
    If not, triggers synthetic generation and logs E_DATA_INSUFFICIENT.
    Returns True if fallback was triggered, False otherwise.
    """
    import pandas as pd

    fallback_triggered = False
    source_status = "REAL"
    row_count = 0
    selected_source = "real_data"

    if real_data_path.exists():
        try:
            df = pd.read_csv(real_data_path)
            # Filter rows with missing density
            valid_df = df.dropna(subset=['density'])
            row_count = len(valid_df)

            if row_count >= MIN_REAL_ROWS:
                selected_source = "real_data"
                source_status = "SUFFICIENT"
                logger.info(f"Data source selected: {selected_source} | Rows: {row_count} | Status: {source_status}")
            else:
                # Trigger fallback
                fallback_triggered = True
                selected_source = "synthetic"
                source_status = "INSUFFICIENT_REAL"
                logger.warning(f"E_DATA_INSUFFICIENT: Real data has only {row_count} rows (min: {MIN_REAL_ROWS}). Switching to synthetic mode.")
                logger.info(f"Data source selected: {selected_source} | Rows: {SYNTHETIC_MIN_ROWS} | Status: {source_status}")
        except Exception as e:
            fallback_triggered = True
            selected_source = "synthetic"
            source_status = "READ_ERROR"
            logger.error(f"Error reading real data: {e}. Switching to synthetic mode.")
            logger.warning(f"E_DATA_INSUFFICIENT: Could not read real data. Switching to synthetic mode.")
            logger.info(f"Data source selected: {selected_source} | Rows: {SYNTHETIC_MIN_ROWS} | Status: {source_status}")
    else:
        fallback_triggered = True
        selected_source = "synthetic"
        source_status = "NOT_FOUND"
        logger.warning(f"E_DATA_INSUFFICIENT: Real data file {real_data_path} not found. Switching to synthetic mode.")
        logger.info(f"Data source selected: {selected_source} | Rows: {SYNTHETIC_MIN_ROWS} | Status: {source_status}")

    if fallback_triggered:
        # Generate synthetic data
        synthetic_data = generate_synthetic_data(num_rows=SYNTHETIC_MIN_ROWS)
        save_synthetic_data(synthetic_data, synthetic_output_path)
        return True

    return False

def main():
    """
    Main entry point for data download and fallback logic.
    """
    config = load_config()
    data_dir = config.data_dir
    raw_data_path = data_dir / "raw_data.csv"
    clean_data_path = data_dir / "clean_data.csv"
    synthetic_data_path = data_dir / "synthetic_data.csv"

    # Ensure directories exist
    data_dir.mkdir(parents=True, exist_ok=True)

    # Check for real data and fallback if needed
    # Note: In a full pipeline, T012 would have downloaded raw_data.csv.
    # T014 would have processed it to clean_data.csv.
    # This task (T016) focuses on the logging and fallback logic.
    # We assume raw_data.csv is the input for this check.
    
    # If raw_data.csv exists, we assume T012 ran.
    # If clean_data.csv exists, we assume T014 ran.
    # The check_and_fallback logic is typically part of the preprocessing or download flow.
    # Here we simulate the check against the clean data output of T014.
    
    # Re-reading the task: "Add logging for data source selection and E_DATA_INSUFFICIENT warnings"
    # The logic is implemented in check_and_fallback.
    
    # For this task, we ensure the logging is present and the function works.
    # We call check_and_fallback to demonstrate the logging.
    
    # If clean_data.csv exists, check it. If not, check raw_data.csv.
    check_path = clean_data_path if clean_data_path.exists() else raw_data_path
    
    check_and_fallback(check_path, synthetic_data_path)

    logger.info("Data source selection and fallback check completed.")

if __name__ == "__main__":
    main()
