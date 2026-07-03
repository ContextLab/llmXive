"""
Streaming VCF processor for memory-efficient mitochondrial data handling.

Implements chunked reading of large VCF files to ensure RAM usage
stays below 7GB while processing 1000 Genomes mitochondrial data.
"""
import os
import sys
import logging
import gc
from pathlib import Path
from typing import Dict, List, Tuple, Iterator, Optional
import vcfpy
import pandas as pd
import numpy as np

from config.environment import ensure_directories, get_local_paths

logger = logging.getLogger(__name__)

# Constants for memory management
MAX_RAM_GB = 7.0
CHUNK_SIZE = 10000  # Number of variants to process per chunk
GC_THRESHOLD = 50   # Run garbage collection every N chunks

class MemoryMonitor:
    """Simple memory monitor to track RAM usage during processing."""
    
    def __init__(self, max_gb: float = MAX_RAM_GB):
        self.max_bytes = max_gb * 1024**3
        self.peak_usage = 0
        self.current_usage = 0
    
    def get_current_usage(self) -> float:
        """Get current memory usage in bytes."""
        try:
            import resource
            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
        except (ImportError, AttributeError):
            # Fallback for systems without resource module
            return 0
    
    def check_and_gc(self, chunk_count: int) -> bool:
        """Check memory usage and trigger GC if necessary."""
        if chunk_count % GC_THRESHOLD == 0:
            gc.collect()
            usage = self.get_current_usage()
            self.current_usage = usage
            if usage > self.peak_usage:
                self.peak_usage = usage
            
            usage_gb = usage / (1024**3)
            logger.debug(f"Memory check at chunk {chunk_count}: {usage_gb:.2f} GB (peak: {self.peak_usage / (1024**3):.2f} GB)")
            
            if usage > self.max_bytes * 0.9:  # 90% threshold
                logger.warning(f"Memory usage approaching limit: {usage_gb:.2f} GB / {MAX_RAM_GB} GB")
                gc.collect()
                return True
        return False

def stream_vcf_variants(
    vcf_path: Path,
    target_chromosomes: Optional[List[str]] = None,
    chunk_size: int = CHUNK_SIZE
) -> Iterator[pd.DataFrame]:
    """
    Stream VCF variants in chunks to prevent memory overflow.
    
    Args:
        vcf_path: Path to the VCF file (can be gzipped)
        target_chromosomes: List of chromosomes to include (e.g., ['chrM'])
        chunk_size: Number of variants per chunk
        
    Yields:
        DataFrames containing variant data for each chunk
    """
    if not vcf_path.exists():
        raise FileNotFoundError(f"VCF file not found: {vcf_path}")
    
    logger.info(f"Starting streaming read of {vcf_path}")
    
    # Determine if file is compressed
    is_gzip = str(vcf_path).endswith('.gz')
    mode = 'rt' if is_gzip else 'r'
    
    reader = vcfpy.Reader.from_path(str(vcf_path))
    
    variant_buffer = []
    chunk_count = 0
    monitor = MemoryMonitor()
    
    try:
        for record in reader:
            # Filter by chromosome if specified
            if target_chromosomes and record.CHROM not in target_chromosomes:
                continue
            
            variant_buffer.append(record)
            
            if len(variant_buffer) >= chunk_size:
                chunk_df = _records_to_dataframe(variant_buffer)
                yield chunk_df
                variant_buffer = []
                chunk_count += 1
                
                # Check memory and trigger GC if needed
                if monitor.check_and_gc(chunk_count):
                    # Force a more aggressive cleanup
                    gc.collect()
                    logger.info("Forced garbage collection due to high memory usage")
    
    finally:
        reader.close()
        # Process remaining variants
        if variant_buffer:
            chunk_df = _records_to_dataframe(variant_buffer)
            yield chunk_df
            chunk_count += 1
    
    logger.info(f"Completed streaming: {chunk_count} chunks processed")

def _records_to_dataframe(records: List[vcfpy.Record]) -> pd.DataFrame:
    """
    Convert a list of VCF records to a DataFrame.
    
    Args:
        records: List of vcfpy.Record objects
        
    Returns:
        DataFrame with variant information
    """
    if not records:
        return pd.DataFrame()
    
    data = []
    for record in records:
        row = {
            'chrom': record.CHROM,
            'pos': record.POS,
            'ref': record.REF,
            'alt': record.ALT[0].value if record.ALT else None,
            'qual': record.QUAL,
            'filter': record.FILTER,
            'id': record.ID,
            'info': record.INFO,
            'samples': {}
        }
        
        # Extract sample data if present
        if record.samples:
            for sample in record.samples:
                sample_data = {}
                for key, value in sample.data.items():
                    if value is not None:
                        sample_data[key] = value
                row['samples'][sample.sample] = sample_data
        
        data.append(row)
    
    return pd.DataFrame(data)

