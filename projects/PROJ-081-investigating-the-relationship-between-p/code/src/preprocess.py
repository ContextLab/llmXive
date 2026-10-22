"""
preprocess.py
---------------
Implements the data ingestion and preprocessing pipeline.

The core function `load_and_preprocess` accepts a list of raw pandas
DataFrames, concatenates them, harmonises column names, handles
documented metabolite absences, filters incomplete rows, caps herbivory
outliers, standardises metabolite concentrations, validates the result
against the JSON schema, writes the cleaned DataFrame to Parquet and
records a SHA‑256 checksum in a JSON log.
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
    # optional name column that may appear in some sources
    "SpeciesName": "species_name",
    "species_name": "species_name",
}

# Columns that must be present and non‑missing for a row to be kept.
REQUIRED_COLUMNS = [
    "species_id",
    "family",
    "alkaloids",
    "terpenes",
    "phenolics",
    "benzoxazinoids",
    "herbivory_score",
]

# Columns that are always written to the final output (including the
# optional species_name which we add later if absent).
FINAL_COLUMNS = REQUIRED_COLUMNS + ["species_name"]

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
    # 1. Process each raw dataframe individually to detect per‑source
    #    documented absences (i.e. columns that are completely missing from
    #    that source).  We add temporary boolean columns
    #    ``_absent_<metabolite>`` to remember which rows had a documented
    #    absence.
    # ------------------------------------------------------------------
    processed_frames = []
    for idx, raw_df in enumerate(raw_dataframes):
        # Apply column renaming (case‑insensitive)
        rename_map = {}
        for col in raw_df.columns:
            canonical = COLUMN_MAP.get(col, None)
            if canonical:
                rename_map[col] = canonical
        df = raw_df.rename(columns=rename_map)

        # Track which metabolite columns are missing from this source
        missing_mets = [m for m in METABOLITE_COLUMNS if m not in df.columns]
        for met in missing_mets:
            # Insert a column of zeros for the absent metabolite (temporary
            # placeholder – will be overwritten after scaling)
            df[met] = 0.0
            # Record the documented absence for every row of this dataframe
            df[f"_absent_{met}"] = True

        # For metabolite columns that are present, create the absence flag
        # column defaulting to False (will be overwritten later if needed)
        for met in METABOLITE_COLUMNS:
            if f"_absent_{met}" not in df.columns:
                df[f"_absent_{met}"] = False

        # Keep a source identifier (useful for debugging)
        df["_source_idx"] = idx
        processed_frames.append(df)

    # ------------------------------------------------------------------
    # 2. Concatenate all processed frames
    # ------------------------------------------------------------------
    log.info("Concatenating %d processed dataframes.", len(processed_frames))
    df = pd.concat(processed_frames, ignore_index=True, sort=False)

    # Ensure all final columns exist; create missing columns as NaN.
    for col in FINAL_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan

    # ------------------------------------------------------------------
    # 3. Row‑wise filtering of missing required data (excluding the
    #    temporary absence‑flag columns).  True missing values in metabolite
    #    columns cause the row to be dropped.
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
    # 4. Ensure species_name is present (fill with species_id when missing)
    # ------------------------------------------------------------------
    if "species_name" not in df.columns:
        df["species_name"] = df["species_id"].astype(str)
    else:
        missing_name_mask = df["species_name"].isnull()
        df.loc[missing_name_mask, "species_name"] = df.loc[missing_name_mask, "species_id"].astype(str)

    # ------------------------------------------------------------------
    # 5. Herbivory outlier detection & capping (IQR method)
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
    # 6. Z‑score standardisation of metabolite columns
    # ------------------------------------------------------------------
    scaler = StandardScaler()
    metabolite_values = df[METABOLITE_COLUMNS].astype(float)
    scaled = scaler.fit_transform(metabolite_values)
    df[METABOLITE_COLUMNS] = scaled

    # ------------------------------------------------------------------
    # 7. Insert zeros **after** standardisation for documented absences.
    #    The temporary ``_absent_<met>`` flags tell us which rows need
    #    this correction.
    # ------------------------------------------------------------------
    for met in METABOLITE_COLUMNS:
        absent_mask = df[f"_absent_{met}"]
        if absent_mask.any():
            df.loc[absent_mask, met] = 0.0

    # ------------------------------------------------------------------
    # 8. Build the absence_indicator JSON column.
    #    For each row we include only the metabolites whose
    #    ``_absent_<met>`` flag is True.
    # ------------------------------------------------------------------
    def build_indicator(row: pd.Series) -> str:
        indicator = {}
        for met in METABOLITE_COLUMNS:
            if row.get(f"_absent_{met}", False):
                indicator[met] = "documented_absent"
        return json.dumps(indicator)

    df["absence_indicator"] = df.apply(build_indicator, axis=1)

    # Drop the temporary helper columns
    temp_absence_cols = [f"_absent_{met}" for met in METABOLITE_COLUMNS] + ["_source_idx"]
    df.drop(columns=temp_absence_cols, inplace=True, errors="ignore")

    # ------------------------------------------------------------------
    # 9. Validate against JSON schema (if present)
    # ------------------------------------------------------------------
    schema_path = paths.contracts("processed_data.schema.yaml")
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
    except FileNotFoundError:
        log.warning(
            "Processed data schema not found at %s – skipping validation.", schema_path
        )
        schema = None
    except json.JSONDecodeError as e:
        log.error(
            "Failed to parse JSON schema at %s: %s – skipping validation.", schema_path, e
        )
        schema = None

    if schema is not None:
        records = df.to_dict(orient="records")
        for i, rec in enumerate(records):
            try:
                validate(instance=rec, schema=schema)
            except ValidationError as ve:
                log.error("Schema validation failed for row %d: %s", i, ve)
                raise

    # ------------------------------------------------------------------
    # 10. Persist cleaned DataFrame
    # ------------------------------------------------------------------
    out_path = paths.data("processed", "clean.parquet")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False)
    log.info("Cleaned data written to %s", out_path)

    # ------------------------------------------------------------------
    # 11. Compute SHA‑256 checksum and write log JSON
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
    log_path.parent.mkdir(parents=True, exist_ok=True)
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
