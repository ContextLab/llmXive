import numpy as np
import pandas as pd
from typing import Tuple, Optional, List, Dict, Any
from pathlib import Path
import logging
import json
import sys
import os

# Ensure the project root is on the path when run as a script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_logger, ProjectConfig
from data.models import HarmonizedDataset
from data.parsers import parse_arxiv_2106_08611, parse_arxiv_2305_06325, parse_raw_data

logger = get_logger(__name__)

# Conversion constants
DYNE_TO_NEWTON = 1e-5          # 1 dyne = 1e-5 N
MICROMETER_TO_METER = 1e-6    # 1 µm = 1e-6 m

def dynes_to_newtons(force_dyne: np.ndarray) -> np.ndarray:
    """Convert force from dynes to Newtons."""
    return force_dyne * DYNE_TO_NEWTON

def micrometers_to_meters(separation_um: np.ndarray) -> np.ndarray:
    """Convert separation distance from micrometers to meters."""
    return separation_um * MICROMETER_TO_METER

def convert_to_si(dataset: HarmonizedDataset) -> HarmonizedDataset:
    """
    Convert a raw ``HarmonizedDataset`` (which may contain values in
    dynes and micrometers) to SI units (Newtons, meters).

    The upstream parsers currently populate the fields ``force_n`` and
    ``separation_m`` with the *raw* values (the naming follows the
    historic convention of the project).  This function checks the
    magnitude of the data to decide whether a conversion is required.
    """
    logger.info("Converting dataset to SI units...")

    # Determine if conversion is needed by inspecting the typical magnitude.
    # Dynes are ~1e-5 N, micrometers are ~1e-6 m.  If the values are > 1e-3,
    # we assume they are already in SI.
    force_raw = np.asarray(dataset.force_n)
    sep_raw = np.asarray(dataset.separation_m)

    # Convert force if it looks like dynes
    if np.abs(force_raw).max() > 1e-3:
        logger.debug("Force values appear to be in dynes; converting to Newtons.")
        force_si = dynes_to_newtons(force_raw)
    else:
        logger.debug("Force values already appear to be in Newtons.")
        force_si = force_raw

    # Convert separation if it looks like micrometers
    if sep_raw.max() > 1e-3:
        logger.debug("Separation values appear to be in micrometers; converting to meters.")
        separation_si = micrometers_to_meters(sep_raw)
    else:
        logger.debug("Separation values already appear to be in meters.")
        separation_si = sep_raw

    # Convert covariance matrix units (force squared)
    cov_raw = np.asarray(dataset.covariance_matrix)
    if cov_raw.ndim == 2 and cov_raw.shape[0] == cov_raw.shape[1]:
        # Assume covariance is expressed in (force_units)^2.
        # If we converted force by DYNE_TO_NEWTON, scale covariance by that factor squared.
        if np.abs(force_raw).max() > 1e-3:
            cov_si = cov_raw * (DYNE_TO_NEWTON ** 2)
        else:
            cov_si = cov_raw
    else:
        cov_si = cov_raw

    return HarmonizedDataset(
        separation_m=separation_si,
        force_n=force_si,
        covariance_matrix=cov_si,
        metadata=dataset.metadata,
    )

def align_to_grid(
    datasets: List[HarmonizedDataset],
    grid_resolution: float = 1e-8,
    grid_range: Optional[Tuple[float, float]] = None,
) -> HarmonizedDataset:
    """
    Align multiple ``HarmonizedDataset`` objects onto a common separation grid.

    Edge‑case handling:
    * If the datasets have no overlapping separation range, a warning is logged
      and an empty ``HarmonizedDataset`` (zero‑length arrays) is returned.
    * Missing points within the overlapping region are filled by linear interpolation.
    """
    if not datasets:
        raise ValueError("No datasets provided for alignment.")

    # Determine the common separation range
    if grid_range:
        min_sep, max_sep = grid_range
    else:
        # Intersection of all ranges
        mins = [d.separation_m.min() for d in datasets]
        maxs = [d.separation_m.max() for d in datasets]
        min_sep = max(mins)
        max_sep = min(maxs)

        if min_sep >= max_sep:
            logger.warning(
                "No overlapping separation range found among the provided datasets. "
                "Returning an empty harmonized dataset."
            )
            # Return empty dataset
            return HarmonizedDataset(
                separation_m=np.array([]),
                force_n=np.array([]),
                covariance_matrix=np.empty((0, 0)),
                metadata={"source_ids": []},
            )

        logger.info(
            f"Inferred common separation range: [{min_sep:.2e}, {max_sep:.2e}] m."
        )

    # Build the common grid (inclusive of endpoints)
    num_points = int(np.ceil((max_sep - min_sep) / grid_resolution)) + 1
    common_grid = np.linspace(min_sep, max_sep, num_points)

    # Containers for interpolated forces and per‑run covariance blocks
    interpolated_forces = []
    cov_blocks = []

    for ds in datasets:
        # Mask to the overlapping region
        mask = (ds.separation_m >= min_sep) & (ds.separation_m <= max_sep)
        if not np.any(mask):
            logger.warning(
                f"Dataset {ds.metadata.get('id', 'unknown')} does not overlap with the common grid; skipping."
            )
            continue

        x = ds.separation_m[mask]
        y = ds.force_n[mask]

        # Linear interpolation onto the common grid
        y_interp = np.interp(common_grid, x, y)

        interpolated_forces.append(y_interp)

        # Build diagonal covariance for this block
        # Extract the diagonal (or treat the whole matrix as diagonal if necessary)
        if ds.covariance_matrix.ndim == 2:
            diag = np.diag(ds.covariance_matrix)
        else:
            diag = ds.covariance_matrix
        std = np.sqrt(diag[mask])

        # Interpolate standard deviations onto the grid
        std_interp = np.interp(common_grid, x, std)
        cov_block = np.diag(std_interp ** 2)
        cov_blocks.append(cov_block)

    if not interpolated_forces:
        logger.warning("All datasets were excluded during alignment; returning empty dataset.")
        return HarmonizedDataset(
            separation_m=np.array([]),
            force_n=np.array([]),
            covariance_matrix=np.empty((0, 0)),
            metadata={"source_ids": []},
        )

    # Stack forces and build block‑diagonal covariance
    final_forces = np.concatenate(interpolated_forces)
    final_separations = np.tile(common_grid, len(interpolated_forces))

    # Assemble block‑diagonal covariance matrix
    total_len = final_forces.size
    final_cov = np.zeros((total_len, total_len))
    idx = 0
    for block in cov_blocks:
        block_len = block.shape[0]
        final_cov[idx : idx + block_len, idx : idx + block_len] = block
        idx += block_len

    # Compile metadata
    source_ids = [d.metadata.get("id", "unknown") for d in datasets]

    return HarmonizedDataset(
        separation_m=final_separations,
        force_n=final_forces,
        covariance_matrix=final_cov,
        metadata={"source_ids": source_ids},
    )

