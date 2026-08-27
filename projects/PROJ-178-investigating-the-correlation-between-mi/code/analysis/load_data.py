import os
import sys
import gzip
import shutil
import logging
import gc
import time
from pathlib import Path
from typing import Dict, List, Tuple, Iterator, Optional, Generator
import vcfpy

# Import environment configuration
try:
    from config.environment import get_local_paths, get_ftp_urls, ensure_directories
except ImportError:
    # Fallback for direct script execution
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config.environment import get_local_paths, get_ftp_urls, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Memory profiling utilities
def get_memory_usage_mb() -> float:
    """
    Get current memory usage of the process in MB.
    Uses /proc/self/status on Linux or psutil if available.
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        # Fallback for Linux systems without psutil
        try:
            with open('/proc/self/status', 'r') as f:
                for line in f:
                    if line.startswith('VmRSS:'):
                        return int(line.split()[1]) / 1024.0
        except (FileNotFoundError, IndexError, ValueError):
            logger.warning("Could not determine memory usage. psutil not available and /proc not found.")
            return 0.0
    return 0.0

class MemoryMonitor:
    """Context manager to track peak memory usage during a block of code."""
    
    def __init__(self, threshold_mb: float = 7000.0):
        self.threshold_mb = threshold_mb
        self.peak_mb = 0.0
        self.start_mb = 0.0
        self.current_mb = 0.0
    
    def __enter__(self):
        self.start_mb = get_memory_usage_mb()
        self.peak_mb = self.start_mb
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.current_mb = get_memory_usage_mb()
        self.peak_mb = max(self.peak_mb, self.current_mb)
        logger.info(f"MemoryMonitor: Start={self.start_mb:.1f}MB, Peak={self.peak_mb:.1f}MB, End={self.current_mb:.1f}MB")
        if self.peak_mb > self.threshold_mb:
            logger.warning(f"MemoryMonitor: Peak usage {self.peak_mb:.1f}MB exceeded threshold {self.threshold_mb:.1f}MB")
        return False

def ensure_dirs() -> Dict[str, Path]:
    """Create necessary directories if they don't exist."""
    paths = get_local_paths()
    ensure_directories(paths)
    return paths

