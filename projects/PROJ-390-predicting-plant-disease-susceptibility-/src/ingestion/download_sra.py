"""
SRA Data Downloader for Plant Disease Susceptibility Project.

Fetches SRA reads for wheat, rice, maize, tomato, and soybean using NCBI E-utilities.
Implements retry logic with exponential backoff and atomic writes with file locking.
"""
import os
import sys
import time
import json
import fcntl
import hashlib
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.utils.config import get_species_accession, get_species_info, ensure_paths_exist
from src.utils.logger import get_logger, setup_logging_for_task, log_error, log_info, log_warning

# Constants
MAX_RETRIES = 3
BASE_DELAY = 2.0  # seconds
MAX_DELAY = 30.0  # seconds
NCBI_EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
SRA_DOWNLOAD_TOOL = "esearch"
SRA_FETCH_TOOL = "efetch"
SRA_TOOLS_DIR = "data/raw/sra_downloads"
LOCK_SUFFIX = ".lock"

logger = get_logger(__name__)


def exponential_backoff(attempt: int, base_delay: float = BASE_DELAY, max_delay: float = MAX_DELAY) -> float:
    """Calculate exponential backoff delay."""
    delay = min(base_delay * (2 ** attempt), max_delay)
    jitter = delay * 0.1 * (hash(str(time.time())) % 100 / 100.0)  # Add small jitter
    return delay + jitter


