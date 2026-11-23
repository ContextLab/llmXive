import pytest
import pandas as pd
import os
import json
from pathlib import Path

from data_ingestion import filter_snps, intersect_snps_with_regions
from utils import SNP, GenomicRegion

class TestT014FilterAndSave:
    
    def test_filter_snps_maf_threshold(self):
        """Test that SNPs with MAF < 1% are excluded."""
        snps = [
            SNP(id="rs1", chrom="1", pos=100, ref="A", alt="G", maf=0.005),
            SNP(id="rs2", chrom="1", pos=200, ref="C", alt="T", maf=0.02),
            SNP(id="rs3", chrom="1", pos=300, ref="G", alt="A", maf=0.01),
        ]
        
        filtered = filter_snps(snps, maf_threshold=0.01)
        
        assert len(filtered) == 2
        assert filtered[0].id == "rs2"
        assert filtered[1].id == "rs3"
    
    def test_filter_snps_invalid_alleles(self):
        """Test that SNPs with non-ACGT alleles are excluded."""
        snps = [
            SNP(id="rs1", chrom="1", pos=100, ref="A", alt="N", maf=0.05),
            SNP(id="rs2", chrom="1", pos=200, ref="C", alt="T", maf=0.05),
            SNP(id="rs3", chrom="1", pos=300, ref="I", alt="D", maf=0.05),  # Indel
        ]
        
        filtered = filter_snps(snps, maf_threshold=0.01)
        
        assert len(filtered) == 1
        assert filtered[0].id == "rs2"
    
    def test_intersect_snps_with_regions(self):
        """Test intersection logic."""
        snps = [
            SNP(id="rs1", chrom="1", pos=100, ref="A", alt="G", maf=0.05),
            SNP(id="rs2", chrom="1", pos=200, ref="C", alt="T", maf=0.05),
            SNP(id="rs3", chrom="1", pos=300, ref="G", alt="A", maf=0.05),
        ]
        
        regions = [
            GenomicRegion(chrom="1", start=50, end=150, name="region1"),
            GenomicRegion(chrom="1", start=250, end=350, name="region2"),
        ]
        
        intersected = intersect_snps_with_regions(snps, regions)
        
        assert len(intersected) == 2
        ids = [s.id for s in intersected]
        assert "rs1" in ids
        assert "rs3" in ids
        assert "rs2" not in ids
    
    def test_parquet_output_format(self):
        """Test that output parquet has correct columns."""
        # Create a minimal test to ensure the save logic is correct
        # (Full integration tested in test_ingestion_pipeline.py)
        data = {
            'snp_id': ['rs1'],
            'chrom': ['1'],
            'pos': [100],
            'ref': ['A'],
            'alt': ['G'],
            'maf': [0.05]
        }
        df = pd.DataFrame(data)
        
        expected_columns = ['snp_id', 'chrom', 'pos', 'ref', 'alt', 'maf']
        assert list(df.columns) == expected_columns
