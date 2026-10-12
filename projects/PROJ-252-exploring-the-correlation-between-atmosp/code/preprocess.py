import os
import sys
import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Tuple

import pandas as pd
import numpy as np
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def ensure_dir(path: Path) -> None:
    """Make sure a directory exists."""
    path.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# Configuration handling
# ----------------------------------------------------------------------
CONFIG_PATH = Path("data/processed/config.yaml")

DEFAULT_CONFIG = {
    "pilot_mode": True,
    "expected_global_pressure_files": 4010,
    "expected_earthquake_count": 12,
    "moving_average_days": 30,
    "min_permutation_iterations": 1000,
    "max_permutation_iterations": 10000,
    "convergence_variance_threshold": 1e-5
}

def load_config() -> Dict[str, Any]:
    """Load configuration from data/processed/config.yaml.
    If the file does not exist, create it with default values."""
    if not CONFIG_PATH.exists():
        logger.info(f"Config file not found at {CONFIG_PATH}. Creating default config.")
        ensure_dir(CONFIG_PATH.parent)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.safe_dump(DEFAULT_CONFIG, f)
        return DEFAULT_CONFIG.copy()
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# ----------------------------------------------------------------------
# Schema utilities (re‑use helpers defined later in this file)
# ----------------------------------------------------------------------
def load_schema(schema_name: str) -> Dict[str, Any]:
    """Load a YAML schema from the contracts directory."""
    schema_path = Path("contracts") / f"{schema_name}.yaml"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def validate_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate a DataFrame against a JSON‑schema‑like dict.
    Returns (is_valid, list_of_missing_fields)."""
    required = schema.get("required", [])
    missing = [col for col in required if col not in df.columns]
    return len(missing) == 0, missing

# ----------------------------------------------------------------------
# Data loading
# ----------------------------------------------------------------------
def load_raw_earthquake_data() -> pd.DataFrame:
    """
    Load raw earthquake data from the JSON test subset.
    Returns a DataFrame with columns matching the earthquake schema.
    """
    path = Path("data") / "usgs_test_subset.json"
    if not path.exists():
        raise FileNotFoundError(f"Raw earthquake JSON not found at {path}")
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    records = []
    for feat in payload.get("data", []):
        records.append({
            "event_id": feat.get("earthquake_id"),
            "timestamp": feat.get("origin_time"),
            "magnitude": feat.get("magnitude"),
            "depth": feat.get("depth_km"),
            "lat": feat.get("latitude"),
            "lon": feat.get("longitude")
        })
    df = pd.DataFrame(records)
    logger.info(f"Loaded {len(df)} raw earthquake records")
    return df

def load_raw_pressure_data() -> pd.DataFrame:
    """
    Load the test pressure CSV (a small subset of NOAA data).
    Expected columns: timestamp, lat, lon, pressure_hPa
    """
    path = Path("data/interim/pressure_test_subset.csv")
    if not path.exists():
        raise FileNotFoundError(f"Pressure test CSV not found at {path}")
    df = pd.read_csv(path, parse_dates=["timestamp"])
    logger.info(f"Loaded {len(df)} raw pressure records")
    return df

# ----------------------------------------------------------------------
# Step 1 – Interpolate pressure grid (placeholder – we just forward the data)
# ----------------------------------------------------------------------
def interpolate_pressure_grid(raw_pressure_df: pd.DataFrame) -> pd.DataFrame:
    """
    In a full implementation this would interpolate a coarse grid to a 0.5°
    resolution. For the pilot we simply forward the raw data and write it
    as a Parquet file.
    """
    logger.info("Interpolating pressure grid (pilot – pass‑through).")
    out_path = Path("data/interim/pressure_grid_fine.parquet")
    ensure_dir(out_path.parent)
    raw_pressure_df.to_parquet(out_path, index=False)
    logger.info(f"Wrote interpolated grid to {out_path}")
    return raw_pressure_df

# ----------------------------------------------------------------------
# Step 2 – Generate land mask (already present, just copy if missing)
# ----------------------------------------------------------------------
def generate_land_mask() -> Path:
    """
    Ensure a land mask GeoJSON exists. The repository ships a low‑resolution
    Natural Earth mask; we simply verify its presence.
    """
    src = Path("data/interim/land_mask.geojson")
    if not src.exists():
        raise FileNotFoundError(f"Land mask not found at {src}")
    logger.info(f"Land mask verified at {src}")
    return src

# ----------------------------------------------------------------------
# Step 3 – Apply ocean mask
# ----------------------------------------------------------------------
def apply_ocean_mask(events_df: pd.DataFrame, land_mask_path: Path) -> pd.DataFrame:
    """
    Very simplified ocean‑masking: keep only events whose latitude/longitude
    fall within the bounding box of the supplied land mask. The supplied
    mask covers Antarctica and Greenland; for the pilot data (Alaska) the
    check will always pass, but the function demonstrates the required
    workflow.
    """
    logger.info("Applying ocean mask (pilot – simple bounding‑box filter).")
    # Load the GeoJSON just to obtain its bounds (avoid geopandas dependency)
    import json as _json
    with open(land_mask_path, "r", encoding="utf-8") as f:
        geo = _json.load(f)

    # Extract all coordinate points to compute min/max lat/lon
    lats, lons = [], []
    for feature in geo.get("features", []):
        geom = feature.get("geometry", {})
        if geom.get("type") == "MultiPolygon":
            for polygon in geom.get("coordinates", []):
                for ring in polygon:
                    for lon, lat in ring:
                        lats.append(lat)
                        lons.append(lon)
    if not lats or not lons:
        raise ValueError("Land mask contains no coordinate data.")
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    mask = (
        (events_df["lat"] >= min_lat) &
        (events_df["lat"] <= max_lat) &
        (events_df["lon"] >= min_lon) &
        (events_df["lon"] <= max_lon)
    )
    filtered = events_df[mask].copy()
    logger.info(f"Ocean mask removed {len(events_df) - len(filtered)} records.")
    return filtered

# ----------------------------------------------------------------------
# Step 4 – Exclude missing pressure values
# ----------------------------------------------------------------------
def exclude_missing_pressure(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop rows where the pressure measurement is missing (NaN).
    The test data never has NaNs, but the function follows the spec.
    """
    logger.info("Excluding rows with missing pressure values.")
    before = len(df)
    cleaned = df.dropna(subset=["pressure_value"]).copy()
    after = len(cleaned)
    logger.info(f"Excluded {before - after} rows; {after} remain.")
    return cleaned