def calculate_burden_streaming(
    vcf_path: Path,
    target_chromosomes: List[str] = None,
    vaf_threshold: float = 0.01,
    min_depth: int = 10
) -> pd.DataFrame:
    """
    Calculate heteroplasmy burden using streaming to handle large VCFs.
    
    This function processes the VCF in chunks, accumulating variant counts
    and burden metrics per sample without loading the entire file into memory.
    
    Args:
        vcf_path: Path to the VCF file
        target_chromosomes: Chromosomes to include (default: ['chrM'])
        vaf_threshold: Minimum variant allele frequency (default: 0.01 for 1%)
        min_depth: Minimum read depth required (default: 10)
        
    Returns:
        DataFrame with per-sample burden metrics
    """
    if target_chromosomes is None:
        target_chromosomes = ['chrM']
    
    logger.info(f"Calculating burden for {vcf_path} with streaming")
    
    # Initialize accumulators
    sample_counts = {}  # sample_id -> count of variants
    sample_burden = {}  # sample_id -> sum of VAFs
    sample_depths = {}  # sample_id -> list of depths
    
    chunk_count = 0
    monitor = MemoryMonitor()
    
    for chunk_df in stream_vcf_variants(vcf_path, target_chromosomes):
        if chunk_df.empty:
            continue
        
        # Process each row in the chunk
        for idx, row in chunk_df.iterrows():
            samples = row.get('samples', {})
            if not samples:
                continue
            
            # Extract VAF and depth from sample data
            for sample_id, sample_data in samples.items():
                if sample_id not in sample_counts:
                    sample_counts[sample_id] = 0
                    sample_burden[sample_id] = 0.0
                    sample_depths[sample_id] = []
                
                # Get VAF and depth
                vaf = sample_data.get('VAF', sample_data.get('AF', 0))
                depth = sample_data.get('DP', 0)
                
                # Apply filters
                if vaf >= vaf_threshold and depth >= min_depth:
                    sample_counts[sample_id] += 1
                    sample_burden[sample_id] += vaf
                    sample_depths[sample_id].append(depth)
        
        chunk_count += 1
        if monitor.check_and_gc(chunk_count):
            logger.info("Memory pressure detected during burden calculation")
    
    # Aggregate results
    results = []
    for sample_id in sample_counts:
        count = sample_counts[sample_id]
        total_vaf = sample_burden[sample_id]
        depths = sample_depths[sample_id]
        
        avg_depth = np.mean(depths) if depths else 0
        
        results.append({
            'sample_id': sample_id,
            'variant_count': count,
            'total_burden': total_vaf,
            'avg_vaf': total_vaf / count if count > 0 else 0,
            'avg_depth': avg_depth,
            'depth_bins': _categorize_depths(depths)
        })
    
    logger.info(f"Processed {len(results)} samples across {chunk_count} chunks")
    return pd.DataFrame(results)

def _categorize_depths(depths: List[int]) -> Dict[str, int]:
    """Categorize depths into Low, Medium, High bins."""
    if not depths:
        return {'Low': 0, 'Medium': 0, 'High': 0}
    
    low = sum(1 for d in depths if d < 50)
    medium = sum(1 for d in depths if 50 <= d < 200)
    high = sum(1 for d in depths if d >= 200)
    
    return {'Low': low, 'Medium': medium, 'High': high}

def main():
    """Main entry point for streaming VCF processing."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Ensure directories exist
    data_paths = get_local_paths()
    ensure_directories(data_paths)
    
    vcf_path = data_paths.get('raw_mito_vcf')
    if not vcf_path or not vcf_path.exists():
        logger.error(f"VCF file not found at {vcf_path}")
        sys.exit(1)
    
    logger.info(f"Processing VCF: {vcf_path}")
    
    # Calculate burden using streaming
    burden_df = calculate_burden_streaming(
        vcf_path,
        target_chromosomes=['chrM'],
        vaf_threshold=0.01,
        min_depth=10
    )
    
    # Save results
    output_path = data_paths.get('processed_burden') or Path(data_paths['processed']) / 'burden_streaming.csv'
    burden_df.to_csv(output_path, index=False)
    
    logger.info(f"Burden calculation complete. Results saved to {output_path}")
    logger.info(f"Total samples processed: {len(burden_df)}")
    
    # Print summary statistics
    if len(burden_df) > 0:
        logger.info(f"Mean variant count: {burden_df['variant_count'].mean():.2f}")
        logger.info(f"Mean burden: {burden_df['total_burden'].mean():.6f}")
        logger.info(f"Max memory usage: {MemoryMonitor().peak_usage / (1024**3):.2f} GB")

if __name__ == '__main__':
    main()
