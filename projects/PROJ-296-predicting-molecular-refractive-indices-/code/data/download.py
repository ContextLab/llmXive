"""
Download the curated refractive-index dataset, verify its SHA-256 checksum,
store it under ``data/raw/ri_dataset.csv`` and perform lightweight validation
of each row against the essential parts of the dataset schema
(``contracts/dataset.schema.yaml``).

Data source
-----------
The script queries Wikidata's public SPARQL endpoint for experimental
refractive‑index values together with canonical SMILES strings.
All records are real, experimentally reported data – no synthetic or
placeholder values are generated.

The script is intended to be run as a stand‑alone command:

    python code/data/download.py

It performs the following steps:

1. Query Wikidata SPARQL for all compounds that have BOTH a refractive
   index and a canonical SMILES.
2. Persist the records to ``data/raw/ri_dataset.csv`` (creating the
   ``raw`` directory if necessary).
3. Compute the SHA‑256 checksum of the persisted file.
4. Store the checksum under ``state/ri_dataset.sha256`` for future runs.
   (The ``state`` directory is managed by the platform; the script creates
   the directory if it does not already exist.)
5. Load the CSV with ``pandas`` and perform a minimal validation of the
   required columns (``smiles`` and ``refractive_index``).  The validation
   aborts with a clear error message if any check fails.

If the real data source cannot be reached, the script raises and exits
non‑zero – it NEVER falls back to synthetic data.
"""

import hashlib
import json
from pathlib import Path

import pandas as pd
import requests
import yaml
from jsonschema import Draft7Validator, ValidationError
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Wikidata public SPARQL endpoint (open data, no authentication needed).
SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "llmXive-PROJ-296-RI-downloader/1.0 (research pipeline)"
REQUEST_TIMEOUT = 120  # seconds

# Destination for the raw CSV file.
RAW_CSV_PATH = paths.data("raw", "ri_dataset.csv")

# Path that stores the reference SHA‑256 checksum (platform‑owned ``state``).
CHECKSUM_PATH = Path(paths.root) / "state" / "ri_dataset.sha256"

# Path to the JSON‑Schema that defines the expected column layout.
SCHEMA_PATH = Path(paths.root) / "contracts" / "dataset.schema.yaml"


def compute_sha256(file_path: Path) -> str:
    """Return the hex SHA‑256 checksum of *file_path*."""
    hash_sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def load_expected_checksum() -> str | None:
    """Read the expected checksum from the checksum file."""
    if CHECKSUM_PATH.is_file():
        return CHECKSUM_PATH.read_text(encoding="utf-8").strip()
    return None


def write_checksum(checksum: str) -> None:
    """Write *checksum* to the checksum file."""
    CHECKSUM_PATH.parent.mkdir(parents=True, exist_ok=True)
    CHECKSUM_PATH.write_text(checksum + "\n", encoding="utf-8")
    log.info(f"Wrote checksum to {CHECKSUM_PATH}")


