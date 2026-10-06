import os
import subprocess
import sys
import time
from pathlib import Path
import shutil
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Target datasets as per FR-001 (corrected GSE IDs)
TARGET_GSE_IDS = [
    "GSE136103",
    "GSE127465",
    "GSE111075",
    "GSE138852"
]

def check_sra_toolkit() -> bool:
    """
    Verify that SRA Toolkit is installed and accessible.
    Checks for 'prefetch' and 'fasterq-dump' commands.
    """
    try:
        # Check prefetch
        result = subprocess.run(
            ["prefetch", "--help"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10
        )
        if result.returncode != 0:
            logger.error("prefetch command returned non-zero exit code.")
            return False

        # Check fasterq-dump
        result = subprocess.run(
            ["fasterq-dump", "--help"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10
        )
        if result.returncode != 0:
            logger.error("fasterq-dump command returned non-zero exit code.")
            return False

        logger.info("SRA Toolkit verification successful.")
        return True
    except FileNotFoundError:
        logger.error("SRA Toolkit commands (prefetch, fasterq-dump) not found in PATH.")
        return False
    except subprocess.TimeoutExpired:
        logger.error("SRA Toolkit command timed out during verification.")
        return False

def get_sra_ids_for_gse(gse_id: str) -> list:
    """
    Fetch SRA accession IDs associated with a GSE accession using eutils.
    Returns a list of SRA IDs (e.g., SRRxxxxxx).
    """
    logger.info(f"Fetching SRA IDs for GSE: {gse_id}")
    
    # Use esearch and efetch to map GSE to SRA
    # Command: esearch -db gds -query <GSE> | efetch -format docsum | xtract -pattern DocumentSummary -element SRA
    # Note: GSE maps to GEO (gds/gene), but SRA runs are often linked via BioProject or direct GSE->SRA mapping in some contexts.
    # A more robust approach for GSE -> SRR:
    # 1. esearch -db sra -query <GSE>[accession]
    # This often works if the GSE is directly linked in SRA metadata.
    
    cmd = [
        "esearch", "-db", "sra", "-query", f"{gse_id}[accession]"
    ]
    
    try:
        search_proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=60
        )
        
        if not search_proc.stdout.strip():
            logger.warning(f"No direct SRA accession found for GSE {gse_id} via direct query. Trying alternative method.")
            # Alternative: Try fetching from BioProject if direct fails, but for simplicity in this script,
            # we assume the direct query or the GSE is known to map to SRRs via the GSE metadata.
            # If esearch returns nothing, we might need to parse the GSE summary.
            # However, standard practice for 'download_data' in this context often assumes
            # the user provides the SRR list or the GSE maps directly.
            # Let's try a more specific query: GSE136103[SRA]
            cmd = [
                "esearch", "-db", "sra", "-query", f"{gse_id}[SRA]"
            ]
            search_proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=60
            )

        if not search_proc.stdout.strip():
            logger.error(f"Could not retrieve any SRA IDs for {gse_id}.")
            return []

        # Parse the XML output to get IDs
        # The output is XML containing <Id> tags
        import xml.etree.ElementTree as ET
        try:
            root = ET.fromstring(search_proc.stdout)
            ids = [elem.text for elem in root.findall('.//Id')]
            if not ids:
                logger.warning(f"Found no <Id> elements in XML for {gse_id}.")
                return []
            logger.info(f"Found {len(ids)} SRA IDs for {gse_id}: {ids[:5]}...")
            return ids
        except ET.ParseError:
            logger.error("Failed to parse XML response from eutils.")
            return []

    except subprocess.CalledProcessError as e:
        logger.error(f"Error searching SRA for {gse_id}: {e}")
        return []
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout searching SRA for {gse_id}.")
        return []

def download_sra(sra_id: str, output_dir: Path) -> bool:
    """
    Download and convert SRA data to FASTQ using fasterq-dump.
    Returns True on success, False on failure.
    """
    logger.info(f"Starting download for {sra_id}...")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Define output paths
    # fasterq-dump outputs .fastq files. We will name them <SRA_ID>.fastq
    # If multiple files (paired), it might output _1.fastq and _2.fastq
    fastq_path = output_dir / f"{sra_id}.fastq"
    
    cmd = [
        "fasterq-dump",
        "--outdir", str(output_dir),
        "--split-files", # Handles paired end if present
        "--skip-technical",
        "--read-filter", "pass",
        sra_id
    ]
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=7200 # 2 hours timeout per dataset
        )
        
        # Check if files were created
        files = list(output_dir.glob(f"{sra_id}*.fastq*"))
        if not files:
            logger.error(f"fasterq-dump finished but no files found for {sra_id}.")
            return False
        
        logger.info(f"Successfully downloaded {sra_id}. Files: {[f.name for f in files]}")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Download failed for {sra_id}: {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        logger.error(f"Download timed out for {sra_id}.")
        return False

def main():
    """
    Main entry point to download raw count matrices (FASTQ) for specified GSE datasets.
    """
    # 1. Check prerequisites
    if not check_sra_toolkit():
        logger.critical("SRA Toolkit is not properly installed or configured. Aborting.")
        sys.exit(1)

    # 2. Setup output directory
    project_root = Path(__file__).resolve().parent.parent
    raw_data_dir = project_root / "data" / "raw"
    raw_data_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Output directory set to: {raw_data_dir}")

    # 3. Process each GSE
    status_log = []
    
    for gse in TARGET_GSE_IDS:
        logger.info(f"Processing GSE: {gse}")
        
        # Fetch SRA IDs
        sra_ids = get_sra_ids_for_gse(gse)
        
        if not sra_ids:
            logger.warning(f"No SRA IDs found for {gse}. Skipping.")
            status_log.append({"gse": gse, "status": "skipped", "reason": "No SRA IDs found"})
            continue
        
        success_count = 0
        for sra_id in sra_ids:
            if download_sra(sra_id, raw_data_dir):
                success_count += 1
            else:
                logger.error(f"Failed to download {sra_id}.")
        
        if success_count > 0:
            status_log.append({"gse": gse, "status": "success", "files_downloaded": success_count})
        else:
            status_log.append({"gse": gse, "status": "failed", "reason": "No files downloaded"})

    # 4. Write status log
    status_file = raw_data_dir / "download_status.json"
    with open(status_file, "w") as f:
        json.dump(status_log, f, indent=2)
    
    logger.info(f"Download process complete. Status written to {status_file}")

if __name__ == "__main__":
    main()
