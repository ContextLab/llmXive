import os
import sys
import pytest
import tempfile
from pathlib import Path
import vcfpy
import resource
import gc
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.streaming_vcf import (
    MemoryMonitor, 
    stream_vcf_variants, 
    calculate_burden_streaming,
    RAM_LIMIT_BYTES
)

def create_test_vcf(tmp_path: Path, num_samples: int = 10, num_variants: int = 1000):
    """
    Creates a synthetic VCF file for testing streaming logic.
    Writes to a temporary file and returns the path.
    """
    vcf_file = tmp_path / "test_mito.vcf.gz"
    
    # Create header
    header = vcfpy.Header()
    header.add_line(vcfpy.HeaderLine('fileformat', 'VCFv4.2'))
    header.add_line(vcfpy.HeaderLine('contig', ID='chrM'))
    header.add_line(vcfpy.HeaderLine('INFO', ID='DP', Number='1', Type='Integer', Description='Depth'))
    header.add_line(vcfpy.HeaderLine('FORMAT', ID='GT', Number='1', Type='String', Description='Genotype'))
    header.add_line(vcfpy.HeaderLine('FORMAT', ID='AD', Number='R', Type='Integer', Description='Allelic Depths'))
    header.add_line(vcfpy.HeaderLine('FORMAT', ID='DP', Number='1', Type='Integer', Description='Depth'))
    header.add_sample_header(vcfpy.SampleHeader('SAMPLE1'))
    
    # Add samples dynamically
    for i in range(1, num_samples):
        header.add_sample_header(vcfpy.SampleHeader(f'SAMPLE{i+1}'))

    writer = vcfpy.Writer.from_path(str(vcf_file), header)
    
    try:
        for i in range(num_variants):
            pos = 1000 + i
            # Create a record with varying depths to test filtering
            # Force some high VAF, some low
            if i % 10 == 0:
                # High VAF (should be counted)
                ad_values = [10, 90] # 90% alt
            else:
                # Low VAF (should be filtered out)
                ad_values = [95, 5] # 5% alt
            
            samples = []
            for j in range(num_samples):
                # Vary depth per sample
                depth = 20 + (j * 5)
                if i % 10 == 0:
                    # High VAF
                    ad = [10, 90]
                else:
                    # Low VAF
                    ad = [95, 5]
                
                samples.append(vcfpy.Sample(
                    sample_id=f'SAMPLE{j+1}',
                    data={
                        'GT': ['0/1'],
                        'AD': ad,
                        'DP': depth
                    }
                ))
            
            record = vcfpy.Record(
                CHROM='chrM',
                POS=pos,
                ID=f'VAR{i}',
                REF='A',
                ALTS=[vcfpy.Substitution('T')],
                QUAL=30.0,
                FILTER=['PASS'],
                INFO={'DP': 100},
                SAMPLES=samples
            )
            writer.write_record(record)
    finally:
        writer.close()
    
    return vcf_file

class TestMemoryMonitor:
    def test_init(self):
        monitor = MemoryMonitor()
        assert monitor.limit_bytes == RAM_LIMIT_BYTES
        assert monitor._peak_usage == 0

    def test_get_current_usage(self):
        monitor = MemoryMonitor()
        usage = monitor.get_current_usage_bytes()
        # Should be a positive number (at least the size of the python process)
        assert usage > 0
        assert isinstance(usage, int)

    def test_check_and_log_safe(self, caplog):
        monitor = MemoryMonitor(limit_bytes=1024**3) # 1GB limit
        # Current usage is likely < 1GB in a test environment
        result = monitor.check_and_log("Test")
        assert result is True

    def test_check_and_log_exceeded(self, monkeypatch):
        # Mock get_current_usage_bytes to return > limit
        monitor = MemoryMonitor(limit_bytes=100) # Tiny limit for testing
        def mock_get_usage():
            return 200
        
        monkeypatch.setattr(monitor, 'get_current_usage_bytes', mock_get_usage)
        
        with pytest.raises(MemoryError):
            monitor.check_and_log("TestExceeded")

class TestStreamingVCF:
    def test_stream_vcf_variants(self, tmp_path):
        vcf_file = create_test_vcf(tmp_path, num_samples=5, num_variants=50)
        count = 0
        for record in stream_vcf_variants(vcf_file):
            assert record.CHROM == 'chrM'
            count += 1
        assert count == 50

    def test_stream_handles_empty(self, tmp_path):
        # Create an empty VCF (header only)
        vcf_file = tmp_path / "empty.vcf.gz"
        header = vcfpy.Header()
        header.add_line(vcfpy.HeaderLine('fileformat', 'VCFv4.2'))
        header.add_line(vcfpy.HeaderLine('contig', ID='chrM'))
        header.add_sample_header(vcfpy.SampleHeader('SAMPLE1'))
        
        writer = vcfpy.Writer.from_path(str(vcf_file), header)
        writer.close()
        
        records = list(stream_vcf_variants(vcf_file))
        assert len(records) == 0

class TestBurdenCalculation:
    def test_burden_streaming_filters_correctly(self, tmp_path):
        # Create VCF with known values:
        # 100 variants total
        # Every 10th variant (10 total) has VAF 0.9 (High) -> Should count
        # Others have VAF 0.05 (Low) -> Should NOT count
        # Depth is always > 10
        vcf_file = create_test_vcf(tmp_path, num_samples=3, num_variants=100)
        
        burdens, peak_mem = calculate_burden_streaming(vcf_file, vaf_threshold=0.1, min_depth=5)
        
        # We expect 10 variants per sample (the high VAF ones)
        assert len(burdens) == 3
        for sample_id, count in burdens.items():
            assert count == 10, f"Expected 10 variants for {sample_id}, got {count}"

    def test_burden_streaming_depth_filter(self, tmp_path):
        # Create VCF where high VAF variants have low depth
        # We need to manually override the helper for this specific test
        # or create a specific VCF. For simplicity, we test the logic 
        # by adjusting the threshold in the function call.
        
        # Re-use the standard test VCF (which has mixed depths)
        # But we will set min_depth very high to filter everything
        vcf_file = create_test_vcf(tmp_path, num_samples=3, num_variants=100)
        
        # Set min_depth to 1000 (higher than any generated depth)
        burdens, _ = calculate_burden_streaming(vcf_file, vaf_threshold=0.01, min_depth=1000)
        
        # Should be empty
        assert len(burdens) == 0
        for count in burdens.values():
            assert count == 0

    def test_memory_limit_enforced(self, tmp_path, monkeypatch):
        # Force a memory error during calculation
        vcf_file = create_test_vcf(tmp_path, num_samples=3, num_variants=100)
        
        # Mock the check_and_log to raise MemoryError immediately
        original_check = MemoryMonitor.check_and_log
        def mock_check(self, stage=""):
            raise MemoryError("Simulated limit exceeded")
        
        monkeypatch.setattr(MemoryMonitor, 'check_and_log', mock_check)
        
        with pytest.raises(MemoryError):
            calculate_burden_streaming(vcf_file)

class TestDepthCategorization:
    # This class tests the logic that would categorize depth,
    # though the specific categorization logic is in preprocess.py.
    # Here we ensure the streaming function correctly exposes depth data
    # if needed for downstream categorization.
    pass
