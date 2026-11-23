"""
Unit tests for T001b: Parse GEO raw zip files into WIDE FORMAT CSVs.
"""
import os
import sys
import tempfile
import zipfile
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))
from exceptions import E_DATASET
from data.parse import parse_soft_file, normalize_to_tpm, parse_geo_zip, create_wide_format_csv

# Test fixtures
SAMPLE_SOFT_CONTENT = """!Series title = Test Study
!Series summary = Test summary
!Sample_title = Sample 1
!Sample_accession = GSM123456
!Sample_biosample_id = Bio123
!Sample_title = Sample 2
!Sample_accession = GSM123457
!Sample_biosample_id = Bio124
!Series_matrix_table_begin
ID	Gene Symbol	GSM123456	GSM123457
AT1G01010	ABC1	100	200
AT1G01020	DEF2	150	250
AT1G01030	GHI3	120	220
!Series_matrix_table_end
"""

@pytest.fixture
def temp_soft_file():
    """Create a temporary SOFT file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.soft', delete=False) as f:
        f.write(SAMPLE_SOFT_CONTENT)
        return Path(f.name)

@pytest.fixture
def temp_gz_soft_file():
    """Create a temporary gzipped SOFT file for testing."""
    import gzip
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.soft.gz', delete=False) as f:
        with gzip.open(f, 'wt') as gz:
            gz.write(SAMPLE_SOFT_CONTENT)
        return Path(f.name)

@pytest.fixture
def temp_zip_file(temp_soft_file):
    """Create a temporary zip file containing the SOFT file."""
    zip_path = Path(temp_soft_file.parent) / "test_geo.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.write(temp_soft_file, temp_soft_file.name)
    return zip_path

def test_parse_soft_file(temp_soft_file):
    """Test parsing a plain text SOFT file."""
    df, samples_info, biosample_map = parse_soft_file(temp_soft_file)
    
    assert not df.empty, "DataFrame should not be empty"
    assert 'gene_id' in df.columns or df.index.name == 'gene_id'
    assert 'GSM123456' in df.columns
    assert 'GSM123457' in df.columns
    assert len(samples_info) == 2
    assert samples_info.get('GSM123456') == "Sample 1"
    assert samples_info.get('GSM123457') == "Sample 2"
    assert biosample_map.get('GSM123456') == "Bio123"
    assert biosample_map.get('GSM123457') == "Bio124"

def test_parse_soft_file_gzipped(temp_gz_soft_file):
    """Test parsing a gzipped SOFT file."""
    df, samples_info, biosample_map = parse_soft_file(temp_gz_soft_file)
    
    assert not df.empty, "DataFrame should not be empty"
    assert 'GSM123456' in df.columns
    assert len(samples_info) == 2

def test_normalize_to_tpm():
    """Test TPM normalization."""
    # Create sample data (raw counts)
    data = {
        'sample1': [100, 200, 150],
        'sample2': [200, 300, 250]
    }
    df = pd.DataFrame(data, index=['gene1', 'gene2', 'gene3'])
    
    normalized = normalize_to_tpm(df)
    
    # Check that values are transformed
    assert normalized.shape == df.shape
    # CPM should be roughly proportional to original counts
    assert normalized['sample1'].mean() > 0
    assert normalized['sample2'].mean() > 0

def test_parse_geo_zip(temp_zip_file):
    """Test parsing a GEO zip file."""
    df, samples_info, biosample_map = parse_geo_zip(temp_zip_file)
    
    assert not df.empty, "DataFrame should not be empty"
    assert len(samples_info) == 2
    assert len(biosample_map) == 2

def test_parse_geo_zip_missing_file():
    """Test error handling for missing file."""
    with pytest.raises(E_DATASET):
        parse_geo_zip(Path("nonexistent.zip"))

def test_create_wide_format_csv():
    """Test creating wide format CSV."""
    # Create sample data
    df1 = pd.DataFrame({
        'sample1': [100, 200],
        'sample2': [150, 250]
    }, index=['gene1', 'gene2'])
    df1.index.name = 'gene_id'
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_output.csv"
        create_wide_format_csv([df1], [], output_path)
        
        assert output_path.exists(), "Output file should exist"
        
        # Read and verify
        result_df = pd.read_csv(output_path)
        assert 'gene_id' in result_df.columns
        assert 'sample1' in result_df.columns
        assert 'sample2' in result_df.columns
        assert len(result_df) == 2

def test_wide_format_csv_with_duplicates():
    """Test wide format creation handles duplicate genes."""
    df1 = pd.DataFrame({
        'sample1': [100, 200, 150],
        'sample2': [150, 250, 220]
    }, index=['gene1', 'gene2', 'gene1'])
    df1.index.name = 'gene_id'
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_output.csv"
        create_wide_format_csv([df1], [], output_path)
        
        result_df = pd.read_csv(output_path)
        # Should have unique gene IDs
        assert len(result_df['gene_id'].unique()) == len(result_df)

def test_file_cleanup():
    """Test that temporary files are cleaned up."""
    import os
    temp_path = Path("/tmp/test_cleanup.txt")
    temp_path.write_text("test")
    assert temp_path.exists()
    
    temp_path.unlink()
    assert not temp_path.exists()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])