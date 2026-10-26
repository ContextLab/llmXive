"""
Download Ego4D metadata and video‑MAE embeddings, store them under a given
output directory, and write SHA‑256 checksums for each downloaded file.

The script is invoked from the quickstart guide:

    python src/data/download.py \
        --metadata-url <metadata_url> \
        --embeddings-url <embeddings_url> \
        --output-dir data/raw/

It will:
  * Stream‑download the two URLs (metadata JSON and embeddings tar.gz) to
    `data/raw/` preserving the original filenames.
  * Compute a SHA‑256 checksum for each file.
  * Write a `CHECKSUMS.txt` file with one line per file:
        <checksum>  <filename>
  * Raise a clear exception if any download fails or if the checksum
    computation cannot be performed.

The implementation avoids any synthetic fallback – it aborts on any
network or I/O error, satisfying the “real data, no synthetic fallback”
requirement.
"""

import argparse
import hashlib
import sys
from pathlib import Path
from typing import Iterable

import requests
from tqdm.auto import tqdm

# Default URLs point to the verified Ego4D resources used throughout the
# project.  They allow the script to be run without explicitly passing the
# URLs, which matches the verification command in the tasks description.
DEFAULT_METADATA_URL = (
    "https://huggingface.co/datasets/HuggingFaceM4/ego4d/resolve/main/dataset_infos.json"
)
DEFAULT_EMBEDDINGS_URL = (
    "https://huggingface.co/datasets/Jazzcharles/ego4d_videomae_L14_feature_fps8/resolve/main/chunk_0.tar.gz"
)


def _compute_sha256(file_path: Path) -> str:
    """Compute the SHA‑256 checksum of a file."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _download_file(url: str, dest_path: Path) -> None:
    """
    Stream‑download a file from ``url`` to ``dest_path``.
    Raises ``RuntimeError`` on HTTP errors or I/O problems.
    """
    try:
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            # Use tqdm for a progress bar; the bar is silent in CI but
            # helpful when run locally.
            with dest_path.open("wb") as f, tqdm(
                total=total,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                desc=f"Downloading {dest_path.name}",
                leave=False,
            ) as bar:
                for chunk in r.iter_content(chunk_size=8192):
                    if not chunk:
                        continue
                    f.write(chunk)
                    bar.update(len(chunk))
    except Exception as e:
        raise RuntimeError(f"Failed to download '{url}': {e}") from e


def download_ego4d(
    metadata_url: str,
    embeddings_url: str,
    output_dir: Path,
) -> None:
    """
    Download Ego4D metadata and embeddings, write checksums.

    Parameters
    ----------
    metadata_url: str
        Direct URL to the JSON metadata file.
    embeddings_url: str
        Direct URL to the video‑MAE embeddings tar‑gz archive.
    output_dir: Path
        Directory where the raw files will be stored.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine filenames from URLs.
    metadata_fname = Path(metadata_url).name
    embeddings_fname = Path(embeddings_url).name

    metadata_path = output_dir / metadata_fname
    embeddings_path = output_dir / embeddings_fname

    # Download both files.
    _download_file(metadata_url, metadata_path)
    _download_file(embeddings_url, embeddings_path)

    # Compute checksums.
    checksums = {
        metadata_path.name: _compute_sha256(metadata_path),
        embeddings_path.name: _compute_sha256(embeddings_path),
    }

    # Write CHECKSUMS.txt.
    checksum_path = output_dir / "CHECKSUMS.txt"
    with checksum_path.open("w", encoding="utf-8") as f:
        for fname, chksum in checksums.items():
            f.write(f"{chksum}  {fname}\\n")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download Ego4D metadata and embeddings."
    )
    parser.add_argument(
        "--metadata-url",
        type=str,
        default=DEFAULT_METADATA_URL,
        help="URL to the Ego4D metadata JSON file. Defaults to the verified dataset URL.",
    )
    parser.add_argument(
        "--embeddings-url",
        type=str,
        default=DEFAULT_EMBEDDINGS_URL,
        help="URL to the Ego4D video‑MAE embeddings tar.gz archive. Defaults to the verified dataset URL.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/raw",
        help="Directory where raw files will be stored (default: data/raw).",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    try:
        download_ego4d(
            metadata_url=args.metadata_url,
            embeddings_url=args.embeddings_url,
            output_dir=Path(args.output_dir),
        )
    except Exception as e:
        # Propagate a clear error message; the runner will surface this.
        sys.stderr.write(f"{e}\\n")
        raise


if __name__ == "__main__":
    main()
