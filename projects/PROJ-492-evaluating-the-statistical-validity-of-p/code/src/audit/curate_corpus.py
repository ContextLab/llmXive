"""
Curate a deterministic corpus of public A/B test summary URLs.

This script reads the original ``data/input/urls.csv`` file, attempts to
download each URL, writes the raw HTML snapshot to ``data/raw/`` using a
deterministic SHA‑256 based filename, and produces a new ``urls.csv`` that
only contains the URLs that were successfully retrieved.  It also writes a
``data/checksums.txt`` file containing a SHA‑256 hash for each snapshot.

The script is deliberately side‑effecting (it writes files) because the
``tests/test_curate_corpus.py`` test suite expects the files to exist after
the module is imported.  A ``pytest`` ``conftest.py`` file (see below) calls
:func:`main` before any test runs.
"""
import csv
import hashlib
import logging
from pathlib import Path

import requests
from tqdm import tqdm

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
MIN_URLS = 300               # Minimum number of successful snapshots required
TIMEOUT = 15                 # Seconds for HTTP request timeout
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
# ----------------------------------------------------------------------


log = get_logger(__name__)


def _load_candidate_urls(csv_path: Path) -> list[str]:
    """Read the ``url`` column from the input CSV."""
    urls = []
    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get("url", "").strip()
            if url:
                urls.append(url)
    # Deterministic order
    urls.sort()
    return urls


def _download_page(url: str) -> bytes:
    """Download a page, returning its raw ``bytes`` content.

    Raises:
        requests.RequestException: for network‑level errors.
        ValueError: if the response is not HTTP 200 or not HTML.
    """
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=TIMEOUT, stream=True)
    response.raise_for_status()

    # Simple content‑type guard – we only care about HTML pages.
    ct = response.headers.get("Content-Type", "")
    if "text/html" not in ct.lower():
        raise ValueError(f"URL did not return HTML (Content‑Type: {ct})")

    return response.content


def _filename_for_url(url: str) -> str:
    """
    Produce a deterministic, filesystem‑safe filename for a given URL.

    The filename is the SHA‑256 hex digest of the URL with a ``.html``
    suffix.  This avoids any Unicode‑normalisation problems that arise
    from directly sanitising the URL string.
    """
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return f"{digest}.html"


def _write_snapshot(content: bytes, dest_path: Path) -> None:
    """Write raw HTML bytes to ``dest_path``."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with dest_path.open("wb") as f:
        f.write(content)


def _compute_sha256(file_path: Path) -> str:
    """Return the SHA‑256 hex digest of the file at ``file_path``."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    """
    Entry point used by the ``pytest`` ``conftest`` and by the normal
    pipeline.  It performs the full curation workflow and exits with ``0`` on
    success or raises an exception on failure.
    """
    input_csv = paths.data("input", "urls.csv")
    raw_dir = paths.data("raw")
    checksums_path = paths.data("checksums.txt")

    log.info("Loading candidate URLs from %s", input_csv)
    candidate_urls = _load_candidate_urls(input_csv)

    successful_records = []  # List of (url, filename, checksum)

    log.info("Attempting to download %d URLs (minimum %d required)", len(candidate_urls), MIN_URLS)
    for url in tqdm(candidate_urls, desc="Downloading URLs", unit="url"):
        try:
            content = _download_page(url)
        except Exception as exc:
            log.error("Failed to download %s: %s", url, exc)
            continue

        filename = _filename_for_url(url)
        file_path = raw_dir / filename

        try:
            _write_snapshot(content, file_path)
        except Exception as exc:
            log.error("Failed to write snapshot for %s: %s", url, exc)
            continue

        checksum = _compute_sha256(file_path)
        successful_records.append((url, filename, checksum))

    if len(successful_records) < MIN_URLS:
        raise RuntimeError(
            f"Only {len(successful_records)} URLs were successfully downloaded; "
            f"minimum required is {MIN_URLS}."
        )

    # ------------------------------------------------------------------
    # Write curated URLs CSV (only successful URLs, preserving header)
    # ------------------------------------------------------------------
    curated_csv_path = paths.data("input", "urls.csv")
    with curated_csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["url"])
        writer.writeheader()
        for url, _, _ in successful_records:
            writer.writerow({"url": url})

    log.info("Wrote curated URLs CSV with %d entries to %s", len(successful_records), curated_csv_path)

    # ------------------------------------------------------------------
    # Write checksums file
    # ------------------------------------------------------------------
    with checksums_path.open("w", encoding="utf-8") as f:
        for _, filename, checksum in successful_records:
            # Path stored relative to the project root as required by the spec
            rel_path = Path("data", "raw", filename)
            f.write(f"{checksum} {rel_path}\n")

    log.info("Wrote checksums for %d snapshots to %s", len(successful_records), checksums_path)

    return 0


if __name__ == "__main__":
    exit(main())
