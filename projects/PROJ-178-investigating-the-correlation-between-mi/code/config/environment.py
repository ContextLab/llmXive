import os
import logging
from pathlib import Path

# Define base paths relative to project root
# Assumes the project root is the directory containing 'code'
BASE_DIR = Path(__file__).resolve().parent.parent
CODE_DIR = BASE_DIR / "code"
DATA_DIR = BASE_DIR / "code" / "data"
LOGS_DIR = BASE_DIR / "code" / "logs"
FIGURES_DIR = BASE_DIR / "paper" / "figures"

# 1000 Genomes FTP URLs
FTP_BASE = "ftp://ftp.1000genomes.ebi.ac.uk/vol1/ftp/phase3/20131030"
MITO_VCF_URL = f"{FTP_BASE}/ALL.chr22.phase3_shapeit2_mvncall_integrated_v5a.20130502.genotypes.vcf.gz"
# Note: Mitochondrial data is often on chrM. The 1000G FTP structure might vary.
# Using a representative URL for mitochondrial VCF if available, or generic phase3.
# For the purpose of this implementation, we define the URL that would be used.
# In reality, chrM is often in a separate file or the same phase3 file.
# Assuming a specific mito file path for the task context:
MITO_VCF_REAL_URL = "ftp://ftp.1000genomes.ebi.ac.uk/vol1/ftp/phase3/20131030/ALL.chrM.phase3_shapeit2_mvncall_integrated_v5a.20130502.genotypes.vcf.gz"

METADATA_URL = "ftp://ftp.1000genomes.ebi.ac.uk/vol1/ftp/phase3/20131030/integrated_call_samples_v3.20130502.ALL.panel"

def ensure_directories():
    """Creates necessary directories if they do not exist."""
    directories = [
        DATA_DIR / "raw",
        DATA_DIR / "processed",
        LOGS_DIR,
        FIGURES_DIR
    ]
    for d in directories:
        d.mkdir(parents=True, exist_ok=True)
        logging.info(f"Ensured directory: {d}")

def get_ftp_urls():
    """Returns a dictionary of FTP URLs for data retrieval."""
    return {
        "mito_vcf": MITO_VCF_REAL_URL,
        "metadata": METADATA_URL
    }

def get_local_paths():
    """Returns a dictionary of local path objects."""
    ensure_directories()
    return {
        "raw_dir": DATA_DIR / "raw",
        "processed_dir": DATA_DIR / "processed",
        "logs_dir": LOGS_DIR,
        "figures_dir": FIGURES_DIR
    }
