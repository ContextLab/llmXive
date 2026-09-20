import pytest
import pandas as pd
import gzip
import tempfile
from pathlib import Path
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data_ingestion import filter_snps, parse_vcf_line
from utils import SNP

def test_parse_vcf_line():
    """Test parsing of a standard VCF line."""
    line = 'chr1\t100\trs123\tA\tG\t.\tPASS\tAF=0.05;AC=10;AN=200'
    snp = parse_vcf_line(line)
    
    assert snp is not None
    assert snp.chrom == "chr1"
    assert snp.pos == 100
    assert snp.id == "rs123"
    assert snp.ref == "A"
    assert snp.alt == "G"
    assert snp.info['AF'] == '0.05'

def test_parse_vcf_line_invalid_alleles():
    """Test parsing of a line with invalid alleles (N)."""
    line = 'chr1\t100\trs456\tN\tG\t.\tPASS\tAF=0.05'
    snp = parse_vcf_line(line)
    assert snp is not None
    # The parser should still return the object, filtering happens later
    assert snp.ref == "N"

def test_filter_snps_maf_threshold(tmp_path):
    """Test that filter_snps correctly excludes SNPs with MAF < threshold."""
    # Create a mock VCF
    vcf_content = """##fileformat=VCFv4.2
    #CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
    chr1\t100\trs1\tA\tG\t.\tPASS\tAF=0.05
    chr1\t200\trs2\tC\tT\t.\tPASS\tAF=0.005
    chr1\t300\trs3\tG\tA\t.\tPASS\tAF=0.10
    """
    
    vcf_file = tmp_path / "test.vcf"
    with gzip.open(vcf_file, 'wt') as f:
        f.write(vcf_content)
    
    output_file = tmp_path / "output.parquet"
    
    # Filter with MAF > 0.01 (1%)
    df = filter_snps(vcf_file, output_file, min_maf=0.01)
    
    assert len(df) == 2
    assert set(df['snp_id']) == {'rs1', 'rs3'}
    assert all(df['maf'] >= 0.01)

def test_filter_snps_invalid_alleles(tmp_path):
    """Test that filter_snps excludes non-ACGT alleles."""
    vcf_content = """##fileformat=VCFv4.2
    #CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
    chr1\t100\trs1\tA\tG\t.\tPASS\tAF=0.05
    chr1\t200\trs2\tN\tT\t.\tPASS\tAF=0.05
    chr1\t300\trs3\tC\tD\t.\tPASS\tAF=0.05
    """
    
    vcf_file = tmp_path / "test.vcf"
    with gzip.open(vcf_file, 'wt') as f:
        f.write(vcf_content)
    
    output_file = tmp_path / "output.parquet"
    
    df = filter_snps(vcf_file, output_file, min_maf=0.01)
    
    # Only rs1 should remain (valid ACGT alleles)
    assert len(df) == 1
    assert df.iloc[0]['snp_id'] == 'rs1'

def test_filter_snps_empty_output(tmp_path):
    """Test behavior when no SNPs pass filtering."""
    vcf_content = """##fileformat=VCFv4.2
    #CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
    chr1\t100\trs1\tA\tG\t.\tPASS\tAF=0.0001
    """
    
    vcf_file = tmp_path / "test.vcf"
    with gzip.open(vcf_file, 'wt') as f:
        f.write(vcf_content)
    
    output_file = tmp_path / "output.parquet"
    
    df = filter_snps(vcf_file, output_file, min_maf=0.01)
    
    assert len(df) == 0
    assert os.path.exists(output_file)
