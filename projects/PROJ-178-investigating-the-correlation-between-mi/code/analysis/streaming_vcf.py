import os
import sys
import logging
import gc
from pathlib import Path
from typing import Dict, List, Tuple, Iterator, Optional
import vcfpy

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

def stream_vcf_variants(vcf_path: str) -> Iterator[vcfpy.Record]:
    """Stream variants from a VCF file."""
    reader = vcfpy.Reader.from_path(vcf_path)
    for record in reader:
        yield record
    reader.close()

def calculate_burden_streaming(vcf_path: str, threshold_vaf: float = 0.01) -> Dict[str, int]:
    """Calculate heteroplasmy burden by streaming VCF."""
    sample_counts = {}
    monitor = MemoryMonitor()
    
    for record in stream_vcf_variants(vcf_path):
        if record.CHROM not in ['chrM', 'MT']:
            continue
        if record.FILTER is not None and record.FILTER.code != 'PASS':
            continue
        
        for call in record.calls:
            if call.sample_name not in sample_counts:
                sample_counts[call.sample_name] = 0
            if 'AD' in call.data:
                ad = call.data['AD']
                if isinstance(ad, list) and len(ad) >= 2:
                    ref, alt = ad[0], ad[1]
                    total = ref + alt
                    if total > 0 and (alt / total) >= threshold_vaf:
                        sample_counts[call.sample_name] += 1
        
        monitor.check()
    
    return sample_counts

def main():
    """Main entry point."""
    logging.basicConfig(level=logging.INFO)
    # Usage example
    # burden = calculate_burden_streaming('data/raw/test.vcf')
    pass

if __name__ == '__main__':
    main()
