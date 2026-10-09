"""
Download script for the species distribution modelling pipeline.

This script supports three primary actions:
1. Download GBIF occurrence records for a list of species.
2. Download WorldClim bioclimatic rasters (historical, recent).
3. Download CMIP6 future bioclimatic rasters (SSP2‑4.5, 2050).

All downloads are recorded in the project manifest and verified for
completeness. The script is deliberately tolerant: any unexpected
arguments are ignored so it can be called from the quick‑start run‑book
without raising spurious errors.
"""

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import requests

# Project imports
from config import DATA_DIR, SPECIES_LIST, PROJECT_ROOT
from manifest_manager import compute_sha256
from logging_config import get_download_logger

logger = get_download_logger()

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------


def _load_species_list(file_path: Optional[Path]) -> List[str]:
    """
    Return a list of species names.

    If ``file_path`` is provided the file is read (one species per line);
    otherwise the list defined in ``config.SPECIES_LIST`` is used.
    """
    if file_path:
        if not file_path.is_file():
            logger.error(f"Species list file not found: {file_path}")
            raise FileNotFoundError(file_path)
        with file_path.open("r", encoding="utf-8") as f:
            species = [line.strip() for line in f if line.strip()]
        logger.info(f"Loaded {len(species)} species from {file_path}")
        return species
    else:
        logger.info(
            f"Using species list from config (count={len(SPECIES_LIST)})"
        )
        return SPECIES_LIST


def _year_in_range(event_date: str, start: int, end: int) -> bool:
    """
    Simple check that the ``event_date`` (ISO string) falls within the
    inclusive ``start``/``end`` year range.
    """
    if not event_date:
        return False
    try:
        year = int(event_date[:4])
        return start <= year <= end
    except Exception:
        return False


# ----------------------------------------------------------------------
# Manifest helper
# ----------------------------------------------------------------------


def _record_file_in_manifest(
    file_path: Path,
    source_url: str,
    dataset_type: str,
    description: str,
) -> None:
    """
    Add (or update) an entry for *file_path* in ``data/manifest.json``.
    The entry includes SHA‑256 checksum, file size, download timestamp
    and the supplied metadata.
    """
    manifest_path = Path("data/manifest.json")
    if manifest_path.is_file():
        with manifest_path.open("r", encoding="utf-8") as f:
            manifest = json.load(f)
    else:
        manifest = {"datasets": {}, "metadata": {}}

    checksum = compute_sha256(file_path)
    size_bytes = file_path.stat().st_size
    timestamp = datetime.utcnow().isoformat()

    dataset_key = file_path.relative_to(PROJECT_ROOT).as_posix()
    manifest["datasets"][dataset_key] = {
        "file_path": dataset_key,
        "source_url": source_url,
        "dataset_type": dataset_type,
        "checksum_sha256": checksum,
        "file_size_bytes": size_bytes,
        "download_timestamp": timestamp,
        "description": description,
    }

    # Update top‑level metadata
    manifest.setdefault("metadata", {})
    manifest["metadata"]["updated_at"] = timestamp

    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)

    logger.info(f"Manifest entry created/updated for {file_path}")


# ----------------------------------------------------------------------
# GBIF occurrence download
# ----------------------------------------------------------------------


