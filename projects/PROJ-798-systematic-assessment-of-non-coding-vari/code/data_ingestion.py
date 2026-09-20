import json
import os
import hashlib
import logging
import gzip
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any

# Attempt to import pybedtools. If missing, the script will fail loudly as per constraints.
try:
    import pybedtools
except ImportError:
    raise ImportError("pybedtools is required for T013 overlap logic. Install via requirements.txt.")

from config import ensure_data_dirs
from utils import SNP, GenomicRegion, parse_vcf_line, parse_bed_line

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
DERIVED_DIR = DATA_DIR / "derived"
SOURCE_LOG_PATH = RAW_DIR / "source_log.txt"
SNPS_RAW_VCF_PATH = RAW_DIR / "snps_raw.vcf"
REGULATORY_REGIONS_BED_PATH = RAW_DIR / "regulatory_regions.bed"
FILTERED_SNPS_PARQUET_PATH = DERIVED_DIR / "filtered_snps.parquet"

def log_source_lineage(source_name: str, details: str) -> None:
    """Appends a log entry to the source log file."""
    ensure_data_dirs()
    with open(SOURCE_LOG_PATH, "a") as f:
        f.write(f"{source_name}: {details}\n")
    logger.info(f"Logged source lineage: {source_name}")

def download_file_http(url: str, output_path: Path) -> None:
    """Downloads a file from HTTP/FTP and saves it."""
    import urllib.request
    import ssl
    
    # Create SSL context that doesn't verify certificates for older servers if needed,
    # but standard urllib usually handles modern ones.
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    except Exception:
        context = None

    logger.info(f"Downloading {url} to {output_path}")
    if context:
        urllib.request.urlretrieve(url, output_path, context=context)
    else:
        urllib.request.urlretrieve(url, output_path)
    
    # Handle .gz if necessary, but we assume the download is raw or gzipped as per source
    logger.info(f"Download complete: {output_path}")

def parse_jaspar_pfm(pfm_content: str) -> Dict[str, Any]:
    """Parses a JASPAR PFM format string into a dictionary."""
    # Placeholder for T010b logic if needed later, not used in T013
    return {}

def convert_jaspar_to_text_format(pfm_dict: Dict[str, Any]) -> str:
    """Converts JASPAR PFM to text format."""
    # Placeholder
    return ""

def download_jaspar_pwms() -> Path:
    """Downloads JASPAR PWMs."""
    # Placeholder for T010b
    return RAW_DIR / "jaspar_pwm.txt"

def load_snps_from_vcf(vcf_path: Path) -> List[SNP]:
    """
    Loads SNPs from a VCF file (potentially gzipped).
    Returns a list of SNP objects.
    """
    snps = []
    logger.info(f"Loading SNPs from {vcf_path}")
    
    if not vcf_path.exists():
        raise FileNotFoundError(f"VCF file not found: {vcf_path}")

    # Handle .gz
    open_func = gzip.open if str(vcf_path).endswith('.gz') else open
    mode = 'rt' if str(vcf_path).endswith('.gz') else 'r'

    with open_func(vcf_path, mode) as f:
        for line_num, line in enumerate(f):
            if line.startswith('#'):
                continue
            
            try:
                snp = parse_vcf_line(line)
                if snp:
                    snps.append(snp)
            except Exception as e:
                logger.warning(f"Skipping malformed VCF line {line_num}: {e}")
    
    logger.info(f"Loaded {len(snps)} SNPs from {vcf_path}")
    return snps

def load_regulatory_regions(bed_path: Path) -> List[GenomicRegion]:
    """
    Loads regulatory regions from a BED file (potentially gzipped).
    Returns a list of GenomicRegion objects.
    """
    regions = []
    logger.info(f"Loading regulatory regions from {bed_path}")

    if not bed_path.exists():
        raise FileNotFoundError(f"BED file not found: {bed_path}")

    open_func = gzip.open if str(bed_path).endswith('.gz') else open
    mode = 'rt' if str(bed_path).endswith('.gz') else 'r'

    with open_func(bed_path, mode) as f:
        for line_num, line in enumerate(f):
            if line.startswith('#') or not line.strip():
                continue
            
            try:
                region = parse_bed_line(line)
                if region:
                    regions.append(region)
            except Exception as e:
                logger.warning(f"Skipping malformed BED line {line_num}: {e}")

    logger.info(f"Loaded {len(regions)} regulatory regions from {bed_path}")
    return regions

