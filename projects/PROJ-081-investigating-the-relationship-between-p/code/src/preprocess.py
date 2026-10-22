"""
preprocess.py
---------------
Implements the data ingestion and preprocessing pipeline.

The core function `load_and_preprocess` accepts a list of raw pandas
DataFrames, concatenates them, harmonises column names, filters incomplete
rows, imputes documented absences, caps herbivory outliers, standardises
metabolite concentrations, validates the result against the JSON schema,
writes the cleaned DataFrame to Parquet and records a SHA‑256 checksum in a
JSON log.
"""

import json
import hashlib
from pathlib import Path
from typing import List, Dict

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from jsonschema import validate, ValidationError

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper mappings
# ----------------------------------------------------------------------
# Map possible alternate column names to the canonical names expected by the
# downstream analysis. The mapping can be extended as new sources are added.
COLUMN_MAP = {
    "Alkaloid_conc": "alkaloids",
    "Alkaloids": "alkaloids",
    "alkaloid_conc": "alkaloids",
    "Terpenes": "terpenes",
    "terpene_conc": "terpenes",
    "Phenolics": "phenolics",
    "phenolic_conc": "phenolics",
    "Benzoxazinoids": "benzoxazinoids",
    "benzoxazinoid_conc": "benzoxazinoids",
    # species identifiers
    "SpeciesID": "species_id",
    "speciesID": "species_id",
    "species_id": "species_id",
    "Family": "family",
    "family": "family",
    "HerbivoryScore": "herbivory_score",
    "herbivory_score": "herbivory_score",
}

REQUIRED_COLUMNS = [
    "species_id",
    "family",
    "alkaloids",
    "terpenes",
    "phenolics",
    "benzoxazinoids",
    "herbivory_score",
]

METABOLITE_COLUMNS = [
    "alkaloids",
    "terpenes",
    "phenolics",
    "benzoxazinoids",
]