def fetch_sra_ids(species: str, accession: str) -> List[str]:
    """
    Fetch SRA run IDs for a given species and accession using NCBI E-utilities.

    Args:
        species: Species name
        accession: Reference genome accession ID

    Returns:
        List of SRA run IDs

    Raises:
        RuntimeError: If fetch fails after max retries
    """
    search_query = f"{species}[Organism] AND {accession}[Assembly]"
    params = {
        "db": "sra",
        "term": search_query,
        "retmax": 100,  # Limit to 100 runs per species for this implementation
        "retmode": "json"
    }

    url = f"{NCBI_EUTILS_BASE}{SRA_DOWNLOAD_TOOL}?{urlencode(params)}"

    for attempt in range(MAX_RETRIES):
        try:
            log_info(logger, f"Fetching SRA IDs for {species} (attempt {attempt + 1}/{MAX_RETRIES})")
            request = Request(url, headers={"User-Agent": "PlantDiseaseSusceptibility/1.0"})
            with urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))

            if "esearchresult" in data and "idlist" in data["esearchresult"]:
                run_ids = data["esearchresult"]["idlist"]
                if run_ids:
                    log_info(logger, f"Found {len(run_ids)} SRA runs for {species}")
                    return run_ids
                else:
                    log_warning(logger, f"No SRA runs found for {species} with accession {accession}")
                    return []
            else:
                raise ValueError(f"Unexpected response format: {data}")

        except (URLError, HTTPError, json.JSONDecodeError) as e:
            log_error(logger, f"Error fetching SRA IDs for {species}: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                delay = exponential_backoff(attempt)
                log_warning(logger, f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
            else:
                raise RuntimeError(f"Failed to fetch SRA IDs for {species} after {MAX_RETRIES} retries: {str(e)}")

    return []


def download_sra_run(run_id: str, output_dir: Path, species: str) -> Path:
    """
    Download SRA data for a specific run ID using prefetch (part of SRA Toolkit).

    Args:
        run_id: SRA run ID
        output_dir: Directory to save downloaded files
        species: Species name for logging

    Returns:
        Path to downloaded file

    Raises:
        RuntimeError: If download fails after max retries
    """
    output_path = output_dir / f"{run_id}.sra"
    lock_path = output_dir / f"{run_id}{LOCK_SUFFIX}"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    for attempt in range(MAX_RETRIES):
        try:
            # Check if file already exists and is complete
            if output_path.exists() and output_path.stat().st_size > 0:
                log_info(logger, f"File {output_path} already exists, skipping download")
                return output_path

            # Create lock file
            lock_file = open(lock_path, 'w')
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

                # Double-check after acquiring lock
                if output_path.exists() and output_path.stat().st_size > 0:
                    log_info(logger, f"File {output_path} created by another process, skipping")
                    return output_path

                log_info(logger, f"Downloading SRA run {run_id} for {species} (attempt {attempt + 1}/{MAX_RETRIES})")

                # Use prefetch from SRA Toolkit
                # Note: This assumes sratoolkit is installed and in PATH
                prefetch_cmd = f"prefetch -O {output_dir} {run_id}"
                result = os.system(prefetch_cmd)

                if result == 0:
                    log_info(logger, f"Successfully downloaded {run_id}")
                    return output_path
                else:
                    raise RuntimeError(f"prefetch command failed with exit code {result}")

            except BlockingIOError:
                log_warning(logger, f"Could not acquire lock for {run_id}, another process is downloading")
                time.sleep(1)
                continue
            finally:
                try:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                    lock_file.close()
                    lock_path.unlink(missing_ok=True)
                except Exception:
                    pass

        except Exception as e:
            log_error(logger, f"Error downloading SRA run {run_id}: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                delay = exponential_backoff(attempt)
                log_warning(logger, f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
            else:
                raise RuntimeError(f"Failed to download SRA run {run_id} after {MAX_RETRIES} retries: {str(e)}")

    raise RuntimeError(f"Failed to download SRA run {run_id}")


def atomic_write_metadata(metadata: Dict[str, Any], output_path: Path):
    """
    Atomically write metadata to a file using temporary file and rename.

    Args:
        metadata: Metadata dictionary to write
        output_path: Path to output file
    """
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create temporary file
    fd, temp_path = tempfile.mkstemp(dir=output_dir, suffix=".tmp")
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(metadata, f, indent=2)

        # Atomic rename
        shutil.move(temp_path, output_path)
        log_info(logger, f"Successfully wrote metadata to {output_path}")
    except Exception as e:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise RuntimeError(f"Failed to write metadata atomically: {str(e)}")


def download_species_data(species: str, accession: str) -> Dict[str, Any]:
    """
    Download all SRA data for a specific species.

    Args:
        species: Species name
        accession: Reference genome accession ID

    Returns:
        Dictionary containing download results
    """
    log_info(logger, f"Starting download for {species} (accession: {accession})")

    output_dir = Path("data/raw/sra_downloads") / species
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "species": species,
        "accession": accession,
        "download_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "runs": []
    }

    try:
        # Fetch SRA run IDs
        run_ids = fetch_sra_ids(species, accession)

        if not run_ids:
            log_warning(logger, f"No SRA runs found for {species}")
            metadata["status"] = "no_runs_found"
            atomic_write_metadata(metadata, output_dir / "metadata.json")
            return metadata

        # Download each run
        downloaded_files = []
        failed_downloads = []

        for run_id in run_ids:
            try:
                file_path = download_sra_run(run_id, output_dir, species)
                downloaded_files.append({
                    "run_id": run_id,
                    "file_path": str(file_path),
                    "status": "success"
                })
            except Exception as e:
                log_error(logger, f"Failed to download {run_id}: {str(e)}")
                failed_downloads.append({
                    "run_id": run_id,
                    "error": str(e)
                })

        metadata["runs"] = downloaded_files
        metadata["failed_downloads"] = failed_downloads
        metadata["status"] = "completed" if not failed_downloads else "partial_failure"
        metadata["total_runs"] = len(run_ids)
        metadata["successful_downloads"] = len(downloaded_files)
        metadata["failed_downloads_count"] = len(failed_downloads)

        # Write metadata
        atomic_write_metadata(metadata, output_dir / "metadata.json")

        if failed_downloads:
            raise RuntimeError(f"Failed to download {len(failed_downloads)}/{len(run_ids)} runs for {species}")

        return metadata

    except Exception as e:
        log_error(logger, f"Critical error downloading {species}: {str(e)}")
        metadata["status"] = "error"
        metadata["error"] = str(e)
        atomic_write_metadata(metadata, output_dir / "metadata.json")
        raise


def main():
    """Main function to download SRA data for all supported species."""
    setup_logging_for_task("download_sra")

    log_info(logger, "Starting SRA data download pipeline")

    # Ensure paths exist
    ensure_paths_exist()

    # Get species information
    species_list = ["wheat", "rice", "maize", "tomato", "soybean"]
    results = {}

    for species in species_list:
        try:
            accession = get_species_accession(species)
            if not accession:
                log_warning(logger, f"No accession ID found for {species}, skipping")
                continue

            result = download_species_data(species, accession)
            results[species] = result

        except Exception as e:
            log_error(logger, f"Failed to download data for {species}: {str(e)}")
            results[species] = {"status": "error", "error": str(e)}

    # Summary
    successful = sum(1 for r in results.values() if r.get("status") == "completed")
    total = len(results)

    log_info(logger, f"Download pipeline completed: {successful}/{total} species successful")

    if successful < total:
        log_error(logger, "Some species failed to download. Check logs for details.")
        sys.exit(1)

    log_info(logger, "All SRA downloads completed successfully")
    return results


if __name__ == "__main__":
    main()