def intersect_snps_with_regions(snps: List[SNP], regions: List[GenomicRegion], min_overlap: int = 1) -> List[SNP]:
    """
    Intersects SNPs with regulatory regions using pybedtools.
    Returns a list of SNPs that overlap at least one region by >= min_overlap bp.
    """
    if not snps:
        logger.warning("No SNPs provided for intersection.")
        return []
    
    if not regions:
        logger.warning("No regulatory regions provided for intersection.")
        return []

    # Create temporary BED files for pybedtools
    # SNPs BED format: chrom, start (0-based), end (1-based for 1bp SNP), name, score, strand
    # VCF is 1-based. BED is 0-based.
    # SNP at pos P: start = P-1, end = P
    
    snp_bed_content = []
    for snp in snps:
        # Convert 1-based VCF pos to 0-based BED start
        start = snp.pos - 1
        end = snp.pos # 1bp length
        strand = snp.strand if snp.strand else "."
        # Name: snp_id or chr:pos
        name = snp.id if snp.id else f"{snp.chrom}:{snp.pos}"
        score = 0
        snp_bed_content.append(f"{snp.chrom}\t{start}\t{end}\t{name}\t{score}\t{strand}")

    # Regions BED format: chrom, start, end, name, score, strand
    # Assuming regions are already 0-based if they came from a standard BED file
    # If they were parsed from a 1-based source, we might need adjustment. 
    # parse_bed_line in utils usually assumes standard BED (0-based).
    region_bed_content = []
    for region in regions:
        strand = region.strand if region.strand else "."
        name = region.name if region.name else "."
        score = region.score if region.score is not None else 0
        region_bed_content.append(f"{region.chrom}\t{region.start}\t{region.end}\t{name}\t{score}\t{strand}")

    # Write to temp files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f_snps:
        f_snps.write('\n'.join(snp_bed_content))
        snp_bed_path = f_snps.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f_regions:
        f_regions.write('\n'.join(region_bed_content))
        region_bed_path = f_regions.name

    try:
        # Create pybedtools objects
        snps_bed = pybedtools.BedTool(snp_bed_path)
        regions_bed = pybedtools.BedTool(region_bed_path)

        # Perform intersection
        # -u: report each input bed entry only once if it overlaps
        # -f: minimum overlap fraction (not used here, we want >=1bp)
        # -r: require reciprocal overlap (not used)
        # -e: require minimum overlap (in bp)
        intersected = snps_bed.intersect(regions_bed, u=True, f=0, e=min_overlap)

        # Extract the names (which we set to SNP IDs) from the intersected results
        matched_snp_ids = set()
        for feature in intersected:
            # feature.name corresponds to the 4th column we wrote
            if feature.name:
                matched_snp_ids.add(feature.name)

        # Filter original SNPs list
        filtered_snps = [snp for snp in snps if (snp.id and snp.id in matched_snp_ids) or 
                       (not snp.id and f"{snp.chrom}:{snp.pos}" in matched_snp_ids)]
        
        logger.info(f"Found {len(filtered_snps)} SNPs overlapping regulatory regions ({min_overlap}bp min).")
        return filtered_snps

    finally:
        # Cleanup temp files
        if os.path.exists(snp_bed_path):
            os.remove(snp_bed_path)
        if os.path.exists(region_bed_path):
            os.remove(region_bed_path)

def main():
    """
    Main entry point for T013: Overlap logic.
    1. Load SNPs from data/raw/snps_raw.vcf (produced by T010/T010a)
    2. Load Regulatory Regions from data/raw/regulatory_regions.bed (produced by T011)
    3. Intersect them using pybedtools.
    4. Save filtered SNPs to data/derived/filtered_snps.parquet (T014 output, done here as part of flow)
    """
    ensure_data_dirs()

    # Dependencies check
    if not SNPS_RAW_VCF_PATH.exists():
        logger.error(f"Required input file not found: {SNPS_RAW_VCF_PATH}. Run T010/T010a first.")
        # In a real pipeline, we might raise or exit.
        # For this task, we assume the file exists as per task description.
        raise FileNotFoundError(f"Missing {SNPS_RAW_VCF_PATH}")

    if not REGULATORY_REGIONS_BED_PATH.exists():
        logger.error(f"Required input file not found: {REGULATORY_REGIONS_BED_PATH}. Run T011 first.")
        raise FileNotFoundError(f"Missing {REGULATORY_REGIONS_BED_PATH}")

    # 1. Load Data
    snps = load_snps_from_vcf(SNPS_RAW_VCF_PATH)
    regions = load_regulatory_regions(REGULATORY_REGIONS_BED_PATH)

    if not snps:
        logger.warning("No SNPs found in raw VCF. Stopping.")
        return

    if not regions:
        logger.warning("No regulatory regions found. Stopping.")
        return

    # 2. Intersect
    filtered_snps = intersect_snps_with_regions(snps, regions, min_overlap=1)

    # 3. Save to Parquet (T014 requirement)
    # We need pandas and pyarrow for this.
    try:
        import pandas as pd
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError:
        logger.error("pandas and pyarrow are required to save Parquet files.")
        raise

    if not filtered_snps:
        logger.warning("No SNPs passed the overlap filter. Saving empty dataframe.")
        df = pd.DataFrame()
    else:
        # Convert SNPs to dict for DataFrame
        data = []
        for snp in filtered_snps:
            data.append({
                'snp_id': snp.id,
                'chrom': snp.chrom,
                'pos': snp.pos,
                'ref': snp.ref,
                'alt': snp.alt,
                'qual': snp.qual,
                'filter': snp.filter,
                'info': snp.info,
                'source': 'dbSNP' # Placeholder, could be dynamic
            })
        df = pd.DataFrame(data)

    # Save
    output_path = DERIVED_DIR / "filtered_snps.parquet"
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved {len(df)} filtered SNPs to {output_path}")

    # Log lineage
    log_source_lineage("T013_Overlap", f"Intersected {len(snps)} raw SNPs with {len(regions)} regions. Result: {len(filtered_snps)} SNPs.")

    return df

if __name__ == "__main__":
    main()