"""Power analysis and data verification for the Pantheon+ supernova dataset.

This script performs the following steps:
1. Downloads the Pantheon+ data file from the official GitHub repository.
2. Verifies that the download succeeded (HTTP 200) and that the required
   columns are present, handling common column name variations.
3. Computes the SHA‑256 checksum of the downloaded file and writes a
   provenance record to ``data/raw/metadata.json``.
4. Calculates an analytic estimate of the minimum dipole amplitude that can
   be detected with ≥ 80 % power at a significance level of p < 0.05.
5. Runs a pilot Monte‑Carlo study (≥ 500 mock catalogs) that injects a dipole
   of exactly the analytic threshold amplitude, rotates the sky positions
   using the shared rotation utilities, and estimates the dipole amplitude
   with a simple inverse‑variance‑weighted estimator. The fraction of mocks
   in which the injected dipole is recovered is recorded as the empirical
   power.
6. Writes the results to ``data/processed/power_analysis.json``.
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

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Correct canonical URL for the Pantheon+ SH0ES data file.
# The plus sign must be URL‑encoded (%2B) for GitHub raw URLs.
DEFAULT_URL = (
    "https://raw.githubusercontent.com/PantheonPlusSH0ES/"
    "DataRelease/main/Pantheon%2B_SH0ES.dat"
)
DEFAULT_DATASET_VERSION = "v1.0"
# Accept both underscore‑less and underscore‑separated column names.
REQUIRED_COLUMNS = {"ID", "RA", "DEC", "ZHD", "MU", "MUERR"}
NUM_PILOT_MOCKS = 500
# Z‑score for two‑sided 5 % significance
Z_ALPHA = 1.645
# Z‑score for 80 % power (one‑sided)
Z_POWER = 0.842

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
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
    """Return the hex SHA‑256 checksum of ``file_path``."""
    import hashlib

    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha.update(chunk)
    return sha.hexdigest()


def write_metadata(
    metadata_path: Path, *, dataset_version: str, source_url: str, sha256: str
) -> None:
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


def verify_columns(df: pd.DataFrame) -> None:
    """
    Raise if any required column is missing.

    The Pantheon+ release sometimes uses underscores (e.g. ``MU_ERR``);
    we normalise column names by stripping underscores before checking.
    """
    norm_cols = {col.upper().replace("_", "") for col in df.columns}
    missing = REQUIRED_COLUMNS - norm_cols
    if missing:
        raise ValueError(f"Missing required columns in dataset: {missing}")
    logger.info("All required columns are present (after normalisation).")


def theoretical_distance_modulus(
    z: float, h0: float = 73.0, omega_m: float = 0.33
) -> float:
    """Compute distance modulus μ for a flat ΛCDM universe."""
    c = 299792.458

    def e_func(z_val):
        omega_lambda = 1.0 - omega_m
        return math.sqrt(omega_m * (1 + z_val) ** 3 + omega_lambda)

    from scipy.integrate import quad

    integral, _ = quad(lambda zz: 1.0 / e_func(zz), 0, z, epsabs=1e-9, epsrel=1e-9)
    d_c = (c / h0) * integral  # comoving distance in Mpc
    d_l = d_c * (1 + z)  # luminosity distance
    return 5.0 * (math.log10(d_l) + 5.0)


def unit_vectors_from_ra_dec(ra_deg: np.ndarray, dec_deg: np.ndarray) -> np.ndarray:
    """Convert arrays of RA/Dec (degrees) to 3‑D unit vectors."""
    ra = np.radians(ra_deg)
    dec = np.radians(dec_deg)
    x = np.cos(dec) * np.cos(ra)
    y = np.cos(dec) * np.sin(ra)
    z = np.sin(dec)
    return np.stack([x, y, z], axis=1)  # shape (N, 3)


def rotate_vectors(vectors: np.ndarray, rot: Rotation) -> np.ndarray:
    """Apply a scipy Rotation to an array of shape (N,3)."""
    return rot.apply(vectors)


def estimate_dipole_amplitude(
    residuals: np.ndarray, cov_inv: np.ndarray, unit_vecs: np.ndarray
) -> float:
    """
    Simple inverse‑variance weighted dipole estimator.

    D = Σ w_i * r_i * n_i
    amplitude = |D| / Σ w_i
    where w_i = 1/σ_i²
    """
    weights = cov_inv  # already 1/σ²
    D = np.sum(weights[:, None] * residuals[:, None] * unit_vecs, axis=0)
    amp = np.linalg.norm(D) / np.sum(weights)
    return amp


# ----------------------------------------------------------------------
# Main workflow
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Power analysis & data verification"
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help="URL of the Pantheon+ dataset (default: official GitHub raw URL).",
    )
    parser.add_argument(
        "--version",
        default=DEFAULT_DATASET_VERSION,
        help="Dataset version identifier for metadata.",
    )
    parser.add_argument(
        "--mocks",
        type=int,
        default=NUM_PILOT_MOCKS,
        help="Number of pilot Monte‑Carlo mock catalogs (default: 500).",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # 1. Download and verify dataset
    # ------------------------------------------------------------------
    raw_path = paths.data("raw", "Pantheon+_SH0ES.dat")
    metadata_path = paths.data("raw", "metadata.json")

    try:
        download_file(args.url, raw_path)
    except Exception as exc:
        logger.error("Failed to download dataset: %s", exc)
        raise

    # Compute checksum
    checksum = compute_sha256(raw_path)

    # Write provenance
    write_metadata(
        metadata_path,
        dataset_version=args.version,
        source_url=args.url,
        sha256=checksum,
    )

    # ------------------------------------------------------------------
    # 2. Load data and verify required columns
    # ------------------------------------------------------------------
    try:
        df = pd.read_csv(
            raw_path, delim_whitespace=True, comment="#", dtype=str
        )
    except Exception as exc:
        logger.error("Failed to read Pantheon+ file: %s", exc)
        raise

    # Normalise column names (upper‑case, strip underscores) for robust checking
    df.columns = [col.upper().replace("_", "") for col in df.columns]
    verify_columns(df)

    # Cast numeric columns
    numeric_cols = ["RA", "DEC", "ZHD", "MU", "MUERR"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop rows with any missing numeric data
    before = len(df)
    df = df.dropna(subset=numeric_cols)
    after = len(df)
    logger.info(
        "Filtered %d rows with missing data (kept %d).", before - after, after
    )

    # ------------------------------------------------------------------
    # 3. Analytic power estimate
    # ------------------------------------------------------------------
    N = len(df)
    if N == 0:
        raise RuntimeError("No valid supernova entries after filtering.")
    sigma_mu = df["MUERR"].median()  # typical per‑SN uncertainty
    # Uncertainty on the dipole amplitude scales roughly as sigma_mu / sqrt(N)
    sigma_amp = sigma_mu / math.sqrt(N)
    analytic_min_amp = (Z_ALPHA + Z_POWER) * sigma_amp
    logger.info(
        "Analytic minimum detectable dipole amplitude: %.5f mag (N=%d, σ≈%.3f)",
        analytic_min_amp,
        N,
        sigma_mu,
    )

    # ------------------------------------------------------------------
    # 4. Pilot Monte‑Carlo power study
    # ------------------------------------------------------------------
    # Theoretical distance modulus and residuals for the real data
    h0_default, omega_m_default = 73.0, 0.33
    df["MU_TH"] = df["ZHD"].apply(
        lambda z: theoretical_distance_modulus(z, h0=h0_default, omega_m=omega_m_default)
    )
    df["RESID"] = df["MU"] - df["MU_TH"]

    # Unit vectors for original sky positions
    original_vecs = unit_vectors_from_ra_dec(df["RA"].values, df["DEC"].values)

    # Inverse variance weights
    inv_var = 1.0 / (df["MUERR"].values ** 2)

    # Choose a fixed dipole direction (unit vector along x‑axis)
    dipole_dir = np.array([1.0, 0.0, 0.0])

    detections = 0
    # Use numpy RandomState for compatibility with scipy Rotation.random
    rng = np.random.RandomState(42)

    for i in range(args.mocks):
        # Random rotation
        rot = Rotation.random(random_state=rng)
        rotated_vecs = rotate_vectors(original_vecs, rot)

        # Inject dipole of amplitude = analytic_min_amp
        injected_residuals = df["RESID"].values + analytic_min_amp * (
            rotated_vecs @ dipole_dir
        )

        # Estimate dipole amplitude from the mock
        est_amp = estimate_dipole_amplitude(
            residuals=injected_residuals,
            cov_inv=inv_var,
            unit_vecs=rotated_vecs,
        )

        if est_amp >= analytic_min_amp:
            detections += 1

        if (i + 1) % 100 == 0:
            logger.info("Completed %d / %d pilot mocks.", i + 1, args.mocks)

    empirical_power = detections / args.mocks
    logger.info(
        "Pilot study: empirical detection power = %.3f (%d / %d detections)",
        empirical_power,
        detections,
        args.mocks,
    )

    # ------------------------------------------------------------------
    # 5. Write power analysis results
    # ------------------------------------------------------------------
    power_path = paths.data("processed", "power_analysis.json")
    power_path.parent.mkdir(parents=True, exist_ok=True)

    power_result = {
        "dataset_version": args.version,
        "source_url": args.url,
        "sha256": checksum,
        "analytic_min_detectable_dipole_mag": analytic_min_amp,
        "empirical_power": empirical_power,
        "min_detectable_dipole_mag": analytic_min_amp,
        "num_mocks": args.mocks,
        "num_supernovae": N,
        "typical_muerr": sigma_mu,
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