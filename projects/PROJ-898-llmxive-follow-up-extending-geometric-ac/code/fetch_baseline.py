"""
fetch_baseline.py

Fetch and validate the baseline Geometric Foundation Model (GFM) weights
``data/raw/gfm_baseline.pt`` according to ``code/config.yaml``.

Behaviour (per task T005-baseline-fetch):
1. Read ``baseline_model_url`` from ``code/config.yaml``.
2. If ``data/raw/gfm_baseline.pt`` already exists on disk (the plan
   designates ``data/raw/`` for user-provided weights), validate it:
   compute its SHA-256, write the checksum sidecar
   ``data/raw/gfm_baseline.pt.sha256``, and exit 0.
3. Otherwise, download the file from the configured URL. On success,
   compute and record the SHA-256 checksum and exit 0.
4. If the file cannot be obtained (network error, HTTP error status,
   missing URL), abort with a CLEAR error message and exit status 1.
   No synthetic or placeholder weights are ever generated.

Note: this script intentionally does NOT import ``code/config.py``
(which requires PyYAML). It reads the flat ``baseline_model_url`` key
directly from ``code/config.yaml`` so it runs in a minimal environment.
"""

import hashlib
import logging
import sys
import urllib.error
import urllib.request
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CODE_DIR.parent
CONFIG_PATH = CODE_DIR / "config.yaml"
DEST_PATH = PROJECT_ROOT / "data" / "raw" / "gfm_baseline.pt"
CHECKSUM_PATH = DEST_PATH.with_suffix(DEST_PATH.suffix + ".sha256")

logger = logging.getLogger("fetch_baseline")


def setup_logging() -> None:
    """Configure basic console logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def read_baseline_url(config_path: Path = CONFIG_PATH) -> str:
    """
    Read the ``baseline_model_url`` key from the flat YAML config.

    Raises FileNotFoundError if the config file is missing and
    RuntimeError if the key is absent or empty.
    """
    if not config_path.is_file():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    url = None
    for raw_line in config_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if line.startswith("baseline_model_url:"):
            value = line.split(":", 1)[1].strip().strip('"').strip("'")
            if value:
                url = value
            break
    if not url:
        raise RuntimeError(
          "Missing or empty 'baseline_model_url' in code/config.yaml"
        )
    return url


def compute_sha256(file_path: Path) -> str:
    """Compute the SHA-256 hex digest of a file."""
    sha = hashlib.sha256()
    with open(file_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            sha.update(chunk)
    return sha.hexdigest()


def download_file(url: str, dest_path: Path) -> None:
    """
    Download ``url`` to ``dest_path`` using urllib.

    Raises RuntimeError with a clear message on any failure
    (network error, HTTP error status, or write failure).
    """
    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            status = getattr(response, "status", None)
            if status is not None and status != 200:
                raise RuntimeError(
                    f"Failed to download baseline model: HTTP {status}"
                )
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = dest_path.with_suffix(dest_path.suffix + ".tmp")
            with open(tmp_path, "wb") as out_file:
                out_file.write(response.read())
            tmp_path.replace(dest_path)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"HTTP error while downloading baseline model from {url}: {exc}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Network error while downloading baseline model from {url}: {exc}"
        ) from exc
    except OSError as exc:
        raise RuntimeError(
            f"I/O error while saving baseline model to {dest_path}: {exc}"
        ) from exc


def record_checksum(file_path: Path) -> str:
    """Compute the checksum and write it next to the weights file."""
    checksum = compute_sha256(file_path)
    CHECKSUM_PATH.write_text(checksum + "\n", encoding="utf-8")
    return checksum


def main() -> int:
    """
    Entry point for the baseline fetch script.

    Returns 0 on success (file present and validated, or downloaded),
    1 on a clear abort when the file cannot be obtained.
    """
    setup_logging()

    try:
        url = read_baseline_url()
    except (FileNotFoundError, RuntimeError) as exc:
        logger.error("Baseline fetch aborted: %s", exc)
        return 1

    if DEST_PATH.is_file() and DEST_PATH.stat().st_size > 0:
        checksum = record_checksum(DEST_PATH)
        logger.info("Found existing baseline model at %s", DEST_PATH)
        logger.info("SHA-256 checksum: %s", checksum)
        return 0

    logger.info("Downloading baseline GFM weights from %s", url)
    try:
        download_file(url, DEST_PATH)
    except RuntimeError as exc:
        logger.error("Baseline fetch aborted: %s", exc)
        logger.error(
            "No synthetic weights are generated. Place the real "
            "baseline weights at %s or fix 'baseline_model_url' "
            "in code/config.yaml.",
            DEST_PATH,
        )
        return 1

    if not DEST_PATH.is_file() or DEST_PATH.stat().st_size == 0:
        logger.error(
            "Baseline fetch aborted: download reported success but "
            "%s is missing or empty.",
            DEST_PATH,
        )
        return 1

    checksum = record_checksum(DEST_PATH)
    logger.info("Downloaded baseline model saved to %s", DEST_PATH)
    logger.info("SHA-256 checksum: %s", checksum)
    return 0


if __name__ == "__main__":
    sys.exit(main())
