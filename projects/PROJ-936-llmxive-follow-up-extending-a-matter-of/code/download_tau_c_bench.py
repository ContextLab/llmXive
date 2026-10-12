"""Download the τ-bench task data from its official HuggingFace repository.

The script uses the `huggingface_hub` library to fetch the official τ-bench dataset
from HuggingFace (`sierra-research/tau-bench`). It merges the tasks from
the supported domains into a single JSON file.

The merged JSON array is written to ``data/raw/τc_bench/tasks.json`` and a
``README.md`` containing the SHA‑256 checksum of the file is also created.

The script aborts with a clear error if the download cannot be performed.
"""

import hashlib
import json
import sys
from pathlib import Path

from huggingface_hub import hf_hub_download
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
HF_REPO = "sierra-research/tau-bench"
DOMAINS = ["retail", "airline"]

# ----------------------------------------------------------------------
def _fetch_via_hf() -> list[dict]:
    """Download tasks from the HuggingFace repository using huggingface_hub.
    
    The τ-bench repository is structured as a collection of files rather than 
    a formal HF Dataset object, so we download the JSON files directly.
    """
    merged: list[dict] = []
    
    try:
        for domain in DOMAINS:
            log.info(f"Fetching domain '{domain}' from HuggingFace: {HF_REPO}")
            
            # The files are typically located at {domain}/test.json in the repo
            filename = f"{domain}/test.json"
            
            # Download the file to a local cache
            local_path = hf_hub_download(
                repo_id=HF_REPO, 
                filename=filename, 
                repo_type="dataset"
            )
            
            # Load the JSON content
            with open(local_path, "r", encoding="utf-8") as f:
                domain_tasks = json.load(f)
            
            if not domain_tasks:
                log.warning(f"No tasks found for domain '{domain}' in {filename}.")
                continue
            
            # Ensure we have a list of dicts
            if not isinstance(domain_tasks, list):
                # Handle cases where the JSON might be a dict containing a list
                if isinstance(domain_tasks, dict) and "tasks" in domain_tasks:
                    domain_tasks = domain_tasks["tasks"]
                else:
                    raise ValueError(f"Expected a list of tasks for domain {domain}, got {type(domain_tasks)}")

            for task in domain_tasks:
                if isinstance(task, dict):
                    task = dict(task)
                    task.setdefault("domain", domain)
                merged.append(task)
            
            log.info(f"Fetched {len(domain_tasks)} tasks for domain '{domain}'.")
    except Exception as exc:
        log.error(f"HuggingFace fetch failed: {exc}")
        raise RuntimeError(f"Could not reach HuggingFace repository {HF_REPO}: {exc}") from exc

    if not merged:
        raise RuntimeError("No tasks were successfully downloaded from any domain.")
    
    return merged

# ----------------------------------------------------------------------
def download_tasks_json() -> Path:
    """Download and merge tasks from the official τ‑bench HF repository.

    Returns
    -------
    Path
        Path to the file containing the merged JSON array.
    """
    merged_tasks = _fetch_via_hf()

    # Ensure the directory exists
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

    dest_dir = dest_file.parent
    readme_path = dest_dir / "README.md"
    readme_contents = (
        "# τ-bench dataset (raw task definitions)\n\n"
        f"Downloaded from the official HuggingFace repository `{HF_REPO}`. "
        f"Domains merged: {', '.join(DOMAINS)}.\n\n"
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