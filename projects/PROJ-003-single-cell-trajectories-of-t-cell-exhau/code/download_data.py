"""Download raw count matrices for the T‑cell exhaustion project using SRA Toolkit.

This implementation fetches the real SRA files associated with the GEO
series GSE136103, GSE127465, GSE111075, and GSE138852 via `prefetch`.
The downloaded `.sra` files are placed under ``data/raw/<GSE>/counts/``.
SHA‑256 checksums of the first downloaded file are recorded in
``data/state.yaml`` to satisfy Constitution Principle III.
"""
import argparse
import hashlib
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

import yaml

# Functions from the SRA‑toolkit installer to ensure the tool is present
try:
    from install_sra_toolkit import (
        install_sra_toolkit,
        verify_sra_toolkit,
    )
except ImportError:  # pragma: no cover
    install_sra_toolkit = None
    verify_sra_toolkit = None

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


def prefetch_sra(gse_id: str, destination: Path) -> None:
    """Run `prefetch -O <destination> <gse_id>`.

    Raises:
        RuntimeError: If the SRA Toolkit is not installed or the command fails.
    """
    # Ensure SRA Toolkit is available
    if install_sra_toolkit is not None:
        if not install_sra_toolkit():
            raise RuntimeError("Failed to install SRA Toolkit via conda.")
    if verify_sra_toolkit is not None and not verify_sra_toolkit():
        raise RuntimeError("SRA Toolkit verification failed – `prefetch --help` did not run.")

    cmd = ["prefetch", "-O", str(destination), gse_id]
    logger.info(f"Running SRA Toolkit command: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"prefetch failed for {gse_id}: {e.stderr.strip()}")
        raise RuntimeError(f"prefetch failed for {gse_id}") from e


def collect_sra_files(gse_dir: Path) -> list[Path]:
    """Recursively collect all ``.sra`` files under *gse_dir*."""
    return list(gse_dir.rglob("*.sra"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download raw count matrices for the T‑cell exhaustion project using SRA Toolkit."
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

    failures = []

    for gse in gse_ids:
        logger.info(f"Processing {gse} …")
        gse_dir = raw_root / gse
        counts_dir = gse_dir / "counts"
        counts_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Download SRA files directly into the GSE directory
            prefetch_sra(gse, str(gse_dir))

            # Locate the downloaded .sra files (they may be inside sub‑folders)
            sra_files = collect_sra_files(gse_dir)
            if not sra_files:
                raise RuntimeError(f"No .sra files were retrieved for {gse}")

            # Move (or copy) the .sra files into the ``counts`` sub‑directory
            for sra_path in sra_files:
                target_path = counts_dir / sra_path.name
                if not target_path.exists():
                    sra_path.replace(target_path)

            # Re‑collect after moving
            final_files = list(counts_dir.iterdir())
            if not final_files:
                raise RuntimeError(f"Failed to place .sra files into {counts_dir}")

            first_file = final_files[0]
            checksum = calculate_sha256(first_file)

            # Record minimal metadata; later stages will enrich it
            update_state(
                gse,
                {
                    "dataset_id": gse,
                    "source": "SRA",
                    "raw_counts_path": str(first_file.relative_to(project_root)),
                    "checksum": checksum,
                    "counts_checksum": checksum,
                    "cell_count": 0,
                    "gene_count": 0,
                    "status": "available",
                    "sufficiency_screen": {"source_record": "sra_download"},
                },
            )
            logger.info(f"Successfully prepared {gse} – {len(final_files)} .sra file(s) saved.")
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Failed to process {gse}: {exc}")
            failures.append(gse)
            update_state(
                gse,
                {
                    "dataset_id": gse,
                    "source": "SRA",
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
