import json
import os
import hashlib
import logging
import gzip
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Local imports matching API surface
from config import ensure_data_dirs
from utils import SNP, parse_vcf_line, calculate_file_checksum, GenomicRegion, parse_bed_line

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MAF_THRESHOLD = 0.01  # 1%
VALID_ALLELES = {'A', 'C', 'G', 'T'}

def download_file_ftp(url: str, output_path: str) -> bool:
    """Download a file from FTP using wget or curl."""
    try:
        # Try wget first
        result = subprocess.run(
            ['wget', '-q', '--show-progress', '-O', output_path, url],
            check=True,
            capture_output=True
        )
        return True
    except subprocess.CalledProcessError:
        try:
            # Fallback to curl
            result = subprocess.run(
                ['curl', '-sL', '-o', output_path, url],
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to download {url}: {e}")
            return False

def log_source_lineage(source: str, output_file: str, status: str = "SUCCESS"):
    """Log the source lineage to a text file."""
    ensure_data_dirs()
    log_path = Path("data/raw/source_log.txt")
    timestamp = datetime.now().isoformat()
    with open(log_path, 'a') as f:
        f.write(f"{timestamp} | {source} | {status}\n")
    logger.info(f"Logged lineage: {source} -> {status}")

def calculate_file_checksum(filepath: str, algorithm: str = 'sha256') -> str:
    """Calculate checksum of a file."""
    hash_func = hashlib.new(algorithm)
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def filter_snps(snps: List[SNP], maf_threshold: float = MAF_THRESHOLD) -> List[SNP]:
    """
    Filter SNPs based on MAF and valid alleles.
    Excludes SNPs with MAF < threshold or non-ACGT alleles.
    """
    filtered = []
    for snp in snps:
        # Check MAF
        if snp.maf < maf_threshold:
            continue
        
        # Check alleles
        ref_allele = snp.ref.upper()
        alt_allele = snp.alt.upper()
        
        if ref_allele not in VALID_ALLELES or alt_allele not in VALID_ALLELES:
            continue
        
        if len(ref_allele) != 1 or len(alt_allele) != 1:
            # Exclude indels
            continue
        
        filtered.append(snp)
    
    logger.info(f"Filtered SNPs: {len(snps)} -> {len(filtered)}")
    return filtered

def intersect_snps_with_regions(snps: List[SNP], regions: List[GenomicRegion]) -> List[SNP]:
    """
    Intersect SNPs with regulatory regions using pybedtools.
    Returns SNPs that overlap at least one region.
    """
    try:
        import pybedtools
    except ImportError:
        logger.error("pybedtools is required for intersection. Install with: pip install pybedtools")
        raise

    # Create temporary BED file for SNPs
    snp_bed_content = []
    for snp in snps:
        # VCF is 1-based, BED is 0-based. 
        # SNP position in VCF is the position of the first base.
        # To overlap, we treat the SNP as a 1bp interval [pos-1, pos)
        snp_bed_content.append(f"{snp.chrom}\t{snp.pos - 1}\t{snp.pos}\t{snp.id}")

    snp_bed_path = tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False)
    snp_bed_path.write('\n'.join(snp_bed_content))
    snp_bed_path.close()

    # Create temporary BED file for regions
    region_bed_content = []
    for reg in regions:
        region_bed_content.append(f"{reg.chrom}\t{reg.start}\t{reg.end}")
    
    region_bed_path = tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False)
    region_bed_path.write('\n'.join(region_bed_content))
    region_bed_path.close()

    try:
        snp_bed = pybedtools.BedTool(snp_bed_path.name)
        region_bed = pybedtools.BedTool(region_bed_path.name)
        
        # Intersect: keep SNPs that overlap regions
        intersected = snp_bed.intersect(region_bed, wa=True, u=True)
        
        overlapping_snps = []
        for interval in intersected:
            # Parse back to SNP object
            # Format: chrom, start, end, id
            snp_id = interval.name
            # Find original SNP
            for snp in snps:
                if snp.id == snp_id:
                    overlapping_snps.append(snp)
                    break
        
        logger.info(f"Intersected SNPs: {len(snps)} -> {len(overlapping_snps)}")
        return overlapping_snps
    finally:
        os.unlink(snp_bed_path.name)
        os.unlink(region_bed_path.name)

def load_pwms(filepath: str) -> Dict[str, Any]:
    """Load PWMs from JASPAR format file."""
    pwms = {}
    current_pwm = None
    current_id = None
    current_matrix = {'A': [], 'C': [], 'G': [], 'T': []}
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('>'):
                # Save previous PWM
                if current_id and current_pwm:
                    pwms[current_id] = current_pwm
                
                # Parse header
                # Format: >MAxxxxx Name
                parts = line[1:].split()
                current_id = parts[0]
                current_pwm = None
                current_matrix = {'A': [], 'C': [], 'G': [], 'T': []}
                continue
            
            if line.startswith('>') and current_id:
                # Save previous
                pwms[current_id] = current_pwm
                continue
            
            # Parse matrix line
            # Format: A: 1 2 3 ...
            if ':' in line:
                parts = line.split(':')
                base = parts[0].strip()
                values = [int(x) for x in parts[1].split()]
                if base in current_matrix:
                    current_matrix[base] = values
            
            # Check for end of matrix (empty line or new header)
            if line == '' or line.startswith('>'):
                if current_id and current_matrix['A']:
                    # Create PWM dict
                    current_pwm = {
                        'id': current_id,
                        'matrix': {
                            'A': current_matrix['A'],
                            'C': current_matrix['C'],
                            'G': current_matrix['G'],
                            'T': current_matrix['T']
                        }
                    }
    
    # Save last PWM
    if current_id and current_matrix['A']:
        pwms[current_id] = {
            'id': current_id,
            'matrix': current_matrix
        }
    
    logger.info(f"Loaded {len(pwms)} PWMs")
    return pwms

