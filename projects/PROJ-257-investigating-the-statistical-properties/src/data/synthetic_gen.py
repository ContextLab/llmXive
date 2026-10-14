"""Conditional simulation catalog acquisition (T003, US1b).

1. Attempt to download a binary-black-hole population synthesis catalog
   from the configured Zenodo URL, verifying its SHA-256 checksum when one
   is configured. On success the raw file is saved to
   ``data/raw/simulation_catalog_raw.csv``.
2. If the download fails after retries (exponential back-off 1s, 2s, 4s,
   three attempts), fall back to generating a synthetic catalog based on
   the ratified "Power-law mass with independent spin" hypothesis
   (Amendment AM-001, FR-002) using parameters from Abbott et al. 2021,
   a fixed random seed, and >= 100 events.

The final catalog is written to ``data/processed/sim_catalog.csv``
conforming to
``specs/001-investigating-the-statistical-properties/contracts/simulation_catalog.schema.yaml``.
"""

import json
import time
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import requests

from llmxive_toolkit import paths, get_logger
from src.utils.checksum import compute_file_hash

log = get_logger(__name__)

# --- Configuration -----------------------------------------------------
#: Zenodo record for a BBH population-synthesis catalog. No verified
#: public catalog with the required resolved component mass / spin schema
#: has been confirmed; the URL below is the configured candidate.
SIM_CATALOG_URL = "https://zenodo.org/record/1234567/files/simulation_catalog.csv"
#: Expected SHA-256 of the remote catalog (hex). None means no checksum
#: has been published; in that case the hash is computed and recorded
#: after a successful download.
SIM_CATALOG_SHA256: Optional[str] = None

RANDOM_SEED = 42
N_EVENTS = 1000

# "Power-law mass with independent spin" hypothesis parameters
# (Abbott et al. 2021, GWTC-3 population baseline; Amendment AM-001).
MASS_SLOPE_ALPHA = 2.35      # p(m1) ~ m1^-alpha
MASS_MIN = 5.0               # solar masses
MASS_MAX = 95.0              # solar masses
SPIN_MIN = -1.0              # dimensionless aligned spins, independent
SPIN_MAX = 1.0

GENERATION_METHOD = (
    "power-law primary mass p(m1) ~ m1^-2.35 on [5, 95] Msun with "
    "secondary mass uniform on [5, m1] and independent uniform spins "
    "chi ~ U(-1, 1); baseline parameters from Abbott et al. 2021 "
    "(Amendment AM-001, FR-002)"
)
FORMATION_CHANNEL = "synthetic_powerlaw"

REQUIRED_COLUMNS = [
    "event_id",
    "component_mass_1",
    "component_mass_2",
    "mass_ratio",
    "effective_spin",
    "formation_channel",
    "generation_method",
]

# --- Download attempt --------------------------------------------------


def _download_with_retries(url: str, dest: Path, max_attempts: int = 3) -> bool:
    """Try to download *url* to *dest* with exponential back-off.

    Returns True on success, False if all attempts fail (the caller then
    falls back to synthetic generation, as mandated by T003 step 2).
    """
    delays = [1, 2, 4]
    for attempt in range(1, max_attempts + 1):
        try:
            log.info("Download attempt %d/%d for %s", attempt, max_attempts, url)
            with requests.get(url, timeout=60, stream=True) as r:
                r.raise_for_status()
                tmp = dest.with_suffix(dest.suffix + ".part")
                with open(tmp, "wb") as fh:
                    for chunk in r.iter_content(chunk_size=1 << 20):
                        fh.write(chunk)
                tmp.rename(dest)
            return True
        except Exception as exc:  # noqa: BLE001 - any failure triggers retry
            log.warning("Download attempt %d failed: %s", attempt, exc)
            if attempt < max_attempts:
                time.sleep(delays[min(attempt - 1, len(delays) - 1)])
    return False


