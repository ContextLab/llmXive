"""Download the τⁿ‑Bench dataset from HuggingFace.

This script fetches the raw ``tasks.json`` file from the official
HuggingFace repository and stores it under ``data/raw/τc_bench/``.
It also writes a ``README.md`` containing the SHA‑256 checksum of the
downloaded file.

The script aborts with a clear error if the dataset cannot be reached.
"""

import hashlib
import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

# huggingface_hub is added to ``requirements.txt`` by this task.
try:
    from huggingface_hub import hf_hub_download
except Exception as e:
    raise RuntimeError(
        "huggingface_hub is required for dataset download. "
        "Make sure it is listed in requirements.txt."
    ) from e

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# A list of candidate repository identifiers.  The first one that
# succeeds is used.  These identifiers correspond to the official
# τⁿ‑Bench HuggingFace repository (the exact name may vary across
# releases).
REPO_CANDIDATES = [
    "tau-c-bench/tau-c-bench",
    "tau_c_bench/tau_c_bench",
    "tau-c-bench/τc-bench",
]
FILENAME = "tasks.json"

# ----------------------------------------------------------------------
def download_tasks_json() -> Path:
    """Download ``tasks.json`` from the first reachable repo.

    Returns
    -------
    Path
        Local path to the downloaded file (temporary location managed by
        ``huggingface_hub``).
    """
    last_err = None
    for repo_id in REPO_CANDIDATES:
        try:
            log.info(f"Attempting to download {FILENAME} from repo '{repo_id}'.")
            downloaded_path = hf_hub_download(repo_id=repo_id, filename=FILENAME)
            log.info(f"Successfully downloaded from '{repo_id}'.")
            return Path(downloaded_path)
        except Exception as exc:  # noqa: BLE001
            log.warning(f"Failed to download from '{repo_id}': {exc}")
            last_err = exc
    raise RuntimeError(
        f"Unable to download '{FILENAME}' from any candidate repository. "
        "Check internet connectivity and repository name."
    ) from last_err

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
    # Download the raw JSON file.
    temp_file = download_tasks_json()

    # Destination directory: data/raw/τc_bench/
    dest_dir = paths.data("raw", "τc_bench")
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Destination file path.
    dest_file = dest_dir / FILENAME
    dest_file.write_bytes(temp_file.read_bytes())
    log.info(f"Wrote tasks.json to {dest_file}")

    # Compute and record checksum.
    checksum = compute_sha256(dest_file)

    readme_path = dest_dir / "README.md"
    readme_contents = (
        "# τⁿ‑Bench dataset\n\n"
        f"SHA‑256 checksum of `{FILENAME}`: `{checksum}`\n"
    )
    readme_path.write_text(readme_contents, encoding="utf-8")
    log.info(f"Wrote checksum README to {readme_path}")

    # Verify that the file is non‑empty; abort loudly if it is.
    if dest_file.stat().st_size == 0:
        raise RuntimeError("Downloaded tasks.json is empty. Aborting.")

    log.info("Dataset download completed successfully.")

# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.error(f"Download failed: {exc}")
        sys.exit(1)
