"""
Data Fetcher for Honeybee CCD GWAS Pipeline.

This module handles the retrieval of genomic data from NCBI BioProject.
It enforces SSL verification and strict failure modes per FR-001.
"""
import os
import sys
import ssl
import argparse
import json
import subprocess
import hashlib
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Project constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
STATE_DIR = PROJECT_ROOT / "state"
VERIFIED_SOURCES_FILE = STATE_DIR / "verified_sources.yaml"

# BioProject ID for Honeybee CCD studies (Example: PRJNA491963 - Honeybee Genome Variation)
# Note: In a real production scenario, this might be dynamic or read from a config.
BIO_PROJECT_ID = "PRJNA491963"
NCBI_BASE_URL = "https://www.ncbi.nlm.nih.gov"
SRA_API_URL = "https://www.ncbi.nlm.nih.gov/sra/docs/sra-accession/"

def check_ssl_verification() -> bool:
    """
    Verifies that the system can establish an SSL connection to NCBI.
    Returns True if successful, False otherwise.
    """
    try:
        context = ssl.create_default_context()
        with context.wrap_socket(requests.get, server_hostname="www.ncbi.nlm.nih.gov") as sock:
            # Just a HEAD request to verify connectivity without downloading
            requests.head("https://www.ncbi.nlm.nih.gov", timeout=10, verify=True)
        return True
    except ssl.SSLError as e:
        print(f"ERROR: SSL verification failed: {e}", file=sys.stderr)
        return False
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Network error during SSL check: {e}", file=sys.stderr)
        return False

