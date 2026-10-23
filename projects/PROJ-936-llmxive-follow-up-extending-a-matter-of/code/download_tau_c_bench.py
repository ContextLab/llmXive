"""Download the τ‑bench task data from its official HuggingFace repository.

This script attempts to fetch the official τ‑bench dataset (`tau_c_bench`) from
HuggingFace.  The primary implementation uses the `datasets` library, but a
fallback that streams the raw `tasks.json` file via HTTP is provided to avoid
the heavy `pyarrow` dependency (which requires NumPy 2.0).  The script writes
the merged task list to ``data/raw/τc_bench/tasks.json`` and creates a
``README.md`` containing the SHA‑256 checksum of that file.

The script aborts with a clear error if the download cannot be performed.
"""

import hashlib
import json
import sys
from pathlib import Path
from typing import List

import requests
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# The HuggingFace dataset identifier.
HF_DATASET = "sierra-research/tau_c_bench"
# Direct URL to the raw ``tasks.json`` file in the repository.  This URL
# follows the standard pattern used by the HuggingFace hub for datasets.
RAW_JSON_URL = (
    f"https://huggingface.co/datasets/{HF_DATASET}/resolve/main/tasks.json"
)
# ----------------------------------------------------------------------


def _load_tasks_via_datasets() -> List[dict]:
    """Load all task records using the ``datasets`` library.

    Returns
    -------
    list[dict]
        A list of task dictionaries.
    """
    try:
        from datasets import load_dataset  # Imported lazily to avoid import‑time errors
    except Exception as exc:
        log.debug(f"datasets import failed ({exc}); falling back to HTTP download.")
        raise RuntimeError("datasets library unavailable") from exc

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
    """Download the raw ``tasks.json`` file directly from the hub.

    Returns
    -------
    list[dict]
        A list of task dictionaries.
    """
    log.info(f"Downloading tasks.json from {RAW_JSON_URL}")
    try:
        response = requests.get(RAW_JSON_URL, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        log.error(f"Failed to download tasks.json via HTTP: {exc}")
        raise RuntimeError("HTTP download of tasks.json failed") from exc

    try:
        data = response.json()
    except json.JSONDecodeError as exc:
        log.error(f"Downloaded tasks.json is not valid JSON: {exc}")
        raise RuntimeError("Downloaded tasks.json is not valid JSON") from exc

    if not isinstance(data, list):
        raise RuntimeError("tasks.json does not contain a JSON array.")
    if not data:
        raise RuntimeError("tasks.json is empty.")
    return data


def download_tasks_json() -> Path:
    """Download and merge tasks from the official τ‑bench HF dataset.

    Returns
    -------
    Path
        Path to the file containing the merged JSON array.
    """
    # First try the high‑level ``datasets`` API.  If that fails (e.g. due to
    # missing pyarrow), fall back to a simple HTTP fetch of the raw file.
    try:
        merged_tasks = _load_tasks_via_datasets()
    except Exception:
        log.info("Falling back to HTTP download for tasks.json.")
        merged_tasks = _load_tasks_via_http()

    dest_dir = paths.data("raw", "τc_bench")
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest_file = dest_dir / "tasks.json"
    dest_file.write_text(json.dumps(merged_tasks, indent=2), encoding="utf-8")
    return dest_file


def compute_sha256(file_path: Path) -> str:
    """Compute the SHA‑256 checksum of ``file_path``."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def main() -> None:
    """Entry point for the download script."""
    dest_file = download_tasks_json()

    # Verify that the file is non‑empty and valid JSON; abort loudly.
    if dest_file.stat().st_size == 0:
        raise RuntimeError("Downloaded tasks.json is empty. Aborting.")
    try:
        data = json.loads(dest_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError("Downloaded tasks.json is not valid JSON.") from exc

    if not isinstance(data, list) or len(data) == 0:
        raise RuntimeError(
            "Downloaded tasks.json does not contain any tasks. Aborting."
        )
    log.info(f"tasks.json contains {len(data)} task records.")

    # Compute and record checksum.
    checksum = compute_sha256(dest_file)

    readme_path = dest_file.parent / "README.md"
    readme_contents = (
        "# τ‑bench dataset (raw task definitions)\\n\\n"
        f"Downloaded from the official HuggingFace dataset `{HF_DATASET}`.\\n"
        f"Number of task records: {len(data)}\\n\\n"
        f"SHA-256 checksum of `tasks.json`: `{checksum}`\\n"
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
