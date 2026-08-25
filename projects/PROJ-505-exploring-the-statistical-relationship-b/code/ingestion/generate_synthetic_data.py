"""
Synthetic Data Generator for Solar Wind Composition and Geomagnetic Indices.

This module generates a multi-year hourly dataset mimicking ACE/WIND composition
and NOAA indices distributions. It is seeded for reproducibility and intended
for use as a fallback when real data fetches fail.

IMPORTANT: This generator produces SYNTHETIC data. It must only be used when
real data sources are unavailable. The output artifacts MUST be labeled as 'synthetic'.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict, Any

import numpy as np
import pandas as pd

# Add project root to path to resolve imports relative to code/
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from utils.logging import get_logger, DataIngestionError
from config import get_config

logger = get_logger(__name__)

# Constants for synthetic generation
DEFAULT_START_DATE = "2015-01-01"
DEFAULT_END_DATE = "2017-12-31"
DEFAULT_SEED = 42
DEFAULT_OUTPUT_PATH = "data/raw/synthetic_solar_wind_data.parquet"

# Physical bounds for synthetic generation (approximate realistic ranges)
BOUNDS = {
    "V_sw": (250.0, 800.0),  # km/s
    "N_p": (0.1, 100.0),     # cm^-3
    "B_tot": (0.1, 50.0),    # nT
    "B_z": (-20.0, 20.0),    # nT (GSM)
    "B_y": (-20.0, 20.0),    # nT (GSM)
    "T_p": (1e4, 1e7),       # K
    "He_H": (0.01, 0.15),    # Ratio
    "O_Fe": (0.1, 10.0),     # Ratio
    "C_O": (0.1, 2.0),       # Ratio
    "Dst": (-300.0, 50.0),   # nT
    "Kp": (0.0, 9.0),        # Index (0-9 in 1/3 steps usually, we use continuous)
}

def generate_temporal_structure(n_hours: int, seed: int) -> np.ndarray:
    """
    Generate a time series with realistic solar wind temporal structure.
    Uses a combination of low-frequency trends and high-frequency noise.
    """
    rng = np.random.default_rng(seed)
    t = np.arange(n_hours)

    # Low frequency trend (solar rotation ~27 days ~ 648 hours)
    trend = np.sin(2 * np.pi * t / 648)

    # Medium frequency variability (geomagnetic storms ~ 3-5 days)
    storm_freq = 1 / (4 * 24)
    storm = rng.normal(0, 0.2, n_hours) * np.sin(2 * np.pi * t * storm_freq)

    # High frequency noise
    noise = rng.normal(0, 0.1, n_hours)

    return trend + storm + noise

def generate_synthetic_dataset(
    start_date: str = DEFAULT_START_DATE,
    end_date: str = DEFAULT_END_DATE,
    seed: int = DEFAULT_SEED,
    output_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Generate a synthetic hourly dataset mimicking ACE/WIND and NOAA data.

    Args:
        start_date: Start date string (YYYY-MM-DD).
        end_date: End date string (YYYY-MM-DD).
        seed: Random seed for reproducibility.
        output_path: Optional path to save the parquet file.

    Returns:
        DataFrame with synthetic solar wind and geomagnetic data.
    """
    logger.info(f"Generating synthetic dataset from {start_date} to {end_date} with seed {seed}")

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    if end <= start:
        raise DataIngestionError("End date must be after start date.")

    # Generate hourly timestamps
    timestamps = pd.date_range(start=start, end=end, freq="h")
    n_hours = len(timestamps)
    logger.info(f"Generated {n_hours} hourly timestamps.")

    rng = np.random.default_rng(seed)

    # 1. Generate base temporal structure
    # We use a single base time series to induce correlation between variables
    base_signal = generate_temporal_structure(n_hours, seed)

    # 2. Generate Bulk Parameters (ACE SWEPAM/SWICS)
    # V_sw: Correlated with base signal, log-normal-ish
    v_sw_mean = 450 + 100 * base_signal
    v_sw = np.clip(v_sw_mean + rng.normal(0, 30, n_hours), *BOUNDS["V_sw"])

    # N_p: Anti-correlated with V_sw roughly, log-normal
    n_p_mean = 5.0 * np.exp(-0.002 * (v_sw - 450)) * (1 + 0.2 * base_signal)
    n_p = np.clip(n_p_mean + rng.lognormal(0, 0.3, n_hours), *BOUNDS["N_p"])

    # B_tot: Correlated with high activity
    b_tot_mean = 5 + 3 * base_signal
    b_tot = np.clip(b_tot_mean + rng.exponential(2, n_hours), *BOUNDS["B_tot"])

    # B_z, B_y: Random walk with mean reversion to simulate IMF fluctuations
    b_z = np.cumsum(rng.normal(0, 1, n_hours)) * 0.5
    b_z = b_z - np.mean(b_z) # Center
    b_z = np.clip(b_z, *BOUNDS["B_z"])

    b_y = np.cumsum(rng.normal(0, 1, n_hours)) * 0.5
    b_y = b_y - np.mean(b_y)
    b_y = np.clip(b_y, *BOUNDS["B_y"])

    # T_p: Correlated with V_sw^2 roughly
    t_p = (v_sw / 450)**2 * 1e5 * (1 + rng.normal(0, 0.2, n_hours))
    t_p = np.clip(t_p, *BOUNDS["T_p"])

    # 3. Generate Composition Ratios (ACE SWICS)
    # He/H: Often elevated in CMEs (high V_sw)
    he_h_base = 0.04
    he_h = he_h_base + 0.03 * (v_sw - 400) / 400 + rng.normal(0, 0.01, n_hours)
    he_h = np.clip(he_h, *BOUNDS["He_H"])

    # O/Fe: Elevated in slow wind, lower in fast wind? Or storm dependent.
    # Let's correlate with B_tot (stormy times)
    o_fe_base = 1.0
    o_fe = o_fe_base + 0.5 * base_signal + rng.normal(0, 0.2, n_hours)
    o_fe = np.clip(o_fe, *BOUNDS["O_Fe"])

    # C/O: Relatively stable but with noise
    c_o = 0.8 + 0.2 * base_signal + rng.normal(0, 0.1, n_hours)
    c_o = np.clip(c_o, *BOUNDS["C_O"])

    # 4. Generate Geomagnetic Indices (NOAA)
    # Dst: Driven by coupling functions (V * Bz)
    # Simplified physics: Dst ~ -Integral(V * Bz_south)
    # We'll create a synthetic Dst based on V_sw and B_z
    # If B_z is negative (south), it contributes to storm
    v_bs = np.where(b_z < 0, v_sw * np.abs(b_z), 0)
    # Simple low-pass filter simulation for Dst decay
    dst = np.zeros(n_hours)
    decay = 0.95 # 1-hour decay
    storm_drive = -0.05 * v_bs
    for i in range(1, n_hours):
        dst[i] = dst[i-1] * decay + storm_drive[i]
    # Add noise and offset
    dst = dst + rng.normal(0, 5, n_hours)
    dst = np.clip(dst, *BOUNDS["Dst"])

    # Kp: Correlated with B_tot and V_sw, bounded 0-9
    # Kp is a 3-hour index, but we generate hourly for alignment
    k_p_raw = 2 + 0.005 * v_sw + 0.1 * b_tot + 0.5 * base_signal
    k_p = np.clip(k_p_raw + rng.normal(0, 0.5, n_hours), *BOUNDS["Kp"])

    # 5. Assemble DataFrame
    df = pd.DataFrame({
        "timestamp": timestamps,
        "V_sw": v_sw,
        "N_p": n_p,
        "B_tot": b_tot,
        "B_z": b_z,
        "B_y": b_y,
        "T_p": t_p,
        "He_H": he_h,
        "O_Fe": o_fe,
        "C_O": c_o,
        "Dst": dst,
        "Kp": k_p,
        "source": "synthetic"
    })

    # Ensure no NaNs
    df = df.fillna(0)

    # Save if path provided
    if output_path:
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(out_file, index=False)
        logger.info(f"Saved synthetic data to {out_file}")

    return df

def main():
    """CLI entry point for synthetic data generation."""
    parser = argparse.ArgumentParser(description="Generate synthetic solar wind data.")
    parser.add_argument("--start", type=str, default=DEFAULT_START_DATE, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, default=DEFAULT_END_DATE, help="End date (YYYY-MM-DD)")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed")
    parser.add_argument("--output", type=str, default=None, help="Output path (relative to project root)")
    args = parser.parse_args()

    # Determine output path relative to project root if not absolute
    output_path = args.output
    if output_path and not os.path.isabs(output_path):
        output_path = str(_project_root / output_path)

    try:
        df = generate_synthetic_dataset(
            start_date=args.start,
            end_date=args.end,
            seed=args.seed,
            output_path=output_path
        )
        print(f"Successfully generated {len(df)} rows.")
        print(df.head())
    except Exception as e:
        logger.error(f"Failed to generate synthetic data: {e}")
        raise DataIngestionError(f"Synthetic data generation failed: {e}")

if __name__ == "__main__":
    main()