import os
import sys
import logging
import gc
from pathlib import Path
from typing import Dict, List, Tuple, Iterator, Optional
import resource
import vcfpy
from config.environment import get_local_paths

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# RAM limit in bytes (7 GB)
RAM_LIMIT_BYTES = 7 * 1024**3

class MemoryMonitor:
    """
    Monitors memory usage of the current process.
    Uses resource.getrusage for POSIX systems (Linux/macOS).
    Falls back to a safe estimation if unavailable.
    """
    def __init__(self, limit_bytes: int = RAM_LIMIT_BYTES):
        self.limit_bytes = limit_bytes
        self._peak_usage = 0
        self._check_count = 0

    def get_current_usage_bytes(self) -> int:
        """
        Returns current RSS (Resident Set Size) in bytes.
        """
        try:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            # ru_maxrss is in kilobytes on Linux, bytes on macOS
            # Detect platform to handle conversion
            if sys.platform == 'darwin':
                return usage.ru_maxrss
            else:
                return usage.ru_maxrss * 1024
        except AttributeError:
            # Fallback for Windows or if resource unavailable
            # We cannot measure precisely, so we return 0 and log a warning
            logger.warning("resource.getrusage not available. Memory monitoring disabled.")
            return 0

    def check_and_log(self, stage: str = "Processing") -> bool:
        """
        Checks current memory usage against the limit.
        Logs current usage and raises MemoryError if exceeded.
        Returns True if safe, False if exceeded.
        """
        current = self.get_current_usage_bytes()
        self._peak_usage = max(self._peak_usage, current)
        self._check_count += 1

        usage_gb = current / (1024**3)
        limit_gb = self.limit_bytes / (1024**3)
        logger.info(f"[MemoryMonitor] {stage}: Current RSS = {usage_gb:.2f} GB (Limit: {limit_gb:.2f} GB)")

        if current > self.limit_bytes:
            logger.error(f"[MemoryMonitor] CRITICAL: Memory usage {usage_gb:.2f} GB exceeds limit {limit_gb:.2f} GB at {stage}.")
            logger.error("Forcing garbage collection and raising MemoryError.")
            gc.collect()
            raise MemoryError(f"Memory limit exceeded: {usage_gb:.2f} GB > {limit_gb:.2f} GB")

        return True

    def get_peak_usage_gb(self) -> float:
        return self._peak_usage / (1024**3)

def stream_vcf_variants(vcf_path: Path) -> Iterator[vcfpy.Record]:
    """
    Generator that yields records from a VCF file one by one using vcfpy.
    This ensures we never load the entire VCF into memory.
    """
    if not vcf_path.exists():
        raise FileNotFoundError(f"VCF file not found: {vcf_path}")

    logger.info(f"Opening VCF for streaming: {vcf_path}")
    reader = vcfpy.Reader.from_path(str(vcf_path))
    
    try:
        for record in reader:
            yield record
    finally:
        reader.close()

def calculate_burden_streaming(
    vcf_path: Path,
    vaf_threshold: float = 0.01,
    min_depth: int = 10
) -> Tuple[Dict[str, int], float]:
    """
    Calculates heteroplasmy burden per sample by streaming the VCF.
    
    Logic:
    1. Iterate through records one by one.
    2. Filter for chrM and PASS status.
    3. Parse GT and AD fields to calculate VAF and Depth.
    4. Count variants per sample if VAF >= threshold and Depth >= min_depth.
    5. Monitor memory usage periodically.
    
    Returns:
        Tuple of (sample_burden_dict, peak_memory_gb)
    """
    monitor = MemoryMonitor()
    sample_burdens: Dict[str, int] = {}
    processed_count = 0
    
    logger.info(f"Starting streaming burden calculation for {vcf_path}")
    logger.info(f"Thresholds: VAF >= {vaf_threshold}, Depth >= {min_depth}")

    for record in stream_vcf_variants(vcf_path):
        # Filter by chromosome
        if record.CHROM != 'chrM':
            continue
        
        # Filter by quality status
        if 'PASS' not in record.FILTER:
            continue

        # Parse samples
        # vcfpy record.samples is a list of Sample objects
        for sample in record.samples:
            sample_id = sample.sample_id
            
            # Extract GT and AD
            gt = sample.get_field('GT')
            ad = sample.get_field('AD')
            
            if gt is None or ad is None:
                continue
            
            # Parse AD (Allelic Depth) - list of ints [ref, alt1, alt2...]
            if not isinstance(ad, (list, tuple)) or len(ad) < 2:
                continue
            
            ref_depth = ad[0]
            alt_depth = sum(ad[1:])
            total_depth = ref_depth + alt_depth
            
            if total_depth == 0:
                continue
            
            vaf = alt_depth / total_depth
            
            if vaf >= vaf_threshold and total_depth >= min_depth:
                if sample_id not in sample_burdens:
                    sample_burdens[sample_id] = 0
                sample_burdens[sample_id] += 1

        processed_count += 1
        
        # Check memory every 10,000 records
        if processed_count % 10000 == 0:
            monitor.check_and_log(f"After {processed_count} records")
            # Force GC occasionally to keep RSS low
            gc.collect()

    final_peak = monitor.get_peak_usage_gb()
    logger.info(f"Finished processing {processed_count} records.")
    logger.info(f"Peak memory usage: {final_peak:.2f} GB")
    
    return sample_burdens, final_peak

def main():
    """
    Entry point for the streaming VCF analysis.
    Reads configuration, runs the streaming burden calculation,
    and writes the results to a CSV file.
    """
    paths = get_local_paths()
    raw_vcf_dir = paths['raw_vcf_dir']
    processed_dir = paths['processed_dir']
    
    # Ensure output directory exists
    os.makedirs(processed_dir, exist_ok=True)
    
    # For this optimization task, we assume a single representative VCF
    # In a real scenario, this might loop over multiple files
    vcf_files = list(Path(raw_vcf_dir).glob("*.vcf.gz"))
    
    if not vcf_files:
        logger.error("No VCF files found in raw directory. Cannot run streaming test.")
        sys.exit(1)
    
    # Use the first file for the optimization test
    target_vcf = vcf_files[0]
    logger.info(f"Selected target VCF for streaming test: {target_vcf}")
    
    try:
        burdens, peak_mem = calculate_burden_streaming(target_vcf)
        
        # Write results to CSV
        output_path = Path(processed_dir) / "streaming_burden_results.csv"
        with open(output_path, 'w') as f:
            f.write("sample_id,burden_count\n")
            for sample_id, count in sorted(burdens.items()):
                f.write(f"{sample_id},{count}\n")
        
        logger.info(f"Results written to {output_path}")
        logger.info(f"Total samples processed: {len(burdens)}")
        logger.info(f"Peak memory usage recorded: {peak_mem:.2f} GB")
        
        if peak_mem > 7.0:
            logger.warning("Memory usage exceeded 7GB limit during processing.")
        else:
            logger.info("Memory usage stayed within 7GB limit.")
            
    except MemoryError as e:
        logger.error(f"Task failed due to memory constraints: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during streaming: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
