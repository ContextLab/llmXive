"""
Tests for streaming VCF processing to ensure memory efficiency.
"""
import os
import sys
import pytest
import tempfile
from pathlib import Path
import vcfpy
import pandas as pd
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.streaming_vcf import (
    stream_vcf_variants,
    calculate_burden_streaming,
    MemoryMonitor,
    _categorize_depths
)

def create_test_vcf(path: Path, num_samples: int = 10, num_variants: int = 100):
    """Create a small test VCF file for testing."""
    header = vcfpy.Header()
    header.add_line(vcfpy.HeaderLine('##fileformat', 'VCFv4.2'))
    header.add_line(vcfpy.HeaderLine('##contig', '<ID=chrM,length=16569>'))
    
    # Add sample headers
    for i in range(num_samples):
        header.add_line(vcfpy.HeaderLine('##SAMPLE', f'<ID=sample{i}>'))
    
    # Add FORMAT fields
    header.add_field(vcfpy.FieldHeader('VAF', 'Number=A', 'Type=Float', 'Description="Variant Allele Frequency"'))
    header.add_field(vcfpy.FieldHeader('DP', 'Number=1', 'Type=Integer', 'Description="Read Depth"'))
    
    records = []
    for i in range(num_variants):
        # Create sample data with varying VAF and depth
        sample_data = []
        for j in range(num_samples):
            vaf = np.random.uniform(0.001, 0.1)
            depth = np.random.randint(10, 300)
            sample_data.append(vcfpy.Sample(
                f'sample{j}',
                data={'VAF': vaf, 'DP': depth}
            ))
        
        record = vcfpy.Record(
            CHROM='chrM',
            POS=i + 1,
            REF='A',
            ALT=[vcfpy.Alt('T')],
            QUAL=30.0,
            FILTER=None,
            INFO={},
            SAMPLES=sample_data
        )
        records.append(record)
    
    writer = vcfpy.Writer.from_path(str(path), header)
    for record in records:
        writer.write_record(record)
    writer.close()
    return path

class TestMemoryMonitor:
    def test_memory_monitor_initialization(self):
        monitor = MemoryMonitor(max_gb=7.0)
        assert monitor.max_bytes == 7.0 * 1024**3
        assert monitor.peak_usage == 0
        assert monitor.current_usage == 0

    def test_check_and_gc(self):
        monitor = MemoryMonitor(max_gb=7.0)
        # Should not trigger GC on first call
        result = monitor.check_and_gc(0)
        assert result is False

        # Should trigger GC at threshold
        result = monitor.check_and_gc(50)
        assert result is False  # Should be False unless memory is very high

class TestStreamingVCF:
    def test_stream_vcf_variants(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            vcf_path = Path(tmpdir) / 'test.vcf'
            create_test_vcf(vcf_path, num_samples=5, num_variants=50)
            
            chunks = list(stream_vcf_variants(vcf_path, target_chromosomes=['chrM'], chunk_size=10))
            
            assert len(chunks) > 0
            total_variants = sum(len(chunk) for chunk in chunks)
            assert total_variants == 50
            
            # Check that all chunks are DataFrames
            for chunk in chunks:
                assert isinstance(chunk, pd.DataFrame)
                assert 'chrom' in chunk.columns

    def test_stream_vcf_variants_filter_chromosome(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            vcf_path = Path(tmpdir) / 'test.vcf'
            create_test_vcf(vcf_path, num_samples=5, num_variants=50)
            
            # Request a chromosome that doesn't exist
            chunks = list(stream_vcf_variants(vcf_path, target_chromosomes=['chr1']))
            
            assert len(chunks) == 0

class TestBurdenCalculation:
    def test_calculate_burden_streaming(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            vcf_path = Path(tmpdir) / 'test.vcf'
            create_test_vcf(vcf_path, num_samples=5, num_variants=100)
            
            burden_df = calculate_burden_streaming(
                vcf_path,
                target_chromosomes=['chrM'],
                vaf_threshold=0.01,
                min_depth=10
            )
            
            assert len(burden_df) == 5
            assert 'sample_id' in burden_df.columns
            assert 'variant_count' in burden_df.columns
            assert 'total_burden' in burden_df.columns
            
            # Check that all samples have non-negative values
            assert (burden_df['variant_count'] >= 0).all()
            assert (burden_df['total_burden'] >= 0).all()

    def test_calculate_burden_with_thresholds(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            vcf_path = Path(tmpdir) / 'test.vcf'
            create_test_vcf(vcf_path, num_samples=5, num_variants=100)
            
            # Use higher threshold to filter out more variants
            burden_df = calculate_burden_streaming(
                vcf_path,
                target_chromosomes=['chrM'],
                vaf_threshold=0.05,
                min_depth=50
            )
            
            # Should have fewer variants than with lower threshold
            lower_threshold_df = calculate_burden_streaming(
                vcf_path,
                target_chromosomes=['chrM'],
                vaf_threshold=0.01,
                min_depth=10
            )
            
            assert (burden_df['variant_count'] <= lower_threshold_df['variant_count']).all()

class TestDepthCategorization:
    def test_categorize_depths(self):
        depths = [10, 20, 30, 100, 150, 250, 300]
        result = _categorize_depths(depths)
        
        assert result['Low'] == 3   # 10, 20, 30
        assert result['Medium'] == 2 # 100, 150
        assert result['High'] == 2   # 250, 300

    def test_categorize_depths_empty(self):
        result = _categorize_depths([])
        assert result['Low'] == 0
        assert result['Medium'] == 0
        assert result['High'] == 0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
