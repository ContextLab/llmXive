"""Preprocess GWTC observational posterior samples to create an i.i.d. point‑estimate dataset.

This module implements the workflow described in task T003:
- Load the GWTC‑1 and GWTC‑2 HDF5 files (``data/raw/gwtc1.h5`` and
  ``data/raw/gwtc2.h5``).
- For each event draw **500** posterior samples (fixed seed
  ``2026-10-24-01``) for the component masses and effective spin.
- Perform a hierarchical bootstrap:
  * Resample events with replacement.
  * For each resampled event randomly pick **one** of its 500 draws.
- Compute ``mass_ratio = m2 / m1`` and retain ``effective_spin``.
- Filter out rows containing any ``NaN`` in the three key fields.
- Abort with a clear error if fewer than 100 valid rows remain.
- Write the resulting CSV to ``data/processed/obs_point_estimates.csv``.
  The CSV contains the columns:
  ``event_id, component_mass_1, component_mass_2, mass_ratio, effective_spin``.

The implementation tolerates minor variations in the HDF5 dataset naming
conventions used by the GWTC releases. It looks for a small set of possible
dataset names for each required quantity. If required datasets are missing
for an event, that event is skipped (with a warning) rather than causing
the whole pipeline to fail.

The module provides a ``preprocess_observations()`` function that returns
the ``Path`` to the created CSV and a ``main()`` entry point for CLI use.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

import h5py
import numpy as np
import pandas as pd

from llmxive_toolkit import paths, get_logger
# Import the download helper to fetch missing raw files on‑demand.
from src.data.download import download_all

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
SEED_STR = "2026-10-24-01"
N_SAMPLES_PER_EVENT = 500
MIN_VALID_ROWS = 100

# Possible dataset names inside each event group (case‑insensitive)
MASS1_KEYS = {"component_mass_1", "mass_1", "mass_1_samples", "primary_mass"}
MASS2_KEYS = {"component_mass_2", "mass_2", "mass_2_samples", "secondary_mass"}
SPIN_KEYS = {"effective_spin", "chi_eff", "effective_spin_samples"}

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def _make_rng(seed_str: str) -> np.random.Generator:
    """Create a deterministic RNG from a human‑readable seed string."""
    # Convert the seed string to an integer hash; use a stable algorithm.
    seed_int = int.from_bytes(seed_str.encode("utf-8"), "big") % (2**32 - 1)
    return np.random.default_rng(seed_int)


def _find_dataset(group: h5py.Group, candidates: set) -> np.ndarray:
    """Return the first matching dataset from *candidates* in *group*.

    Raises:
        KeyError: if none of the candidate names are present.
    """
    for name in candidates:
        if name in group:
            data = group[name][()]
            if isinstance(data, np.ndarray):
                return data
    # Try a case‑insensitive search as a fallback
    lower_map = {k.lower(): k for k in group.keys()}
    for cand in candidates:
        low = cand.lower()
        if low in lower_map:
            data = group[lower_map[low]][()]
            if isinstance(data, np.ndarray):
                return data
    raise KeyError(f"None of {candidates} found in group {group.name}")


def _load_event_draws(
    h5_path: Path, rng: np.random.Generator
) -> Tuple[List[str], Dict[str, np.ndarray], Dict[str, np.ndarray], Dict[str, np.ndarray]]:
    """Load posterior draws for all events in a GWTC HDF5 file.

    Returns:
        event_ids: list of event identifiers (preserved order)
        m1_draws, m2_draws, chi_eff_draws: dict mapping event_id -> (N_SAMPLES,) arrays
    """
    event_ids: List[str] = []
    m1_dict: Dict[str, np.ndarray] = {}
    m2_dict: Dict[str, np.ndarray] = {}
    chi_dict: Dict[str, np.ndarray] = {}

    with h5py.File(h5_path, "r") as h5f:
        for ev_id in h5f.keys():
            grp = h5f[ev_id]
            try:
                m1_all = _find_dataset(grp, MASS1_KEYS)
                m2_all = _find_dataset(grp, MASS2_KEYS)
                chi_all = _find_dataset(grp, SPIN_KEYS)
            except KeyError as exc:
                # Skip events missing required data; log and continue.
                logging.getLogger(__name__).warning(
                    "Skipping event %s due to missing dataset: %s", ev_id, exc
                )
                continue

            # Ensure we have at least N_SAMPLES_PER_EVENT available.
            n_available = int(m1_all.shape[0])
            if n_available < N_SAMPLES_PER_EVENT:
                # Sample with replacement if the posterior is smaller.
                idx = rng.choice(n_available, size=N_SAMPLES_PER_EVENT, replace=True)
            else:
                idx = rng.choice(n_available, size=N_SAMPLES_PER_EVENT, replace=False)

            m1_draws = m1_all[idx]
            m2_draws = m2_all[idx]
            chi_draws = chi_all[idx]

            event_ids.append(ev_id)
            m1_dict[ev_id] = m1_draws
            m2_dict[ev_id] = m2_draws
            chi_dict[ev_id] = chi_draws

    return event_ids, m1_dict, m2_dict, chi_dict


def _hierarchical_bootstrap(
    event_ids: List[str],
    m1_dict: Dict[str, np.ndarray],
    m2_dict: Dict[str, np.ndarray],
    chi_dict: Dict[str, np.ndarray],
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Create an i.i.d. point‑estimate DataFrame via hierarchical bootstrap."""
    n_events = len(event_ids)
    # Resample events with replacement
    resampled_event_ids = rng.choice(event_ids, size=n_events, replace=True)

    rows = []
    for ev_id in resampled_event_ids:
        # Randomly pick one of the 500 draws for this event
        draw_idx = rng.integers(0, N_SAMPLES_PER_EVENT)
        m1 = m1_dict[ev_id][draw_idx]
        m2 = m2_dict[ev_id][draw_idx]
        chi = chi_dict[ev_id][draw_idx]

        # Compute derived quantities
        if m1 == 0:
            # Avoid division‑by‑zero; skip this draw.
            continue
        mass_ratio = m2 / m1

        rows.append(
            {
                "event_id": ev_id,
                "component_mass_1": float(m1),
                "component_mass_2": float(m2),
                "mass_ratio": float(mass_ratio),
                "effective_spin": float(chi),
            }
        )

    df = pd.DataFrame(rows)

    # Filter NaNs in the three key fields
    df = df.dropna(subset=["component_mass_1", "component_mass_2", "effective_spin"])

    return df


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------


