"""
Full resolution × class sweep for Moran's I power analysis.

This script iterates over the resolution levels [30, 60, 120, 240, 480] m
and the two land‑cover classes (forest = 41, urban = 12). For each
combination it:

1. Generates a binary indicator raster.
2. Computes the observed Moran's I statistic and its permutation p‑value.
3. Generates a null distribution via 1 000 random permutations.
4. Simulates 1 000 H1 binary rasters using the calibrated spatial‑lag
   parameter λ.
5. Estimates statistical power (proportion of H1 simulations whose
   Moran's I exceeds the (1‑α) quantile of the null distribution).
6. Writes a row to ``data/results/morans_i_results.csv`` with the
   required columns.
7. Applies Benjamini‑Hochberg correction across all rows and adds the
   adjusted p‑value column ``p_value_adj``.

The script is intended to be invoked via the project ``main.py`` CLI
(``--action sweep``) but can also be run directly:

    python code/full_sweep.py

All output paths are created using ``llmxive_toolkit.paths`` which
guarantees that parent directories exist.
"""

import json
import logging
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from libpysal.weights import lat2W

from llmxive_toolkit import paths, get_logger

# Project‑local imports
from analysis import (
    create_binary_indicator_map,
    calculate_moran_i,
    generate_null_distribution,
    simulate_h1_gibbs,
    calculate_statistical_power,
)
from bh_correction import run_bh_correction

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration (could be moved to a config module)
# ----------------------------------------------------------------------
RESOLUTIONS = [30, 60, 120, 240, 480]          # metres
CLASS_MAP = {
    "forest": 41,   # NLCD class ID for forest
    "urban": 12,    # NLCD class ID for developed/urban
}
PERMUTATIONS = 1000
H1_SIMULATIONS = 1000
ALPHA = 0.05
CSV_PATH = paths.data("results", "morans_i_results.csv")
CALIBRATION_PATH = paths.data("results", "calibration_lambda.json")

# ----------------------------------------------------------------------
def _load_lambda(calibration_path: Path) -> float:
    """Load the calibrated spatial‑lag parameter λ."""
    if not calibration_path.is_file():
        raise FileNotFoundError(f"Calibration file not found: {calibration_path}")
    with calibration_path.open() as fh:
        data = json.load(fh)
    lam = data.get("lambda")
    if lam is None:
        raise ValueError(f"'lambda' key missing in {calibration_path}")
    log.info("Loaded calibrated lambda = %s", lam)
    return float(lam)

# ----------------------------------------------------------------------
def _binary_raster_path(class_name: str, res: int) -> Path:
    """Utility to build the binary raster output path."""
    filename = f"binary_{class_name}_{res}m_co.tif"
    return paths.data("derived", filename)

# ----------------------------------------------------------------------
def _source_raster_path(res: int) -> Path:
    """Path to the aggregated NLCD raster at the given resolution."""
    return paths.data("derived", f"nlcd_{res}m_co.tif")

# ----------------------------------------------------------------------
def _weights_from_array(arr: np.ndarray):
    """Create a queen‑contiguity (lat2W) weight matrix for a 2‑D array."""
    rows, cols = arr.shape
    return lat2W(rows, cols, rook=False)  # queen contiguity

# ----------------------------------------------------------------------
def process_one(resolution: int, class_name: str, class_id: int, lambda_val: float):
    """Run the full analysis for a single (resolution, class) pair."""
    log.info("Processing resolution=%dm, class=%s (ID=%d)", resolution, class_name, class_id)

    src_path = _source_raster_path(resolution)
    if not src_path.is_file():
        raise FileNotFoundError(f"Aggregated raster missing: {src_path}")

    # 1. Create / load binary indicator raster
    binary_path = _binary_raster_path(class_name, resolution)
    if not binary_path.is_file():
        # The function returns the path when a file is written.
        create_binary_indicator_map(
            input_path=src_path,
            output_path=binary_path,
            target_class_id=class_id,
        )
    else:
        log.debug("Binary raster already exists: %s", binary_path)

    # 2. Load binary raster as a 2‑D numpy array
    with rasterio.open(binary_path) as src:
        binary_arr = src.read(1, masked=True).filled(0).astype(np.uint8)

    # 3. Build spatial weights
    weights = _weights_from_array(binary_arr)

    # 4. Compute observed Moran's I and permutation p‑value
    flat = binary_arr.ravel()
    observed_i, p_value = calculate_moran_i(flat, weights)

    # 5. Generate null distribution (permutations)
    null_dist = generate_null_distribution(flat, weights, permutations=PERMUTATIONS)

    # 6. Simulate H1 rasters using Gibbs sampler
    h1_samples = simulate_h1_gibbs(
        binary_map=binary_arr,
        lambda_val=lambda_val,
        seed=42,
        iterations=H1_SIMULATIONS,
        burn_in=H1_SIMULATIONS // 2,
        thin=1,
    )

    # 7. Estimate power
    power = calculate_statistical_power(null_dist, h1_samples, weights=weights, alpha=ALPHA)

    # 8. Assemble result row
    row = {
        "resolution_m": resolution,
        "class_name": class_name,
        "class_id": class_id,
        "observed_morans_i": round(observed_i, 6),
        "p_value": round(p_value, 6),
        "n_permutations": PERMUTATIONS,
        "n_simulations": H1_SIMULATIONS,
        "power_estimate": round(power, 6),
        "is_below_threshold": power < 0.80,
    }
    log.info(
        "Result – res=%dm, class=%s: I=%.4f, p=%.4f, power=%.4f",
        resolution, class_name, observed_i, p_value, power,
    )
    return row

# ----------------------------------------------------------------------
def main() -> None:
    """Entry point for the full sweep."""
    lambda_val = _load_lambda(CALIBRATION_PATH)

    results = []
    for res in RESOLUTIONS:
        for class_name, class_id in CLASS_MAP.items():
            row = process_one(res, class_name, class_id, lambda_val)
            results.append(row)

    # Convert to pandas DataFrame for CSV output
    import pandas as pd

    df = pd.DataFrame(results)
    # Ensure deterministic column order
    column_order = [
        "resolution_m",
        "class_name",
        "class_id",
        "observed_morans_i",
        "p_value",
        "n_permutations",
        "n_simulations",
        "power_estimate",
        "is_below_threshold",
    ]
    df = df[column_order]

    # Write CSV
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CSV_PATH, index=False)
    log.info("Saved raw results to %s", CSV_PATH)

    # Apply Benjamini‑Hochberg correction in‑place
    run_bh_correction(csv_path=CSV_PATH, output_path=CSV_PATH, alpha=ALPHA)
    log.info("Applied Benjamini‑Hochberg correction; final CSV at %s", CSV_PATH)

# ----------------------------------------------------------------------
if __name__ == "__main__":
    main()