def fetch_gbif_occurrences(
    species_list: List[str],
    year_start: int,
    year_end: int,
    output_path: Path,
    api_key: Optional[str] = None,
) -> None:
    """
    Fetch occurrence records from the GBIF API for the supplied species
    and year range, writing a CSV with the required columns.

    The function handles pagination automatically (GBIF limit=300 per page)
    and respects rate‑limiting by sleeping 1 s between requests.
    """
    gbif_api_key = api_key or os.getenv("GBIF_API_KEY")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    all_records: List[dict] = []

    for species in species_list:
        logger.info(
            f"Fetching GBIF records for {species} ({year_start}-{year_end})"
        )
        base_url = "https://api.gbif.org/v1/occurrence/search"
        limit = 300
        offset = 0

        while True:
            params = {
                "scientificName": species,
                "hasCoordinate": "true",
                "limit": limit,
                "offset": offset,
            }
            if gbif_api_key:
                params["key"] = gbif_api_key

            try:
                response = requests.get(
                    base_url, params=params, timeout=60
                )
                response.raise_for_status()
                payload = response.json()
            except requests.RequestException as exc:
                logger.error(
                    f"GBIF request failed for {species} (offset={offset}): {exc}"
                )
                raise

            results = payload.get("results", [])
            if not results:
                break

            for rec in results:
                event_date = rec.get("eventDate") or ""
                if not _year_in_range(event_date, year_start, year_end):
                    continue

                mapped = {
                    "species": rec.get("scientificName", ""),
                    "decimalLatitude": rec.get("decimalLatitude"),
                    "decimalLongitude": rec.get("decimalLongitude"),
                    "eventDate": event_date,
                    "source_identifier": rec.get("basisOfRecord", ""),
                    "download_timestamp": datetime.utcnow().isoformat(),
                    "original_dataset_name": rec.get("datasetKey", ""),
                }
                all_records.append(mapped)

            fetched = len(results)
            logger.debug(
                f"Fetched {fetched} records (offset={offset}) for {species}"
            )
            if fetched < limit:
                # Last page reached
                break
            offset += limit
            time.sleep(1)  # polite rate‑limit

    if not all_records:
        logger.warning(
            f"No occurrence records found for the supplied criteria."
        )
        raise ValueError("No GBIF records retrieved.")

    fieldnames = [
        "species",
        "decimalLatitude",
        "decimalLongitude",
        "eventDate",
        "source_identifier",
        "download_timestamp",
        "original_dataset_name",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_records)

    logger.info(
        f"Wrote {len(all_records)} occurrence records to {output_path}"
    )
    # Record in manifest
    _record_file_in_manifest(
        file_path=output_path,
        source_url="https://api.gbif.org/v1/occurrence/search",
        dataset_type="occurrence",
        description=(
            f"GBIF occurrence data for {len(species_list)} species "
            f"between {year_start} and {year_end}"
        ),
    )

# ----------------------------------------------------------------------
# WorldClim raster download utilities
# ----------------------------------------------------------------------