def harmonize_experiment(raw_data_path: Path, output_path: Optional[Path] = None) -> HarmonizedDataset:
    """
    Process a raw data file or directory and return a harmonized dataset.

    The function:
    1. Parses the raw CSV(s) using the project's parsers.
    2. Converts all values to SI units.
    3. Aligns the (potentially multiple) runs onto a common grid.
    4. Optionally writes the result to ``output_path`` using ``save_harmonized_data``.
    """
    logger.info(f"Processing raw data from {raw_data_path}")

    # Gather HarmonizedDataset objects from the input path
    datasets: List[HarmonizedDataset] = []

    if raw_data_path.is_dir():
        csv_files = list(raw_data_path.glob("*.csv"))
        if not csv_files:
            raise FileNotFoundError(f"No CSV files found in {raw_data_path}")

        for csv_file in csv_files:
            try:
                ds = parse_raw_data(csv_file)
                if ds is not None:
                    datasets.append(ds)
            except Exception as exc:
                logger.warning(f"Failed to parse {csv_file}: {exc}")
    else:
        # Single file
        ds = parse_raw_data(raw_data_path)
        if ds is not None:
            datasets.append(ds)

    if not datasets:
        raise RuntimeError("No valid datasets could be parsed from the input path.")

    # Convert each dataset to SI
    si_datasets = [convert_to_si(ds) for ds in datasets]

    # Align onto a common grid
    harmonized = align_to_grid(si_datasets)

    # Persist if requested
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        from data.loaders import save_harmonized_data
        save_harmonized_data(harmonized, output_path)
        logger.info(f"Saved harmonized dataset to {output_path}")

    return harmonized

def construct_covariance_matrix(
    separation_m: np.ndarray,
    force_n: np.ndarray,
    uncertainties: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Helper to build a diagonal covariance matrix from uncertainties.
    If ``uncertainties`` are not supplied, a conservative 1 % relative
    uncertainty is assumed.
    """
    if uncertainties is None:
        uncertainties = np.abs(force_n) * 0.01  # 1 % default

    return np.diag(uncertainties ** 2)

def main():
    """
    Entry point for the harmonization script.
    It processes all CSV files found in the configured raw data directory,
    produces a single harmonized dataset, and writes it to the processed
    data directory.
    """
    # Initialise configuration and logging
    config = ProjectConfig()
    # ``setup_logging`` lives in ``config.py``; import lazily to avoid circular import.
    from config import setup_logging
    setup_logging()

    raw_dir = config.data_raw_dir
    processed_dir = config.data_processed_dir

    if not raw_dir.exists():
        logger.error(f"Raw data directory not found: {raw_dir}")
        sys.exit(1)

    processed_dir.mkdir(parents=True, exist_ok=True)

    csv_files = list(raw_dir.glob("*.csv"))
    if not csv_files:
        logger.warning("No CSV files found in raw directory. Skipping harmonization.")
        return

    logger.info(f"Found {len(csv_files)} raw CSV files.")

    # Process each file individually; ``harmonize_experiment`` will return a
    # ``HarmonizedDataset`` for each file (or combined runs within the file).
    per_file_datasets = []
    for csv_file in csv_files:
        try:
            ds = harmonize_experiment(csv_file, None)
            per_file_datasets.append(ds)
        except Exception as exc:
            logger.error(f"Error processing {csv_file}: {exc}")

    if not per_file_datasets:
        logger.error("No datasets were successfully processed.")
        sys.exit(1)

    # Merge all per‑file datasets onto a single common grid
    final_dataset = align_to_grid(per_file_datasets)

    output_path = processed_dir / "harmonized_dataset.json"
    from data.loaders import save_harmonized_data
    save_harmonized_data(final_dataset, output_path)

    logger.info(f"Harmonization complete. Output saved to {output_path}")

if __name__ == "__main__":
    main()
