"""Download the τ‑bench task data from its official HuggingFace repository.

This script attempts to fetch the official τ‑bench dataset (`tau_c_bench`) from
HuggingFace. The primary implementation uses the `datasets` library. If that
fails, a fallback HTTP download is performed, trying several possible locations
for the raw `tasks.json` file. If all of those fail, we finally attempt to
download the file via the `huggingface_hub` utilities. The script writes the
merged task list to `data/raw/τc_bench/tasks.json` and creates a `README.md`
containing the SHA‑256 checksum of that file.

The script aborts with a clear error if the download cannot be performed.
"""

import hashlib
import json
import sys
from pathlib import Path
from typing import List

import requests
from llmxive_toolkit import paths, get_logger

# Optional imports that may not be present in the base environment.
try:
    from datasets import load_dataset  # type: ignore
except Exception:
    load_dataset = None  # type: ignore

try:
    from huggingface_hub import hf_hub_download  # type: ignore
except Exception:
    hf_hub_download = None  # type: ignore

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# The HuggingFace dataset identifier as specified in tasks.md
HF_DATASET = "tau_c_bench"

# Possible URLs for the raw tasks.json file in the repository.
RAW_JSON_URLS = [
    f"https://huggingface.co/datasets/{HF_DATASET}/resolve/main/tasks.json",
    f"https://huggingface.co/datasets/{HF_DATASET}/resolve/main/data/tasks.json",
    f"https://raw.githubusercontent.com/sierra-research/tau_c_bench/main/tasks.json",
    f"https://raw.githubusercontent.com/sierra-research/tau_c_bench/main/data/tasks.json",
]
# ----------------------------------------------------------------------

def _load_tasks_via_datasets() -> List[dict]:
    """Load all task records using the `datasets` library."""
    if load_dataset is None:
        raise RuntimeError("datasets library unavailable")

    try:
        ds = load_dataset(HF_DATASET)
    except Exception as exc:
        log.error(f"Failed to load dataset {HF_DATASET} via `datasets`: {exc}")
        raise RuntimeError(f"Could not load HuggingFace dataset {HF_DATASET}") from exc

    # Normalise to a flat list of dictionaries
    if isinstance(ds, dict):
        records = []
        for split_name, split_ds in ds.items():
            log.info(f"Loading split '{split_name}' with {len(split_ds)} records.")
            records.extend([dict(item) for item in split_ds])
    else:
        log.info(f"Loading single split with {len(ds)} records.")
        records = [dict(item) for item in ds]

    if not records:
        raise RuntimeError("The loaded dataset contains no task records.")
    return records

def _load_tasks_via_http() -> List[dict]:
    """Download the raw tasks.json file directly from the hub."""
    for url in RAW_JSON_URLS:
        log.info(f"Attempting to download tasks.json from {url}")
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
        except Exception as exc:
            log.warning(f"Download from {url} failed: {exc}")
            continue

        try:
            data = response.json()
        except json.JSONDecodeError as exc:
            log.error(f"Downloaded content from {url} is not valid JSON: {exc}")
            continue

        if not isinstance(data, list):
            log.error(f"Data from {url} is not a JSON array.")
            continue
        if not data:
            log.error(f"Data from {url} is empty.")
            continue

        log.info(f"Successfully downloaded tasks.json from {url}")
        return data

    raise RuntimeError("HTTP download of tasks.json failed for all known URLs")

def _load_tasks_via_hf_hub() -> List[dict]:
    """Download tasks.json using huggingface_hub utilities."""
    if hf_hub_download is None:
        raise RuntimeError("huggingface_hub library unavailable")

    possible_paths = ["tasks.json", "data/tasks.json"]
    last_err = None
    for repo_path in possible_paths:
        try:
            local_path = hf_hub_download(repo_id=HF_DATASET, filename=repo_path)
            log.info(f"Downloaded {repo_path} via huggingface_hub to {local_path}")
            with open(local_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("Downloaded JSON is not a list")
            return data
        except Exception as exc:
            log.warning(f"hf_hub_download failed for {repo_path}: {exc}")
            last_err = exc
            continue

    raise RuntimeError("All huggingface_hub download attempts failed") from last_err

def download_tasks_json() -> Path:
    """Download and merge tasks from the official τ‑bench HF dataset."""
    try:
        merged_tasks = _load_tasks_via_datasets()
    except Exception as exc:
        log.info(f"datasets load failed ({exc}); falling back to HTTP download.")
        try:
            merged_tasks = _load_tasks_via_http()
        except Exception as exc_http:
            log.info(f"HTTP download failed ({exc_http}); trying huggingface_hub.")
            merged_tasks = _load_tasks_via_hf_hub()

    dest_dir = paths.data("raw", "τc_bench")
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest_file = dest_dir / "tasks.json"
    dest_file.write_text(json.dumps(merged_tasks, indent=2), encoding="utf-8")
    return dest_file

def compute_sha256(file_path: Path) -> str:
    """Compute the SHA‑256 checksum of `file_path`."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def main() -> None:
    """Entry point for the download script."""
    dest_file = download_tasks_json()

    if dest_file.stat().st_size == 0:
        raise RuntimeError("Downloaded tasks.json is empty. Aborting.")
    try:
        data = json.loads(dest_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError("Downloaded tasks.json is not valid JSON.") from exc

    if not isinstance(data, list) or len(data) == 0:
        raise RuntimeError("Downloaded tasks.json does not contain any tasks. Aborting.")
    log.info(f"tasks.json contains {len(data)} task records.")

    checksum = compute_sha256(dest_file)

    readme_path = dest_file.parent / "README.md"
    readme_contents = (
        "# τ‑bench dataset (raw task definitions)\n\n"
        f"Downloaded from the official HuggingFace dataset `{HF_DATASET}`.\n"
        f"Number of task records: {len(data)}\n\n"
        f"SHA-256 checksum of `tasks.json`: `{checksum}`\n"
    )
    readme_path.write_text(readme_contents, encoding="utf-8")
    log.info(f"Wrote checksum README to {readme_path}")
    log.info("Dataset download completed successfully.")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.error(f"Download failed: {exc}")
        sys.exit(1)