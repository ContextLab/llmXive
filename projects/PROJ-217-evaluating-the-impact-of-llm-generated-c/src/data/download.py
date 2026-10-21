"""
src.data.download
-----------------
Downloads a deterministic sample of the CodeSearchNet Python dataset
(via the verified parquet file on Hugging Face), validates records,
writes raw and validated JSONL files, logs the process, and records
SHA‑256 checksums of the source artifact.

Run via:
    python -m src.data.download

The script exits with a non‑zero status if the download fails after
three attempts, if the checksum verification fails, or if fewer than
150 valid snippets are obtained.
"""

import hashlib
import json
import random
import sys
from pathlib import Path
from typing import List, Dict

import pandas as pd
import yaml
from huggingface_hub import hf_hub_download, HfHubDownloadError
from tqdm import tqdm

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
REPO_ID = "codeparrot/code-search-net"
REPO_TYPE = "dataset"
FILENAME = "python/train-00000-of-00001.parquet"
MAX_RETRIES = 3
RETRY_BACKOFF = 60  # seconds

PROJECT_SEED = int(Path.cwd().joinpath("project_seed.txt").read_text().strip()
                   if Path.cwd().joinpath("project_seed.txt").exists()
                   else "42")
random.seed(PROJECT_SEED)

N_SNIPPETS = 500
MIN_VALID_SNIPPETS = 150

RAW_OUTPUT = paths.data("raw_snippets.jsonl")
VALIDATED_OUTPUT = paths.data("validated_snippets.jsonl")
EXCLUDED_OUTPUT = paths.data("excluded_records.json")
HASHES_OUTPUT = paths.data("artifact_hashes.yaml")
LOG_OUTPUT = paths.data("dataset_preparation.log")

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _sha256(file_path: Path) -> str:
    """Compute SHA‑256 checksum of *file_path*."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_hash_manifest() -> Dict[str, str]:
    """Load (or bootstrap) the artifact hash manifest."""
    if HASHES_OUTPUT.is_file():
        with HASHES_OUTPUT.open() as f:
            return yaml.safe_load(f) or {}
    return {}


def _save_hash_manifest(manifest: Dict[str, str]) -> None:
    """Persist the artifact hash manifest."""
    with HASHES_OUTPUT.open("w", encoding="utf-8") as f:
        yaml.safe_dump(manifest, f, default_flow_style=False, sort_keys=True)


def _download_parquet() -> Path:
    """Download the parquet file with a retry loop; raise on final failure."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            log.info(
                f"Attempt {attempt}/{MAX_RETRIES}: downloading {FILENAME} from {REPO_ID}"
            )
            parquet_path = hf_hub_download(
                repo_id=REPO_ID,
                repo_type=REPO_TYPE,
                filename=FILENAME,
            )
            log.info(f"Downloaded parquet to {parquet_path}")
            return Path(parquet_path)
        except HfHubDownloadError as e:
            log.error(f"Download attempt {attempt} failed: {e}")
            if attempt == MAX_RETRIES:
                raise RuntimeError(
                    f"Failed to download {FILENAME} after {MAX_RETRIES} attempts"
                ) from e
            else:
                import time

                backoff = RETRY_BACKOFF * (2 ** (attempt - 1))
                log.info(f"Retrying after {backoff}s...")
                time.sleep(backoff)

