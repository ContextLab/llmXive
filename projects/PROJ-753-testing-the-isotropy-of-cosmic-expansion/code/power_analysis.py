"""Power analysis and data verification for the Pantheon+ supernova dataset.

This script performs the following steps:
1. Downloads the Pantheon+ data file from the official GitHub repository.
2. Verifies the download and ensures required columns (ID, RA, DEC, ZHD, MU, MUERR) are present.
3. Computes the SHA-256 checksum and writes provenance to data/raw/metadata.json.
4. Calculates an analytic estimate of the minimum detectable dipole amplitude
   at p < 0.05 with >= 80% power.
5. Runs a pilot Monte-Carlo study to empirically verify the detection power
   at the analytic threshold.
6. Writes the results to data/processed/power_analysis.json.
"""

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from scipy.spatial.transform import Rotation

from llmxive_toolkit import paths, get_logger
from code.rotations import unit_vectors_from_ra_dec, rotate_vectors
from code.utils import calculate_distance_modulus_theoretical

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
DEFAULT_URL = (
    "https://raw.githubusercontent.com/PantheonPlusSH0ES/"
    "DataRelease/main/Pantheon%2B_SH0ES.dat"
)
DEFAULT_DATASET_VERSION = "v1.0"
REQUIRED_COLUMNS = {"ID", "RA", "DEC", "ZHD", "MU", "MUERR"}
NUM_PILOT_MOCKS = 500

# Z-scores for power analysis
# For p < 0.05 (one-sided, as amplitude is positive)
Z_ALPHA = 1.645 
# For 80% power (one-sided)
Z_BETA = 0.842

logger = get_logger(__name__)