def try_download_catalog() -> Optional[Path]:
    """Attempt to acquire the external simulation catalog.

    Returns the path to ``data/raw/simulation_catalog_raw.csv`` on
    success, or ``None`` if the download failed after all retries.
    """
    raw_path = paths.data("raw", "simulation_catalog_raw.csv")
    if not _download_with_retries(SIM_CATALOG_URL, raw_path):
        return None
    digest = compute_file_hash(str(raw_path))
    if SIM_CATALOG_SHA256 is not None and digest != SIM_CATALOG_SHA256:
        raise RuntimeError(
            f"Checksum mismatch for {raw_path}: expected {SIM_CATALOG_SHA256}, "
            f"got {digest}"
        )
    log.info("Downloaded simulation catalog %s (sha256=%s)", raw_path, digest)
    return raw_path

# --- Synthetic generation (AM-001 fallback) -----------------------------


def _sample_primary_mass(rng: np.random.Generator, n: int) -> np.ndarray:
    """Inverse-CDF sampling of a truncated power law p(m1) ~ m1^-alpha."""
    a = MASS_SLOPE_ALPHA
    u = rng.random(n)
    lo = MASS_MIN ** (1.0 - a)
    hi = MASS_MAX ** (1.0 - a)
    return (lo + u * (hi - lo)) ** (1.0 / (1.0 - a))


def generate_synthetic_catalog(
    n_events: int = N_EVENTS, seed: int = RANDOM_SEED
) -> pd.DataFrame:
    """Generate the synthetic BBH catalog (AM-001 hypothesis).

    Primary masses follow a truncated power law, secondary masses are
    uniform on [MASS_MIN, m1], and the two aligned component spins are
    independent uniforms on [-1, 1]; chi_eff is the mass‑weighted mean.
    """
    rng = np.random.default_rng(seed)
    m1 = _sample_primary_mass(rng, n_events)
    # Secondary mass uniform between MASS_MIN and the primary mass.
    m2 = rng.uniform(MASS_MIN, 1.0, n_events) * (m1 - MASS_MIN) + MASS_MIN
    chi1 = rng.uniform(SPIN_MIN, SPIN_MAX, n_events)
    chi2 = rng.uniform(SPIN_MIN, SPIN_MAX, n_events)
    chi_eff = (chi1 * m1 + chi2 * m2) / (m1 + m2)

    df = pd.DataFrame(
        {
            "event_id": [f"SIM_{i:04d}" for i in range(n_events)],
            "component_mass_1": m1,
            "component_mass_2": m2,
            "mass_ratio": m2 / m1,
            "effective_spin": chi_eff,
            "formation_channel": FORMATION_CHANNEL,
            "generation_method": GENERATION_METHOD,
        }
    )
    return df[REQUIRED_COLUMNS]


def _validate_catalog(df: pd.DataFrame) -> None:
    """Fail loudly if the catalog violates the contract (SC-007)."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise RuntimeError(f"Simulation catalog missing required fields: {missing}")
    if len(df) < 100:
        raise RuntimeError(
            f"Simulation catalog has only {len(df)} events; >= 100 required"
        )
    if df["component_mass_1"].isna().any() or df["component_mass_2"].isna().any():
        raise RuntimeError("NaN component masses in simulation catalog")
    if not ((df["mass_ratio"] > 0) & (df["mass_ratio"] <= 1)).all():
        raise RuntimeError("mass_ratio outside (0, 1] in simulation catalog")
    if not df["effective_spin"].between(-1.0, 1.0).all():
        raise RuntimeError("effective_spin outside [-1, 1] in simulation catalog")


# --- Orchestration ------------------------------------------------------


def acquire_sim_catalog() -> Path:
    """Run the conditional acquisition and write ``sim_catalog.csv``.

    Returns the path to ``data/processed/sim_catalog.csv``.
    """
    raw = try_download_catalog()
    if raw is not None:
        df = pd.read_csv(raw)
        log.info("Using downloaded simulation catalog (%d events)", len(df))
    else:
        log.warning(
            "External simulation catalog unavailable after retries; "
            "falling back to synthetic generation per Amendment AM-001."
        )
        df = generate_synthetic_catalog()

    _validate_catalog(df)
    out = paths.data("processed", "sim_catalog.csv")
    df.to_csv(out, index=False)
    log.info("Wrote simulation catalog to %s (%d events)", out, len(df))
    return out


def main() -> None:
    out = acquire_sim_catalog()
    df = pd.read_csv(out)
    print(json.dumps({"output": str(out), "n_events": len(df)}, indent=2))


if __name__ == "__main__":
    main()