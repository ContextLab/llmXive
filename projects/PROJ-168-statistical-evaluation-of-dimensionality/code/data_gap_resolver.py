import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Project imports
from config import Config
from download import (
    download_dataset,
    calculate_md5,
    DownloadError,
    ChecksumValidationError,
    LabelValidationError,
)

# Configure module‑level logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class DatasetStatus:
    """Enum‑like container for dataset availability status."""
    AVAILABLE = "Available"
    UNAVAILABLE = "Unavailable"


class DataGapResolver:
    """
    Resolves the Phase 0 data‑gap by ensuring that raw count matrices for the
    configured GEO accessions exist, are valid, and are recorded in a manifest.
    """

    def __init__(self, config: Config):
        self.config = config
        # Directories from the Config object
        self.raw_dir: Path = config.data_raw
        self.results_dir: Path = config.results_dir
        # Ensure the results folder exists
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # List of GEO accessions we must attempt to obtain
        self.accessions: List[str] = config.accessions

    # -----------------------------------------------------------------
    # Helper methods
    # -----------------------------------------------------------------
    def _find_existing_file(self, accession: str) -> Optional[Path]:
        """
        Look for a file that starts with the accession name inside the raw
        directory. Returns the first match or None.
        """
        candidates = list(self.raw_dir.glob(f"{accession}*"))
        return candidates[0] if candidates else None

    def _download_if_missing(self, accession: str) -> Tuple[Optional[Path], str]:
        """
        Ensure a raw count matrix for *accession* exists.
        If a file is already present we reuse it; otherwise we attempt to
        download it via ``download_dataset``.
        Returns a tuple ``(path_to_file, status)`` where *status* is one of
        ``DatasetStatus.AVAILABLE`` or ``DatasetStatus.UNAVAILABLE``.
        """
        existing = self._find_existing_file(accession)
        if existing:
            logger.info(f"Found existing raw file for {accession}: {existing}")
            return existing, DatasetStatus.AVAILABLE

        logger.info(f"No local file for {accession}; attempting download.")
        try:
            # ``download_dataset`` creates the file inside ``self.raw_dir``.
            downloaded_path = download_dataset(
                accession,
                raw_dir=str(self.raw_dir),
            )
            logger.info(f"Downloaded {accession} to {downloaded_path}")
            return Path(downloaded_path), DatasetStatus.AVAILABLE
        except (DownloadError, ChecksumValidationError, LabelValidationError) as e:
            logger.error(f"Failed to obtain {accession}: {e}")
            return None, DatasetStatus.UNAVAILABLE
        except Exception as e:
            logger.exception(f"Unexpected error while handling {accession}: {e}")
            return None, DatasetStatus.UNAVAILABLE

    def _build_manifest_entry(
        self,
        accession: str,
        file_path: Optional[Path],
        status: str,
    ) -> Dict[str, Any]:
        """
        Construct a single manifest dictionary entry.
        """
        entry: Dict[str, Any] = {
            "dataset_id": accession,
            "source_url": f"https://www.ncbi.nlm.nih.gov/geo/download/?acc={accession}&format=txt&file={accession}_series_matrix.txt.gz",
            "status": status,
            "checksum": None,
            "raw_file_path": None,
            "processed_file_path": None,
        }

        if file_path and status == DatasetStatus.AVAILABLE:
            # Compute checksum (MD5) – the download module already uses MD5
            try:
                checksum = calculate_md5(str(file_path))
                entry["checksum"] = checksum
            except Exception as e:
                logger.warning(f"Could not compute checksum for {file_path}: {e}")

            entry["raw_file_path"] = str(file_path)

        return entry

    # -----------------------------------------------------------------
    # Core public method
    # -----------------------------------------------------------------
    def resolve_all_gaps(self) -> Dict[str, Any]:
        """
        Main driver that attempts to obtain each dataset, writes a JSON
        manifest, and enforces the three‑dataset requirement.
        Returns a summary dictionary (also written to ``data_gap_report.json``).
        """
        manifest_entries: List[Dict[str, Any]] = []
        available_count = 0

        for accession in self.accessions:
            logger.info(f"Processing accession {accession}")
            file_path, status = self._download_if_missing(accession)
            if status == DatasetStatus.AVAILABLE:
                available_count += 1

            entry = self._build_manifest_entry(accession, file_path, status)
            manifest_entries.append(entry)

        # -----------------------------------------------------------------
        # Write the manifest (data/manifest.json)
        # -----------------------------------------------------------------
        manifest_path = Path("data") / "manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with manifest_path.open("w", encoding="utf-8") as f:
            json.dump(manifest_entries, f, indent=2)
        logger.info(f"Manifest written to {manifest_path}")

        # -----------------------------------------------------------------
        # Write a human‑readable summary if we have fewer than three datasets
        # -----------------------------------------------------------------
        if available_count < 3:
            summary_path = self.results_dir / "data_gap_summary.txt"
            summary_msg = (
                f"Data‑gap resolution failed: only {available_count} dataset(s) "
                f"available (minimum required: 3). Pipeline abort."
            )
            with summary_path.open("w", encoding="utf-8") as f:
                f.write(summary_msg + "\n")
            logger.error(summary_msg)
            # Exit code 1 signals the pipeline to stop.
            sys.exit(1)

        # -----------------------------------------------------------------
        # Produce a detailed report (legacy artifact used by earlier tasks)
        # -----------------------------------------------------------------
        report = {
            "datasets": manifest_entries,
            "summary": {
                "total_requested": len(self.accessions),
                "available": available_count,
                "unavailable": len(self.accessions) - available_count,
            },
        }
        report_path = self.results_dir / "data_gap_report.json"
        with report_path.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        logger.info(f"Data‑gap report written to {report_path}")

        return report

# -----------------------------------------------------------------
# CLI entry point
# -----------------------------------------------------------------
def main() -> None:
    """
    Execute the data‑gap resolution when the module is run as a script.
    """
    cfg = Config()
    resolver = DataGapResolver(cfg)
    resolver.resolve_all_gaps()
    # Successful completion (>=3 datasets) exits with code 0.
    sys.exit(0)


if __name__ == "__main__":
    main()
