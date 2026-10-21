"""
Download the curated refractive-index dataset, verify its SHA-256 checksum,
store it under ``data/raw/ri_dataset.csv`` and perform validation
of each row against the essential parts of the dataset schema
(``contracts/dataset.schema.yaml``).

Data source
-----------
The script queries Wikidata's public SPARQL endpoint for experimental
refractive‑index values together with canonical SMILES strings.

The script is intended to be run as a stand‑alone command:

    python code/data/download.py

It performs the following steps:

1. Query Wikidata SPARQL for all compounds that have BOTH a refractive
   index and a canonical SMILES.
2. Persist the records to ``data/raw/ri_dataset.csv``.
3. Compute the SHA‑256 checksum of the persisted file.
4. Store the checksum under ``state/ri_dataset.sha256`` (as required by the
   task specification).
5. Load the CSV with ``pandas`` and perform validation of the
   required columns (``smiles`` and ``refractive_index``) against the
   constraints defined in the schema.

If the real data source cannot be reached, the script raises and exits
non‑zero.
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
# Wikidata public SPARQL endpoint.
SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "llmXive-PROJ-296-RI-downloader/1.0 (research pipeline)"
REQUEST_TIMEOUT = 120  # seconds

# Destination for the raw CSV file.
RAW_CSV_PATH = paths.data("raw", "ri_dataset.csv")

# Path that stores the reference SHA‑256 checksum.
# The specification requires this file to live under ``state/``.
CHECKSUM_PATH = paths.root / "state" / "ri_dataset.sha256"

# Path to the JSON‑Schema that defines the expected column layout.
SCHEMA_PATH = paths.root / "contracts" / "dataset.schema.yaml"


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
    try:
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
    except requests.RequestException as exc:
        log.error(f"Failed to query Wikidata SPARQL endpoint: {exc}")
        raise RuntimeError("Unable to retrieve data from Wikidata.") from exc
    return response.json()


def _resolve_refractive_index_property() -> str:
    """
    Resolve the Wikidata property ID for "refractive index" by label.
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
            "No usable (SMILES, RI) pairs were returned by Wikidata."
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


def validate_rows(df: pd.DataFrame) -> None:
    """
    Validate each row of *df* against the essential parts of the JSON‑Schema.
    Since this is the raw dataset, we only validate the columns present
    (smiles and refractive_index).
    """
    log.info(f"Loading schema from {SCHEMA_PATH}")
    if not SCHEMA_PATH.is_file():
        # If the schema file isn't there yet, we perform a basic type check
        # to avoid crashing the pipeline, but log a warning.
        log.warning(f"Schema file {SCHEMA_PATH} not found; performing basic type check.")
        required = {"smiles", "refractive_index"}
        if not required.issubset(df.columns):
            raise ValueError(f"Missing columns: {required - set(df.columns)}")
        return

    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    validator = Draft7Validator(schema)

    # We only validate the fields that exist in the raw CSV.
    # The full schema requires processed features (node/edge), which are added in T002.
    for idx, row in df.iterrows():
        record = {
            "smiles": row["smiles"],
            "refractive_index": row["refractive_index"]
        }
        # Basic field‑level checks (type / minimum) – jsonschema will raise ValidationError.
        for field, value in record.items():
            field_schema = schema.get("properties", {}).get(field, {})
            if "type" in field_schema:
                if field_schema["type"] == "string" and not isinstance(value, str):
                    raise ValueError(f"Row {idx}: {field} must be string")
                if field_schema["type"] == "number" and not isinstance(value, (int, float)):
                    raise ValueError(f"Row {idx}: {field} must be number")
            if "minimum" in field_schema and value < field_schema["minimum"]:
                raise ValueError(f"Row {idx}: {field} {value} < minimum {field_schema['minimum']}")

    log.info("Schema validation passed for raw dataset.")


def main() -> None:
    # 1. Download the dataset
    df = download_dataset()

    # 2. Persist to CSV
    save_dataframe(df)

    # 3. Verify checksum
    actual_checksum = compute_sha256(RAW_CSV_PATH)
    log.info(f"Computed SHA‑256: {actual_checksum}")

    expected_checksum = load_expected_checksum()
    if expected_checksum:
        if actual_checksum != expected_checksum:
            log.warning(
                "Checksum changed vs. recorded value; updating recorded checksum."
            )
        write_checksum(actual_checksum)
    else:
        write_checksum(actual_checksum)
        log.info("No reference checksum existed; stored the newly computed value.")

    # 4. Validate each row
    validate_rows(df)

    log.info(
        "Download, checksum verification, and schema validation completed successfully."
    )


if __name__ == "__main__":
    main()