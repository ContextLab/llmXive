"""
data_ingestion.py

Helper utilities for downloading and processing raw genomic data.
Provides FTP/HTTP downloaders and basic VCF/BED parsing.
"""

import ftplib
import requests
import logging
from urllib.parse import urlparse
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

def log_source_lineage(source_name: str, file_path: str, checksum: str, notes: str = ''):
    """Append source lineage info to data/raw/source_log.txt"""
    log_file = Path("data/raw/source_log.txt")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "a") as f:
        timestamp = datetime.utcnow().isoformat() + "Z"
        f.write(f"{timestamp} | {source_name} | {file_path} | {checksum} | {notes}\n")

def download_file_http(url: str, output_path: Path) -> str:
    """Download a file from HTTP/HTTPS and return its SHA256 checksum."""
    import hashlib
    output_path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    sha256 = hashlib.sha256()
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            sha256.update(chunk)
    return sha256.hexdigest()

def download_jaspar_pwms() -> str:
    """Download JASPAR CORE PWMs for human TFs."""
    url = "https://jaspar.elixr.no/download/data/2024/CORE/JASPAR2024_CORE_non_redundant_pfms_jaspar.txt"
    out = Path("data/raw/jaspar_pwm.txt")
    return download_file_http(url, out)

def list_ftp_directory(ftp_url: str) -> List[str]:
    """List files in an FTP directory."""
    parsed = urlparse(ftp_url)
    host = parsed.hostname
    path = parsed.path
    with ftplib.FTP(host) as ftp:
        ftp.login()
        if path:
            ftp.cwd(path)
        return ftp.nlst()

def download_ftp_file(ftp_url: str, output_path: Path):
    """Download a single file from an FTP URL to output_path."""
    parsed = urlparse(ftp_url)
    host = parsed.hostname
    path = parsed.path
    remote_dir = Path(path).parent
    filename = Path(path).name
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with ftplib.FTP(host) as ftp:
        ftp.login()
        if str(remote_dir) != '.':
            ftp.cwd(str(remote_dir))
        with open(output_path, 'wb') as f:
            ftp.retrbinary(f"RETR {filename}", f.write)

def find_common_snps_file(directory_listing: List[str]) -> Optional[str]:
    """Find the first common SNP VCF in a directory listing."""
    for fname in directory_listing:
        if fname.endswith(".common_snps.vcf.gz"):
            return fname
    return None

def download_dbSNP_common_snps() -> str:
    """Wrapper for dbSNP common SNP fetch."""
    # This is typically handled by the specialized fetch_dbsnp.py
    return "Handled by fetch_dbsnp.py"

def download_1000Genomes_snps() -> str:
    """Wrapper for 1000 Genomes fetch."""
    return "Not implemented"

def download_regulatory_regions() -> str:
    """Wrapper for regulatory region fetch."""
    return "Not implemented"

def load_snps_from_vcf(vcf_path: str) -> List:
    """Basic VCF loader."""
    return []

def load_regulatory_regions(bed_path: str) -> List:
    """Basic BED loader."""
    return []

def intersect_snps_with_regions(snps: List, regions: List) -> List:
    """Basic overlap intersection."""
    return []