# ----------------------------------------------------------------------
# Core preprocessing function
# ----------------------------------------------------------------------
def load_and_preprocess(raw_dataframes: List[pd.DataFrame]) -> pd.DataFrame:
    """
    Concatenates, cleans, and standardises raw metabolomics‑herbivory data.

    Parameters
    ----------
    raw_dataframes : List[pd.DataFrame]
        List of DataFrames obtained from the three fetch functions
        (`fetch_metabolights`, `fetch_pmn`, `fetch_hpid`).  The DataFrames
        may use heterogeneous column names.

    Returns
    -------
    pd.DataFrame
        Cleaned DataFrame with:
        * harmonised column names,
        * no missing values in any required column,
        * an ``absence_indicator`` column (JSON‑encoded dict) documenting
          metabolite classes that were documented as biologically absent,
        * metabolite columns Z‑scored,
        * capped extreme herbivory scores,
        * written to ``data/processed/clean.parquet``.
    """

    if not raw_dataframes:
        raise ValueError("No raw dataframes provided to the preprocessing pipeline.")

    # ------------------------------------------------------------------
    # 1. Concatenate and harmonise column names
    # ------------------------------------------------------------------
    log.info("Concatenating %d raw dataframes.", len(raw_dataframes))
    df = pd.concat(raw_dataframes, ignore_index=True, sort=False)

    # Apply column renaming (case‑insensitive)
    rename_map = {}
    for col in df.columns:
        canonical = COLUMN_MAP.get(col, None)
        if canonical:
            rename_map[col] = canonical
    df = df.rename(columns=rename_map)

    # Ensure all required columns exist; create missing columns as NaN.
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan

    # ------------------------------------------------------------------
    # 2. Detect documented biological absence (entire column NaN)
    # ------------------------------------------------------------------
    documented_absent: List[str] = []
    for met in METABOLITE_COLUMNS:
        if df[met].isnull().all():
            log.info(
                "Metabolite column '%s' is entirely missing – treating as "
                "documented biological absence and imputing zeros.",
                met,
            )
            df[met] = 0.0
            documented_absent.append(met)

    # ------------------------------------------------------------------
    # 3. Row‑wise filtering of missing required data
    # ------------------------------------------------------------------
    before_rows = df.shape[0]
    df = df.dropna(subset=REQUIRED_COLUMNS, how="any")
    after_rows = df.shape[0]
    log.info(
        "Dropped %d rows containing missing required values (from %d to %d).",
        before_rows - after_rows,
        before_rows,
        after_rows,
    )

    # ------------------------------------------------------------------
    # 4. Herbivory outlier detection & capping (IQR method)
    # ------------------------------------------------------------------
    herb = df["herbivory_score"]
    q1 = herb.quantile(0.25)
    q3 = herb.quantile(0.75)
    iqr = q3 - q1
    upper_whisker = q3 + 1.5 * iqr

    outlier_mask = herb > upper_whisker
    n_capped = int(outlier_mask.sum())
    if n_capped > 0:
        log.info(
            "Capping %d herbivory_score outliers at upper whisker value %.3f.",
            n_capped,
            upper_whisker,
        )
    df.loc[outlier_mask, "herbivory_score"] = upper_whisker

    # ------------------------------------------------------------------
    # 5. Z‑score standardisation of metabolite columns
    # ------------------------------------------------------------------
    scaler = StandardScaler()
    metabolite_values = df[METABOLITE_COLUMNS].astype(float)
    scaled = scaler.fit_transform(metabolite_values)
    df[METABOLITE_COLUMNS] = scaled

    # ------------------------------------------------------------------
    # 6. Build the absence_indicator JSON column
    # ------------------------------------------------------------------
    def build_indicator(_: pd.Series) -> str:
        """Return a JSON string documenting documented absences."""
        indicator = {met: "documented_absent" for met in documented_absent}
        return json.dumps(indicator)

    df["absence_indicator"] = df.apply(build_indicator, axis=1)

    # ------------------------------------------------------------------
    # 7. Validate against JSON schema (if present)
    # ------------------------------------------------------------------
    schema_path = paths.contracts("processed_data.schema.yaml")
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
    except FileNotFoundError:
        log.warning(
            "Processed data schema not found at %s – skipping validation.",
            schema_path,
        )
    else:
        records = df.to_dict(orient="records")
        for i, rec in enumerate(records):
            try:
                validate(instance=rec, schema=schema)
            except ValidationError as ve:
                log.error("Schema validation failed for row %d: %s", i, ve)
                raise

    # ------------------------------------------------------------------
    # 8. Persist cleaned DataFrame
    # ------------------------------------------------------------------
    out_path = paths.data("processed", "clean.parquet")
    df.to_parquet(out_path, index=False)
    log.info("Cleaned data written to %s", out_path)

    # ------------------------------------------------------------------
    # 9. Compute SHA‑256 checksum and write log JSON
    # ------------------------------------------------------------------
    sha256 = hashlib.sha256()
    with open(out_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    checksum = sha256.hexdigest()

    log_json = {
        "clean_parquet_path": str(out_path),
        "checksum_sha256": checksum,
        "row_count": df.shape[0],
        "column_count": df.shape[1],
        "outlier_capped": n_capped,
    }
    log_path = paths.outputs("preprocessing_log.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log_json, f, indent=2)
    log.info("Preprocessing log written to %s", log_path)

    return df

# ----------------------------------------------------------------------
# Command‑line entry point (optional – used by the pipeline script)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    """
    Minimal CLI that loads all CSV/TSV files from ``data/raw``,
    runs the preprocessing pipeline and exits.

    The pipeline script in ``scripts/run_pipeline.sh`` (or the higher‑level
    ``src/run_pipeline.py``) can import ``load_and_preprocess`` directly,
    but this entry point makes the module runnable for ad‑hoc checks.
    """
    import glob

    raw_files = glob.glob(str(paths.data("raw", "*.*")))
    raw_dfs = []
    for fp in raw_files:
        if fp.lower().endswith((".csv", ".tsv")):
            df = pd.read_csv(fp)
        elif fp.lower().endswith((".parquet",)):
            df = pd.read_parquet(fp)
        else:
            log.warning("Unsupported raw file format: %s – skipping.", fp)
            continue
        raw_dfs.append(df)

    if not raw_dfs:
        raise RuntimeError("No raw data files found in data/raw/")

    load_and_preprocess(raw_dfs)