def download_encode_regulatory_regions(output_dir: str = "data/raw"):
    """Download ENCODE regulatory regions BED files."""
    ensure_data_dirs()
    
    # URLs for promoter and enhancer regions
    # Using specific wgEnRegTss patterns as per task description
    urls = {
        'promoter': 'https://www.encodeproject.org/files/wgEncodeRegTssRecurrent/ENCFF001TJJ/@@download/ENCFF001TJJ.bed.gz',
        'enhancer': 'https://www.encodeproject.org/files/wgEncodeRegEnhancers/ENCFF001VQI/@@download/ENCFF001VQI.bed.gz'
    }
    
    downloaded_files = {}
    for name, url in urls.items():
        output_path = os.path.join(output_dir, f"{name}_regions.bed.gz")
        if os.path.exists(output_path):
            logger.info(f"Found existing file: {output_path}")
            downloaded_files[name] = output_path
            continue
        
        logger.info(f"Downloading {name} regions from {url}")
        # Download gzipped file
        if download_file_ftp(url, output_path):
            # Decompress
            output_bed = output_path.replace('.gz', '')
            with gzip.open(output_path, 'rb') as f_in:
                with open(output_bed, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(output_path)
            downloaded_files[name] = output_bed
            log_source_lineage(url, output_bed)
        else:
            logger.warning(f"Failed to download {name} regions")
    
    return downloaded_files

def main():
    """
    Main pipeline for T014:
    1. Load raw SNPs (from T010/T010a)
    2. Load regulatory regions (from T011)
    3. Filter SNPs by MAF and alleles (T012)
    4. Intersect with regulatory regions (T013)
    5. Validate against schema
    6. Save to parquet
    """
    ensure_data_dirs()
    
    # Paths
    snps_raw_path = "data/raw/snps_raw.vcf"
    regions_path = "data/raw/regulatory_regions.bed"
    output_path = "data/derived/filtered_snps.parquet"
    schema_path = "specs/001-gene-regulation/contracts/snp_schema.schema.yaml"
    
    # Check prerequisites
    if not os.path.exists(snps_raw_path):
        # Try to find if it's gzipped
        if os.path.exists(snps_raw_path + '.gz'):
            snps_raw_path = snps_raw_path + '.gz'
        else:
            logger.error(f"Raw SNPs file not found: {snps_raw_path}")
            return
    
    if not os.path.exists(regions_path):
        logger.error(f"Regulatory regions file not found: {regions_path}")
        return
    
    # Load SNPs from VCF
    logger.info("Loading SNPs from VCF...")
    snps = []
    with open(snps_raw_path, 'r') as f:
        for line in f:
            if line.startswith('#'):
                continue
            snp = parse_vcf_line(line)
            if snp:
                snps.append(snp)
    logger.info(f"Loaded {len(snps)} raw SNPs")
    
    # Load regulatory regions
    logger.info("Loading regulatory regions...")
    regions = []
    with open(regions_path, 'r') as f:
        for line in f:
            if line.startswith('#'):
                continue
            region = parse_bed_line(line)
            if region:
                regions.append(region)
    logger.info(f"Loaded {len(regions)} regulatory regions")
    
    # Filter SNPs (T012)
    filtered_snps = filter_snps(snps, maf_threshold=MAF_THRESHOLD)
    
    # Intersect with regions (T013)
    overlapping_snps = intersect_snps_with_regions(filtered_snps, regions)
    
    if not overlapping_snps:
        logger.warning("No SNPs overlapped with regulatory regions!")
        # Still save empty file for pipeline continuity
        import pandas as pd
        df = pd.DataFrame(columns=['snp_id', 'chrom', 'pos', 'ref', 'alt', 'maf'])
        df.to_parquet(output_path, index=False)
        return
    
    # Validate against schema (T014)
    logger.info("Validating against schema...")
    try:
        import yaml
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        # Proceed without validation if schema missing, but log warning
        logger.warning("Proceeding without schema validation")
        schema = None
    
    # Prepare data for saving
    data = []
    for snp in overlapping_snps:
        data.append({
            'snp_id': snp.id,
            'chrom': snp.chrom,
            'pos': snp.pos,
            'ref': snp.ref,
            'alt': snp.alt,
            'maf': snp.maf
        })
    
    # Basic schema validation if schema loaded
    if schema:
        required_fields = schema.get('required', [])
        for record in data:
            for field in required_fields:
                if field not in record:
                    logger.error(f"Missing required field {field} in record: {record}")
                    raise ValueError(f"Schema validation failed: missing {field}")
    
    # Save to parquet
    import pandas as pd
    df = pd.DataFrame(data)
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved {len(data)} filtered SNPs to {output_path}")
    
    # Calculate checksum
    checksum = calculate_file_checksum(output_path)
    checksums_file = "data/checksums.json"
    checksums = {}
    if os.path.exists(checksums_file):
        with open(checksums_file, 'r') as f:
            checksums = json.load(f)
    checksums['filtered_snps.parquet'] = checksum
    with open(checksums_file, 'w') as f:
        json.dump(checksums, f, indent=2)
    
    logger.info("T014 completed successfully")

if __name__ == "__main__":
    main()
