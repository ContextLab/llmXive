"""Download raw count matrices for the T‑cell exhaustion project using public GEO FTP.

This implementation fetches the supplementary files associated with the GEO
series GSE136103, GSE127465, GSE111075, and GSE138852 via HTTP(S). The
downloaded files are placed under ``data/raw/<GSE>/counts/``. SHA‑256
checksums of the first downloaded file for each series are recorded in
``data/state.yaml`` to satisfy Constitution Principle III.

The script does **not** rely on the SRA Toolkit (which may be unavailable in
CI environments). Instead it uses the public GEO FTP server, which hosts the
original raw count matrices or related files for each dataset.
"""
import argparse
import hashlib
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List
import urllib.request
import urllib.error
import re
import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# The four GEO series required for the study
TARGET_GSE_IDS = [
    "GSE136103",
    "GSE127465",
    "GSE111075",
    "GSE138852",
]


def calculate_sha256(file_path: Path) -> str:
    """Calculate the SHA‑256 checksum of *file_path*."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def update_state(dataset_id: str, metadata: Dict[str, Any]) -> None:
    """Write *metadata* for *dataset_id* into ``data/state.yaml``."""
    project_root = Path(__file__).resolve().parent.parent
    state_path = project_root / "data" / "state.yaml"
    state_path.parent.mkdir(parents=True, exist_ok=True)

    if state_path.exists():
        with state_path.open("r") as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {}

    state.setdefault("datasets", {})
    state["datasets"][dataset_id] = metadata

    with state_path.open("w") as f:
        yaml.dump(state, f, default_flow_style=False)


def _geo_series_ftp_base(gse_id: str) -> str:
    """
    Return the base FTP URL for a GEO series.

    GEO groups series in directories of the form
    ``.../GSEnnnxxx/GSEnnnxxx/suppl/`` where the middle component replaces
    the last three digits with ``nnn``.
    """
    if not re.match(r"^GSE\\d+$", gse_id):
        raise ValueError(f"Invalid GEO series identifier: {gse_id}")

    # Replace the last three digits with 'nnn'
    prefix = gse_id[:-3] + "nnn"
    return f"https://ftp.ncbi.nlm.nih.gov/geo/series/{prefix}/{gse_id}/suppl/"


def _list_ftp_directory(url: str) -> List[str]:
    """
    Return a list of filenames present in the given FTP/HTTP directory.

    The function fetches the HTML index page and extracts ``href`` links.
    """
    try:
        with urllib.request.urlopen(url) as response:
            html = response.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Failed to list directory {url}: {e}") from e

    # Simple regex to capture href values that do not end with '/' (i.e., files)
    links = re.findall(r'href="([^"?]+)"', html)
    files = [link for link in links if not link.endswith("/")]
    return files


def _download_file(url: str, dest_path: Path) -> None:
    """
    Stream‑download a file from *url* to *dest_path*.

    Raises RuntimeError on network errors.
    """
    logger.info(f"Downloading {url} → {dest_path}")
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(url) as response, dest_path.open("wb") as out_file:
            while True:
                chunk = response.read(1 << 20)  # 1 MiB
                if not chunk:
                    break
                out_file.write(chunk)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP error while downloading {url}: {e}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"URL error while downloading {url}: {e}") from e


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Download raw count matrices for the T‑cell exhaustion project "
            "using public GEO FTP servers."
        )
    )
    parser.add_argument(
        "--datasets",
        type=str,
        default=",".join(TARGET_GSE_IDS),
        help="Comma‑separated list of GSE accessions to process.",
    )
    args = parser.parse_args()
    gse_ids = [g.strip() for g in args.datasets.split(",") if g.strip()]

    project_root = Path(__file__).resolve().parent.parent
    raw_root = project_root / "data" / "raw"
    raw_root.mkdir(parents=True, exist_ok=True)

    failures: List[str] = []

    for gse in gse_ids:
        logger.info(f"Processing {gse} …")
        gse_dir = raw_root / gse
        counts_dir = gse_dir / "counts"
        counts_dir.mkdir(parents=True, exist_ok=True)

        try:
            base_url = _geo_series_ftp_base(gse)
            logger.info(f"Listing files at {base_url}")
            files = _list_ftp_directory(base_url)

            if not files:
                raise RuntimeError(f"No supplementary files found for {gse} at {base_url}")

            # Download all files (or a subset if desired). Here we download all.
            downloaded_paths: List[Path] = []
            for filename in files:
                file_url = base_url + filename
                dest_file = counts_dir / filename
                _download_file(file_url, dest_file)
                downloaded_paths.append(dest_file)

            # Record checksum of the first downloaded file (as required)
            first_file = downloaded_paths[0]
            checksum = calculate_sha256(first_file)

            update_state(
                gse,
                {
                    "dataset_id": gse,
                    "source": "GEO_FTP",
                    "raw_counts_path": str(first_file.relative_to(project_root)),
                    "checksum": checksum,
                    "counts_checksum": checksum,
                    "cell_count": 0,
                    "gene_count": 0,
                    "status": "available",
                    "sufficiency_screen": {"source_record": "geo_ftp_download"},
                },
            )
            logger.info(
                f"Successfully prepared {gse} – {len(downloaded_paths)} file(s) saved."
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Failed to process {gse}: {exc}")
            failures.append(gse)
            update_state(
                gse,
                {
                    "dataset_id": gse,
                    "source": "GEO_FTP",
                    "raw_counts_path": "",
                    "checksum": "",
                    "counts_checksum": "",
                    "cell_count": 0,
                    "gene_count": 0,
                    "status": "unavailable",
                    "error": str(exc),
                },
            )
            continue

    if failures:
        logger.critical(f"Data preparation failed for: {', '.join(failures)}")
        sys.exit(1)

    logger.info("All datasets prepared successfully. State written to data/state.yaml")


if __name__ == "__main__":
    main()
