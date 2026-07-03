"""
Tests for the preprocessing module.

Tests variant filtering functionality:
- Filtering by chromosome (chrM only)
- Filtering by filter status (PASS only)
- Correct output file generation
"""

import os
import sys
import pytest
import tempfile
from pathlib import Path
import vcfpy
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.preprocess import filter_variants, filter_vcf_file, MITO_CHROMOSOME, PASS_FILTER


class TestVariantFiltering:
    """Test cases for variant filtering functionality."""
    
    @pytest.fixture
    def sample_vcf_header(self):
        """Create a minimal VCF header for testing."""
        header_lines = [
            vcfpy.HeaderLine('fileformat', 'VCFv4.2'),
            vcfpy.HeaderLine('source', 'test'),
            vcfpy.HeaderLine('reference', 'GRCh38'),
            vcfpy.SampleHeaderLine('SAMPLE1', 'GT'),
            vcfpy.HeaderLine('contig', 'chrM'),
            vcfpy.HeaderLine('contig', 'chr1'),
            vcfpy.FilterHeaderLine('PASS', 'All filters passed'),
            vcfpy.FilterHeaderLine('LowQual', 'Low quality'),
        ]
        return vcfpy.Header(header_lines)
    
    @pytest.fixture
    def sample_variants(self, sample_vcf_header):
        """Create sample variants for testing."""
        variants = []
        
        # Valid chrM PASS variant
        variants.append(vcfpy.Record(
            CHROM='chrM',
            POS=100,
            ID='.',
            REF='A',
            ALT=[vcfpy.Alt.from_string('T')],
            QUAL=30.0,
            FILTER=[PASS_FILTER],
            INFO={},
            FORMAT=['GT'],
            samples=[vcfpy.Sample('SAMPLE1', {'GT': '0/1'})]
        ))
        
        # Valid chrM PASS variant (second)
        variants.append(vcfpy.Record(
            CHROM='chrM',
            POS=200,
            ID='.',
            REF='C',
            ALT=[vcfpy.Alt.from_string('G')],
            QUAL=35.0,
            FILTER=[PASS_FILTER],
            INFO={},
            FORMAT=['GT'],
            samples=[vcfpy.Sample('SAMPLE1', {'GT': '0/1'})]
        ))
        
        # Invalid: chrM but LowQual filter
        variants.append(vcfpy.Record(
            CHROM='chrM',
            POS=300,
            ID='.',
            REF='G',
            ALT=[vcfpy.Alt.from_string('A')],
            QUAL=15.0,
            FILTER=['LowQual'],
            INFO={},
            FORMAT=['GT'],
            samples=[vcfpy.Sample('SAMPLE1', {'GT': '0/1'})]
        ))
        
        # Invalid: chr1 (not chrM) but PASS
        variants.append(vcfpy.Record(
            CHROM='chr1',
            POS=1000,
            ID='.',
            REF='T',
            ALT=[vcfpy.Alt.from_string('C')],
            QUAL=40.0,
            FILTER=[PASS_FILTER],
            INFO={},
            FORMAT=['GT'],
            samples=[vcfpy.Sample('SAMPLE1', {'GT': '0/1'})]
        ))
        
        # Invalid: chr1 and LowQual
        variants.append(vcfpy.Record(
            CHROM='chr1',
            POS=2000,
            ID='.',
            REF='A',
            ALT=[vcfpy.Alt.from_string('G')],
            QUAL=10.0,
            FILTER=['LowQual'],
            INFO={},
            FORMAT=['GT'],
            samples=[vcfpy.Sample('SAMPLE1', {'GT': '0/1'})]
        ))
        
        return variants
    
    def test_filter_variants_count(self, sample_vcf_header, sample_variants):
        """Test that only chrM PASS variants are counted."""
        with tempfile.NamedTemporaryFile(suffix='.vcf', delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        try:
            # Write sample variants to a temporary VCF
            with vcfpy.Writer(str(tmp_path), sample_vcf_header) as writer:
                for variant in sample_variants:
                    writer.write_record(variant)
            
            # Read back and filter
            with vcfpy.Reader.from_path(str(tmp_path)) as reader:
                output_path = tmp_path.parent / 'filtered.vcf'
                count = filter_variants(reader, output_path)
            
            # Should have 2 variants (chrM + PASS)
            assert count == 2, f"Expected 2 variants, got {count}"
            
            # Verify output file
            assert output_path.exists(), "Output VCF file was not created"
            
            # Count variants in output
            with vcfpy.Reader.from_path(str(output_path)) as reader:
                output_variants = list(reader)
            
            assert len(output_variants) == 2, f"Output should have 2 variants, got {len(output_variants)}"
            
            # Verify all are chrM
            for var in output_variants:
                assert var.CHROM == 'chrM', f"Variant chromosome should be chrM, got {var.CHROM}"
                assert PASS_FILTER in var.FILTER, f"Variant should have PASS filter, got {var.FILTER}"
                
        finally:
            # Cleanup
            if tmp_path.exists():
                tmp_path.unlink()
            output_path = tmp_path.parent / 'filtered.vcf'
            if output_path.exists():
                output_path.unlink()
    
    def test_filter_variants_content(self, sample_vcf_header, sample_variants):
        """Test that filtered variants contain correct positions."""
        with tempfile.NamedTemporaryFile(suffix='.vcf', delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        try:
            # Write sample variants
            with vcfpy.Writer(str(tmp_path), sample_vcf_header) as writer:
                for variant in sample_variants:
                    writer.write_record(variant)
            
            # Filter
            with vcfpy.Reader.from_path(str(tmp_path)) as reader:
                output_path = tmp_path.parent / 'filtered.vcf'
                filter_variants(reader, output_path)
            
            # Read output
            with vcfpy.Reader.from_path(str(output_path)) as reader:
                output_variants = list(reader)
            
            # Check positions (should be 100 and 200)
            positions = sorted([v.POS for v in output_variants])
            assert positions == [100, 200], f"Expected positions [100, 200], got {positions}"
                
        finally:
            # Cleanup
            if tmp_path.exists():
                tmp_path.unlink()
            output_path = tmp_path.parent / 'filtered.vcf'
            if output_path.exists():
                output_path.unlink()
    
    def test_filter_vcf_file_integration(self, sample_vcf_header, sample_variants):
        """Integration test for filter_vcf_file function."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            input_vcf = tmp_path / 'input.vcf'
            output_vcf = tmp_path / 'output.vcf'
            
            # Write input VCF
            with vcfpy.Writer(str(input_vcf), sample_vcf_header) as writer:
                for variant in sample_variants:
                    writer.write_record(variant)
            
            # Filter
            count = filter_vcf_file(input_vcf, output_vcf)
            
            # Verify
            assert count == 2, f"Expected 2 variants, got {count}"
            assert output_vcf.exists(), "Output file not created"
            
            # Verify content
            with vcfpy.Reader.from_path(str(output_vcf)) as reader:
                output_variants = list(reader)
            
            assert len(output_variants) == 2
            for var in output_variants:
                assert var.CHROM == 'chrM'
                assert PASS_FILTER in var.FILTER
    
    def test_file_not_found_error(self):
        """Test that FileNotFoundError is raised for missing input."""
        with pytest.raises(FileNotFoundError):
            filter_vcf_file(Path('/nonexistent/path.vcf'), Path('/output.vcf'))