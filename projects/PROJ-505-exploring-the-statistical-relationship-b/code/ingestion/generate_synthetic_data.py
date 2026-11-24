"""
Synthetic data generator for ACE and NOAA datasets.
Used as a fallback when real data fetch fails.
This script now provides a deterministic generator that creates a 20‑year
hourly dataset matching the expected schema for the tests.
"""
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

# Fixed imports – use the fully‑qualified package path.
from code.utils.io import save_parquet
from code.utils.logging import get_logger
from code.config import SEED, RAW_DIR

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def generate_temporal_structure(start_date: datetime, end_date: datetime, freq: str = 'h') -> pd.DatetimeIndex:
    """Generate a regular time index."""
    return pd.date_range(start=start_date, end=end_date, freq=freq)

def generate_synthetic_dataset(start_date: datetime, end_date: datetime, source: str = "ACE") -> pd.DataFrame:
    """
    Generate a multi‑year hourly dataset mimicking ACE/WIND composition or NOAA indices.
    This function is retained for backward compatibility but is not used by the
    test suite.
    """
    np.random.seed(SEED)  # reproducibility
    time_index = generate_temporal_structure(start_date, end_date)
    n_rows = len(time_index)

    df = pd.DataFrame({'timestamp': time_index})

    if source == "ACE":
        # Bulk solar‑wind parameters
        df['V'] = np.random.normal(400, 50, n_rows)          # km/s
        df['Bz'] = np.random.normal(0, 5, n_rows)           # nT
        df['By'] = np.random.normal(0, 5, n_rows)           # nT
        df['Bt'] = np.sqrt(df['Bz']**2 + df['By']**2).abs()
        # Composition ratios
        df['O/Fe'] = np.random.lognormal(mean=-2, sigma=0.5, size=n_rows)
        df['He/H'] = np.random.lognormal(mean=-1.5, sigma=0.3, size=n_rows)
        df['C/O'] = np.random.lognormal(mean=-0.5, sigma=0.4, size=n_rows)
        df['instrument'] = np.random.choice(['SWICS', 'SWICS-2'], n_rows)
    elif source == "NOAA":
        df['Kp'] = np.random.beta(2, 5, n_rows) * 9          # 0‑9
        df['Dst'] = np.random.normal(-20, 15, n_rows)       # nT
    else:
        raise ValueError(f"Unknown source: {source}")

    return df

# ----------------------------------------------------------------------
# Public API required by the unit tests
# ----------------------------------------------------------------------
def generate_solar_wind_composition(
    n_samples: int,
    seed: int,
    start_time: datetime,
    output_dir: Path
) -> pd.DataFrame:
    """
    Generate a deterministic synthetic solar‑wind / geomagnetic dataset.

    Parameters
    ----------
    n_samples : int
        Number of hourly samples to generate.
    seed : int
        Random seed for reproducibility.
    start_time : datetime
        Timestamp of the first sample.
    output_dir : Path
        Directory where the parquet file ``synthetic_solar_wind_hourly.parquet``
        will be written.

    Returns
    -------
    pd.DataFrame
        DataFrame indexed by hourly timestamps with columns:
        ``Kp``, ``Dst``, ``O_Fe``, ``He_H``, ``C_O``, ``V_sw``, ``B_total``.
    """
    rng = np.random.default_rng(seed)

    # Build the hourly index
    timestamps = pd.date_range(start=start_time, periods=n_samples, freq='h')
    df = pd.DataFrame(index=timestamps)

    # Geomagnetic indices
    df['Kp'] = rng.beta(a=2.0, b=5.0, size=n_samples) * 9.0                     # 0‑9
    df['Dst'] = rng.normal(loc=-20.0, scale=15.0, size=n_samples)                # typical range

    # Composition ratios – strictly positive
    df['O_Fe'] = rng.lognormal(mean=-2.0, sigma=0.5, size=n_samples)
    df['He_H'] = rng.lognormal(mean=-1.5, sigma=0.3, size=n_samples)
    df['C_O'] = rng.lognormal(mean=-0.5, sigma=0.4, size=n_samples)

    # Bulk solar‑wind parameters
    df['V_sw'] = rng.uniform(250.0, 1200.0, n_samples)                           # km/s
    df['B_total'] = rng.uniform(1.0, 20.0, n_samples)                            # nT, positive

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write parquet file required by the tests
    parquet_path = output_dir / "synthetic_solar_wind_hourly.parquet"
    save_parquet(df, parquet_path)

    logger.info(f"Synthetic solar‑wind dataset written to {parquet_path}")

    return df

# ----------------------------------------------------------------------
# Command‑line entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    CLI entry point.

    The quick‑start guide calls this script with only ``--output``.
    If ``--start`` / ``--end`` are omitted, a default 20‑year period
    (2000‑01‑01 to 2020‑01‑01, inclusive) is used.
    """
    parser = argparse.ArgumentParser(
        description="Generate deterministic synthetic solar‑wind and geomagnetic data."
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to the final aligned parquet file (e.g. data/processed/synthetic_aligned.parquet).",
    )
    parser.add_argument(
        "--start",
        type=str,
        default="2000-01-01",
        help="Start date (YYYY‑MM‑DD). Defaults to 2000‑01‑01.",
    )
    parser.add_argument(
        "--end",
        type=str,
        default="2020-01-01",
        help="End date (YYYY‑MM‑DD). Defaults to 2020‑01‑01 (20‑year span).",
    )

    args = parser.parse_args()
    output_path = Path(args.output)

    # Resolve dates
    start_date = datetime.strptime(args.start, "%Y-%m-%d")
    end_date = datetime.strptime(args.end, "%Y-%m-%d")

    # Compute number of hourly samples (inclusive of both endpoints)
    total_hours = int((end_date - start_date).total_seconds() // 3600) + 1

    # Generate the dataset
    df = generate_solar_wind_composition(
        n_samples=total_hours,
        seed=SEED,
        start_time=start_date,
        output_dir=output_path.parent,
    )

    # Save the aligned dataset to the user‑specified location
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_parquet(df, output_path)

    # Record generation parameters for provenance
    config_path = RAW_DIR / "synthetic_config.yaml"
    config_data = {
        "source": "synthetic",
        "seed": SEED,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "n_samples": total_hours,
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config_data, f)

    logger.info(f"Synthetic generation parameters saved to {config_path}")

if __name__ == "__main__":
    main()
