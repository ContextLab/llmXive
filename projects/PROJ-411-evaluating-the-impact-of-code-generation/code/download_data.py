"""
download_data.py

Phase 0 script: download three verified PR parquet datasets from HuggingFace,
compute SHA‑256 checksums, validate columns against the raw PR schema, and
write a schema‑map documentation file.

Usage (no arguments):
    python code/download_data.py

The script aborts with a clear error if any required column is missing
from the primary dataset (loubnabnl/prs‑v2‑sample).
"""
import argparse
import hashlib
import os
from pathlib import Path

import pandas as pd
import yaml
import pyarrow  # ensure parquet engine is available
from huggingface_hub import hf_hub_download, list_repo_files

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
DATASETS = [
    {
        "repo_id": "loubnabnl/prs-v2-sample",
        "tag": "primary",
    },
    {
        "repo_id": "davanstrien/authors_merged_model_prs",
        "tag": "auxiliary",
    },
    {
        "repo_id": "davanstrien/authors_merged_dataset_prs",
        "tag": "auxiliary",
    },
]

# Required columns according to contracts/raw_prs.schema.yaml
SCHEMA_PATH = (
    paths.root
    / "specs"
    / "001-evaluating-the-impact-of-code-generation"
    / "contracts"
    / "raw_prs.schema.yaml"
)
REQUIRED_FIELDS = []  # will be populated after loading the schema

# Outcome fields that must exist in the primary dataset (FR‑001 scope check)
PRIMARY_MANDATORY_FIELDS = {"comment_count", "merged_at"}

# ----------------------------------------------------------------------
def load_schema_required_fields(schema_path: Path) -> list[str]:
    """Load the JSON‑schema file and return the list of required property names."""
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    required = schema.get("required", [])
    if not isinstance(required, list):
        raise RuntimeError("Invalid schema: 'required' must be a list")
    return required

# ----------------------------------------------------------------------
def find_parquet_file(repo_id: str) -> str:
    """
    Return the first file ending with '.parquet' in the given repository.
    Raises if none is found.
    """
    log.info(f"Listing files for repo {repo_id}")
    files = list_repo_files(repo_id, repo_type="dataset")
    parquet_files = [f for f in files if f.lower().endswith(".parquet")]
    if not parquet_files:
        raise RuntimeError(f"No parquet file found in repository {repo_id}")
    # Prefer a file named 'data.parquet' if present
    for candidate in parquet_files:
        if os.path.basename(candidate) == "data.parquet":
            return candidate
    # Fallback to the first parquet file
    return parquet_files[0]

# ----------------------------------------------------------------------
def download_parquet(repo_id: str, dest_path: Path) -> Path:
    """
    Download the parquet file from ``repo_id`` into ``dest_path``.
    Returns the path to the downloaded file.
    """
    parquet_file = find_parquet_file(repo_id)
    log.info(f"Downloading {parquet_file} from {repo_id}")
    local_path = hf_hub_download(
        repo_id=repo_id, filename=parquet_file, repo_type="dataset"
    )
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    # Copy to the canonical location inside the project
    dest_path.write_bytes(Path(local_path).read_bytes())
    return dest_path

# ----------------------------------------------------------------------
def compute_sha256(file_path: Path) -> str:
    """Compute SHA‑256 checksum of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# ----------------------------------------------------------------------
def validate_columns(df: pd.DataFrame, required: list[str]) -> dict[str, str]:
    """
    For each required field return a status string:
    - 'present' if column exists
    - 'missing' otherwise
    """
    present = set(df.columns)
    status = {}
    for field in required:
        status[field] = "present" if field in present else "missing"
    return status

# ----------------------------------------------------------------------
def write_checksums(checksum_dict: dict[Path, str], out_path: Path) -> None:
    """Write SHA‑256 checksums to a text file."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for path, chksum in checksum_dict.items():
            f.write(f"{path.name}\\t{chksum}\\n")

# ----------------------------------------------------------------------
def write_schema_map(map_info: dict[str, dict[str, str]], out_path: Path) -> None:
    """
    Write a markdown table documenting, per dataset, whether each required
    variable is present or missing.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# Schema Mapping Report\\n\\n")
        for tag, info in map_info.items():
            f.write(f"## Dataset: {tag}\\n\\n")
            f.write("| Variable | Status |\\n")
            f.write("|---|---|\\n")
            for var, status in info.items():
                f.write(f"| `{var}` | {status} |\\n")
            f.write("\\n")

# ----------------------------------------------------------------------
def main() -> None:
    global REQUIRED_FIELDS
    REQUIRED_FIELDS = load_schema_required_fields(SCHEMA_PATH)
    log.info(f"Required fields from schema: {REQUIRED_FIELDS}")

    checksum_dict: dict[Path, str] = {}
    schema_map: dict[str, dict[str, str]] = {}

    raw_dir = paths.data("raw")
    for ds in DATASETS:
        repo_id = ds["repo_id"]
        tag = ds["tag"]
        # Destination filename: replace '/' with '__' to avoid subfolders
        dest_filename = repo_id.replace("/", "__") + ".parquet"
        dest_path = raw_dir / dest_filename

        # Download
        downloaded_path = download_parquet(repo_id, dest_path)

        # Compute checksum
        checksum = compute_sha256(downloaded_path)
        checksum_dict[downloaded_path] = checksum
        log.info(f"Checksum for {downloaded_path.name}: {checksum}")

        # Load and validate columns
        try:
            df = pd.read_parquet(downloaded_path)
        except Exception as e:
            raise RuntimeError(
                f"Failed to read parquet file {downloaded_path}: {e}"
            ) from e

        col_status = validate_columns(df, REQUIRED_FIELDS)
        schema_map[tag] = col_status

        # Scope‑mismatch check for primary dataset
        if tag == "primary":
            missing_mandatory = [
                fld
                for fld in PRIMARY_MANDATORY_FIELDS
                if col_status.get(fld) != "present"
            ]
            if missing_mandatory:
                raise RuntimeError(
                    f"Primary dataset '{repo_id}' is missing mandatory fields required for scope: {missing_mandatory}"
                )
            log.info("Primary dataset passed mandatory field check.")

    # Write outputs
    checksums_path = paths.data("checksums.txt")
    write_checksums(checksum_dict, checksums_path)
    log.info(f"Wrote checksums to {checksums_path}")

    schema_map_path = raw_dir / "schema_map.md"
    write_schema_map(schema_map, schema_map_path)
    log.info(f"Wrote schema map to {schema_map_path}")

    log.info("Data download and validation completed successfully.")

# ----------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download verified PR parquet datasets, checksum them, and validate schema."
    )
    # No arguments required; parser kept for future extensibility
    _ = parser.parse_args()
    main()
