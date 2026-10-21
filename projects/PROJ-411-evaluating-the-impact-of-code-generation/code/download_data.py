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
from pathlib import Path
from typing import Dict, List

import pandas as pd
import yaml
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
REQUIRED_FIELDS: List[str] = []  # populated at runtime

# Outcome fields that must exist in the primary dataset (FR‑001 scope check)
PRIMARY_MANDATORY_FIELDS = {"comment_count", "merged_at"}

# ----------------------------------------------------------------------
def load_schema_required_fields(schema_path: Path) -> List[str]:
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
def _normalize_name(name: str) -> str:
    """
    Normalise a column or field name for fuzzy matching:
    - lower‑case
    - remove underscores
    """
    return name.lower().replace("_", "")

# ----------------------------------------------------------------------
def list_parquet_files(repo_id: str) -> List[str]:
    """
    Return a list of all parquet files in the given repository.
    Raises if none is found.
    """
    log.info(f"Listing files for repo {repo_id}")
    files = list_repo_files(repo_id, repo_type="dataset")
    parquet_files = [f for f in files if f.lower().endswith(".parquet")]
    if not parquet_files:
        raise RuntimeError(f"No parquet file found in repository {repo_id}")
    return parquet_files

# ----------------------------------------------------------------------
def download_and_combine_parquet(repo_id: str, dest_path: Path) -> Path:
    """
    Download all parquet files from ``repo_id``, concatenate them into a single
    DataFrame, and write the combined parquet to ``dest_path``.
    Returns the path to the combined parquet file.
    """
    parquet_files = list_parquet_files(repo_id)

    data_frames: List[pd.DataFrame] = []
    for parquet_file in parquet_files:
        log.info(f"Downloading {parquet_file} from {repo_id}")
        local_path = hf_hub_download(
            repo_id=repo_id, filename=parquet_file, repo_type="dataset"
        )
        df = pd.read_parquet(local_path, engine="pyarrow")
        data_frames.append(df)

    if not data_frames:
        raise RuntimeError(f"Failed to load any parquet data from {repo_id}")

    combined_df = pd.concat(data_frames, ignore_index=True)

    # Ensure destination directory exists
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    combined_df.to_parquet(dest_path, engine="pyarrow", index=False)
    log.info(f"Combined parquet written to {dest_path}")

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
def validate_columns(df: pd.DataFrame, required: List[str]) -> Dict[str, str]:
    """
    For each required field return a status string:
    - 'present' if column exists (case‑insensitive match, tolerant of
      underscore differences)
    - 'missing' otherwise
    """
    existing_norm = {_normalize_name(col): col for col in df.columns}
    status: Dict[str, str] = {}
    for field in required:
        norm_field = _normalize_name(field)
        if norm_field in existing_norm:
            status[field] = "present"
        else:
            status[field] = "missing"
    return status

# ----------------------------------------------------------------------
def write_checksums(checksum_dict: Dict[Path, str], out_path: Path) -> None:
    """Write SHA‑256 checksums to a text file."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for path, chksum in checksum_dict.items():
            f.write(f"{path.name}\\t{chksum}\\n")

# ----------------------------------------------------------------------
def write_schema_map(map_info: Dict[str, Dict[str, str]], out_path: Path) -> None:
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

    checksum_dict: Dict[Path, str] = {}
    schema_map: Dict[str, Dict[str, str]] = {}

    raw_dir = paths.data("raw")
    for ds in DATASETS:
        repo_id = ds["repo_id"]
        tag = ds["tag"]
        # Destination filename: use only the dataset name (no owner)
        dest_filename = repo_id.split("/")[-1] + ".parquet"
        dest_path = raw_dir / dest_filename

        # Download and combine all parquet shards
        combined_path = download_and_combine_parquet(repo_id, dest_path)

        # Compute checksum
        checksum = compute_sha256(combined_path)
        checksum_dict[combined_path] = checksum
        log.info(f"Checksum for {combined_path.name}: {checksum}")

        # Load and validate columns
        try:
            df = pd.read_parquet(combined_path, engine="pyarrow")
        except Exception as e:
            raise RuntimeError(
                f"Failed to read combined parquet file {combined_path}: {e}"
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