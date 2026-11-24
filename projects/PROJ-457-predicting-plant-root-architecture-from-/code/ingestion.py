"""T006: Data ingestion and merging.

Downloads a verified merged root-phenotype + soil-nutrient dataset from
Hugging Face (verified URLs from research.md), normalises columns,
performs geographic nearest‑neighbour soil matching (<= 10 km) without
re‑using soil points, computes ``merge_success_rate`` (SC-001 / FR-023)
and writes:

  * ``data/raw/merged_dataset.parquet``
  * ``artifacts/reports/metrics.json`` (contains ``merge_success_rate``)

The script FAILS LOUDLY if no verified source can be fetched or if none
contain the required nutrient columns. No synthetic fallback is used.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import requests

from config import get_config, setup_logging

# Verified real data sources (research.md, "Verified" status).
VERIFIED_MERGED_DATASET_URLS: List[str] = [
    "https://huggingface.co/datasets/blanchon/merged_dataset/resolve/main/data/train-00000-of-00001.parquet",
    "https://huggingface.co/datasets/joaosanches/merged_dataset_no_duplicates/resolve/main/data/train-00000-of-00001.parquet",
    "https://huggingface.co/datasets/aizenSosuke/merged_dataset/resolve/main/data/train-00000-of-00001.parquet",
]

MAX_MERGE_DISTANCE_KM = 10.0

# Canonical column names -> accepted aliases (case‑insensitive).
COLUMN_ALIASES: Dict[str, List[str]] = {
    "species": ["species", "species_name", "scientific_name", "taxon"],
    "root_length": ["root_length", "total_root_length", "rootlength"],
    "branching_density": [
        "branching_density",
        "branch_density",
        "root_branching_density",
    ],
    "surface_area": ["surface_area", "root_surface_area"],
    "phosphorus": [
        "phosphorus",
        "phosphorus_concentration",
        "p_concentration",
        "soil_p",
    ],
    "nitrogen": [
        "nitrogen",
        "nitrogen_concentration",
        "n_concentration",
        "soil_n",
    ],
    "latitude": ["latitude", "lat", "y"],
    "longitude": ["longitude", "lon", "long", "x"],
    "data_source_type": [
        "data_source_type",
        "source_type",
        "experiment_type",
        "data_origin",
    ],
    "soil_moisture": ["soil_moisture", "moisture"],
    "temperature": ["temperature", "temp", "mean_temp"],
    "elevation": ["elevation", "alt", "altitude"],
}

ROOT_COLUMNS = ["root_length", "branching_density", "surface_area"]
NUTRIENT_COLUMNS = ["phosphorus", "nitrogen"]


def normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename dataset columns to the canonical project names."""
    df = df.copy()
    lookup = {c.lower().strip(): c for c in df.columns}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in lookup and canonical not in df.columns:
                df = df.rename(columns={lookup[alias]: canonical})
                break
    return df


