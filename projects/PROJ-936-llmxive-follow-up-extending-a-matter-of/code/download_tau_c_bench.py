"""Download the τ-bench task data from its official repository.

The script attempts to fetch the raw ``tasks.json`` files from the official
GitHub repository ``sierra-research/tau-bench``. If the direct fetch fails
(e.g., due to network issues or repository changes), it falls back to
downloading the repository archive as a ZIP file, extracting the required
``tasks.json`` files, and merging them.

The merged JSON array is written to ``data/raw/τc_bench/tasks.json`` and a
``README.md`` containing the SHA‑256 checksum of the file is also created.

The script aborts with a clear error if both download strategies fail.
"""

import hashlib
import json
import sys
import zipfile
from pathlib import Path
from io import BytesIO

import requests

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Official τ-bench repository (sierra-research/tau-bench). The task
# definitions live under ``data/<domain>/tasks.json`` on the default
# branch. Both public domains are fetched and merged.
GITHUB_RAW_BASE = (
    "https://raw.githubusercontent.com/sierra-research/tau-bench/main/data"
)
GITHUB_ZIP_URL = (
    "https://github.com/sierra-research/tau-bench/archive/refs/heads/main.zip"
)
DOMAINS = ["retail", "airline"]
TIMEOUT_S = 60

# ----------------------------------------------------------------------
def _fetch_via_raw() -> list[dict]:
    """Attempt to download each domain's ``tasks.json`` via the raw URL."""
    merged = []
    last_err = None
    for domain in DOMAINS:
        url = f"{GITHUB_RAW_BASE}/{domain}/tasks.json"
        try:
            log.info(f"Fetching {url}")
            response = requests.get(url, timeout=TIMEOUT_S)
            response.raise_for_status()
            domain_tasks = json.loads(response.text)
        except Exception as exc:  # noqa: BLE001
            log.error(f"Failed to fetch {url}: {exc}")
            last_err = exc
            continue

        if not isinstance(domain_tasks, list) or not domain_tasks:
            raise RuntimeError(
                f"Content fetched from {url} is empty or not a task list."
            )
        for task in domain_tasks:
            if isinstance(task, dict):
                task = dict(task)
                task.setdefault("domain", domain)
            merged.append(task)
        log.info(f"Fetched {len(domain_tasks)} tasks for domain '{domain}'.")
    if not merged:
        raise RuntimeError(
            "All raw fetch attempts failed."
        ) from (last_err or RuntimeError("No error captured"))
    return merged

# ----------------------------------------------------------------------
def _fetch_via_zip() -> list[dict]:
    """Download the repository archive as a ZIP and extract tasks.json files."""
    log.info(f"Downloading repository ZIP from {GITHUB_ZIP_URL}")
    try:
        resp = requests.get(GITHUB_ZIP_URL, timeout=TIMEOUT_S, stream=True)
        resp.raise_for_status()
    except Exception as exc:
        raise RuntimeError(
            f"Failed to download repository ZIP from {GITHUB_ZIP_URL}"
        ) from exc

    with zipfile.ZipFile(BytesIO(resp.content)) as zip_ref:
        # The ZIP contains a top‑level folder named ``tau-bench-main/``.
        merged = []
        for domain in DOMAINS:
            task_path = f"tau-bench-main/data/{domain}/tasks.json"
            try:
                with zip_ref.open(task_path) as f:
                    data = json.load(f)
            except KeyError:
                raise RuntimeError(
                    f"tasks.json not found in ZIP at expected path {task_path}"
                )
            if not isinstance(data, list) or not data:
                raise RuntimeError(
                    f"Extracted {task_path} is empty or not a task list."
                )
            for task in data:
                if isinstance(task, dict):
                    task = dict(task)
                    task.setdefault("domain", domain)
                merged.append(task)
            log.info(f"Extracted {len(data)} tasks for domain '{domain}'.")
        if not merged:
            raise RuntimeError("ZIP extraction yielded no tasks.")
        return merged

# ----------------------------------------------------------------------
def download_tasks_json() -> Path:
    """Download and merge ``tasks.json`` from the official τ‑bench repository.

    Returns
    -------
    Path
        Path to a temporary file containing the merged JSON array.
    """
    try:
        merged_tasks = _fetch_via_raw()
    except Exception as raw_err:
        log.warning(f"Raw fetch failed ({raw_err}); attempting ZIP fallback.")
        try:
            merged_tasks = _fetch_via_zip()
        except Exception as zip_err:
            log.error(f"ZIP fallback also failed: {zip_err}")
            raise RuntimeError(
                "Unable to download tasks.json from the official τ‑bench "
                "repository via both raw and ZIP methods."
            ) from zip_err

    tmp_file = Path(paths.data("raw", "τc_bench")) / "_tasks_merged.tmp.json"
    tmp_file.parent.mkdir(parents=True, exist_ok=True)
    tmp_file.write_text(json.dumps(merged_tasks, indent=2), encoding="utf-8")
    return tmp_file

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
    # Download the raw JSON file(s) (with fallback).
    temp_file = download_tasks_json()

    # Destination directory: data/raw/τc_bench/
    dest_dir = paths.data("raw", "τc_bench")
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Destination file path.
    dest_file = dest_dir / "tasks.json"
    dest_file.write_bytes(temp_file.read_bytes())
    temp_file.unlink(missing_ok=True)
    log.info(f"Wrote tasks.json to {dest_file}")

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

    readme_path = dest_dir / "README.md"
    readme_contents = (
        "# τ-bench dataset (raw task definitions)\\n\\n"
        "Downloaded from the official repository "
        "`sierra-research/tau-bench` on GitHub "
        f"({GITHUB_RAW_BASE}), domains: {', '.join(DOMAINS)}.\\n\\n"
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
