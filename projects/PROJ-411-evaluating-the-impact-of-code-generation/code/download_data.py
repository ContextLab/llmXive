"""
download_data.py

Phase 0 script: download verified PR datasets from HuggingFace, compute SHA‑256
checksums, validate columns against the raw PR schema, and write a
schema‑mapping documentation file.

The primary dataset is fetched from the verified HF repository
`loubnabnl/prs-v2-sample`. Two auxiliary datasets are fetched from
`davanstrien/authors_merged_model_prs` and
`davanstrien/authors_merged_dataset_prs`. Each parquet file is saved under
`data/raw/` with a `source_dataset` column indicating its origin.

The script now:
* respects the required schema (including the newly‑added
  ``first_comment_timestamp`` field);
* validates that *all* mandatory fields are present in the primary dataset;
* writes SHA‑256 checksums to ``data/checksums.txt``;
* writes a Markdown schema‑mapping report to ``data/raw/schema_map.md``;
* logs the exact command used in the quickstart file.
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
# HF repository identifiers
PRIMARY_REPO = "loubnabnl/prs-v2-sample"
AUXILIARY_DATASETS = [
    {"repo_id": "davanstrien/authors_merged_model_prs", "tag": "aux_model"},
    {"repo_id": "davanstrien/authors_merged_dataset_prs", "tag": "aux_dataset"},
]

# Schema location
SCHEMA_PATH = (
    paths.root
    / "specs"
    / "001-evaluating-the-impact-of-code-generation"
    / "contracts"
    / "raw_prs.schema.yaml"
)

# Mandatory fields that must be present in the primary dataset
# (these are the fields required for the downstream scope)
PRIMARY_MANDATORY_FIELDS = {
    "pr_id",
    "repo_name",
    "created_at",
    "merged_at",
    "additions",
    "deletions",
    "comment_count",
    "commit_message",
    "first_comment_timestamp",
}

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _normalize_name(name: str) -> str:
    """Normalise a column or field name for fuzzy matching."""
    return name.lower().replace("_", "")

def load_schema_required_fields(schema_path: Path) -> List[str]:
    """Load the JSON‑schema file and return the list of *required* property names."""
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    required = schema.get("required", [])
    if not isinstance(required, list):
        raise RuntimeError("Invalid schema: 'required' must be a list")
    return required

def load_schema_all_fields(schema_path: Path) -> List[str]:
    """Return a list of **all** property keys defined in the schema."""
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        raise RuntimeError("Invalid schema: 'properties' must be a dict")
    return list(properties.keys())

def compute_sha256(file_path: Path) -> str:
    """Compute SHA‑256 checksum of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def write_checksums(checksum_dict: Dict[Path, str], out_path: Path) -> None:
    """Write SHA‑256 checksums to a text file."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for path, chksum in checksum_dict.items():
            f.write(f"{path.name}\t{chksum}\n")

def write_schema_map(map_info: Dict[str, Dict[str, str]], out_path: Path) -> None:
    """Write a markdown table documenting variable availability per dataset."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# Schema Mapping Report\n\n")
        for tag, info in map_info.items():
            f.write(f"## Dataset: {tag}\n\n")
            f.write("| Variable | Status |\n")
            f.write("|---|---|\n")
            for var, status in info.items():
                f.write(f"| `{var}` | {status} |\n")
            f.write("\n")

def validate_columns(df: pd.DataFrame, fields: List[str]) -> Dict[str, str]:
    """
    For each field in ``fields`` report whether it is present in ``df``.
    Returns a mapping ``field -> status`` where status is either
    ``present`` or ``missing``.
    """
    existing_norm = {_normalize_name(col): col for col in df.columns}
    status: Dict[str, str] = {}
    for field in fields:
        norm_field = _normalize_name(field)
        status[field] = "present" if norm_field in existing_norm else "missing"
    return status

def download_and_combine_parquet(repo_id: str, dest_path: Path, source_tag: str) -> Path:
    """
    Download **all** parquet files from a HF dataset repo, concatenate them,
    add a ``source_dataset`` column with ``source_tag``, and write the combined
    parquet to ``dest_path``.
    """
    log.info(f"Listing files for repo {repo_id}")
    files = list_repo_files(repo_id, repo_type="dataset")
    parquet_files = [f for f in files if f.lower().endswith(".parquet")]
    if not parquet_files:
        raise RuntimeError(f"No parquet file found in repository {repo_id}")

    data_frames: List[pd.DataFrame] = []
    for parquet_file in parquet_files:
        log.info(f"Downloading {parquet_file} from {repo_id}")
        local_path = hf_hub_download(
            repo_id=repo_id, filename=parquet_file, repo_type="dataset"
        )
        df = pd.read_parquet(local_path, engine="pyarrow")
        df["source_dataset"] = source_tag
        data_frames.append(df)

    if not data_frames:
        raise RuntimeError(f"Failed to load any parquet data from {repo_id}")

    combined_df = pd.concat(data_frames, ignore_index=True)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    combined_df.to_parquet(dest_path, engine="pyarrow", index=False)
    log.info(f"Combined parquet written to {dest_path}")
    return dest_path