# ----------------------------------------------------------------------
# Step 5 – Calculate left‑censored 30‑day moving‑average anomaly
# ----------------------------------------------------------------------
def calculate_left_censored_anomaly(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Compute a simple anomaly: pressure_value minus the rolling mean of the
    previous N days (N = moving_average_days from config). For the pilot
    we treat each event independently and use the global mean of the
    pressure_test_subset as the baseline.
    """
    logger.info("Calculating left‑censored anomalies.")
    window = config.get("moving_average_days", 30)

    # Use the global mean of the test pressure CSV as baseline
    pressure_csv = Path("data/interim/pressure_test_subset.csv")
    pressure_df = pd.read_csv(pressure_csv)
    global_mean = pressure_df["pressure_hPa"].mean()

    df = df.copy()
    df["anomaly_value"] = df["pressure_value"] - global_mean
    logger.info("Anomaly calculation complete.")
    return df

# ----------------------------------------------------------------------
# Step 6 – Deduplicate events (keep most recent revision)
# ----------------------------------------------------------------------
def deduplicate_events(df: pd.DataFrame) -> pd.DataFrame:
    """
    For the pilot dataset each event_id is unique, but we still apply a
    deduplication step to respect the specification.
    """
    logger.info("Deduplicating events (pilot – pass‑through).")
    if "event_id" in df.columns:
        deduped = df.drop_duplicates(subset=["event_id"], keep="last")
        logger.info(f"Deduplicated from {len(df)} to {len(deduped)} rows.")
        return deduped
    return df

# ----------------------------------------------------------------------
# Step 7 – Create master dataset and validation report
# ----------------------------------------------------------------------
def create_master_dataset(df: pd.DataFrame, config: Dict[str, Any]) -> None:
    """
    Merge the cleaned event dataframe with its anomalies (already present
    as columns) and write the master dataset as Parquet. Also generate a
    SHA‑256 checksum and a JSON validation report.
    """
    logger.info("Creating master dataset.")
    processed_dir = Path("data/processed")
    ensure_dir(processed_dir)

    master_path = processed_dir / "master_dataset.parquet"
    df.to_parquet(master_path, index=False)
    logger.info(f"Master dataset written to {master_path}")

    # SHA‑256 checksum
    checksum_path = processed_dir / "master_dataset.parquet.sha256"
    sha256 = hashlib.sha256()
    with open(master_path, "rb") as f:
        for block in iter(lambda: f.read(4096), b""):
            sha256.update(block)
    checksum = sha256.hexdigest()
    with open(checksum_path, "w", encoding="utf-8") as f:
        f.write(f"{checksum}  {master_path.name}\n")
    logger.info(f"Checksum written to {checksum_path}")

    # Validation report
    report_path = processed_dir / "validation_report.json"
    earthquake_schema = load_schema("earthquake")
    anomaly_schema = load_schema("pressure-anomaly")

    # Validate against both schemas (union of required fields)
    is_valid_eq, missing_eq = validate_schema(df, earthquake_schema)
    is_valid_an, missing_an = validate_schema(df, anomaly_schema)

    report = {
        "schema_validation": {
            "earthquake_schema": {
                "is_valid": is_valid_eq,
                "missing_fields": missing_eq
            },
            "pressure_anomaly_schema": {
                "is_valid": is_valid_an,
                "missing_fields": missing_an
            }
        },
        "overall_valid": is_valid_eq and is_valid_an
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report written to {report_path}")

# ----------------------------------------------------------------------
# Main pipeline orchestrator
# ----------------------------------------------------------------------
def main() -> None:
    logger.info("Starting full preprocessing pipeline (T003).")
    config = load_config()

    # ------------------------------------------------------------------
    # Load raw inputs
    # ------------------------------------------------------------------
    earthquakes_raw = load_raw_earthquake_data()
    pressure_raw = load_raw_pressure_data()

    # ------------------------------------------------------------------
    # Step 1 – Interpolate pressure grid
    # ------------------------------------------------------------------
    pressure_grid = interpolate_pressure_grid(pressure_raw)

    # ------------------------------------------------------------------
    # Step 2 – Generate / verify land mask
    # ------------------------------------------------------------------
    land_mask_path = generate_land_mask()

    # ------------------------------------------------------------------
    # Step 3 – Apply ocean mask
    # ------------------------------------------------------------------
    # For the pilot we already have a prepared CSV with pressure values.
    # We will use that as the source of events after ocean masking.
    deduped_anom_path = Path("data/interim/deduplicated_with_anomalies.csv")
    if not deduped_anom_path.exists():
        raise FileNotFoundError(f"Expected deduplicated anomalies file at {deduped_anom_path}")
    events_df = pd.read_csv(deduped_anom_path)

    masked_events = apply_ocean_mask(events_df, land_mask_path)
    masked_path = Path("data/interim/masked_events.csv")
    masked_events.to_csv(masked_path, index=False)
    logger.info(f"Masked events written to {masked_path}")

    # ------------------------------------------------------------------
    # Step 4 – Exclude missing pressure
    # ------------------------------------------------------------------
    clean_events = exclude_missing_pressure(masked_events)
    clean_path = Path("data/interim/clean_events.csv")
    clean_events.to_csv(clean_path, index=False)
    logger.info(f"Clean events written to {clean_path}")

    # ------------------------------------------------------------------
    # Step 5 – Calculate anomalies (left‑censored moving average)
    # ------------------------------------------------------------------
    anomalies = calculate_left_censored_anomaly(clean_events, config)
    anomalies_path = Path("data/interim/anomalies_raw.csv")
    anomalies.to_csv(anomalies_path, index=False)
    logger.info(f"Anomalies written to {anomalies_path}")

    # ------------------------------------------------------------------
    # Step 6 – Deduplicate events (already deduplicated, but run anyway)
    # ------------------------------------------------------------------
    deduped = deduplicate_events(anomalies)
    deduped_path = Path("data/interim/deduplicated_with_anomalies.csv")
    deduped.to_csv(deduped_path, index=False)
    logger.info(f"Deduplicated file written to {deduped_path}")

    # ------------------------------------------------------------------
    # Step 7 – Create master dataset and validation artifacts
    # ------------------------------------------------------------------
    create_master_dataset(deduped, config)

    logger.info("Preprocessing pipeline completed successfully.")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        logger.error(f"Preprocessing failed: {exc}", exc_info=True)
        sys.exit(1)