def fetch_biomaterial_list(project_id: str) -> Optional[List[Dict[str, Any]]]:
    """
    Fetches a list of SRA accessions associated with a BioProject.
    Uses the NCBI E-Utilities (esearch/efetch) API.
    """
    # Step 1: Search for SRA experiments in the BioProject
    esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "sra",
        "term": f"{project_id}[BioProject] AND SRA[Source]",
        "retmode": "json",
        "retmax": 1000
    }

    session = _create_retry_session()
    try:
        response = session.get(esearch_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "esearchresult" not in data or "idlist" not in data["esearchresult"]:
            print(f"WARNING: No SRA accessions found for BioProject {project_id}", file=sys.stderr)
            return None

        accessions = data["esearchresult"]["idlist"]
        print(f"Found {len(accessions)} SRA accessions for {project_id}")

        # Step 2: Fetch details for these accessions to get run IDs
        # (Simplified: we just need the list of runs for now)
        return [{"accession": acc} for acc in accessions]

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to fetch biomaterial list: {e}", file=sys.stderr)
        return None

def _create_retry_session() -> requests.Session:
    """Creates a requests session with retry logic."""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def download_sra_accessions(accessions: List[Dict[str, Any]], output_dir: Path) -> bool:
    """
    Downloads SRA data using `fasterq-dump` (from SRA Toolkit).
    Note: This assumes `fasterq-dump` is installed and in PATH.
    """
    if not accessions:
        print("WARNING: No accessions to download.", file=sys.stderr)
        return False

    output_dir.mkdir(parents=True, exist_ok=True)
    success_count = 0

    for item in accessions:
        acc = item["accession"]
        print(f"Downloading SRA accession: {acc}...")

        # Construct command for fasterq-dump
        # Output to specific directory with single file per run
        cmd = [
            "fasterq-dump",
            "--split-files",
            "--outdir", str(output_dir),
            "--threads", "4",
            acc
        ]

        try:
            result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            success_count += 1
            print(f"Successfully downloaded {acc}")
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to download {acc}: {e.stderr.decode()}", file=sys.stderr)
        except FileNotFoundError:
            print("ERROR: 'fasterq-dump' not found. Please install SRA Toolkit.", file=sys.stderr)
            return False

    return success_count > 0

def generate_synthetic_fallback(output_dir: Path) -> bool:
    """
    Generates synthetic data by invoking the synthetic data generator script.
    This is ONLY called if USE_SYNTHETIC_DATA=true is set.
    """
    print("Synthetic mode enabled. Generating baseline dataset...")
    synth_script = PROJECT_ROOT / "code" / "00_generate_synthetic_data.py"
    
    if not synth_script.exists():
        print("ERROR: Synthetic data generator script not found.", file=sys.stderr)
        return False

    try:
        # Run the synthetic generator
        subprocess.run([sys.executable, str(synth_script)], check=True)
        print("Synthetic data generation completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Synthetic data generation failed: {e}", file=sys.stderr)
        return False

def _compute_sha256(file_path: Path) -> str:
    """Computes SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def _save_verified_source(artifact_path: Path, source_url: str, package_name: str, access_recipe: str):
    """
    Saves the verification record to state/verified_sources.yaml.
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    artifact_hash = _compute_sha256(artifact_path)
    
    record = {
        "package_name": package_name,
        "access_recipe": access_recipe,
        "artifact_hash": artifact_hash,
        "source_url": source_url,
        "timestamp": datetime.now().isoformat()
    }

    # Simple YAML serialization for the single record
    yaml_content = f"""package_name: "{record['package_name']}"
access_recipe: "{record['access_recipe']}"
artifact_hash: "{record['artifact_hash']}"
source_url: "{record['source_url']}"
"""
    with open(VERIFIED_SOURCES_FILE, "w") as f:
        f.write(yaml_content)
    print(f"Verification record saved to {VERIFIED_SOURCES_FILE}")

def main():
    parser = argparse.ArgumentParser(description="Fetch genomic data from NCBI BioProject.")
    parser.add_argument(
        "--project-id", 
        type=str, 
        default=BIO_PROJECT_ID, 
        help=f"NCBI BioProject ID (default: {BIO_PROJECT_ID})"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(DATA_RAW_DIR),
        help="Directory to store downloaded data"
    )
    
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    
    # 1. Check SSL Verification
    print("Verifying SSL connection to NCBI...")
    if not check_ssl_verification():
        print("ERROR: SSL verification failed. Halting pipeline.")
        sys.exit(1)

    # 2. Check Environment Variable for Synthetic Mode
    use_synthetic = os.getenv("USE_SYNTHETIC_DATA", "").lower() == "true"

    if use_synthetic:
        print("USE_SYNTHETIC_DATA is set. Invoking synthetic generator.")
        if not generate_synthetic_fallback(output_dir):
            sys.exit(1)
        # Do NOT write to verified_sources.yaml in synthetic mode
        print("Synthetic mode completed. Skipping verification state write.")
        return

    # 3. Real Data Fetch Path
    print(f"Attempting to fetch data from NCBI BioProject: {args.project_id}")
    
    # Fetch list of SRA accessions
    accessions = fetch_biomaterial_list(args.project_id)
    if not accessions:
        print(f"ERROR: Could not retrieve accessions for {args.project_id}. Halting.")
        sys.exit(1)

    # Download the data
    if not download_sra_accessions(accessions, output_dir):
        print("ERROR: Data download failed. Halting pipeline.")
        sys.exit(1)

    # Verify at least one file was created
    files = list(output_dir.glob("*.fastq")) + list(output_dir.glob("*.fq"))
    if not files:
        print("ERROR: No FASTQ files found after download. Halting.")
        sys.exit(1)

    # 4. Verify and Save State
    # We verify the first file found as a proxy for the batch, or aggregate if needed.
    # For this task, we record the source and the first artifact hash.
    first_file = files[0]
    _save_verified_source(
        artifact_path=first_file,
        source_url=f"https://www.ncbi.nlm.nih.gov/bioproject/{args.project_id}",
        package_name="NCBI BioProject",
        access_recipe=f"SRA Download via fasterq-dump for {args.project_id}"
    )

    print("Data fetch and verification completed successfully.")

if __name__ == "__main__":
    main()