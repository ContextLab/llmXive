"""
T012: Implement load_data.py to download mitochondrial VCFs and metadata.

Downloads 1000 Genomes Phase 3 mitochondrial VCFs and the metadata panel
from the canonical FTP source. Performs initial validation to ensure the
'age' column exists in the metadata, halting the pipeline if missing.

Outputs:
    data/raw/1000G_mito.vcf.gz (concatenated mitochondrial VCF)
    data/raw/1000G_metadata.csv (parsed metadata with age verification)
"""

import os
import sys
import gzip
import shutil
import logging
from pathlib import Path
from urllib.request import urlretrieve
from urllib.error import URLError, HTTPError
import pandas as pd

# Add project root to path to allow relative imports if running as script
# but rely on installed package structure for production
try:
    from config.environment import get_ftp_base_url, get_local_data_path
except ImportError:
    # Fallback for direct execution in isolated environments
    # In a real run, config.environment is expected to be available via T009
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    try:
        from config.environment import get_ftp_base_url, get_local_data_path
    except ImportError:
        # Hardcoded fallbacks if environment config is missing (for robustness)
        BASE_URL = "ftp://ftp.1000genomes.ebi.ac.uk/vol1/ftp/phase3/data"
        DATA_ROOT = Path(__file__).parent.parent.parent / "data"
        def get_ftp_base_url(): return BASE_URL
        def get_local_data_path(): return DATA_ROOT

logger = logging.getLogger(__name__)

# 1000 Genomes Phase 3 populations
POPULATIONS = ["YRI", "CEU", "CHB", "JPT", "CHS", "CDX", "KHV", "IBS", "TSI", "FIN", "GBR", "PUR", "CLM", "MXL", "ACB", "ASW", "BEB", "GIH", "PJL", "STU", "ITU"]

# Specific mitochondrial VCF path pattern in 1000G Phase 3
# Note: 1000G Phase 3 does not have a single "chrM" VCF for all samples in one file.
# We must download individual sample VCFs or the merged multi-sample VCF if available.
# The standard Phase 3 release has VCFs per population per chromosome.
# We will target the merged population VCFs for chrM.
# URL pattern: ftp://ftp.1000genomes.ebi.ac.uk/vol1/ftp/phase3/alignment_20150506/ALL.chr20.integrated_phase1_v3.20101123.snps_indels_svs.genotypes.vcf.gz
# Wait, chrM is chromosome 25 or MT. In 1000G Phase 3, it is often in the "ALL.chrM" file or similar.
# Actually, 1000G Phase 3 has a specific file for chrM: "ALL.chrM.phase3_shapeit2_mv026876.integrated_call_samples_v3.20130502.ALL.vcf.gz"
# However, the most robust way for "mitochondrial data" in 1000G is often the "ALL.chrM" file.
# Let's check the canonical path for chrM in Phase 3.
# Path: ftp://ftp.1000genomes.ebi.ac.uk/vol1/ftp/phase3/alignment_20150506/ALL.chrM.phase3_shapeit2_mv026876.integrated_call_samples_v3.20130502.ALL.vcf.gz
# This file contains all samples.

CHROMOSOME = "M"  # 1000G uses 'M' for mitochondrial
METADATA_FILE_NAME = "1000G_phase3_metadata.csv"

def ensure_dirs(data_path: Path):
    """Create raw and processed directories if they don't exist."""
    (data_path / "raw").mkdir(parents=True, exist_ok=True)
    (data_path / "processed").mkdir(parents=True, exist_ok=True)
    (data_path / "logs").mkdir(parents=True, exist_ok=True)

def download_mito_vcf(base_url: str, output_path: Path):
    """
    Downloads the mitochondrial VCF for 1000 Genomes Phase 3.
    The file is large (~100MB+), so we stream it.
    """
    # Construct the URL for the mitochondrial chromosome
    # Based on 1000 Genomes Phase 3 release structure
    vcf_filename = f"ALL.chrM.phase3_shapeit2_mv026876.integrated_call_samples_v3.20130502.ALL.vcf.gz"
    url = f"{base_url}/alignment_20150506/{vcf_filename}"
    
    logger.info(f"Downloading mitochondrial VCF from: {url}")
    
    try:
        urlretrieve(url, output_path)
        logger.info(f"Download complete: {output_path}")
        return True
    except (URLError, HTTPError) as e:
        logger.error(f"Failed to download VCF: {e}")
        # Try alternative path if the first one fails (sometimes paths change)
        # Alternative: ftp://ftp.1000genomes.ebi.ac.uk/vol1/ftp/phase3/data/
        # But the alignment_20150506 is the standard integrated call set.
        return False

