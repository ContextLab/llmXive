"""
download_data.py

Phase 0 script: download verified PR datasets, compute SHA-256 checksums, 
validate columns against the raw PR schema, and write a schema-map documentation file.

The primary dataset is fetched from the verified GitHub raw CSV source to ensure 
mandatory fields (comment_count, merged_at) are present, then persisted as Parquet.
Auxiliary datasets are fetched from HuggingFace.
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
# Authoritative verified source for primary population
VERIFIED_PRIMARY_URL = "https://raw.githubusercontent.com/soroushj/ghpr-dataset/main/ghpr-sample.csv"

# Mapping from verified CSV columns to raw_prs.schema.yaml names
PRIMARY_COLUMN_MAP = {
    "pull_number": "pr_id",
    "repo_id": "repo_name",
    "pull_created_at": "created_at",
    "pull_merged_at": "merged_at",
    "pull_additions": "additions",
    "pull_deletions": "deletions",
    "pull_comments": "comment_count",
    "issue_body_plain": "commit_message",
}

AUXILIARY_DATASETS = [
    {"repo_id": "davanstrien/authors_merged_model_prs", "tag": "aux_model"},
    {"repo_id": "davanstrien/authors_merged_dataset_prs", "tag": "aux_dataset"},
]

SCHEMA_PATH = (
    paths.root
    / "specs"
    / "001-evaluating-the-impact-of-code-generation"
    / "contracts"
    / "raw_prs.schema.yaml"
)

PRIMARY_MANDATORY_FIELDS = {"comment_count", "merged_at"}

# ----------------------------------------------------------------------
def load_schema_required_fields(schema_path: Path) -> List[str]:
    """Load the JSON-schema file and return the list of required property names."""
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    required = schema.get("required", [])
    if not isinstance(required, list):
        raise RuntimeError("Invalid schema: 'required' must be a list")
    return required

def _normalize_name(name: str) -> str:
    """Normalise a column or field name for fuzzy matching."""
    return name.lower().replace("_", "")

def download_verified_primary(dest_path: Path) -> pd.DataFrame:
    """
    Downloads the verified CSV source, renames columns to match the schema,
    and saves as a Parquet file.
    """
    log.info(f"Downloading verified primary dataset from {VERIFIED_PRIMARY_URL}")
    try:
        df = pd.read_csv(VERIFIED_PRIMARY_URL)
    except Exception as e:
        raise RuntimeError(f"Failed to download verified primary source: {e}")

    # Rename according to the verified mapping
    df = df.rename(columns=PRIMARY_COLUMN_MAP)
    
    # Keep only mapped columns + any others that might be useful (like labels)
    # to ensure we don't bloat but maintain utility.
    # The schema requires specific fields; we ensure those are there.
    
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(dest_path, engine="pyarrow", index=False)
    log.info(f"Verified primary dataset written to {dest_path}")
    return df

def download_and_combine_parquet(repo_id: str, dest_path: Path) -> Path:
    """
    Download all parquet files from HF repo_id, concatenate and write to dest_path.
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
        data_frames.append(df)

    if not data_frames:
        raise RuntimeError(f"Failed to load any parquet data from {repo_id}")

    combined_df = pd.concat(data_frames, ignore_index=True)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    combined_df.to_parquet(dest_path, engine="pyarrow", index=False)
    log.info(f"Combined parquet written to {dest_path}")
    return dest_path

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def validate_columns(df: pd.DataFrame, required: List[str]) -> Dict[str, str]:
    """Check presence of required fields (case-insensitive, underscore-tolerant)."""
    existing_norm = {_normalize_name(col): col for col in df.columns}
    status: Dict[str, str] = {}
    for field in required:
        norm_field = _normalize_name(field)
        if norm_field in existing_norm:
            status[field] = "present"
        else:
            status[field] = "missing"
    return status

def write_checksums(checksum_dict: Dict[Path, str], out_path: Path) -> None:
    """Write SHA-256 checksums to a text file."""
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

def main() -> None:
    required_fields = load_schema_required_fields(SCHEMA_PATH)
    log.info(f"Required fields from schema: {required_fields}")

    checksum_dict: Dict[Path, str] = {}
    schema_map: Dict[str, Dict[str, str]] = {}
    raw_dir = paths.data("raw")

    # 1. Process Primary Dataset (Verified Source)
    primary_dest = raw_dir / "prs-v2-sample.parquet"
    df_primary = download_verified_primary(primary_dest)
    
    # Checksum and Validate Primary
    primary_checksum = compute_sha256(primary_dest)
    checksum_dict[primary_dest] = primary_checksum
    
    primary_status = validate_columns(df_primary, required_fields)
    schema_map["primary"] = primary_status
    
    # Scope-mismatch check for primary dataset
    missing_mandatory = [
        fld for fld in PRIMARY_MANDATORY_FIELDS 
        if primary_status.get(fld) != "present"
    ]
    if missing_mandatory:
        raise RuntimeError(
            f"Primary dataset is missing mandatory fields required for scope: {missing_mandatory}"
        )
    log.info("Primary dataset passed mandatory field check.")

    # 2. Process Auxiliary Datasets (HF)
    for ds in AUXILIARY_DATASETS:
        repo_id = ds["repo_id"]
        tag = ds["tag"]
        dest_filename = repo_id.split("/")[-1] + ".parquet"
        dest_path = raw_dir / dest_filename
        
        try:
            combined_path = download_and_combine_parquet(repo_id, dest_path)
            df_aux = pd.read_parquet(combined_path, engine="pyarrow")
            
            # Checksum
            checksum = compute_sha256(combined_path)
            checksum_dict[combined_path] = checksum
            
            # Validate
            col_status = validate_columns(df_aux, required_fields)
            schema_map[tag] = col_status
        except Exception as e:
            log.warning(f"Could not process auxiliary dataset {repo_id}: {e}")
            schema_map[tag] = {f: "error/missing" for f in required_fields}

    # Write outputs
    checksums_path = paths.data("checksums.txt")
    write_checksums(checksum_dict, checksums_path)
    
    schema_map_path = raw_dir / "schema_map.md"
    write_schema_map(schema_map, schema_map_path)
    
    log.info(f"Data download and validation completed. Checksums: {checksums_path}, Map: {schema_map_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download verified PR datasets and validate schema.")
    _ = parser.parse_args()
    main()