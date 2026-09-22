import os
import sys
import gzip
import shutil
import logging
import gc
from pathlib import Path
import vcfpy
import pandas as pd
from config.environment import get_ftp_urls, get_local_paths

logger = logging.getLogger(__name__)

class MemoryMonitor:
    def __init__(self):
        self.peak_mb = 0.0

    def get_current_mb(self) -> float:
        try:
            import resource
            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
        except ImportError:
            return 0.0

    def check(self, threshold_mb: float = 7000):
        current = self.get_current_mb()
        if current > self.peak_mb:
            self.peak_mb = current
        if current > threshold_mb:
            logger.warning(f"Memory usage {current:.1f}MB exceeds threshold {threshold_mb}MB")
            gc.collect()

def get_memory_usage_mb() -> float:
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    except ImportError:
        return 0.0

def ensure_dirs():
    paths = get_local_paths()
    for key in ['raw', 'processed', 'logs']:
        p = paths.get(key, f'data/{key}')
        Path(p).mkdir(parents=True, exist_ok=True)

def download_mito_vcf(ftp_url: str, output_path: str):
    """Download the mitochondrial VCF from FTP."""
    import requests
    logger.info(f"Downloading VCF from {ftp_url} to {output_path}")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with requests.get(ftp_url, stream=True) as r:
            r.raise_for_status()
            with open(output_path, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
        logger.info("Download complete.")
    except Exception as e:
        logger.error(f"Failed to download VCF: {e}")
        raise

def download_metadata(ftp_url: str, output_path: str):
    """Download the metadata panel from FTP."""
    import requests
    logger.info(f"Downloading metadata from {ftp_url} to {output_path}")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with requests.get(ftp_url, stream=True) as r:
            r.raise_for_status()
            with open(output_path, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
        logger.info("Metadata download complete.")
    except Exception as e:
        logger.error(f"Failed to download metadata: {e}")
        raise

def validate_age_column(metadata_df: pd.DataFrame) -> bool:
    """Check if 'age' column exists in metadata."""
    if 'age' not in metadata_df.columns:
        logger.error("CRITICAL: 'age' column missing in metadata. HALTING.")
        return False
    return True

def stream_vcf_variants(vcf_path: str) -> Iterator[vcfpy.Record]:
    """Stream variants from a VCF file."""
    reader = vcfpy.Reader.from_path(vcf_path)
    for record in reader:
        yield record
    reader.close()

def filter_variant(record: vcfpy.Record) -> bool:
    """Check if variant is on chrM and has PASS status."""
    if record.CHROM != 'chrM' and record.CHROM != 'MT':
        return False
    if record.FILTER is not None and record.FILTER.code != 'PASS':
        return False
    return True

def calculate_burden_streaming(vcf_path: str, threshold_vaf: float = 0.01) -> pd.DataFrame:
    """
    Stream VCF variants, filter for chrM/PASS, and calculate heteroplasmy burden per sample.
    Returns a DataFrame with sample_id and burden count.
    """
    logger.info(f"Streaming VCF: {vcf_path}")
    sample_counts = {}
    monitor = MemoryMonitor()
    
    for record in stream_vcf_variants(vcf_path):
        if not filter_variant(record):
            continue
        
        # Check VAF in FORMAT fields (assuming 'AF' or 'VAF' exists)
        # 1000 Genomes often uses 'AF' in INFO or FORMAT
        # For heteroplasmy, we look at sample-specific fields if available
        # Simplified: assume 'GT' and 'DP' or 'AD' are present
        
        for call in record.calls:
            if call.sample_name not in sample_counts:
                sample_counts[call.sample_name] = 0
            
            # Parse genotype info
            if 'AD' in call.data:
                ad = call.data['AD']
                if isinstance(ad, list) and len(ad) >= 2:
                    ref, alt = ad[0], ad[1]
                    total = ref + alt
                    if total > 0:
                        vaf = alt / total
                        if vaf >= threshold_vaf:
                            sample_counts[call.sample_name] += 1
            elif 'GT' in call.data:
                # Fallback if only GT is present (simplified)
                gt = call.data['GT']
                if gt and gt != './.':
                    sample_counts[call.sample_name] += 1
        
        monitor.check()
        if monitor.peak_mb > 6000:
            logger.info("Garbage collection triggered due to high memory.")
            gc.collect()

    return pd.DataFrame(list(sample_counts.items()), columns=['sample_id', 'heteroplasmy_burden'])

def main():
    """Main entry point for data loading."""
    logging.basicConfig(level=logging.INFO)
    ensure_dirs()
    
    urls = get_ftp_urls()
    paths = get_local_paths()
    
    vcf_url = urls.get('mito_vcf')
    meta_url = urls.get('metadata_panel')
    
    if not vcf_url or not meta_url:
        logger.error("Missing FTP URLs in environment config.")
        sys.exit(1)
    
    vcf_path = paths['raw'] / '1000G_mito.vcf.gz'
    meta_path = paths['raw'] / '1000G_metadata.tsv'
    
    if not vcf_path.exists():
        download_mito_vcf(vcf_url, str(vcf_path))
    if not meta_path.exists():
        download_metadata(meta_url, str(meta_path))
    
    meta_df = pd.read_csv(meta_path, sep='\t')
    if not validate_age_column(meta_df):
        # Write error log and exit
        log_path = Path('data/validation/log_age_column.json')
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, 'w') as f:
            f.write('{"error": "age column missing", "status": "HALTED"}')
        sys.exit(1)
    
    # Calculate burden
    burden_df = calculate_burden_streaming(str(vcf_path))
    output_path = paths['processed'] / 'burden_raw.csv'
    burden_df.to_csv(output_path, index=False)
    logger.info(f"Burden calculation complete. Saved to {output_path}")

if __name__ == '__main__':
    main()
