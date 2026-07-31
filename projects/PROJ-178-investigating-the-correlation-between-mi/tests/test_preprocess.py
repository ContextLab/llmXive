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

from analysis.preprocess import (
    filter_variants,
    filter_vcf_file,
    calculate_burden_per_sample,
    calculate_depth_stratified_burden
)

def create_test_vcf(tmp_path: Path, sample_count: int = 3, variant_count: int = 5):
    """Create a minimal VCF file for testing."""
    vcf_file = tmp_path / "test.vcf"
    
    header = vcfpy.Header()
    header.add_line("#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSample1\tSample2\tSample3")
    header.add_line("##fileformat=VCFv4.2")
    header.add_line("##contig=<ID=chrM>")
    header.add_line("##FORMAT=<ID=AD,Number=R,Type=Integer>")
    header.add_line("##FORMAT=<ID=DP,Number=1,Type=Integer>")
    header.add_line("##FORMAT=<ID=GT,Number=1,Type=String>")
    header.add_line("##INFO=<ID=VAF,Number=1,Type=Float>")
    
    with vcfpy.Writer.from_path(str(vcf_file), header) as writer:
        for i in range(variant_count):
            # Create variants with different filters and depths
            filter_val = 'PASS' if i % 2 == 0 else 'LowQual'
            vaf_val = 0.02 if i % 3 == 0 else 0.005  # Some above 1%, some below
            dp_val = 60 if i % 2 == 0 else 40  # Some Medium/High, some Low
            
            ad_val = [50, 1] if i % 3 == 0 else [100, 1] # Ref, Alt
            if i % 3 == 0:
                vaf_val = ad_val[1] / sum(ad_val) # Ensure VAF matches AD
            
            record = vcfpy.Record(
                CHROM='chrM',
                POS=i + 100,
                ID=f'var{i}',
                REF='A',
                ALT=[vcfpy.Substitution('T')],
                QUAL=30.0,
                FILTER=filter_val,
                INFO={'VAF': vaf_val},
                FORMAT=['GT', 'AD', 'DP'],
                calls=[
                    vcfpy.Call(
                        sample_name=f'Sample{j}',
                        data={
                            'GT': '0/1',
                            'AD': ad_val,
                            'DP': dp_val
                        }
                    ) for j in range(sample_count)
                ]
            )
            writer.write_record(record)
    
    return vcf_file

class TestVariantFiltering:
    def test_filter_passes_chrM_pass(self):
        record = vcfpy.Record(CHROM='chrM', POS=1, ID='.', REF='A', ALT=['T'], QUAL=30, FILTER='PASS', INFO={}, FORMAT=[], calls=[])
        assert filter_variants(record) is True

    def test_filter_rejects_non_chrM(self):
        record = vcfpy.Record(CHROM='chr1', POS=1, ID='.', REF='A', ALT=['T'], QUAL=30, FILTER='PASS', INFO={}, FORMAT=[], calls=[])
        assert filter_variants(record) is False

    def test_filter_rejects_low_qual(self):
        record = vcfpy.Record(CHROM='chrM', POS=1, ID='.', REF='A', ALT=['T'], QUAL=30, FILTER='LowQual', INFO={}, FORMAT=[], calls=[])
        assert filter_variants(record) is False

class TestBurdenCalculation:
    def test_burden_calculation_with_threshold(self, tmp_path):
        # Create test VCF with known VAFs
        vcf_file = create_test_vcf(tmp_path, sample_count=2, variant_count=4)
        
        # 4 variants:
        # 0: PASS, VAF=0.02 (>= 0.01) -> Count
        # 1: LowQual -> Skip
        # 2: PASS, VAF=0.005 (< 0.01) -> Skip
        # 3: PASS, VAF=0.02 (>= 0.01) -> Count
        
        # Expected burden per sample: 2
        
        filtered_vcf = tmp_path / "filtered.vcf"
        from analysis.preprocess import filter_vcf_file
        filter_vcf_file(vcf_file, filtered_vcf)
        
        df = calculate_burden_per_sample(filtered_vcf, vaf_threshold=0.01)
        
        assert len(df) == 2
        assert all(df['burden_count'] == 2), f"Expected burden 2, got {df['burden_count'].tolist()}"

    def test_depth_stratified_burden(self, tmp_path):
        # Create test VCF with varying depths
        vcf_file = create_test_vcf(tmp_path, sample_count=1, variant_count=4)
        
        filtered_vcf = tmp_path / "filtered.vcf"
        from analysis.preprocess import filter_vcf_file
        filter_vcf_file(vcf_file, filtered_vcf)
        
        df = calculate_depth_stratified_burden(filtered_vcf, vaf_threshold=0.01)
        
        # We expect entries for Low, Medium, High based on the test data
        # Test data:
        # Var 0: DP=60 (Medium), VAF=0.02 -> Count in Medium
        # Var 1: Skipped (LowQual)
        # Var 2: Skipped (Low VAF)
        # Var 3: DP=40 (Low), VAF=0.02 -> Count in Low
        
        # So we expect 'Low' and 'Medium' bins to have counts > 0
        assert 'depth_bin' in df.columns
        assert 'burden_count' in df.columns
        
        low_count = df[(df['depth_bin'] == 'Low') & (df['burden_count'] > 0)]
        med_count = df[(df['depth_bin'] == 'Medium') & (df['burden_count'] > 0)]
        
        assert len(low_count) > 0, "Expected Low depth burden"
        assert len(med_count) > 0, "Expected Medium depth burden"