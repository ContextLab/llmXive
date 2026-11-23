"""Download the verified real fMRI parquet shard and record checksum + column inventory.

Verified source (sole input; the previously guessed OpenNeuro dataset IDs
ds000246/ds001600 are NOT retried): the HuggingFace dataset mirror
``clane9/openneuro-fslr64k`` (real, pre-normalized fsLR-64k CIFTI-format
BOLD timeseries), test split, shard ``test-00000-of-00016.parquet``.

The loader FAILS LOUDLY on any fetch error (raises; never falls back to
synthetic or bundled data).

Outputs:
  data/raw/test-00000-of-00016.parquet  -- the raw shard
  data/checksums.json                   -- SHA-256 of the raw shard
  data/raw/column_inventory.json        -- real schema, presence of each
      expected behavioral/covariate field, and available_subject_count
      (distinct subject IDs actually present in the shard).
"""
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional

import pyarrow.parquet as pq
from huggingface_hub import HfApi, hf_hub_download

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

REPO_ID = "clane9/openneuro-fslr64k"
REPO_TYPE = "dataset"
SPLIT = "test"
SHARD_BASENAME = "test-00000-of-00016.parquet"
RAW_DEST_RELATIVE = Path("raw") / SHARD_BASENAME

# Expected behavioral / covariate fields (FR-004/FR-009/FR-011); each is
# marked present/absent against the REAL schema. Nothing is fabricated.
EXPECTED_FIELDS: Dict[str, List[str]] = {
    "subject_id": ["subject_id", "subject", "participant_id", "sub"],
    "task_labels": ["task", "task_label", "task_condition", "condition"],
    "expert_rating": ["expert_rating", "rating", "skill", "improvisation_score"],
    "task_condition": ["task_condition", "condition", "improv", "scripted"],
    "years_of_training": ["years_training", "years_of_training", "training_years"],
    "age": ["age"],
    "fd": ["fd", "framewise_displacement", "motion", "mean_fd"],
    "instrument": ["instrument", "instrument_type"],
    "genre": ["genre", "musical_genre"],
    "practice_intensity": ["practice", "practice_intensity", "practice_hours"],
    "education": ["education", "education_level"],
}

SUBJECT_NAME_CANDIDATES = [
    "subject_id", "subject", "participant_id", "sub", "source_id",
]
SUB_PATTERN = re.compile(r"^(sub[-_]?\d+|ds\d{4,8})", re.IGNORECASE)