def download_mito_vcf(ftp_url: str, output_path: Path) -> bool:
    """
    Download mitochondrial VCF from 1000 Genomes FTP.
    Returns True on success, False on failure.
    """
    import requests
    from tqdm import tqdm

    if not ftp_url:
        logger.error("FTP URL is empty or not configured.")
        return False

    logger.info(f"Downloading VCF from {ftp_url} to {output_path}")
    
    try:
        response = requests.get(ftp_url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(output_path, 'wb') as f, tqdm(
            total=total_size, unit='B', unit_scale=True, desc=output_path.name
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
        
        logger.info(f"Download complete: {output_path} ({output_path.stat().st_size / 1024 / 1024:.2f} MB)")
        return True
    except Exception as e:
        logger.error(f"Failed to download VCF: {e}")
        return False

def download_metadata(ftp_url: str, output_path: Path) -> bool:
    """
    Download metadata panel from 1000 Genomes FTP.
    Returns True on success, False on failure.
    """
    import requests
    from tqdm import tqdm

    if not ftp_url:
        logger.error("Metadata FTP URL is empty or not configured.")
        return False

    logger.info(f"Downloading metadata from {ftp_url} to {output_path}")
    
    try:
        response = requests.get(ftp_url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(output_path, 'wb') as f, tqdm(
            total=total_size, unit='B', unit_scale=True, desc=output_path.name
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
        
        logger.info(f"Download complete: {output_path} ({output_path.stat().st_size / 1024 / 1024:.2f} MB)")
        return True
    except Exception as e:
        logger.error(f"Failed to download metadata: {e}")
        return False

def validate_age_column(metadata_df: 'pd.DataFrame') -> bool:
    """
    Validate that the 'age' column exists in the metadata dataframe.
    Returns True if valid, raises ValueError if missing.
    """
    import pandas as pd
    
    if 'age' not in metadata_df.columns:
        error_msg = "CRITICAL: 'age' column missing from metadata. Pipeline must halt."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("Age column validation passed.")
    return True

def stream_vcf_variants(vcf_path: Path, sample_ids: List[str]) -> Generator[Tuple[vcfpy.Record, Dict[str, str]], None, None]:
    """
    Stream variants from a VCF file in chunks to minimize memory usage.
    Yields (record, sample_genotypes) tuples.
    
    Args:
        vcf_path: Path to the VCF file
        sample_ids: List of sample IDs to extract genotypes for
    
    Yields:
        Tuple of (vcfpy.Record, dict of sample_id -> genotype_info)
    """
    logger.info(f"Streaming variants from {vcf_path} for {len(sample_ids)} samples")
    
    reader = vcfpy.Reader.from_path(str(vcf_path))
    
    with reader:
        for record in reader:
            # Filter for chrM and PASS status immediately
            if record.CHROM != 'chrM' and record.CHROM != 'MT':
                continue
            
            if record.FILTER and 'PASS' not in record.FILTER:
                continue
            
            # Extract genotypes for requested samples
            sample_genotypes = {}
            for sample in record.samples:
                if sample.name in sample_ids:
                    gt_info = {
                        'GT': sample['GT'] if 'GT' in sample else None,
                        'DP': sample['DP'] if 'DP' in sample else None,
                        'AF': sample['AF'] if 'AF' in sample else None,
                        'HP': sample['HP'] if 'HP' in sample else None
                    }
                    sample_genotypes[sample.name] = gt_info
            
            if sample_genotypes:
                yield record, sample_genotypes

def filter_variant(record: vcfpy.Record) -> bool:
    """
    Filter a VCF record based on quality and type criteria.
    Returns True if the variant should be kept.
    """
    # Keep only chrM and PASS status
    if record.CHROM not in ['chrM', 'MT']:
        return False
    
    if record.FILTER and 'PASS' not in record.FILTER:
        return False
    
    # Optional: Filter by quality score if needed
    if hasattr(record, 'QUAL') and record.QUAL is not None:
        if record.QUAL < 30.0:  # Standard VCF quality threshold
            return False
    
    return True

def calculate_burden_streaming(
    vcf_path: Path, 
    sample_ids: List[str],
    vaf_threshold: float = 0.01,
    memory_threshold_mb: float = 7000.0
) -> Dict[str, Dict[str, float]]:
    """
    Calculate heteroplasmy burden for each sample using streaming VCF processing.
    Implements chunking strategy to ensure peak RAM usage < 7GB.
    
    Args:
        vcf_path: Path to the VCF file
        sample_ids: List of sample IDs to process
        vaf_threshold: Minimum variant allele frequency (default 1%)
        memory_threshold_mb: Maximum allowed memory usage (default 7GB)
    
    Returns:
        Dictionary mapping sample_id to burden metrics:
        {
            'sample_id': {
                'total_variants': int,
                'heteroplasmic_variants': int,
                'burden_count': float,
                'burden_frequency': float,
                'depth_bins': {'Low': int, 'Medium': int, 'High': int}
            }
        }
    """
    import pandas as pd
    import gc

    # Initialize burden accumulator
    burden_data = {
        sample_id: {
            'total_variants': 0,
            'heteroplasmic_variants': 0,
            'burden_count': 0.0,
            'burden_frequency': 0.0,
            'depth_bins': {'Low': 0, 'Medium': 0, 'High': 0}
        }
        for sample_id in sample_ids
    }
    
    logger.info(f"Starting streaming burden calculation for {len(sample_ids)} samples")
    logger.info(f"Memory threshold set to {memory_threshold_mb}MB")
    
    # Process VCF in streaming mode
    with MemoryMonitor(threshold_mb=memory_threshold_mb) as monitor:
        variant_count = 0
        
        for record, sample_genotypes in stream_vcf_variants(vcf_path, sample_ids):
            variant_count += 1
            
            # Process each sample for this variant
            for sample_id, gt_info in sample_genotypes.items():
                # Extract AF (Allele Frequency)
                af = gt_info.get('AF')
                if af is None or af == '.':
                    continue
                
                try:
                    af_val = float(af)
                except (ValueError, TypeError):
                    continue
                
                # Check VAF threshold
                if af_val >= vaf_threshold:
                    burden_data[sample_id]['heteroplasmic_variants'] += 1
                    burden_data[sample_id]['burden_frequency'] += af_val
                
                # Count total variants for this sample
                burden_data[sample_id]['total_variants'] += 1
                
                # Depth binning
                dp = gt_info.get('DP')
                if dp is not None and dp != '.':
                    try:
                        dp_val = int(dp)
                        if dp_val < 50:
                            burden_data[sample_id]['depth_bins']['Low'] += 1
                        elif dp_val < 200:
                            burden_data[sample_id]['depth_bins']['Medium'] += 1
                        else:
                            burden_data[sample_id]['depth_bins']['High'] += 1
                    except (ValueError, TypeError):
                        pass
          
          # Periodic memory cleanup and monitoring
            if variant_count % 10000 == 0:
                gc.collect()
                current_mem = get_memory_usage_mb()
                if current_mem > memory_threshold_mb * 0.9:
                    logger.warning(f"Memory usage at {current_mem:.1f}MB approaching threshold. Forcing GC.")
                    gc.collect()
    
    # Calculate final burden counts (sum of AFs)
    for sample_id in burden_data:
        if burden_data[sample_id]['heteroplasmic_variants'] > 0:
            burden_data[sample_id]['burden_count'] = burden_data[sample_id]['burden_frequency']
        else:
            burden_data[sample_id]['burden_count'] = 0.0
    
    logger.info(f"Streaming burden calculation complete. Processed {variant_count} variants.")
    logger.info(f"Peak memory usage: {monitor.peak_mb:.1f}MB")
    
    return burden_data

def main():
    """
    Main entry point for the load_data module.
    Downloads data, validates, and performs streaming burden calculation.
    """
    import pandas as pd
    from pathlib import Path

    paths = ensure_dirs()
    urls = get_ftp_urls()
    
    # Configuration
    vcf_url = urls.get('mito_vcf')
    metadata_url = urls.get('metadata_panel')
    
    if not vcf_url or not metadata_url:
        logger.error("Missing FTP URLs in configuration. Check environment.py")
        sys.exit(1)
    
    # Download data
    vcf_path = paths['raw'] / '1000g_mito.vcf.gz'
    metadata_path = paths['raw'] / '1000g_metadata.tsv'
    
    if not vcf_path.exists():
        if not download_mito_vcf(vcf_url, vcf_path):
            logger.error("Failed to download VCF. Exiting.")
            sys.exit(1)
    
    if not metadata_path.exists():
        if not download_metadata(metadata_url, metadata_path):
            logger.error("Failed to download metadata. Exiting.")
            sys.exit(1)
    
    # Load metadata
    logger.info("Loading metadata panel...")
    metadata_df = pd.read_csv(metadata_path, sep='\t', comment='#')
    
    # Validate age column
    try:
        validate_age_column(metadata_df)
    except ValueError as e:
        logger.error(str(e))
        # Log to validation file as per T007A
        validation_log = paths['logs'] / 'validation'
        validation_log.mkdir(parents=True, exist_ok=True)
        log_file = validation_log / 'log_age_column.json'
        with open(log_file, 'w') as f:
            f.write(f'{{"status": "error", "message": "{str(e)}"}}')
        sys.exit(1)
    
    # Extract sample IDs
    sample_ids = metadata_df['sample_id'].tolist()
    logger.info(f"Processing {len(sample_ids)} samples")
    
    # Perform streaming burden calculation
    logger.info("Starting streaming VCF analysis...")
    burden_results = calculate_burden_streaming(
        vcf_path=vcf_path,
        sample_ids=sample_ids,
        vaf_threshold=0.01,
        memory_threshold_mb=7000.0
    )
    
    # Convert results to DataFrame for downstream use
    burden_df = pd.DataFrame([
        {
            'sample_id': sid,
            'total_variants': data['total_variants'],
            'heteroplasmic_variants': data['heteroplasmic_variants'],
            'burden_count': data['burden_count'],
            'burden_frequency': data['burden_frequency'],
            'depth_low': data['depth_bins']['Low'],
            'depth_medium': data['depth_bins']['Medium'],
            'depth_high': data['depth_bins']['High']
        }
        for sid, data in burden_results.items()
    ])
    
    # Save intermediate results
    processed_path = paths['processed']
    processed_path.mkdir(parents=True, exist_ok=True)
    intermediate_file = processed_path / 'mito_burden_intermediate.csv'
    burden_df.to_csv(intermediate_file, index=False)
    
    logger.info(f"Intermediate burden data saved to {intermediate_file}")
    logger.info("Load data pipeline completed successfully.")

if __name__ == '__main__':
    main()