def download_merged_dataset(
    raw_dir: Path, logger=None
) -> Tuple[pd.DataFrame, str]:
    """Download the first reachable verified merged dataset that contains
    the required nutrient columns.

    Raises RuntimeError if none of the verified URLs can be fetched or if
    none contain the needed columns.
    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    last_error: Optional[Exception] = None
    for url in VERIFIED_MERGED_DATASET_URLS:
        name = url.split("/datasets/")[1].split("/")[0].replace("/", "_")
        dest = raw_dir / f"{name}.parquet"
        try:
            if logger:
                logger.info("Fetching verified dataset: %s", url)
            resp = requests.get(url, timeout=180)
            resp.raise_for_status()
            dest.write_bytes(resp.content)
            df = pd.read_parquet(dest)
            if df.empty:
                raise ValueError("downloaded dataset is empty")
            # Verify required nutrient columns are present
            if not all(col in df.columns for col in NUTRIENT_COLUMNS):
                if logger:
                    logger.warning(
                        "Dataset %s does not contain required nutrient columns; trying next source.",
                        url,
                    )
                continue  # try next URL
            if logger:
                logger.info(
                    "Downloaded %d rows x %d cols from %s",
                    len(df),
                    df.shape[1],
                    url,
                )
            return df, str(dest)
        except Exception as exc:  # noqa: BLE001 - log and try next mirror
            last_error = exc
            if logger:
                logger.warning("Fetch failed for %s: %s", url, exc)
    raise RuntimeError(
        "Could not fetch any verified merged dataset with required nutrient columns "
        f"({len(VERIFIED_MERGED_DATASET_URLS)} URLs tried). "
        f"Last error: {last_error}"
    )


def _haversine_km(
    lat1, lon1, lat2, lon2
):
    """Vectorised haversine distance in kilometres."""
    r = 6371.0088
    lat1 = np.radians(np.asarray(lat1, dtype=float))
    lon1 = np.radians(np.asarray(lon1, dtype=float))
    lat2 = np.radians(np.asarray(lat2, dtype=float))
    lon2 = np.radians(np.asarray(lon2, dtype=float))
    dlat = lat2[:, None] - lat1[None, :]
    dlon = lon2[:, None] - lon1[None, :]
    a = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(lat1)[None, :] * np.cos(lat2)[:, None] * np.sin(dlon / 2.0) ** 2
    )
    return 2 * r * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def merge_nearest_soil(
    root_df: pd.DataFrame,
    soil_df: pd.DataFrame,
    max_distance_km: float = MAX_MERGE_DISTANCE_KM,
) -> pd.DataFrame:
    """Attach soil nutrient values to root records via nearest‑neighbour
    geographic matching within ``max_distance_km``.

    Each soil point may be used **once only** (greedy matching). Rows
    beyond the radius keep NaN nutrients (counted as unmerged).
    """
    out = root_df.copy()

    # Ensure required coordinate columns exist
    if not {"latitude", "longitude"}.issubset(soil_df.columns):
        raise ValueError("soil_df must contain latitude/longitude columns")
    if not {"latitude", "longitude"}.issubset(root_df.columns):
        raise ValueError("root_df must contain latitude/longitude columns")

    # Prepare soil and root tables (drop rows without coordinates)
    soil = soil_df.dropna(subset=["latitude", "longitude"]).reset_index(drop=True)
    roots = root_df.dropna(subset=["latitude", "longitude"]).reset_index()

    # Initialise nutrient columns with NaN if they are missing
    for col in NUTRIENT_COLUMNS:
        if col not in out.columns:
            out[col] = np.nan
    out["merge_distance_km"] = np.nan

    if soil.empty or roots.empty:
        return out

    used_soil_idxs = set()

    # Greedy matching: iterate over roots in original order
    for _, root in roots.iterrows():
        lat_r, lon_r = root["latitude"], root["longitude"]
        # Compute distances to all soil points
        distances = _haversine_km(
            [lat_r], [lon_r], soil["latitude"].to_numpy(), soil["longitude"].to_numpy()
        ).flatten()  # shape (n_soil,)

        # Mask out already‑used soil points and enforce max distance
        valid_mask = np.array(
            [(i not in used_soil_idxs) and (dist <= max_distance_km) for i, dist in enumerate(distances)]
        )

        if not valid_mask.any():
            # No suitable soil point for this root
            continue

        # Choose the nearest available soil point
        nearest_idx = np.argmin(np.where(valid_mask, distances, np.inf))
        used_soil_idxs.add(nearest_idx)

        # Assign nutrient values and distance
        for col in NUTRIENT_COLUMNS:
            if col in soil.columns:
                out.at[root["index"], col] = soil.at[nearest_idx, col]
        out.at[root["index"], "merge_distance_km"] = distances[nearest_idx]

    return out


def compute_merge_success_rate(df: pd.DataFrame) -> float:
    """SC-001 / FR-023: proportion of root records merged with soil data."""
    available = [c for c in NUTRIENT_COLUMNS if c in df.columns]
    if not available:
        return 0.0
    merged = df[available].notna().all(axis=1).sum()
    return float(merged) / float(len(df)) if len(df) else 0.0


def main() -> int:
    config = get_config()
    logger = setup_logging()
    logger.info("Starting T006: data ingestion and merging")

    raw_dir = Path(config["RAW_DATA_PATH"])
    reports_dir = Path(config["REPORTS_PATH"])
    reports_dir.mkdir(parents=True, exist_ok=True)

    # 1. Download a verified merged dataset that contains nutrient columns
    df, source_file = download_merged_dataset(raw_dir, logger)

    # 2. Normalise column names to canonical identifiers
    df = normalise_columns(df)
    logger.info("Normalised columns: %s", sorted(df.columns.tolist()))

    # 3. Perform geographic nearest‑neighbour soil interpolation (<= 10 km)
    #    Only if the dataset does not already have nutrient columns fully populated.
    has_coords = {"latitude", "longitude"}.issubset(df.columns)
    has_nutrients = all(col in df.columns for col in NUTRIENT_COLUMNS)
    if has_coords and has_nutrients:
        # Build a soil reference table (rows that have nutrient values)
        soil_rows = df[NUTRIENT_COLUMNS + ["latitude", "longitude"]].dropna(
            subset=NUTRIENT_COLUMNS + ["latitude", "longitude"]
        )
        if not soil_rows.empty:
            logger.info(
                "Applying nearest‑neighbour soil interpolation (<= %.1f km) over %d soil reference points",
                MAX_MERGE_DISTANCE_KM,
                len(soil_rows),
            )
            df = merge_nearest_soil(df, soil_rows)
    elif not has_nutrients:
        raise RuntimeError(
            "Verified dataset does not contain phosphorus/nitrogen columns; cannot compute nutrient merge."
        )

    # 4. Ensure required output columns exist.
    for col in ROOT_COLUMNS + NUTRIENT_COLUMNS + ["data_source_type"]:
        if col not in df.columns:
            df[col] = np.nan
    if "species" not in df.columns:
        raise RuntimeError("Verified dataset lacks a species column")

    # 5. Compute merge_success_rate (SC-001).
    merge_success_rate = compute_merge_success_rate(df)
    logger.info("merge_success_rate = %.4f", merge_success_rate)

    # 6. Write outputs.
    out_path = raw_dir / "merged_dataset.parquet"
    df.to_parquet(out_path, index=False)
    logger.info("Wrote merged dataset to %s", out_path)

    metrics = {
        "merge_success_rate": merge_success_rate,
        "total_root_records": int(len(df)),
        "merged_root_records": int(df[NUTRIENT_COLUMNS].notna().all(axis=1).sum()),
        "source_file": source_file,
        "max_merge_distance_km": MAX_MERGE_DISTANCE_KM,
    }
    metrics_path = reports_dir / "metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info("Wrote metrics to %s", metrics_path)

    # Print JSON for quick inspection (not required by pipeline)
    print(json.dumps({"merge_success_rate": merge_success_rate}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
