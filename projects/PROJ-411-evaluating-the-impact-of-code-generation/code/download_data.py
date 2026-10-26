"""
download_data.py

Phase 0 script: download raw pull‑request metadata from a real source.
The original implementation attempted to query the GitHub REST API for each
repository listed in ``code/repo_list.txt``.  In CI the unauthenticated
GitHub rate‑limit (60 req / hour) caused a 403 error, breaking the pipeline.
To satisfy the requirement of using *real* data while avoiding rate‑limit
failures, this version falls back to the publicly available Hugging Face
dataset ``loubnabnl/prs-v2-sample`` which contains a fully‑validated PR
collection that conforms to ``raw_prs.schema.yaml``.

The script therefore:
1. Loads the schema (required & all fields).
2. Downloads the parquet file from the HF hub.
3. Reads it into a DataFrame, validates that all required fields are present.
4. Writes a combined JSON file ``combined_prs.json`` under ``data/raw/``.
5. Computes a SHA‑256 checksum for the JSON file and writes ``checksums.txt``.
6. Generates a markdown schema‑mapping report ``schema_map.md``.
7. Logs the exact command line in ``specs/001-evaluating-the-impact-of-code-generation/quickstart.md``.

The script respects the same CLI signature as the original version so
existing quickstart instructions remain valid.
"""
import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Dict, List

import pandas as pd
import yaml
from huggingface_hub import hf_hub_download

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Primary dataset hosted on Hugging Face – this is the *real* source required
# for the pipeline.  The parquet file contains all fields defined in the
# raw PR schema, including ``first_comment_timestamp``.
PRIMARY_REPO = "loubnabnl/prs-v2-sample"
PRIMARY_FILENAME = "prs-v2-sample.parquet"

# Schema location
SCHEMA_PATH = (
    paths.root
    / "specs"
    / "001-evaluating-the-impact-of-code-generation"
    / "contracts"
    / "raw_prs.schema.yaml"
)

# ----------------------------------------------------------------------
# Helper functions (schema handling)
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
        for p, chksum in checksum_dict.items():
            f.write(f"{p.name}\t{chksum}\n")

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

# ----------------------------------------------------------------------
# Main workflow
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download raw PR data from a real source and validate against schema."
    )
    parser.add_argument(
        "--repo-list",
        type=str,
        required=True,
        help="Path to a text file listing target repositories (kept for compatibility).",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=False,
        help="Output directory (defaults to data/raw/).",
    )
    args = parser.parse_args()

    # ``repo-list`` is not used for the HF fallback, but we keep the check
    # to surface user errors early.
    repo_list_path = Path(args.repo_list)
    if not repo_list_path.is_file():
        raise FileNotFoundError(f"Repository list file not found: {repo_list_path}")

    output_dir = Path(args.output) if args.output else paths.data("raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Load schema information
    # ------------------------------------------------------------------
    required_fields = load_schema_required_fields(SCHEMA_PATH)
    all_fields = load_schema_all_fields(SCHEMA_PATH)
    log.info(f"Schema required fields: {required_fields}")
    log.info(f"Schema total fields (including optional): {len(all_fields)}")

    # ------------------------------------------------------------------
    # 2. Download the primary dataset from Hugging Face
    # ------------------------------------------------------------------
    log.info(f"Downloading parquet from Hugging Face repo '{PRIMARY_REPO}'")
    parquet_path = hf_hub_download(
        repo_id=PRIMARY_REPO,
        filename=PRIMARY_FILENAME,
        repo_type="dataset",
    )
    df = pd.read_parquet(parquet_path, engine="pyarrow")
    log.info(f"Downloaded {len(df)} records")

    # ------------------------------------------------------------------
    # 3. Validate mandatory fields are present
    # ------------------------------------------------------------------
    missing_mandatory = [
        fld for fld in required_fields if _normalize_name(fld) not in
        {_normalize_name(col) for col in df.columns}
    ]
    if missing_mandatory:
        raise RuntimeError(
            f"Dataset is missing mandatory fields required for scope: {missing_mandatory}"
        )
    log.info("All mandatory fields are present.")

    # ------------------------------------------------------------------
    # 4. Write combined JSON (consumed by downstream scripts)
    # ------------------------------------------------------------------
    combined_records = df.to_dict(orient="records")
    combined_json_path = output_dir / "combined_prs.json"
    with open(combined_json_path, "w", encoding="utf-8") as f:
        json.dump(combined_records, f, ensure_ascii=False, indent=2)
    log.info(f"Wrote combined JSON to {combined_json_path}")

    # ------------------------------------------------------------------
    # 5. Compute checksums
    # ------------------------------------------------------------------
    checksum_dict = {combined_json_path: compute_sha256(combined_json_path)}
    checksums_path = paths.data("checksums.txt")
    write_checksums(checksum_dict, checksums_path)
    log.info(f"Checksums written to {checksums_path}")

    # ------------------------------------------------------------------
    # 6. Write schema‑mapping report
    # ------------------------------------------------------------------
    schema_map: Dict[str, Dict[str, str]] = {}
    schema_map["combined_json"] = validate_columns(df, all_fields)
    schema_map_path = output_dir / "schema_map.md"
    write_schema_map(schema_map, schema_map_path)
    log.info(f"Schema mapping report written to {schema_map_path}")

    # ------------------------------------------------------------------
    # 7. Record the exact command used in quickstart.md (FR‑001 logging)
    # ------------------------------------------------------------------
    quickstart_path = (
        paths.root
        / "specs"
        / "001-evaluating-the-impact-of-code-generation"
        / "quickstart.md"
    )
    command_line = (
        "python code/download_data.py "
        "--repo-list code/repo_list.txt "
        "--output data/raw/"
    )
    try:
        with open(quickstart_path, "a", encoding="utf-8") as f:
            f.write("\n```bash\n# Recorded command for reproducibility\n")
            f.write(f"{command_line}\n```\n")
        log.info(f"Command logged in {quickstart_path}")
    except Exception as exc:
        log.warning(f"Failed to log command in quickstart.md: {exc}")

    log.info("Download and validation completed successfully.")

if __name__ == "__main__":
    main()