def _map_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tolerant column mapping:
    - Prefer columns ``code`` / ``docstring``.
    - Fallback to ``func_code_string`` / ``func_documentation_string``.
    - If neither pair is present, raise a clear error listing the columns.
    Returns a DataFrame with exactly ``code`` and ``docstring`` columns.
    """
    cols = set(df.columns)
    if {"code", "docstring"}.issubset(cols):
        return df[["code", "docstring"]].copy()
    elif {"func_code_string", "func_documentation_string"}.issubset(cols):
        mapped = df.rename(
            columns={
                "func_code_string": "code",
                "func_documentation_string": "docstring",
            }
        )
        return mapped[["code", "docstring"]].copy()
    else:
        raise RuntimeError(
            f"Unexpected column set {sorted(cols)} – expected either "
            "`code`/`docstring` or `func_code_string`/`func_documentation_string`."
        )

def _is_valid_docstring(doc: str) -> bool:
    """
    Validation rules for a docstring:
    - Non‑empty after stripping.
    - Does not consist solely of a boilerplate like ``TODO`` (case‑insensitive).
    - Does not look like a bare type signature (heuristic: contains only
      a type name and optional brackets/commas).
    """
    stripped = doc.strip()
    if not stripped:
        return False
    lowered = stripped.lower()
    if lowered == "todo" or lowered == '"""todo"""':
        return False
    # Heuristic for a bare type signature: e.g. ``int`` or ``List[int]``
    import re

    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(\[[^\]]+\])?", stripped):
        # If it looks like a single identifier (or generic), treat as invalid
        return False
    return True

def _write_jsonl(records: List[Dict], out_path: Path) -> None:
    """Write a list of dicts as JSON Lines."""
    with out_path.open("w", encoding="utf-8") as f:
        for rec in records:
            json.dump(rec, f, ensure_ascii=False)
            f.write("\n")

# ----------------------------------------------------------------------
# Main workflow
# ----------------------------------------------------------------------
def main() -> None:
    # 1. Download parquet and verify checksum
    parquet_path = _download_parquet()
    checksum = _sha256(parquet_path)

    manifest = _load_hash_manifest()
    key = FILENAME
    if key in manifest:
        if manifest[key] != checksum:
            log.error(
                f"Checksum mismatch for {key}: expected {manifest[key]}, got {checksum}"
            )
            raise RuntimeError("Checksum verification failed")
        else:
            log.info(f"Checksum verified for {key}")
    else:
        log.info(f"Recording new checksum for {key}")
        manifest[key] = checksum
        _save_hash_manifest(manifest)

    # 2. Load parquet with tolerant column mapping
    log.info(f"Loading parquet file {parquet_path}")
    df_raw = pd.read_parquet(parquet_path, engine="pyarrow")
    df_mapped = _map_columns(df_raw)

    # 3. Deterministic sampling of N_SNIPPETS records
    total_available = len(df_mapped)
    if total_available == 0:
        raise RuntimeError("Parquet file contains no records after column mapping")
    indices = list(range(total_available))
    random.shuffle(indices)
    selected_indices = indices[: min(N_SNIPPETS, total_available)]
    df_selected = df_mapped.iloc[selected_indices].reset_index(drop=True)

    # 4. Validation & partitioning
    raw_records = []
    valid_records = []
    excluded_records = []

    for idx, row in df_selected.iterrows():
        code = row["code"]
        doc = row["docstring"]
        snippet_id = f"snippet_{idx:06d}"

        raw_records.append(
            {"snippet_id": snippet_id, "code": code, "human_comment": doc}
        )

        if not code.strip():
            excluded_records.append(
                {
                    "snippet_id": snippet_id,
                    "code": code,
                    "human_comment": doc,
                    "reason": "missing_code",
                }
            )
            continue

        if not _is_valid_docstring(doc):
            excluded_records.append(
                {
                    "snippet_id": snippet_id,
                    "code": code,
                    "human_comment": doc,
                    "reason": "invalid_docstring",
                }
            )
            continue

        valid_records.append(
            {"snippet_id": snippet_id, "code": code, "human_comment": doc}
        )

    # 5. Write outputs
    _write_jsonl(raw_records, RAW_OUTPUT)
    _write_jsonl(valid_records, VALIDATED_OUTPUT)
    _write_jsonl(excluded_records, EXCLUDED_OUTPUT)

    # 6. Log summary
    total = len(raw_records)
    valid = len(valid_records)
    excluded = len(excluded_records)

    log_msg = (
        f"Dataset preparation completed. Total records processed: {total}\\n"
        f"Valid snippets: {valid}\\n"
        f"Excluded records: {excluded}\\n"
        f"Checksum recorded for {FILENAME}: {checksum}\\n"
    )
    log.info(log_msg)

    with LOG_OUTPUT.open("w", encoding="utf-8") as log_f:
        log_f.write(log_msg)

    # 7. Sanity check per SC‑006 (minimum valid snippets)
    if valid < MIN_VALID_SNIPPETS:
        log.error(
            f"Only {valid} valid snippets were extracted (minimum required is {MIN_VALID_SNIPPETS})."
        )
        raise RuntimeError("Insufficient valid snippets")

    log.info("All checks passed. Exiting with status 0.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.exception("Fatal error during dataset preparation")
        sys.exit(1)