def preprocess_observations() -> Path:
    """Run the full preprocessing pipeline.

    Returns:
        Path to the generated CSV file (``data/processed/obs_point_estimates.csv``).

    Raises:
        RuntimeError: if the resulting dataset contains fewer than
          ``MIN_VALID_ROWS`` valid rows.
    """
    log = get_logger(__name__)

    rng = _make_rng(SEED_STR)

    # Resolve raw GWTC file locations
    raw_paths = [
        paths.data("raw", "gwtc1.h5"),
        paths.data("raw", "gwtc2.h5"),
    ]

    # If any required raw file is missing, attempt to download them.
    missing = [p for p in raw_paths if not p.is_file()]
    if missing:
        log.info("Missing GWTC raw files (%s); invoking download routine.", ", ".join(str(p) for p in missing))
        # download_all returns a dict of filename -> Path; it also writes checksums.json.
        download_all()
        # Re‑check existence after download attempt.
        for p in missing:
            if not p.is_file():
                raise FileNotFoundError(f"Required GWTC file not found after download attempt: {p}")

    # Load draws for each file and concatenate
    all_event_ids: List[str] = []
    all_m1: Dict[str, np.ndarray] = {}
    all_m2: Dict[str, np.ndarray] = {}
    all_chi: Dict[str, np.ndarray] = {}

    for raw_path in raw_paths:
        ev_ids, m1_dict, m2_dict, chi_dict = _load_event_draws(raw_path, rng)
        all_event_ids.extend(ev_ids)
        all_m1.update(m1_dict)
        all_m2.update(m2_dict)
        all_chi.update(chi_dict)

    if not all_event_ids:
        raise RuntimeError("No events with complete posterior data were found.")

    # Hierarchical bootstrap to obtain i.i.d. point estimates
    df_point = _hierarchical_bootstrap(all_event_ids, all_m1, all_m2, all_chi, rng)

    if len(df_point) < MIN_VALID_ROWS:
        raise RuntimeError(
            f"Insufficient valid events after preprocessing: {len(df_point)} "
            f"(minimum required is {MIN_VALID_ROWS})."
        )

    out_path = paths.data("processed", "obs_point_estimates.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df_point.to_csv(out_path, index=False)
    log.info(
        "Wrote observational point‑estimate catalog to %s (%d rows)",
        out_path,
        len(df_point),
    )

    return out_path


def main() -> None:
    """CLI entry point."""
    try:
        out = preprocess_observations()
        # Emit a tiny JSON payload for possible downstream consumption.
        print(json.dumps({"output": str(out), "rows": out.stat().st_size}, indent=2))
    except Exception as exc:
        get_logger(__name__).error("preprocess_observations failed: %s", exc)
        raise


if __name__ == "__main__":
    main()