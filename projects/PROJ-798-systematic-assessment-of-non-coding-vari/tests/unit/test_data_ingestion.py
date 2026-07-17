import pytest
import os
import tempfile
import gzip
from pathlib import Path
from unittest.mock import patch, MagicMock

from data_ingestion import filter_snps, MAF_THRESHOLD
from utils import SNP

# Mock MAF_THRESHOLD if not defined in config for testing
if 'MAF_THRESHOLD' not in globals():
    MAF_THRESHOLD = 0.01

def create_test_vcf(content_lines, filename="test.vcf"):
    """Helper to create a temporary VCF file."""
    fd, path = tempfile.mkstemp(suffix=".vcf")
    with os.fdopen(fd, 'w') as f:
        f.write("\n".join(content_lines))
    return path

def test_filter_snps_maf_exclusion():
    """Test that SNPs with MAF < 1% are excluded."""
    vcf_content = [
        "##fileformat=VCFv4.2",
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE1",
        "chr1\t100\trs1\tA\tG\t30\tPASS\tAF=0.005\tGT\t0/1", # MAF 0.5%
        "chr1\t200\trs2\tC\tT\t30\tPASS\tAF=0.05\tGT\t0/1",  # MAF 5%
    ]
    vcf_path = create_test_vcf(vcf_content)
    
    try:
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
            out_path = tmp.name
        
        filtered = filter_snps(vcf_path, out_path)
        
        # Should only contain rs2
        assert len(filtered) == 1
        assert filtered[0].snp_id == "rs2"
    finally:
        os.unlink(vcf_path)
        if os.path.exists(out_path):
            os.unlink(out_path)

def test_filter_snps_allele_exclusion():
    """Test that SNPs with non-ACGT alleles are excluded."""
    vcf_content = [
        "##fileformat=VCFv4.2",
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE1",
        "chr1\t100\trs1\tA\tN\t30\tPASS\tAF=0.05\tGT\t0/1", # Non-ACGT
        "chr1\t200\trs2\tG\tT\t30\tPASS\tAF=0.05\tGT\t0/1", # Valid
    ]
    vcf_path = create_test_vcf(vcf_content)
    
    try:
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
            out_path = tmp.name
        
        filtered = filter_snps(vcf_path, out_path)
        
        # Should only contain rs2
        assert len(filtered) == 1
        assert filtered[0].snp_id == "rs2"
    finally:
        os.unlink(vcf_path)
        if os.path.exists(out_path):
            os.unlink(out_path)

def test_filter_snps_indel_exclusion():
    """Test that indels are excluded."""
    vcf_content = [
        "##fileformat=VCFv4.2",
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE1",
        "chr1\t100\trs1\tA\tAT\t30\tPASS\tAF=0.05\tGT\t0/1", # Indel
        "chr1\t200\trs2\tC\tT\t30\tPASS\tAF=0.05\tGT\t0/1",  # SNP
    ]
    vcf_path = create_test_vcf(vcf_content)
    
    try:
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
            out_path = tmp.name
        
        filtered = filter_snps(vcf_path, out_path)
        
        # Should only contain rs2
        assert len(filtered) == 1
        assert filtered[0].snp_id == "rs2"
    finally:
        os.unlink(vcf_path)
        if os.path.exists(out_path):
            os.unlink(out_path)

def test_filter_snps_combined():
    """Test combined filtering logic."""
    vcf_content = [
        "##fileformat=VCFv4.2",
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE1",
        "chr1\t100\trs1\tA\tG\t30\tPASS\tAF=0.005\tGT\t0/1", # MAF fail
        "chr1\t200\trs2\tA\tN\t30\tPASS\tAF=0.05\tGT\t0/1", # Allele fail
        "chr1\t300\trs3\tA\tAT\t30\tPASS\tAF=0.05\tGT\t0/1", # Indel fail
        "chr1\t400\trs4\tC\tT\t30\tPASS\tAF=0.05\tGT\t0/1", # Pass
        "chr1\t500\trs5\tG\tA\t30\tPASS\tAF=0.02\tGT\t0/1", # Pass
    ]
    vcf_path = create_test_vcf(vcf_content)
    
    try:
        with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
            out_path = tmp.name
        
        filtered = filter_snps(vcf_path, out_path)
        
        assert len(filtered) == 2
        ids = [s.snp_id for s in filtered]
        assert "rs4" in ids
        assert "rs5" in ids
    finally:
        os.unlink(vcf_path)
        if os.path.exists(out_path):
            os.unlink(out_path)