"""
Download FASTA sequences from NCBI for specified BioProjects.

This script fetches genome assemblies for E. coli isolates using NCBI E-utilities.
It enforces the MAX_ISOLATES limit defined in the project configuration.
"""
import os
import sys
import logging
import time
import json
from pathlib import Path
from typing import List, Optional, Dict, Any

import requests
import pandas as pd

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from utils.logging import get_logger
from utils.config import get_max_isolates, get_bio_project_ids, get_paths

# NCBI E-utilities base URL
EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
REQUESTS_DELAY = 0.34  # NCBI recommends no more than 3 requests per second

logger = get_logger(__name__)


def fetch_assembly_summaries(
    bio_project_id: str, max_results: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Fetch assembly summaries for a given BioProject.

    Args:
        bio_project_id: The BioProject accession number (e.g., 'PRJNA123456').
        max_results: Maximum number of results to fetch.

    Returns:
        List of assembly summary dictionaries.
    """
    search_url = f"{EUTILS_BASE}/esearch.fcgi"
    params = {
        "db": "assembly",
        "term": f"{bio_project_id}[BioProject] AND bacteria[Organism] AND latest[Filter] AND refseq[Filter]",
        "retmax": max_results if max_results else 10000,
        "usehistory": "y",
        "retmode": "json",
    }

    try:
        response = requests.get(search_url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        if "esearchresult" not in data or "idlist" not in data["esearchresult"]:
            logger.warning(f"No assemblies found for BioProject {bio_project_id}")
            return []

        assembly_ids = data["esearchresult"]["idlist"]
        logger.info(f"Found {len(assembly_ids)} assemblies for BioProject {bio_project_id}")

        if not assembly_ids:
            return []

        # Fetch summaries for these IDs
        summary_url = f"{EUTILS_BASE}/esummary.fcgi"
        summary_params = {
            "db": "assembly",
            "id": ",".join(assembly_ids),
            "retmode": "json",
        }

        # NCBI limits batch size, chunk if necessary
        chunk_size = 200
        all_summaries = []

        for i in range(0, len(assembly_ids), chunk_size):
            chunk_ids = assembly_ids[i : i + chunk_size]
            summary_params["id"] = ",".join(chunk_ids)

            time.sleep(REQUESTS_DELAY)
            resp = requests.get(summary_url, params=summary_params, timeout=60)
            resp.raise_for_status()
            resp_data = resp.json()

            if "result" in resp_data:
                # resp_data['result'] keys are assembly UIDs, values are summary dicts
                summaries = resp_data["result"]
                # Skip 'uidlist' if present
                for uid in summaries:
                    if uid != "uidlist":
                        all_summaries.append(summaries[uid])

        return all_summaries

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch assembly summaries for {bio_project_id}: {e}")
        return []


def select_fasta_url(assembly_summary: Dict[str, Any]) -> Optional[str]:
    """
    Extract the FASTA URL (genomic DNA) from an assembly summary.

    Prioritizes 'Genomic DNA' or 'Assembly' level sequences.
    """
    ftp_path = assembly_summary.get("FtpPath_GenBank")
    if not ftp_path:
        return None

    # Construct URL to the assembly report to find the FASTA file
    # Alternatively, use the 'Genomic DNA' link directly if available in summary
    # The summary often contains 'ftppath' variants. Let's try to find the specific fasta.
    # Standard structure: .../genbank/.../GCA_.../..._genomic.fna.gz
    
    # A more robust way using the FTP path from the summary:
    # The summary usually has 'FtpPath_GenBank'. We need to find the specific .fna.gz file.
    # However, for simplicity and speed, we can construct the likely path or fetch the assembly report.
    
    # Let's try to fetch the assembly report to get the exact filename
    # But to avoid extra HTTP calls, we can try to construct the URL based on common patterns
    # or use the 'ftppath' if it points to the directory.
    
    # Actually, the summary often contains 'Genome' -> 'Assembly' -> 'Genomic DNA' link?
    # No, usually we need to parse the FTP path.
    
    # Let's use a helper to fetch the assembly report text file to get the FASTA name.
    # This is safer than guessing.
    
    # Base FTP path
    base_ftp = ftp_path
    if not base_ftp.startswith("ftp"):
        return None
    
    # Convert to HTTP for requests
    http_ftp = base_ftp.replace("ftp://", "https://")
    
    # The assembly report is usually named <AssemblyAccession>_assembly_report.txt
    # We need the AssemblyAccession.
    asm_accession = assembly_summary.get("AssemblyAccession")
    if not asm_accession:
        return None
        
    report_url = f"{http_ftp}/{asm_accession}_assembly_report.txt"
    
    try:
        time.sleep(REQUESTS_DELAY)
        resp = requests.get(report_url, timeout=30)
        if resp.status_code != 200:
            logger.debug(f"Could not fetch report for {asm_accession}: {resp.status_code}")
            return None
        
        # Parse report to find the genomic.fna.gz line
        # Lines look like: ... genomic.fna.gz ...
        for line in resp.text.splitlines():
            if "genomic.fna.gz" in line:
                parts = line.split()
                if len(parts) >= 7:
                    # The last column is the relative path
                    fasta_rel_path = parts[-1]
                    return f"{http_ftp}/{fasta_rel_path}"
        
        return None
    except Exception as e:
        logger.debug(f"Error fetching report for {asm_accession}: {e}")
        return None


def download_fasta(
    url: str, output_path: Path, timeout: int = 300
) -> bool:
    """
    Download a FASTA file from a URL.
    """
    try:
        logger.info(f"Downloading from {url}")
        time.sleep(REQUESTS_DELAY)
        with requests.get(url, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            with open(output_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return True
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False


def main():
    """
    Main entry point for downloading sequences.
    """
    logger.info("Starting NCBI download process")
    
    paths = get_paths()
    raw_data_dir = paths.get("raw_data_dir", Path("data/raw"))
    os.makedirs(raw_data_dir, exist_ok=True)
    
    bio_project_ids = get_bio_project_ids()
    max_isolates = get_max_isolates()
    
    if not bio_project_ids:
        logger.error("No BioProject IDs found in configuration. Please update config.yaml.")
        sys.exit(1)
    
    all_fasta_files = []
    isolates_downloaded = 0
    
    for project_id in bio_project_ids:
        if isolates_downloaded >= max_isolates:
            logger.info(f"Reached MAX_ISOLATES limit ({max_isolates}). Stopping download.")
            break
        
        logger.info(f"Processing BioProject: {project_id}")
        summaries = fetch_assembly_summaries(project_id, max_results=max_isolates - isolates_downloaded)
        
        if not summaries:
            logger.warning(f"No assemblies found for {project_id}")
            continue
        
        for summary in summaries:
            if isolates_downloaded >= max_isolates:
                break
            
            asm_accession = summary.get("AssemblyAccession")
            organism = summary.get("OrganismName", "Unknown")
            isolate_id = summary.get("BioSampleAccession") or asm_accession
            
            if not asm_accession:
                continue
            
            fasta_url = select_fasta_url(summary)
            if not fasta_url:
                logger.warning(f"No FASTA URL found for {asm_accession}")
                continue
            
            # Ensure unique filename
            safe_name = asm_accession.replace(".", "_")
            output_file = raw_data_dir / f"{safe_name}_genomic.fna.gz"
            
            if output_file.exists():
                logger.debug(f"File already exists: {output_file}")
                isolates_downloaded += 1
                all_fasta_files.append(str(output_file))
                continue
            
            if download_fasta(fasta_url, output_file):
                logger.info(f"Downloaded {asm_accession} -> {output_file}")
                isolates_downloaded += 1
                all_fasta_files.append(str(output_file))
            else:
                logger.warning(f"Failed to download {asm_accession}")
    
    # Write a manifest of downloaded files
    manifest_path = raw_data_dir / "download_manifest.json"
    manifest_data = {
        "total_downloaded": isolates_downloaded,
        "max_isolates_limit": max_isolates,
        "bio_projects": bio_project_ids,
        "files": all_fasta_files
    }
    
    with open(manifest_path, "w") as f:
        json.dump(manifest_data, f, indent=2)
    
    logger.info(f"Download complete. {isolates_downloaded} isolates saved to {raw_data_dir}")
    logger.info(f"Manifest written to {manifest_path}")


if __name__ == "__main__":
    # Initialize logging for this script
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    init_logger = get_logger("download_ncbi")
    # Setup file logging if not already done globally
    # Assuming init_pipeline_logging is called elsewhere or we do it here
    # For standalone run:
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "download_ncbi.log"),
            logging.StreamHandler()
        ]
    )
    
    main()