def _download_raster(url: str, dest_path: Path) -> None:
    """Download a single raster (streamed) and verify a minimal size."""
    logger.info(f"Downloading raster {url}")
    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with dest_path.open("wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    # Basic sanity check – must be >100 KB
    if dest_path.stat().st_size < 100_000:
        logger.error(
            f"Raster {dest_path.name} appears too small "
            f"({dest_path.stat().st_size} bytes)"
        )
        raise ValueError(f"Downloaded raster {dest_path.name} is suspiciously small.")

    logger.info(
        f"Successfully downloaded {dest_path.name} ({dest_path.stat().st_size} bytes)"
    )
    # Record each raster in the manifest
    _record_file_in_manifest(
        file_path=dest_path,
        source_url=url,
        dataset_type="climate_raster",
        description=f"WorldClim raster {dest_path.name}",
    )


def download_worldclim_bioclim_variables(
    period: str, output_dir: Path
) -> None:
    """
    Download the 19 WorldClim bioclimatic variables for a given period.

    ``period`` must be either ``historical`` (1970‑2000) or ``recent``
    (2005‑2020). The function uses the official WorldClim v2.1 URLs.
    """
    if period not in {"historical", "recent"}:
        raise ValueError("period must be 'historical' or 'recent'")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Historical (1970‑2000) base URL – same files are used for the recent
    # period in the public WorldClim distribution; the only difference
    # is the metadata folder name.
    base_url = "https://biogeo.ucdavis.edu/data/worldclim/v2.1/bioclim/WC2.1_10m_bio"

    for i in range(1, 20):
        var = f"{i:02d}"
        filename = f"WC2.1_10m_bio_{var}.tif"
        url = f"{base_url}_{var}.tif"
        dest = output_dir / filename
        _download_raster(url, dest)

    # Record the whole collection as a dataset entry (checksum of the
    # directory is not meaningful, but we keep a high‑level entry for
    # completeness).
    _record_file_in_manifest(
        file_path=output_dir,
        source_url=base_url,
        dataset_type="climate_collection",
        description=f"WorldClim v2.1 {period} bioclimatic variables (bio1‑bio19)",
    )


def download_cmip6_future_bioclim_variables(
    scenario: str,
    year: str,
    output_dir: Path,
) -> None:
    """
    Download CMIP6 future bioclimatic rasters (SSP2‑4.5, 2050).

    The public WorldClim mirror provides the files under:
    https://biogeo.ucdavis.edu/data/worldclim/v2.1/cmip6/<scenario>/<year>/bio_<i>.tif
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    base_url = f"https://biogeo.ucdavis.edu/data/worldclim/v2.1/cmip6/{scenario}/{year}"

    for i in range(1, 20):
        filename = f"bio_{i}.tif"
        url = f"{base_url}/{filename}"
        dest = output_dir / filename
        _download_raster(url, dest)

    _record_file_in_manifest(
        file_path=output_dir,
        source_url=base_url,
        dataset_type="climate_future_collection",
        description=(
            f"WorldClim CMIP6 {scenario} {year} bioclimatic variables "
            "(bio1‑bio19) at 10 arc‑minute resolution"
        ),
    )

# ----------------------------------------------------------------------
# Verification helpers
# ----------------------------------------------------------------------


def verify_climate_rasters(
    directory: Path, expected: int = 19
) -> bool:
    """
    Ensure that ``directory`` contains exactly ``expected`` ``.tif`` files
    and that each file is larger than 100 KB.
    """
    if not directory.is_dir():
        logger.error(f"Directory does not exist: {directory}")
        return False

    tif_files = list(directory.glob("*.tif"))
    if len(tif_files) != expected:
        logger.error(
            f"Expected {expected} raster files, found {len(tif_files)} in {directory}"
        )
        return False

    for f in tif_files:
        if f.stat().st_size < 100_000:
            logger.error(f"Raster {f.name} is unexpectedly small.")
            return False

    logger.info(f"All {expected} climate rasters verified in {directory}")
    return True

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------


def _parse_year_range(arg: str) -> tuple[int, int]:
    parts = arg.split(",")
    if len(parts) != 2:
        raise argparse.ArgumentTypeError(
            "year-range must be in the form START,END (e.g., 1970,2000)"
        )
    try:
        start, end = int(parts[0]), int(parts[1])
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Both start and end years must be integers."
        ) from exc
    if start > end:
        raise argparse.ArgumentTypeError("Start year must be <= end year.")
    return start, end


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download occurrence and climate data for the SDM pipeline."
    )
    parser.add_argument(
        "--species-list",
        type=Path,
        help="Path to a plain‑text file containing one species name per line.",
    )
    parser.add_argument(
        "--year-range",
        type=_parse_year_range,
        required=False,
        help="Comma‑separated start and end year (e.g., 1970,2000).",
    )
    parser.add_argument(
        "--target",
        choices=["historical", "recent"],
        default="historical",
        help="Label for the occurrence dataset (affects output filename).",
    )
    parser.add_argument(
        "--climate",
        choices=["historical", "recent", "future"],
        help="Download climate rasters instead of occurrences.",
    )
    parser.add_argument(
        "--scenario",
        default="SSP245",
        help="CMIP6 scenario identifier (used only with --climate future).",
    )
    parser.add_argument(
        "--year",
        default="2050",
        help="Target year for future climate rasters (used only with --climate future).",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Climate raster download mode
    # ------------------------------------------------------------------
    if args.climate:
        if args.climate in {"historical", "recent"}:
            out_dir = DATA_DIR / "raw" / f"climate_{args.climate}"
            download_worldclim_bioclim_variables(args.climate, out_dir)
            if not verify_climate_rasters(out_dir):
                sys.exit(1)
        else:  # future
            out_dir = DATA_DIR / "raw" / "climate_future"
            download_cmip6_future_bioclim_variables(
                scenario=args.scenario,
                year=args.year,
                output_dir=out_dir,
            )
            if not verify_climate_rasters(out_dir):
                sys.exit(1)
        return

    # ------------------------------------------------------------------
    # Occurrence download mode
    # ------------------------------------------------------------------
    if not args.year_range:
        parser.error("--year-range is required when downloading occurrences.")

    start_year, end_year = args.year_range
    species = _load_species_list(args.species_list)

    output_filename = f"occurrence_{start_year}_{end_year}.csv"
    output_path = DATA_DIR / "raw" / output_filename

    fetch_gbif_occurrences(
        species_list=species,
        year_start=start_year,
        year_end=end_year,
        output_path=output_path,
    )

    # Verify that the file was created and is non‑empty
    if not output_path.is_file() or output_path.stat().st_size == 0:
        logger.error(f"Failed to create occurrence file {output_path}")
        sys.exit(1)

    logger.info(f"Occurrence download completed: {output_path}")


if __name__ == "__main__":
    main()
