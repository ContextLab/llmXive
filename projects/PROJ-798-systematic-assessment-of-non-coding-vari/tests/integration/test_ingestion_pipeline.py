import pytest
import pandas as pd
import gzip
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data_ingestion import filter_snps, log_source_lineage
from utils import calculate_file_checksum

def test_full_ingestion_flow(tmp_path):
    """
    Integration test:
    1. Create a synthetic VCF with mixed valid/invalid SNPs.
    2. Run filter_snps.
    3. Verify output contains only valid SNPs with MAF > 1%.
    4. Verify source logging works.
    """
    # Setup synthetic data
    vcf_content = """##fileformat=VCFv4.2
    ##INFO=<ID=AF,Number=1,Type=Float,Description="Allele Frequency">
    #CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
    chr1\t100\trs100\tA\tG\t.\tPASS\tAF=0.05
    chr1\t200\trs200\tC\tT\t.\tPASS\tAF=0.005
    chr1\t300\trs300\tG\tA\t.\tPASS\tAF=0.15
    chr1\t400\trs400\tN\tT\t.\tPASS\tAF=0.05
    chr1\t500\trs500\tA\tC\t.\tPASS\tAF=0.02
    """
    
    vcf_file = tmp_path / "input.vcf.gz"
    with gzip.open(vcf_file, 'wt') as f:
        f.write(vcf_content)
    
    output_file = tmp_path / "filtered.parquet"
    log_file = tmp_path / "source_log.txt"
    
    # Run filter
    df = filter_snps(vcf_file, output_file, min_maf=0.01)
    
    # Assertions
    assert output_file.exists()
    assert len(df) == 3  # rs100, rs300, rs500
    assert set(df['snp_id']) == {'rs100', 'rs300', 'rs500'}
    
    # Verify checksum calculation works
    checksum = calculate_file_checksum(vcf_file)
    assert len(checksum) == 64  # SHA256 length
    
    # Test logging
    log_source_lineage("TestSource", vcf_file.name, checksum)
    assert log_file.exists()
    
    with open(log_file, 'r') as f:
        content = f.read()
    assert "TestSource" in content
    assert vcf_file.name in content

def test_overlap_logic_synthetic(tmp_path):
    """
    Test that the filtering logic correctly handles the overlap of criteria:
    - MAF > 1%
    - Valid alleles (ACGT)
    
    This simulates the logic that would be used when intersecting with regulatory regions,
    ensuring we only keep valid SNPs before the BED overlap step.
    """
    vcf_content = """##fileformat=VCFv4.2
    #CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
    chr1\t100\trs_valid_high_maf\tA\tG\t.\tPASS\tAF=0.20
    chr1\t101\trs_valid_low_maf\tC\tT\t.\tPASS\tAF=0.001
    chr1\t102\trs_invalid_allele\tG\tN\t.\tPASS\tAF=0.20
    chr1\t103\trs_invalid_both\tA\tC\t.\tPASS\tAF=0.001
    """
    
    vcf_file = tmp_path / "test.vcf.gz"
    with gzip.open(vcf_file, 'wt') as f:
        f.write(vcf_content)
    
    output_file = tmp_path / "result.parquet"
    df = filter_snps(vcf_file, output_file, min_maf=0.01)
    
    # Expected: Only rs_valid_high_maf
    assert len(df) == 1
    assert df.iloc[0]['snp_id'] == 'rs_valid_high_maf'
    assert df.iloc[0]['maf'] == 0.20