def download_file(url: str, destination: Path) -> None:
    """Download a file via streaming request; raise on HTTP errors."""
    logger.info("Downloading Pantheon+ dataset from %s", url)
    with requests.get(url, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        with open(destination, "wb") as out_f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    out_f.write(chunk)
    logger.info("Saved dataset to %s", destination)

def compute_sha256(file_path: Path) -> str:
    """Return the hex SHA-256 checksum of file_path."""
    import hashlib
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha.update(chunk)
    return sha.hexdigest()

def write_metadata(metadata_path: Path, *, dataset_version: str, source_url: str, sha256: str) -> None:
    """Write provenance JSON file."""
    data = {
        "dataset_version": dataset_version,
        "source_url": source_url,
        "sha256": sha256,
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info("Wrote metadata to %s", metadata_path)

def normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise column names: upper-case and strip underscores."""
    df.columns = [col.upper().replace("_", "") for col in df.columns]
    alias_map = {
        "SN": "ID",
        "NAME": "ID",
        "ZCMB": "ZHD",
        "REDSHIFT": "ZHD",
    }
    cols = list(df.columns)
    for i, col in enumerate(cols):
        if col in alias_map:
            cols[i] = alias_map[col]
    df.columns = cols
    return df

def verify_columns(df: pd.DataFrame) -> None:
    """Raise if any required column is missing."""
    norm_cols = set(df.columns)
    missing = REQUIRED_COLUMNS - norm_cols
    if missing:
        raise ValueError(f"Missing required columns in dataset: {missing}")
    logger.info("All required columns are present.")

def estimate_dipole_amplitude(residuals: np.ndarray, weights: np.ndarray, unit_vecs: np.ndarray) -> float:
    """
    Simple inverse-variance weighted dipole estimator.
    D = Σ w_i * r_i * n_i
    amplitude = |D| / Σ w_i
    """
    # residuals: (N,), weights: (N,), unit_vecs: (N, 3)
    D = np.sum(weights[:, None] * residuals[:, None] * unit_vecs, axis=0)
    amp = np.linalg.norm(D) / np.sum(weights)
    return amp

def main() -> None:
    parser = argparse.ArgumentParser(description="Power analysis & data verification")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--version", default=DEFAULT_DATASET_VERSION)
    parser.add_argument("--mocks", type=int, default=NUM_PILOT_MOCKS)
    args = parser.parse_args()

    # 1. Data Verification
    raw_path = paths.data("raw", "Pantheon+_SH0ES.dat")
    metadata_path = paths.data("raw", "metadata.json")

    download_file(args.url, raw_path)
    checksum = compute_sha256(raw_path)
    write_metadata(metadata_path, dataset_version=args.version, source_url=args.url, sha256=checksum)

    # 2. Load and verify columns
    df = pd.read_csv(raw_path, sep=r'\s+', comment="#", dtype=str)
    df = normalise_columns(df)
    verify_columns(df)

    numeric_cols = ["RA", "DEC", "ZHD", "MU", "MUERR"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=numeric_cols)
    
    N = len(df)
    if N == 0:
        raise RuntimeError("No valid supernova entries found.")
    
    sigma_mu = df["MUERR"].median()
    logger.info("Dataset verified: N=%d, median sigma_mu=%.4f", N, sigma_mu)

    # 3. Analytic Power Estimate
    # sigma_amp = sigma_mu / sqrt(N)
    sigma_amp = sigma_mu / math.sqrt(N)
    analytic_min_amp = (Z_ALPHA + Z_BETA) * sigma_amp
    logger.info("Analytic min detectable dipole: %.5f mag", analytic_min_amp)

    # 4. Pilot Monte-Carlo Power Study
    # Use theoretical distance modulus to get residuals (Planck 2018 priors)
    df["MU_TH"] = df["ZHD"].apply(lambda z: calculate_distance_modulus_theoretical(z, h0=67.4, omega_m=0.315))
    df["RESID"] = df["MU"] - df["MU_TH"]
    
    original_vecs = unit_vectors_from_ra_dec(df["RA"].values, df["DEC"].values)
    weights = 1.0 / (df["MUERR"].values ** 2)
    
    rng = np.random.RandomState(42)
    
    # A. Determine critical amplitude from null distribution
    null_amps = []
    for _ in range(args.mocks):
        rot = Rotation.random(random_state=rng)
        vecs = rotate_vectors(original_vecs, rot)
        amp = estimate_dipole_amplitude(df["RESID"].values, weights, vecs)
        null_amps.append(amp)
    
    a_crit = np.percentile(null_amps, 95)
    logger.info("Null distribution 95th percentile (A_crit): %.5f mag", a_crit)

    # B. Test detection power at analytic threshold
    detections = 0
    dipole_dir = np.array([1.0, 0.0, 0.0])
    for _ in range(args.mocks):
        rot = Rotation.random(random_state=rng)
        vecs = rotate_vectors(original_vecs, rot)
        # Inject signal: residuals = r_iso + A * (n . d)
        injected_res = df["RESID"].values + analytic_min_amp * (vecs @ dipole_dir)
        est_amp = estimate_dipole_amplitude(injected_res, weights, vecs)
        if est_amp > a_crit:
            detections += 1
    
    empirical_power = detections / args.mocks
    logger.info("Empirical detection power at threshold: %.3f", empirical_power)

    # 5. Write results
    power_path = paths.data("processed", "power_analysis.json")
    power_result = {
        "dataset_version": args.version,
        "source_url": args.url,
        "sha256": checksum,
        "num_supernovae": N,
        "typical_muerr": sigma_mu,
        "analytic_min_detectable_dipole_mag": analytic_min_amp,
        "empirical_power": empirical_power,
        "min_detectable_dipole_mag": analytic_min_amp,
        "num_mocks": args.mocks,
        "derivation": f"A_min = (Z_alpha={Z_ALPHA} + Z_beta={Z_BETA}) * sigma_mu/sqrt(N)"
    }
    with open(power_path, "w", encoding="utf-8") as f:
        json.dump(power_result, f, indent=2)
    logger.info("Wrote power analysis to %s", power_path)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        logger.error("Power analysis failed: %s", exc)
        sys.exit(1)