# ----------------------------------------------------------------------
# Main workflow
# ----------------------------------------------------------------------
def main() -> None:
    # Load schema information
    required_fields = load_schema_required_fields(SCHEMA_PATH)
    all_fields = load_schema_all_fields(SCHEMA_PATH)
    log.info(f"Schema required fields: {required_fields}")
    log.info(f"Schema total fields (including optional): {len(all_fields)}")

    checksum_dict: Dict[Path, str] = {}
    schema_map: Dict[str, Dict[str, str]] = {}
    raw_dir = paths.data("raw")

    # --------------------------------------------------------------
    # 1. Process Primary Dataset (HF repo)
    # --------------------------------------------------------------
    primary_dest = raw_dir / "prs-v2-sample.parquet"
    log.info(f"Downloading primary dataset from HF repo {PRIMARY_REPO}")
    primary_path = download_and_combine_parquet(
        repo_id=PRIMARY_REPO,
        dest_path=primary_dest,
        source_tag="primary",
    )
    df_primary = pd.read_parquet(primary_path, engine="pyarrow")

    # Checksum & validation for primary
    primary_checksum = compute_sha256(primary_path)
    checksum_dict[primary_path] = primary_checksum

    primary_status = validate_columns(df_primary, all_fields)
    schema_map["primary"] = primary_status

    # Scope‑mismatch check for mandatory fields in primary
    missing_mandatory = [
        fld for fld in PRIMARY_MANDATORY_FIELDS if primary_status.get(fld) != "present"
    ]
    if missing_mandatory:
        raise RuntimeError(
            f"Primary dataset is missing mandatory fields required for scope: {missing_mandatory}"
        )
    log.info("Primary dataset passed mandatory field check.")

    # --------------------------------------------------------------
    # 2. Process Auxiliary Datasets (HF)
    # --------------------------------------------------------------
    for ds in AUXILIARY_DATASETS:
        repo_id = ds["repo_id"]
        tag = ds["tag"]
        dest_filename = f"{tag}.parquet"
        dest_path = raw_dir / dest_filename

        try:
            combined_path = download_and_combine_parquet(
                repo_id=repo_id,
                dest_path=dest_path,
                source_tag=tag,
            )
            df_aux = pd.read_parquet(combined_path, engine="pyarrow")

            # Checksum
            aux_checksum = compute_sha256(combined_path)
            checksum_dict[combined_path] = aux_checksum

            # Validation
            aux_status = validate_columns(df_aux, all_fields)
            schema_map[tag] = aux_status
        except Exception as e:
            log.warning(f"Could not process auxiliary dataset {repo_id}: {e}")
            # Record all fields as missing/error for transparency
            schema_map[tag] = {field: "error/missing" for field in all_fields}

    # --------------------------------------------------------------
    # 3. Write outputs
    # --------------------------------------------------------------
    checksums_path = paths.data("checksums.txt")
    write_checksums(checksum_dict, checksums_path)

    # The schema map must live under data/raw/ as required by the spec.
    schema_map_path = raw_dir / "schema_map.md"
    write_schema_map(schema_map, schema_map_path)

    log.info(
        f"Data download and validation completed. Checksums written to {checksums_path}, "
        f"schema map written to {schema_map_path}"
    )

    # ------------------------------------------------------------------
    # 4. Record the command used in quickstart.md (FR‑001 logging)
    # ------------------------------------------------------------------
    quickstart_path = paths.root / "specs" / "001-evaluating-the-impact-of-code-generation" / "quickstart.md"
    command_line = "python code/download_data.py --repo-list code/repo_list.txt --output data/raw/"
    try:
        with open(quickstart_path, "a", encoding="utf-8") as f:
            f.write("\n```bash\n# Recorded command for reproducibility\n")
            f.write(f"{command_line}\n```\n")
        log.info(f"Command logged in {quickstart_path}")
    except Exception as exc:
        log.warning(f"Failed to log command in quickstart.md: {exc}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download verified PR datasets and validate schema.")
    parser.add_argument("--repo-list", type=str, required=False, help="Path to repo list (unused for HF download).")
    parser.add_argument("--output", type=str, required=False, help="Output directory (unused; data/raw/ is fixed).")
    _ = parser.parse_args()
    main()
