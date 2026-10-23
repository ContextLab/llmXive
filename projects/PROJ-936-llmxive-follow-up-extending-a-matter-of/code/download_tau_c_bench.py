"""Download the τ-bench task data from its official HuggingFace repository.

This script uses the `datasets` library to fetch the official τ‑bench dataset
(`tau_c_bench`) from HuggingFace. It merges all available splits into a single
JSON array and writes the result to ``data/raw/τc_bench/tasks.json``. A
``README.md`` containing the SHA‑256 checksum of the file is also created.

The script aborts with a clear error if the download cannot be performed.
"""

import hashlib
import json
import sys
from pathlib import Path

from datasets import load_dataset
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# The dataset identifier on HuggingFace.  According to the specification
# it is hosted under the `sierra-research` organization.
HF_DATASET = "sierra-research/tau_c_bench"

# ----------------------------------------------------------------------
def _load_tasks_via_datasets() -> list[dict]:
    """Load all task records from the ``tau_c_bench`` HuggingFace dataset.

    The dataset may contain multiple splits (e.g. ``train``, ``test``).  All
    splits are concatenated into a single list of dictionaries.

    Returns
    -------
    list[dict]
        A list of task dictionaries.
    """
    try:
        ds = load_dataset(HF_DATASET)
    except Exception as exc:
        log.error(f"Failed to load dataset {HF_DATASET}: {exc}")
        raise RuntimeError(f"Could not load HuggingFace dataset {HF_DATASET}") from exc

    # ``load_dataset`` can return a ``DatasetDict`` (multiple splits) or a
    # single ``Dataset``.  Normalise to an iterable of records.
    if isinstance(ds, dict):
        # Concatenate all splits
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

# ----------------------------------------------------------------------
def download_tasks_json() -> Path:
    """Download and merge tasks from the official τ‑bench HF dataset.

    Returns
    -------
    Path
        Path to the file containing the merged JSON array.
    """
    merged_tasks = _load_tasks_via_datasets()

    # Ensure the destination directory exists
    dest_dir = paths.data("raw", "τc_bench")
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest_file = dest_dir / "tasks.json"
    dest_file.write_text(json.dumps(merged_tasks, indent=2), encoding="utf-8")
    return dest_file

# ----------------------------------------------------------------------
def compute_sha256(file_path: Path) -> str:
    """Compute the SHA‑256 checksum of ``file_path``."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

# ----------------------------------------------------------------------
def main() -> None:
    """Entry point for the download script."""
    # Download the tasks from HF.
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
        "# τ-bench dataset (raw task definitions)\\n\\n"
        f"Downloaded from the official HuggingFace dataset `{HF_DATASET}`.\\n"
        f"Number of task records: {len(data)}\\n\\n"
        f"SHA-256 checksum of `tasks.json`: `{checksum}`\\n"
    )
    readme_path.write_text(readme_contents, encoding="utf-8")
    log.info(f"Wrote checksum README to {readme_path}")
    log.info("Dataset download completed successfully.")

# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.error(f"Download failed: {exc}")
        sys.exit(1)