def compute_sha256(file_path: Path) -> str:
    """Return the SHA-256 checksum of ``file_path``."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download_file(url: str, dest: Path) -> None:
    """Download a file from a URL to a destination path (fails loudly)."""
    import requests

    log.info(f"Downloading {url} -> {dest}")
    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        with dest.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                if chunk:
                    f.write(chunk)


def parse_participants_tsv(tsv_path: Path) -> Dict[str, Dict[str, Optional[float]]]:
    """Legacy helper kept for API compatibility: parse participants.tsv."""
    import csv

    mapping: Dict[str, Dict[str, Optional[float]]] = {}
    if not tsv_path.is_file():
        return mapping
    with tsv_path.open(newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            sid = row.get("participant_id") or row.get("subject_id") or row.get("sub")
            if not sid:
                continue
            if not sid.lower().startswith("sub-"):
                sid = f"sub-{sid}"

            def _num(key):
                v = row.get(key)
                try:
                    return float(v) if v not in (None, "", "n/a") else None
                except (ValueError, TypeError):
                    return None

            mapping[sid] = {"age": _num("age"), "years_training": _num("years_training")}
    return mapping


def locate_shard_filename(api: HfApi) -> str:
    """Find the exact repo-relative path of the verified shard (fails loudly)."""
    files = api.list_repo_files(repo_id=REPO_ID, repo_type=REPO_TYPE)
    matches = [f for f in files if f.endswith(SHARD_BASENAME)]
    if not matches:
        # Fall back to any test-split shard of the same naming pattern.
        matches = [
            f for f in files
            if re.search(r"test-\d+-of-\d+\.parquet$", f)
        ]
    if not matches:
        raise RuntimeError(
            f"No parquet shard matching {SHARD_BASENAME} found in "
            f"{REPO_ID}; available files (first 50): {files[:50]}"
        )
    matches.sort()
    chosen = matches[0]
    if chosen != SHARD_BASENAME and not chosen.endswith(SHARD_BASENAME):
        log.warning(f"Exact shard not found; using {chosen} from {REPO_ID}")
    return chosen


def norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def find_subject_column(parquet_path: Path) -> Optional[str]:
    """Identify the real subject-ID column; None if genuinely absent."""
    pf = pq.ParquetFile(parquet_path)
    names = pf.schema_arrow.names

    # 1) exact/substring name match
    for cand in SUBJECT_NAME_CANDIDATES:
        for n in names:
            if norm(n) == cand:
                return n
    for cand in SUBJECT_NAME_CANDIDATES:
        for n in names:
            if cand in norm(n):
                return n

    # 2) pattern scan: string column whose values look like subject IDs
    first_rg = pf.read_row_group(0)
    for n in names:
        col = first_rg.column(n)
        try:
            vals = col.to_pylist()
        except Exception:
            continue
        sample = [v for v in vals if isinstance(v, str)][:200]
        if sample and sum(bool(SUB_PATTERN.match(v)) for v in sample) / len(sample) > 0.5:
            return n
    return None


def distinct_subject_count(parquet_path: Path, subject_column: str) -> int:
    """Stream the subject column row-group by row-group; count distinct IDs."""
    pf = pq.ParquetFile(parquet_path)
    seen = set()
    for rg in range(pf.num_row_groups):
        tbl = pf.read_row_group(rg, columns=[subject_column])
        seen.update(tbl.column(subject_column).to_pylist())
    seen.discard(None)
    return len(seen)


def main() -> None:
    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    dest = raw_dir / SHARD_BASENAME

    api = HfApi()
    shard_repo_path = locate_shard_filename(api)
    log.info(f"Verified shard repo path: {REPO_ID}/{shard_repo_path}")

    if dest.is_file() and dest.stat().st_size > 0:
        log.info(f"{dest} already exists; skipping download.")
    else:
        # FAIL LOUDLY: any download error propagates; no synthetic fallback.
        local = hf_hub_download(
            repo_id=REPO_ID,
            filename=shard_repo_path,
            repo_type=REPO_TYPE,
        )
        shutil.copyfile(local, dest)

    if not dest.is_file() or dest.stat().st_size == 0:
        raise RuntimeError(f"Downloaded shard missing or empty: {dest}")

    # SHA-256 checksum of the raw shard.
    sha = compute_sha256(dest)
    checksums = {SHARD_BASENAME: sha}
    checksums_path = paths.data("checksums.json")
    checksums_path.write_text(json.dumps(checksums, indent=2))
    log.info(f"SHA-256 {sha} written to {checksums_path}")

    # Column inventory from the REAL parquet schema (streamed, low memory).
    pf = pq.ParquetFile(dest)
    real_columns = list(pf.schema_arrow.names)

    subject_column = find_subject_column(dest)
    if subject_column is not None:
        n_subjects = distinct_subject_count(dest, subject_column)
    else:
        n_subjects = 0
        log.warning(
            "No subject-ID column detected in the shard; "
            "available_subject_count recorded as 0 (honest inventory)."
        )

    normalized = {norm(c): c for c in real_columns}
    field_status = {}
    for field, keys in EXPECTED_FIELDS.items():
        matched = None
        for key in keys:
            nk = norm(key)
            if nk in normalized:
                matched = normalized[nk]
                break
            for nc, orig in normalized.items():
                if nk and nk in nc:
                    matched = orig
                    break
            if matched:
                break
        field_status[field] = {
            "present": matched is not None,
            "matched_column": matched,
        }

    inventory = {
        "source": {
            "repo_id": REPO_ID,
            "repo_type": REPO_TYPE,
            "split": SPLIT,
            "shard_repo_path": shard_repo_path,
            "local_path": str(RAW_DEST_RELATIVE),
            "sha256": sha,
        },
        "columns": real_columns,
        "n_columns": len(real_columns),
        "n_row_groups": pf.num_row_groups,
        "expected_fields": field_status,
        "subject_column": subject_column,
        "available_subject_count": n_subjects,
    }
    inventory_path = raw_dir / "column_inventory.json"
    inventory_path.write_text(json.dumps(inventory, indent=2))
    log.info(
        f"Column inventory written to {inventory_path} "
        f"({len(real_columns)} columns, available_subject_count={n_subjects})"
    )
    missing = [f for f, s in field_status.items() if not s["present"]]
    log.info(f"Expected fields ABSENT from shard (honest record): {missing}")


if __name__ == "__main__":
    main()
