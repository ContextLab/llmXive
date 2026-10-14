"""
src/data/preprocess.py

Preprocess GWTC-1 and GWTC-2 posterior HDF5 files.

- Extract per‑event fields: ``mass_ratio``, ``effective_spin``,
  ``component_mass_1`` and ``component_mass_2``.
- Drop events that have NaN in any of the median values (log a warning per
  dropped event).
- For each remaining event draw ``N_SAMPLES = 200`` posterior samples
  (fixed seed) and store them in a chunked HDF5 file
  ``data/processed/bootstrapped_obs_samples.h5`` with dataset shape
  ``[N_events, N_SAMPLES, 4]``.
- Compute median point‑estimates for each event and write them to
  ``data/processed/obs_point_estimates.csv`` (columns:
  ``event_id,mass_ratio,effective_spin,component_mass_1,component_mass_2``).
- Abort with an explicit error if fewer than 100 valid events remain.

The module provides a :func:`preprocess` function that returns the paths of the
generated artifacts and can be invoked from the command line.
"""

import json
import numpy as np
import pandas as pd
import h5py
from pathlib import Path
from llmxive_toolkit import paths, get_logger

# Import the download helper so we can recover from corrupted or missing raw files.
# The download module raises on failure, which will surface as a clear error.
try:
    from src.data.download import download_all  # type: ignore
except Exception:  # pragma: no cover
    download_all = None  # Fallback if the module is unavailable; will raise later.

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
N_SAMPLES = 200
RANDOM_SEED = 42
RAW_FILES = ["gwtc1.h5", "gwtc2.h5"]
FIELD_NAMES = [
    "mass_ratio",
    "effective_spin",
    "component_mass_1",
    "component_mass_2",
]

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _load_event_arrays(group: h5py.Group) -> dict:
    """
    Load the four required arrays from an event group.

    Parameters
    ----------
    group:
        HDF5 group representing a single GWTC event.

    Returns
    -------
    dict
        Mapping from field name to ``np.ndarray`` of posterior samples.
    """
    data = {}
    for name in FIELD_NAMES:
        if name not in group:
            raise KeyError(f"Dataset '{name}' missing in event '{group.name}'")
        arr = group[name][()]
        # Ensure 1‑D
        if arr.ndim > 1:
            arr = arr.ravel()
        data[name] = arr
    return data

