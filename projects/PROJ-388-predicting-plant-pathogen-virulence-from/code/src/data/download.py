"""
Data download module for fetching plant pathogen genomes and phenotypic scores.

This module implements 'Fail Loudly' error handling using the unified error
pattern defined in src.utils.errors. No synthetic fallbacks are allowed.
"""
import os
import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import requests
from Bio import Entrez
from Bio.SeqIO import parse as seq_parse
import pandas as pd
from io import StringIO
from urllib.error import URLError
from json import JSONDecodeError

from src.utils.config import DATA_ROOT, SEED
from src.utils.errors import DataFetchError, handle_data_fetch_error, wrap_fetch_operation

# Configure logging
logger = logging.getLogger(__name__)
Entrez.email = "pipeline@llmxive.org"  # Required by NCBI

# Retry configuration
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0  # seconds

# Target organisms
TARGET_ORGANISMS = [
    "Fusarium graminearum",
    "Pseudomonas syringae",
    "Xanthomonas"
]

def _retry_fetch(func):
    """Internal decorator to add exponential backoff retry logic."""
    def wrapper(*args, **kwargs):
        last_exception = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return func(*args, **kwargs)
            except (requests.exceptions.RequestException, URLError, JSONDecodeError) as e:
                last_exception = e
                if attempt < MAX_RETRIES:
                    wait_time = RETRY_BACKOFF * (2 ** (attempt - 1))
                    logger.warning(f"Attempt {attempt} failed. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed after {MAX_RETRIES} attempts.")
                    raise
        raise last_exception
    return wrapper


@_retry_fetch
def fetch_genome_from_ncbi(accession: str, output_dir: Path) -> Path:
    """
    Fetch a genome assembly from NCBI using E-utilities.
    
    Args:
        accession: The NCBI assembly accession (e.g., GCF_00000xxx).
        output_dir: Directory to save the downloaded FASTA file.
    
    Returns:
        Path to the downloaded FASTA file.
    
    Raises:
        DataFetchError: If the fetch fails after retries.
    """
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=assembly&id={accession}&rettype=fasta&retmode=text"
    output_path = output_dir / f"{accession}.fna"
    
    try:
        response = requests.get(url, stream=True, timeout=60)
        if response.status_code != 200:
            raise DataFetchError(
                f"NCBI E-utilities returned status {response.status_code}",
                url=url,
                status_code=response.status_code
            )
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        logger.info(f"Downloaded genome for {accession} to {output_path}")
        return output_path
    
    except DataFetchError:
        raise
    except Exception as e:
        handle_data_fetch_error(e, url=url, step="ncbi_genome_fetch")


@_retry_fetch
def fetch_phenotype_from_phibase(species: str) -> List[Dict[str, Any]]:
    """
    Fetch phenotypic disease severity scores from PHI-base.
    
    Note: PHI-base does not have a simple direct API for bulk fetch by species.
    This implementation simulates a structured fetch or uses a known endpoint
    if available, otherwise raises an error to be handled by the pipeline.
    
    Args:
        species: The species name to search.
    
    Returns:
        List of phenotype records.
    
    Raises:
        DataFetchError: If the fetch fails.
    """
    # PHI-base search URL (simplified example)
    search_url = f"https://www.phi-base.org/search?q={species}&type=organism"
    
    try:
        # In a real scenario, we would parse the HTML or use their API if available.
        # For this implementation, we assume a JSON endpoint or raise if not found.
        # Since PHI-base is primarily a web database, we will attempt to fetch
        # a known structured dataset or raise a clear error if the specific
        # programmatic access isn't available.
        
        # Placeholder for actual API logic if available, else raise
        # to enforce "Fail Loudly"
        raise DataFetchError(
            f"Direct programmatic fetch for PHI-base species '{species}' not implemented or unavailable. "
            "Please download the PHI-base dataset manually and place it in data/raw/ or implement the specific scraper.",
            url=search_url
        )
        
    except DataFetchError:
        raise
    except Exception as e:
        handle_data_fetch_error(e, url=search_url, step="phibase_fetch")


def load_local_phenotypes(file_path: Path) -> pd.DataFrame:
    """
    Load phenotypic scores from a local CSV file (fallback for when API fails).
    
    This is NOT a synthetic fallback. It expects a real file downloaded by the user
    or a previous step. If the file is missing, it raises DataFetchError.
    
    Args:
        file_path: Path to the local CSV file.
    
    Returns:
        DataFrame with phenotypic scores.
    
    Raises:
        DataFetchError: If the file is missing or invalid.
    """
    if not file_path.exists():
        raise DataFetchError(
            f"Local phenotype file not found: {file_path}",
            context={"expected_path": str(file_path)}
        )
    
    try:
        df = pd.read_csv(file_path)
        if 'species' not in df.columns or 'phenotype_score' not in df.columns:
            raise DataFetchError(
                "Invalid phenotype file schema",
                context={"columns": list(df.columns)}
            )
        return df
    except Exception as e:
        handle_data_fetch_error(e, step="local_phenotype_load")


def download_genomes() -> Dict[str, Path]:
    """
    Main function to download genomes for target organisms.
    
    Returns:
        Dictionary mapping accession to file path.
    """
    output_dir = Path(DATA_ROOT) / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Example accessions (these would be looked up dynamically in a real pipeline)
    # For now, we simulate the lookup or use hardcoded example accessions
    # to demonstrate the fetch logic.
    example_accessions = {
        "Fusarium graminearum": "GCF_000002365.2",
        "Pseudomonas syringae": "GCF_000006765.1",
        "Xanthomonas oryzae": "GCF_000007885.1"
    }
    
    downloaded = {}
    for org, acc in example_accessions.items():
        try:
            path = fetch_genome_from_ncbi(acc, output_dir)
            downloaded[org] = path
        except DataFetchError as e:
            logger.error(f"Failed to download {org}: {e}")
            # Re-raise to stop the pipeline (Fail Loudly)
            raise
    
    return downloaded


def run_download_pipeline() -> None:
    """
    Orchestrates the download pipeline.
    """
    logger.info("Starting download pipeline...")
    try:
        genomes = download_genomes()
        logger.info(f"Successfully downloaded {len(genomes)} genomes.")
        # Log URLs for provenance (T058)
        metadata = {
            "source": "NCBI E-utilities",
            "accessions": list(genomes.keys()),
            "download_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(Path(DATA_ROOT) / "processed" / "download_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
    except DataFetchError as e:
        logger.critical(f"Pipeline failed due to data fetch error: {e}")
        raise
    except Exception as e:
        handle_data_fetch_error(e, step="download_pipeline_orchestration")


if __name__ == "__main__":
    run_download_pipeline()