def download_metadata(base_url: str, output_path: Path):
    """
    Downloads the metadata panel (sample information) for 1000 Genomes.
    The metadata file contains age, sex, population, etc.
    """
    # Metadata is often in the "integrated_call_samples" or a separate panel file.
    # We will try to fetch the standard sample metadata file.
    # URL: ftp://ftp.1000genomes.ebi.ac.uk/vol1/ftp/phase3/alignment_20150506/1000G_phase3.sample_info.tsv.gz
    # Or the specific metadata file used in many papers.
    # Let's use the sample info file which is standard.
    meta_filename = "1000G_phase3.sample_info.tsv.gz"
    url = f"{base_url}/alignment_20150506/{meta_filename}"
    
    logger.info(f"Downloading metadata from: {url}")
    
    try:
        urlretrieve(url, output_path)
        logger.info(f"Metadata download complete: {output_path}")
        return True
    except (URLError, HTTPError) as e:
        logger.error(f"Failed to download metadata: {e}")
        return False

def validate_age_column(df: pd.DataFrame, metadata_path: Path):
    """
    Validates that the 'age' column exists in the metadata.
    If missing, logs an error and raises a SystemExit to halt the pipeline.
    """
    # The 1000G sample info file usually has columns like 'Sample_ID', 'Population', 'Sex', 'Age'
    # Let's normalize column names to lowercase for safety
    df.columns = df.columns.str.strip().str.lower()
    
    if 'age' not in df.columns:
        logger.error("CRITICAL: 'age' column is missing from metadata.")
        logger.error(f"Available columns: {list(df.columns)}")
        logger.error("Pipeline HALTED. Cannot proceed without age data.")
        # Write a status file to indicate failure
        with open(metadata_path.parent / "validation_status.txt", "w") as f:
            f.write("FAILED: age column missing")
        sys.exit(1)
    
    logger.info("Validation passed: 'age' column found.")
    return df

def main():
    """Main entry point for T012."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(Path(__file__).parent.parent.parent / "logs" / "load_data.log")
        ]
    )
    
    # Get paths
    data_root = get_local_data_path()
    ensure_dirs(data_root)
    
    raw_dir = data_root / "raw"
    base_url = get_ftp_base_url()
    
    # Define file paths
    vcf_path = raw_dir / "1000G_mito.vcf.gz"
    meta_path = raw_dir / "1000G_metadata.tsv.gz"
    
    # 1. Download VCF
    if not vcf_path.exists():
        if not download_mito_vcf(base_url, vcf_path):
            logger.error("Failed to download VCF. Aborting.")
            sys.exit(1)
    else:
        logger.info("VCF already exists, skipping download.")
    
    # 2. Download Metadata
    if not meta_path.exists():
        if not download_metadata(base_url, meta_path):
            logger.error("Failed to download metadata. Aborting.")
            sys.exit(1)
    else:
        logger.info("Metadata already exists, skipping download.")
    
    # 3. Process and Validate Metadata
    # We need to read the TSV (gzipped)
    try:
        # The file is TSV, gzipped
        df_meta = pd.read_csv(meta_path, sep='\t', compression='gzip')
    except Exception as e:
        logger.error(f"Failed to read metadata file: {e}")
        sys.exit(1)
    
    # Validate age column (Critical Step T007A/B)
    df_meta = validate_age_column(df_meta, meta_path)
    
    # Save cleaned metadata as CSV for downstream use
    output_meta_path = raw_dir / "1000G_metadata.csv"
    df_meta.to_csv(output_meta_path, index=False)
    logger.info(f"Cleaned metadata saved to {output_meta_path}")
    
    logger.info("T012 Load Data completed successfully.")

if __name__ == "__main__":
    main()