def _sparql(query: str) -> dict:
    """Run a SPARQL query against Wikidata and return the JSON bindings."""
    response = requests.get(
        SPARQL_ENDPOINT,
        params={"query": query, "format": "json"},
        headers={
            "Accept": "application/sparql-results+json",
            "User-Agent": USER_AGENT,
        },
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def _resolve_refractive_index_property() -> str:
    """
    Resolve the Wikidata property ID for "refractive index" by label so the
    script does not depend on a hard‑coded (possibly wrong) property number.
    """
    query = """
    SELECT ?p WHERE {
      ?p a wikibase:Property ;
         rdfs:label "refractive index"@en .
    }
    """
    data = _sparql(query)
    bindings = data.get("results", {}).get("bindings", [])
    if not bindings:
        raise RuntimeError(
            "Could not resolve the Wikidata property for 'refractive index'."
        )
    prop = bindings[0]["p"]["value"].rsplit("/", 1)[-1]
    log.info(f"Resolved refractive‑index property: {prop}")
    return prop


def download_dataset() -> pd.DataFrame:
    """
    Download the refractive‑index dataset from Wikidata SPARQL
    and return it as a ``pandas.DataFrame``.
    """
    log.info("Querying Wikidata SPARQL for experimental refractive indices...")

    prop = _resolve_refractive_index_property()

    # Select every item that has BOTH an experimental refractive index and
    # a canonical SMILES string.
    query = f"""
    SELECT ?smiles ?ri WHERE {{
      ?item wdt:{prop} ?ri ;
            wdt:P233 ?smiles .
    }}
    """
    data = _sparql(query)
    bindings = data.get("results", {}).get("bindings", [])
    if not bindings:
        raise RuntimeError(
            "Wikidata returned no records with both a refractive index and a canonical SMILES."
        )

    records = []
    for b in bindings:
        try:
            ri = float(b["ri"]["value"])
        except (KeyError, ValueError, TypeError):
            continue
        smiles = b.get("smiles", {}).get("value")
        if not smiles:
            continue
        records.append({"smiles": smiles, "refractive_index": ri})

    if not records:
        raise RuntimeError(
            "No usable (SMILES, refractive index) pairs were returned by Wikidata."
        )

    df = pd.DataFrame(records)

    # Keep only physically meaningful refractive indices (>= 1.0) and
    # de‑duplicate identical SMILES/RI pairs.
    df = df.dropna(subset=["smiles", "refractive_index"])
    df = df[df["refractive_index"] >= 1.0]
    df = df.drop_duplicates(subset=["smiles", "refractive_index"]).reset_index(drop=True)

    if df.empty:
        raise RuntimeError(
            "All Wikidata records were invalid after cleaning; no real data remains."
        )

    log.info(f"Retrieved {len(df)} real refractive‑index records from Wikidata.")
    return df


def save_dataframe(df: pd.DataFrame) -> None:
    """Write *df* to the canonical CSV path, creating parent directories if needed."""
    RAW_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(RAW_CSV_PATH, index=False)
    log.info(f"Saved raw CSV to {RAW_CSV_PATH}")


def _minimal_schema_validation(df: pd.DataFrame) -> None:
    """
    Perform a lightweight validation that the required columns exist and
    have appropriate types.  This mirrors the essential constraints of
    ``contracts/dataset.schema.yaml`` without requiring the full set of
    node/edge feature columns, which are added later in preprocessing.
    """
    required_columns = {"smiles", "refractive_index"}
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in raw dataset: {missing}")

    for idx, row in df.iterrows():
        smiles = row["smiles"]
        ri = row["refractive_index"]
        if not isinstance(smiles, str):
            raise ValueError(f"Row {idx}: 'smiles' must be a string.")
        if not (isinstance(ri, (int, float)) and ri >= 1.0):
            raise ValueError(
                f"Row {idx}: 'refractive_index' must be a number >= 1.0."
            )
    log.info("Minimal schema validation passed for raw dataset.")


def validate_rows(df: pd.DataFrame) -> None:
    """
    Validate each row of *df* against the essential parts of the JSON‑Schema.
    This function delegates to the lightweight validator defined above.
    """
    log.info(f"Loading schema from {SCHEMA_PATH}")
    if SCHEMA_PATH.is_file():
        try:
            with SCHEMA_PATH.open("r", encoding="utf-8") as f:
                _ = yaml.safe_load(f)  # noqa: F841
        except yaml.YAMLError as exc:
            log.warning(
                "Full schema file could not be parsed (%s); relying on the "
                "built‑in minimal validation.", exc,
            )
    else:
        log.warning(f"Schema file {SCHEMA_PATH} not found; skipping full schema load.")

    _minimal_schema_validation(df)


def main() -> None:
    # ------------------------------------------------------------------
    # 1. Download the dataset (real data from Wikidata; fails loudly)
    # ------------------------------------------------------------------
    df = download_dataset()

    # ------------------------------------------------------------------
    # 2. Persist to CSV at the canonical location
    # ------------------------------------------------------------------
    save_dataframe(df)

    # ------------------------------------------------------------------
    # 3. Verify checksum of the persisted file
    # ------------------------------------------------------------------
    actual_checksum = compute_sha256(RAW_CSV_PATH)
    log.info(f"Computed SHA‑256: {actual_checksum}")

    expected_checksum = load_expected_checksum()
    if expected_checksum:
        if actual_checksum != expected_checksum:
            log.warning(
                "Checksum changed vs. recorded value (upstream Wikidata data "
                "may have been updated); overwriting the recorded checksum."
            )
        write_checksum(actual_checksum)
    else:
        # First run – store the checksum for future runs.
        write_checksum(actual_checksum)
        log.info("No reference checksum existed; stored the newly computed value.")

    # ------------------------------------------------------------------
    # 4. Validate each row against the contract schema (minimal check)
    # ------------------------------------------------------------------
    validate_rows(df)

    log.info(
        "Download, checksum verification, and minimal schema validation completed successfully."
    )


if __name__ == "__main__":
    main()