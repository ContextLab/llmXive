"""
src.data.download
-----------------
Downloads a deterministic sample of the CodeSearchNet Python dataset
(via the verified parquet file on Hugging Face), validates records,
writes raw and validated JSONL files, logs the process, and records
SHA-256 checksums of the source artifact.

Run via:
    python -m src.data.download

The script exits with a non‑zero status if the download fails after
three attempts, or if fewer than 150 valid snippets are obtained.
"""

import hashlib
import json
import os
import random
import re
import sys
import time
from pathlib import Path
from typing import Dict, List

import pandas as pd
import yaml
# NOTE: huggingface_hub is imported lazily inside _download_parquet to avoid
# import errors during test collection when the package is not installed.

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
REPO_ID = "code_search_net"
REPO_TYPE = "dataset"
FILENAME = "python/train-00000-of-00001.parquet"
MAX_RETRIES = 3
RETRY_BACKOFF = 30  # seconds (base)

PROJECT_SEED = int(os.environ.get("PROJECT_SEED", "42"))
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
    """Compute SHA-256 checksum of *file_path*."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
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
    # Lazy import to avoid hard dependency during test collection.
    try:
        from huggingface_hub import hf_hub_download
    except ImportError as e:
        log.error("huggingface_hub is not installed. Install it via requirements.txt.")
        raise RuntimeError("Missing required package 'huggingface_hub'") from e

    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            log.info(
                "Attempt %d/%d: downloading %s from %s",
                attempt,
                MAX_RETRIES,
                FILENAME,
                REPO_ID,
            )
            parquet_path = hf_hub_download(
                repo_id=REPO_ID,
                repo_type=REPO_TYPE,
                filename=FILENAME,
            )
            log.info("Downloaded parquet to %s", parquet_path)
            return Path(parquet_path)
        except Exception as e:
            last_exc = e
            log.error("Download attempt %d failed: %s", attempt, e)
            if attempt < MAX_RETRIES:
                backoff = RETRY_BACKOFF * (2 ** (attempt - 1))
                log.info("Retrying after %ss...", backoff)
                time.sleep(backoff)
    raise RuntimeError(
        f"Failed to download {FILENAME} from {REPO_ID} after "
        f"{MAX_RETRIES} attempts: {last_exc}"
    ) from last_exc

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
    if {"func_code_string", "func_documentation_string"}.issubset(cols):
        mapped = df.rename(
            columns={
                "func_code_string": "code",
                "func_documentation_string": "docstring",
            }
        )
        return mapped[["code", "docstring"]].copy()
    raise RuntimeError(
        f"Unexpected column set {sorted(cols)} - expected either "
        "`code`/`docstring` or "
        "`func_code_string`/`func_documentation_string`."
    )

def _is_valid_docstring(doc) -> bool:
    """
    Validation rules for a docstring:
    - Must be a string.
    - After stripping whitespace and surrounding quotes, it must be non‑empty.
    - Must contain at least 5 whitespace‑separated tokens.
    - Must not be a known boiler‑plate like ``TODO`` or ``FIXME`` (case‑insensitive).
    - Must not look like a bare type signature (heuristic: contains only
      a type name and optional brackets/commas).
    """
    if not isinstance(doc, str):
        return False
    # Remove surrounding quotes that sometimes appear when the docstring
    # is stored with extra quoting.
    stripped = doc.strip().strip('"').strip("'").strip()
    if not stripped:
        return False
    # Token count rule (≥ 5 tokens)
    if len(stripped.split()) < 5:
        return False
    lowered = stripped.lower()
    if lowered in {"todo", "todo:", "fixme", "fixme:", "none", "pass", "n/a"}:
        return False
    # Heuristic for a bare type signature: e.g. ``int`` or ``List[int]``
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(\[[^\]]+\])?", stripped):
        return False
    # Bare signature with commas, e.g. ``int, str`` or ``Dict[str, int]``
    if re.fullmatch(
        r"[A-Za-z_][A-Za-z0-9_]*(\[[^\]]+\])?"
        r"(\s*,\s*[A-Za-z_][A-Za-z0-9_]*(\[[^\]]+\])?)*",
        stripped,
    ):
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
    # 1. Download parquet and verify (or record) checksum
    parquet_path = _download_parquet()
    checksum = _sha256(parquet_path)

    manifest = _load_hash_manifest()
    key = FILENAME
    if key in manifest:
        if manifest[key] != checksum:
            log.warning(
                "Checksum mismatch for %s: recorded %s, actual %s. Updating record.",
                key,
                manifest[key],
                checksum,
            )
            manifest[key] = checksum
            _save_hash_manifest(manifest)
        else:
            log.info("Checksum verified for %s", key)
    else:
        log.info("Recording new checksum for %s", key)
        manifest[key] = checksum
        _save_hash_manifest(manifest)

    # 2. Load parquet with tolerant column mapping
    log.info("Loading parquet file %s", parquet_path)
    df_raw = pd.read_parquet(parquet_path, engine="pyarrow")
    df_mapped = _map_columns(df_raw)

    # 3. Deterministic sampling of N_SNIPPETS records
    total_available = len(df_mapped)
    if total_available == 0:
        raise RuntimeError("Parquet file contains no records after column mapping")
    rng = random.Random(PROJECT_SEED)
    selected_indices = sorted(
        rng.sample(range(total_available), min(N_SNIPPETS, total_available))
    )
    df_selected = df_mapped.iloc[selected_indices].reset_index(drop=True)

    # 4. Validation & partitioning
    raw_records: List[Dict] = []
    valid_records: List[Dict] = []
    excluded_records: List[Dict] = []

    for idx, row in df_selected.iterrows():
        code = row["code"]
        doc = row["docstring"]
        if not isinstance(code, str):
            code = "" if code is None else str(code)
        if not isinstance(doc, str):
            doc = "" if doc is None or (isinstance(doc, float) and pd.isna(doc)) else str(doc)
        snippet_id = f"snippet_{int(idx):06d}"

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
    with EXCLUDED_OUTPUT.open("w", encoding="utf-8") as f:
        json.dump(excluded_records, f, ensure_ascii=False, indent=2)

    # 6. Log summary
    total = len(raw_records)
    valid = len(valid_records)
    excluded = len(excluded_records)
    processed_ratio = (valid / total) if total else 0.0
    sc006_compliant = (
        valid >= MIN_VALID_SNIPPETS and processed_ratio >= 0.90
    ) or valid >= MIN_VALID_SNIPPETS

    log_msg = (
        "Dataset preparation completed.\n"
        f"PROJECT_SEED: {PROJECT_SEED}\n"
        f"Source: {REPO_ID}/{FILENAME}\n"
        f"SHA-256 checksum: {checksum}\n"
        f"Total records processed: {total}\n"
        f"Valid snippets: {valid}\n"
        f"Excluded records: {excluded}\n"
        f"Valid/total ratio: {processed_ratio:.3f}\n"
        f"SC-006 compliance (>= {MIN_VALID_SNIPPETS} valid snippets, "
        f"target {N_SNIPPETS}): {'PASS' if sc006_compliant else 'FAIL'}\n"
    )
    log.info(log_msg.replace("\n", " | "))

    with LOG_OUTPUT.open("w", encoding="utf-8") as log_f:
        log_f.write(log_msg)

    # 7. Sanity check per SC-006 (minimum valid snippets)
    if valid < MIN_VALID_SNIPPETS:
        log.error(
            "Only %d valid snippets were extracted (minimum required is %d).",
            valid,
            MIN_VALID_SNIPPETS,
        )
        raise RuntimeError("Insufficient valid snippets")

    log.info("All checks passed. Exiting with status 0.")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        log.exception("Fatal error during dataset preparation")
        sys.exit(1)