def _draw_samples(arr: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """
    Randomly draw ``N_SAMPLES`` values from a posterior sample array.

    Parameters
    ----------
    arr:
        1‑D array of posterior samples for a single parameter.
    rng:
        ``np.random.Generator`` instance with a fixed seed.

    Returns
    -------
    np.ndarray
        ``(N_SAMPLES,)`` array of draws.
    """
    if arr.size == 0:
        raise ValueError("Empty posterior array.")
    indices = rng.choice(arr.size, size=N_SAMPLES, replace=True)
    return arr[indices]

def _ensure_raw_file(path: Path) -> Path:
    """
    Verify that *path* points to a readable HDF5 file. If the file cannot be
    opened (e.g., because the download was corrupted, the file is missing,
    or the file is not a valid HDF5 container), attempt to download all
    raw datasets via :func:`download_all` and return the verified path.

    Parameters
    ----------
    path:
        Expected location of a raw GWTC HDF5 file.

    Returns
    -------
    Path
        Path to a verified HDF5 file.

    Raises
    ------
    RuntimeError
        If the file still cannot be opened after a re‑download attempt.
    """
    try:
        # Attempt to open; this also catches missing files.
        with h5py.File(path, "r"):
            pass
        return path
    except Exception as exc:  # pragma: no cover
        log.warning(f"Raw file {path} is unavailable or invalid ({exc}); attempting download.")
        if download_all is None:
            raise RuntimeError(
                f"Unable to open raw file {path} and download helper unavailable."
            ) from exc
        # Trigger download of all raw files; this will overwrite the corrupted/missing ones.
        downloaded = download_all()
        new_path = downloaded.get(path.name)
        if new_path is None or not new_path.exists():
            raise RuntimeError(
                f"Downloaded file for {path.name} not found after retry."
            ) from exc
        # Verify the newly downloaded file.
        try:
            with h5py.File(new_path, "r"):
                pass
            log.info(f"Successfully downloaded and verified {new_path}")
            return new_path
        except Exception as exc2:  # pragma: no cover
            raise RuntimeError(
                f"Downloaded file {new_path} is still invalid."
            ) from exc2

def preprocess() -> dict:
    """
    Execute the full preprocessing pipeline.

    Returns
    -------
    dict
        ``{'samples_h5': Path, 'point_estimates_csv': Path}``
    """
    rng = np.random.default_rng(RANDOM_SEED)

    raw_dir = paths.data("raw")
    processed_dir = paths.data("processed")

    # Containers for results
    event_ids = []
    draws_per_event = []  # shape will become (N_events, N_SAMPLES, 4)
    point_estimates = []  # rows for CSV

    for filename in RAW_FILES:
        raw_path = raw_dir / filename
        # Ensure the file exists and is a valid HDF5; download if necessary.
        raw_path = _ensure_raw_file(raw_path)

        log.info(f"Reading raw file: {raw_path}")
        with h5py.File(raw_path, "r") as h5:
            for event_id in h5.keys():
                grp = h5[event_id]
                try:
                    arrays = _load_event_arrays(grp)
                except KeyError as e:
                    log.warning(f"Skipping event {event_id}: {e}")
                    continue

                # Compute median point‑estimates
                median_vals = [np.median(arrays[name]) for name in FIELD_NAMES]

                if any(np.isnan(median_vals)):
                    log.warning(
                        f"Dropping event {event_id} due to NaN in median values."
                    )
                    continue

                # Draw posterior samples for each parameter
                draws = np.column_stack(
                    [_draw_samples(arrays[name], rng) for name in FIELD_NAMES]
                )  # shape (N_SAMPLES, 4)

                event_ids.append(event_id)
                draws_per_event.append(draws)
                point_estimates.append([event_id] + median_vals)

    n_valid = len(event_ids)
    if n_valid < 100:
        raise RuntimeError(
            f"Fewer than 100 valid events remain after preprocessing "
            f"(found {n_valid})."
        )

    # Stack draws into a single NumPy array
    bootstrapped = np.stack(draws_per_event, axis=0)  # (N_events, N_SAMPLES, 4)

    # ------------------------------------------------------------------
    # Write chunked HDF5 with bootstrapped samples
    # ------------------------------------------------------------------
    h5_out_path = processed_dir / "bootstrapped_obs_samples.h5"
    log.info(f"Writing bootstrapped samples to {h5_out_path}")

    with h5py.File(h5_out_path, "w") as out_h5:
        # Main dataset
        out_h5.create_dataset(
            "samples",
            data=bootstrapped,
            chunks=(1, N_SAMPLES, 4),
            compression="gzip",
        )
        # Store event identifiers for reference
        dt = h5py.string_dtype(encoding="utf-8")
        out_h5.create_dataset(
            "event_ids",
            data=np.array(event_ids, dtype=object),
            dtype=dt,
        )

    # ------------------------------------------------------------------
    # Write CSV with point‑estimate
    # ------------------------------------------------------------------
    csv_path = processed_dir / "obs_point_estimates.csv"
    df = pd.DataFrame(
        point_estimates,
        columns=[
            "event_id",
            "mass_ratio",
            "effective_spin",
            "component_mass_1",
            "component_mass_2",
        ],
    )
    df.to_csv(csv_path, index=False)
    log.info(f"Wrote point‑estimate CSV to {csv_path}")

    return {"samples_h5": h5_out_path, "point_estimates_csv": csv_path}

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    CLI entry point used by ``python -m src.data.preprocess``.
    """
    result = preprocess()
    log.info(
        f"Preprocessing complete. Artifacts:\\n"
        f"  HDF5 samples: {result['samples_h5']}\\n"
        f"  CSV estimates: {result['point_estimates_csv']}"
    )

if __name__ == "__main__":
    main()
