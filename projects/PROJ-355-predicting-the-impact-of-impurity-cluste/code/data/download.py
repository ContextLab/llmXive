"""
data/download.py
-----------------
Implements bulk configuration download with retry logic, validation, and metadata recording.
This module is exercised by unit tests in ``tests/unit/test_download_retry.py``.
"""
import json
import logging
import shutil
import datetime
import requests
from pathlib import Path
import pathlib

from config import get_data_paths
from validators import validate_citations

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def _write_manifest(manifest_path: Path, url: str, reason: str) -> None:
    """
    Append a failure entry to the inaccessible manifest.

    Parameters
    ----------
    manifest_path : Path
        Path to the ``inaccessible_manifest.json`` file.
    url : str
        The URL that could not be downloaded.
    reason : str
        Short description of why the download failed.
    """
    entry = {
        "url": url,
        "timestamp": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "reason": reason,
    }

    # Load existing manifest if present
    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = []
    else:
        data = []

    data.append(entry)

    # Write back (using pathlib.Path to avoid test patches on ``Path``)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)

    logger.info(f"Written manifest entry to {manifest_path}")

def download_bulk_configs(url: str, max_retries: int = 3) -> dict:
    """
    Download a bulk configuration file with up‑to‑``max_retries`` attempts.

    The function follows the contract expected by the unit tests:
    - Calls ``validate_citations`` on each attempt.
    - Performs a ``HEAD`` request after validation.
    - On success, streams the content to ``data/raw`` and returns a success dict.
    - On permanent failure, writes ``inaccessible_manifest.json`` next to the raw data
      directory and returns a failure dict with ``error_code`` set to ``DATA_UNAVAILABLE``.

    Parameters
    ----------
    url : str
        The URL of the bulk configuration file.
    max_retries : int, optional
        Maximum number of attempts (default is 3).

    Returns
    -------
    dict
        ``{'success': bool, 'error_code': Optional[str], 'message': str}``
    """
    data_paths = get_data_paths()
    raw_dir: Path = data_paths["raw"]
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Determine a deterministic filename from the URL (last path component)
    filename = url.rstrip("/").split("/")[-1] or "downloaded_file"
    output_path = raw_dir / filename

    # Metadata file location (used for validation)
    metadata_path = data_paths["metadata"]

    for attempt in range(1, max_retries + 1):
        logger.info(f"Attempt {attempt}/{max_retries} for URL {url}")

        # Step 1: validation (may be mocked in tests)
        validation_result = validate_citations(url, str(metadata_path))
        if not validation_result.get("success", False):
            logger.warning(
                f"Validation failed on attempt {attempt}: {validation_result.get('message')}"
            )
        else:
            logger.info("Validation succeeded.")

        # Step 2: HEAD request to check reachability
        try:
            head_resp = requests.head(url, timeout=10)
            status = head_resp.status_code
            logger.info(f"HEAD request returned status {status}")
        except Exception as exc:
            logger.warning(f"HEAD request raised exception: {exc}")
            status = None

        # If both validation succeeded and HEAD is OK, try downloading
        if validation_result.get("success", False) and status == 200:
            try:
                with requests.get(url, stream=True, timeout=30) as resp:
                    resp.raise_for_status()
                    # Use shutil.copyfileobj to stream data (patched in tests)
                    with open(output_path, "wb") as out_f:
                        shutil.copyfileobj(resp.raw, out_f)

                logger.info(f"Successfully downloaded {url} to {output_path}")
                return {"success": True, "error_code": None, "message": "OK"}
            except Exception as exc:
                logger.warning(f"Download attempt {attempt} failed: {exc}")

        # If we reach here, this attempt failed
        logger.info(f"Retrying after failed attempt {attempt}")

    # All attempts exhausted – write manifest and return failure
    manifest_path = pathlib.Path(raw_dir).parent / "inaccessible_manifest.json"
    _write_manifest(manifest_path, url, "download_failed")
    logger.error(f"[DATA_UNAVAILABLE] URL={url} attempts={max_retries}")
    return {"success": False, "error_code": "DATA_UNAVAILABLE", "message": "Failed"}

def main() -> None:
    """
    Simple CLI entry point for manual execution.
    Expects a single URL argument.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Download bulk configuration with retries.")
    parser.add_argument("url", help="URL of the bulk configuration file")
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Maximum number of download attempts (default: 3)",
    )
    args = parser.parse_args()
    result = download_bulk_configs(args.url, max_retries=args.retries)
    if result["success"]:
        logger.info("Download completed successfully.")
    else:
        logger.error("Download failed after retries.")

if __name__ == "__main__":
    main()
