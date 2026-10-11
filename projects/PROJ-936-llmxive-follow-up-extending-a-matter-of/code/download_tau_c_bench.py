"""Download the τ-bench task data from its official repository.

The previous version of this script guessed HuggingFace repository
identifiers that do not exist, which caused the download to fail.
The τ-bench benchmark (Yao et al., 2024, "τ-bench: A Benchmark for
Tool-Agent-User Interaction in Real-World Domains") publishes its
task definitions as ``tasks.json`` files in the official GitHub
repository ``sierra-research/tau-bench`` (data for the ``retail``
and ``airline`` domains).

This script fetches the raw ``tasks.json`` files from the official
GitHub repository via ``https://raw.githubusercontent.com``, merges
them into a single JSON array of task records (annotated with a
``domain`` field), and stores the result under
``data/raw/τc_bench/tasks.json``.  It also writes a ``README.md``
containing the SHA-256 checksum of the downloaded file.

The script aborts with a clear error if the repository cannot be
reached.  It never falls back to synthetic data.
"""

import hashlib
import json
import sys
from pathlib import Path

import requests

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Official τ-bench repository (sierra-research/tau-bench).  The task
# definitions live under ``data/<domain>/tasks.json`` on the default
# branch.  Both public domains are fetched and merged.
GITHUB_RAW_BASE = (
    "https://raw.githubusercontent.com/sierra-research/tau-bench/main/data"
)
DOMAINS = ["retail", "airline"]
TIMEOUT_S = 60

# ----------------------------------------------------------------------
def download_tasks_json() -> Path:
    """Download ``tasks.json`` from the official τ-bench repository.

    Fetches the task definitions for every configured domain,
    annotates each task record with its ``domain``, and merges them
    into a single JSON array written to a temporary file.

    Returns
    -------
    Path
        Local path to the merged, downloaded JSON file.

    Raises
    ------
    RuntimeError
        If the repository cannot be reached or the downloaded
        content is not valid JSON.
    """
    merged_tasks = []
    last_err = None
    for domain in DOMAINS:
        url = f"{GITHUB_RAW_BASE}/{domain}/tasks.json"
        try:
            log.info(f"Fetching {url}")
            response = requests.get(url, timeout=TIMEOUT_S)
            response.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            log.error(f"Failed to fetch {url}: {exc}")
            last_err = exc
            continue
        try:
            domain_tasks = json.loads(response.text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Content fetched from {url} is not valid JSON."
            ) from exc
        if not isinstance(domain_tasks, list) or not domain_tasks:
            raise RuntimeError(
                f"Content fetched from {url} is empty or not a task list."
            )
        for task in domain_tasks:
            if isinstance(task, dict):
                task = dict(task)
                task.setdefault("domain", domain)
            merged_tasks.append(task)
        log.info(f"Fetched {len(domain_tasks)} tasks for domain '{domain}'.")

    if not merged_tasks:
        raise RuntimeError(
            "Unable to download tasks.json from the official τ-bench "
            f"repository ({GITHUB_RAW_BASE}). Check internet "
            "connectivity and repository availability."
        ) from last_err

    tmp_file = Path(paths.data("raw", "τc_bench")) / "_tasks_merged.tmp.json"
    tmp_file.parent.mkdir(parents=True, exist_ok=True)
    tmp_file.write_text(json.dumps(merged_tasks, indent=2), encoding="utf-8")
    return tmp_file

# ----------------------------------------------------------------------
def compute_sha256(file_path: Path) -> str:
    """Compute the SHA-256 checksum of ``file_path``."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

# ----------------------------------------------------------------------
def main() -> None:
    # Download the raw JSON file(s).
    temp_file = download_tasks_json()

    # Destination directory: data/raw/τc_bench/
    dest_dir = paths.data("raw", "τc_bench")
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Destination file path.
    dest_file = dest_dir / "tasks.json"
    dest_file.write_bytes(temp_file.read_bytes())
    temp_file.unlink(missing_ok=True)
    log.info(f"Wrote tasks.json to {dest_file}")

    # Verify that the file is non-empty and valid JSON; abort loudly.
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

    readme_path = dest_dir / "README.md"
    readme_contents = (
        "# τ-bench dataset (raw task definitions)\n\n"
        "Downloaded from the official repository "
        "`sierra-research/tau-bench` on GitHub "
        f"({GITHUB_RAW_BASE}), domains: {', '.join(DOMAINS)}.\n\n"
        f"Number of task records: {len(data)}\n\n"
        f"SHA-256 checksum of `tasks.json`: `{checksum}`\n"
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
