import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

from utils import get_logger, ensure_directory
from config import get_config, load_config
from aggregate import update_metadata

logger = get_logger(__name__)

def parse_sparc_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Parse a single SPARC galaxy data file.

    Expects columns:
    R (kpc), V (km/s), V_err (km/s), inclination, inclination_err
    """
    logger.info(f"Parsing SPARC file: {file_path}")

    try:
        df = pd.read_csv(
            file_path,
            delim_whitespace=True,
            comment="#",
            header=None,
        )
        if df.shape[1] < 5:
            logger.warning(f"File {file_path} has fewer than 5 columns, skipping.")
            return None

        rotation_data = {
            "r": df.iloc[:, 0].values,
            "v": df.iloc[:, 1].values,
            "v_err": df.iloc[:, 2].values,
            "inclination": df.iloc[:, 3].values,
            "inclination_err": df.iloc[:, 4].values,
        }

        galaxy_name = file_path.stem

        return {
            "name": galaxy_name,
            "file_path": str(file_path),
            "rotation_data": rotation_data,
            "n_points": len(rotation_data["r"]),
        }

    except Exception as e:
        logger.error(f"Failed to parse {file_path}: {e}")
        return None


def parse_galaxy_directory(data_dir: Path) -> List[Dict[str, Any]]:
    """
    Parse all SPARC files in ``data_dir``.
    """
    logger.info(f"Parsing galaxy directory: {data_dir}")

    if not data_dir.exists():
        logger.error(f"Directory does not exist: {data_dir}")
        return []

    galaxies = []
    for file_path in data_dir.iterdir():
        if file_path.suffix.lower() in {".txt", ".dat"}:
            galaxy_data = parse_sparc_file(file_path)
            if galaxy_data:
                galaxies.append(galaxy_data)

    logger.info(f"Parsed {len(galaxies)} galaxies from {data_dir}")
    return galaxies


def apply_quality_filters(
    galaxies: List[Dict[str, Any]],
    min_points: int = 15,
    max_inclination_err: float = 10.0,
) -> List[Dict[str, Any]]:
    """
    Apply the quality criteria required by FR‑003.
    """
    logger.info(
        f"Applying quality filters: min_points={min_points}, "
        f"max_inclination_err={max_inclination_err}"
    )

    filtered = []
    rejected = 0
    reasons = {"low_points": 0, "high_inclination_err": 0}

    for galaxy in galaxies:
        n_points = galaxy["n_points"]
        inc_err = galaxy["rotation_data"]["inclination_err"]
        if n_points < min_points:
            reasons["low_points"] += 1
            rejected += 1
            continue

        # inclination_err may be an array – use the mean.
        mean_err = np.mean(inc_err) if isinstance(inc_err, np.ndarray) else inc_err
        if mean_err >= max_inclination_err:
            reasons["high_inclination_err"] += 1
            rejected += 1
            continue

        filtered.append(galaxy)

    logger.info(
        f"Quality filter complete: {len(filtered)} passed, {rejected} rejected "
        f"(low points: {reasons['low_points']}, high inc err: {reasons['high_inclination_err']})"
    )
    return filtered


def extract_rotation_curves(
    filtered_galaxies: List[Dict[str, Any]]
) -> pd.DataFrame:
    """
    Flatten the filtered galaxy list into a single DataFrame.
    """
    logger.info(f"Extracting rotation curves from {len(filtered_galaxies)} galaxies")
    rows = []
    for galaxy in filtered_galaxies:
        name = galaxy["name"]
        rd = galaxy["rotation_data"]
        n = len(rd["r"])
        for i in range(n):
            rows.append(
                {
                    "galaxy": name,
                    "r": rd["r"][i],
                    "v": rd["v"][i],
                    "v_err": rd["v_err"][i],
                    "inclination": rd["inclination"][i],
                    "inclination_err": rd["inclination_err"][i],
                }
            )
    df = pd.DataFrame(rows)
    logger.info(f"Extracted {len(df)} data points")
    return df


def main() -> int:
    """
    End‑to‑end preprocessing pipeline (T013 → T014 → T015).

    1. Load configuration (fallback to sensible defaults if missing).
    2. Parse raw SPARC files.
    3. Apply quality filters.
    4. Write ``filtered_galaxies.csv``.
    5. Update ``metadata.yaml`` with processing timestamp and version.
    """
    # ------------------------------------------------------------------
    # Configuration handling – we use ``config.get_config`` if the
    # configuration file exists; otherwise we fall back to defaults.
    # ------------------------------------------------------------------
    try:
        cfg = get_config()
    except Exception:
        # Minimal fallback configuration
        cfg = {
            "data": {
                "source_dir": "data/raw",
                "processed_dir": "data/processed",
                "metadata_path": "data/metadata.yaml",
            }
        }

    raw_dir = Path(cfg["data"]["source_dir"])
    processed_dir = Path(cfg["data"]["processed_dir"])
    metadata_path = Path(cfg["data"]["metadata_path"])

    ensure_directory(processed_dir)

    # --------------------------------------------------------------
    # Step 1 – parse raw files
    # --------------------------------------------------------------
    galaxies = parse_galaxy_directory(raw_dir)
    if not galaxies:
        logger.error("No galaxy files found – aborting preprocessing.")
        return 1

    # --------------------------------------------------------------
    # Step 2 – quality filtering (T014)
    # --------------------------------------------------------------
    filtered = apply_quality_filters(
        galaxies, min_points=15, max_inclination_err=10.0
    )
    if not filtered:
        logger.error("All galaxies filtered out – aborting.")
        return 1

    # --------------------------------------------------------------
    # Step 3 – flatten to DataFrame
    # --------------------------------------------------------------
    df = extract_rotation_curves(filtered)

    # --------------------------------------------------------------
    # Step 4 – write CSV (T015 artifact)
    # --------------------------------------------------------------
    output_file = processed_dir / "filtered_galaxies.csv"
    df.to_csv(output_file, index=False)
    logger.info(f"Filtered data written to {output_file}")

    # --------------------------------------------------------------
    # Step 5 – update metadata (T015 requirement)
    # --------------------------------------------------------------
    timestamp = pd.Timestamp.utcnow().isoformat()
    version = "1.1"
    try:
        update_metadata(
            metadata_path=str(metadata_path),
            output_path=str(output_file),
            timestamp=timestamp,
            version=version,
        )
        logger.info(
            f"metadata.yaml updated with timestamp {timestamp} and version {version}"
        )
    except Exception as e:
        logger.error(f"Failed to update metadata: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
