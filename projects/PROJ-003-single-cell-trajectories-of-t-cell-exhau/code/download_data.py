import os
import subprocess
import sys
import hashlib
import logging
import yaml
from pathlib import Path
from typing import List, Dict, Any
from Bio import Entrez

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set Entrez email (required by NCBI)
Entrez.email = "researcher@llmxive.org"

TARGET_GSE_IDS = [
    "GSE136103",
    "GSE127465",
    "GSE111075",
    "GSE138852"
]

def check_sra_toolkit() -> bool:
    """Verify that SRA Toolkit is installed and accessible."""
    try:
        subprocess.run(["prefetch", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        subprocess.run(["fasterq-dump", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("SRA Toolkit (prefetch/fasterq-dump) not found in PATH.")
        return False

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_state(dataset_id: str, metadata: Dict[str, Any]):
    """Update the project state YAML with dataset metadata."""
    state_path = Path("data/state.yaml")
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    state = {}
    if state_path.exists():
        with open(state_path, "r") as f:
            state = yaml.safe_load(f) or {}
    
    if "datasets" not in state:
        state["datasets"] = {}
    
    state["datasets"][dataset_id] = metadata
    
    with open(state_path, "w") as f:
        yaml.dump(state, f, default_flow_style=False)

def get_sra_ids_for_gse(gse_id: str) -> List[str]:
    """Fetch SRA accession IDs associated with a GSE accession using Biopython Entrez."""
    logger.info(f"Fetching SRA IDs for {gse_id}...")
    try:
        handle = Entrez.esearch(db="sra", term=f"{gse_id}[accession]")
        record = Entrez.read(handle)
        handle.close()
        return record.get("IdList", [])
    except Exception as e:
        logger.error(f"Error fetching SRA IDs for {gse_id}: {e}")
        return []

def download_sra_sample(sra_id: str, output_dir: Path) -> bool:
    """Download a sample of SRA data to FASTQ using fasterq-dump."""
    logger.info(f"Downloading sample for {sra_id}...")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Using --max-reads to ensure the script completes within CI limits 
    # while still obtaining real data from the real source.
    cmd = [
        "fasterq-dump",
        "--outdir", str(output_dir),
        "--split-files",
        "--max-reads", "10000", 
        sra_id
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"SRA download failed for {sra_id}: {e.stderr}")
        return False

def download_geo_counts(gse_id: str, output_dir: Path) -> Path:
    """Download processed count matrices from GEO via FTP/HTTP."""
    logger.info(f"Fetching processed counts for {gse_id}...")
    counts_dir = output_dir / "counts"
    counts_dir.mkdir(parents=True, exist_ok=True)
    
    # In a real scenario, we would parse the GEO record to find the exact supplementary file URL.
    # For this implementation, we simulate the fetch of the primary count matrix.
    # Note: We use a real GEO FTP pattern.
    import requests
    
    # Simplified: try to find the most common count matrix pattern for these GSEs
    # In production, this would be a loop over the 'ftp' field in the GEO record.
    # For the sake of this task, we target the known supplementary file locations.
    # Since we cannot reliably guess the exact filename without full API parsing,
    # we'll use the Biopython approach to get the FTP link.
    
    try:
        handle = Entrez.efetch(db="gds", id=gse_id, rettype="full", retmode="text")
        content = handle.read()
        handle.close()
        
        # Search for FTP links to supplementary files (usually .txt.gz or .csv.gz)
        import re
        links = re.findall(r'ftp://ftp\.ncbi\.nlm\.nih\.gov/geo/samples/.*?\.gz', content)
        if not links:
            # Fallback to the general GSE supplementary folder
            links = [f"https://ftp.ncbi.nlm.nih.gov/geo/series/{gse_id[0:3]}/{gse_id}/{gse_id}_RAW.tar"]
        
        target_url = links[0]
        target_file = counts_dir / os.path.basename(target_url)
        
        response = requests.get(target_url, stream=True, timeout=60)
        response.raise_for_status()
        with open(target_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return target_file
    except Exception as e:
        logger.error(f"Failed to download GEO counts for {gse_id}: {e}")
        return None

def main():
    if not check_sra_toolkit():
        logger.critical("SRA Toolkit not found. Aborting.")
        sys.exit(1)

    project_root = Path(__file__).resolve().parent.parent
    raw_data_dir = project_root / "data" / "raw"
    raw_data_dir.mkdir(parents=True, exist_ok=True)

    for gse in TARGET_GSE_IDS:
        logger.info(f"Processing {gse}...")
        gse_dir = raw_data_dir / gse
        
        # 1. Download processed counts (required for SC-005 verification)
        counts_file = download_geo_counts(gse, gse_dir)
        if not counts_file:
            logger.warning(f"Could not fetch counts for {gse}. Skipping.")
            continue
        
        counts_checksum = calculate_sha256(counts_file)
        
        # 2. Download SRA sample (required by T002 tool specification)
        sra_ids = get_sra_ids_for_gse(gse)
        if sra_ids:
            sra_dir = gse_dir / "raw_reads"
            if download_sra_sample(sra_ids[0], sra_dir):
                # Checksum the first resulting fastq
                fastq_files = list(sra_dir.glob("*.fastq"))
                sra_checksum = calculate_sha256(fastq_files[0]) if fastq_files else "N/A"
            else:
                sra_checksum = "failed"
        else:
                sra_checksum = "no_ids"

        # 3. Update State
        update_state(gse, {
            "source": "GEO/SRA",
            "raw_counts_path": str(counts_file.relative_to(project_root)),
            "sra_sample_checksum": sra_checksum,
            "counts_checksum": counts_checksum,
            "status": "available",
            "cell_count": 0, # To be populated by T003
            "gene_count": 0  # To be populated by T003
        })
        
    logger.info("Data download complete. State updated in data/state.yaml")

if __name__ == "__main__":
    main()
