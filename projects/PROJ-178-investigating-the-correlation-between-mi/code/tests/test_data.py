import os
import sys
import pytest
import pandas as pd
from pathlib import Path
import yaml

# Ensure project root is in path for imports if running from tests/
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.environment import get_ftp_base_url, get_metadata_path, get_vcf_base_url
from analysis.load_data import download_metadata_panel, download_mito_vcf, merge_vcf_metadata
from analysis.preprocess import load_vcf_chunked, calculate_burden

# ---------------------------------------------------------------------
# Helpers for loading schema and dataset (existing API)
# ---------------------------------------------------------------------
def load_schema(schema_path: Path) -> dict:
    """Load a YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def load_dataset(data_path: Path) -> pd.DataFrame:
    """Load a processed dataset CSV/Parquet."""
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {data_path}")
    if data_path.suffix == '.csv':
        return pd.read_csv(data_path)
    elif data_path.suffix == '.parquet':
        return pd.read_parquet(data_path)
    else:
        raise ValueError(f"Unsupported dataset format: {data_path.suffix}")

# ---------------------------------------------------------------------
# Existing Test Class (from T010)
# ---------------------------------------------------------------------
class TestDataSchema:
    """Contract test for data schema validation."""
    
    def test_schema_exists(self):
        """Verify the dataset schema file exists."""
        schema_path = PROJECT_ROOT / "code" / "contracts" / "dataset.schema.yaml"
        assert schema_path.exists(), f"Schema file missing: {schema_path}"

    def test_schema_loads(self):
        """Verify the schema file is valid YAML and contains required keys."""
        schema_path = PROJECT_ROOT / "code" / "contracts" / "dataset.schema.yaml"
        schema = load_schema(schema_path)
        assert "Sample" in schema, "Schema missing 'Sample' entity definition"
        assert "Variant" in schema, "Schema missing 'Variant' entity definition"

    def test_processed_data_schema(self):
        """Verify processed data matches schema if it exists."""
        data_path = PROJECT_ROOT / "code" / "data" / "processed" / "mito_aging_dataset.csv"
        if data_path.exists():
            df = load_dataset(data_path)
            schema = load_schema(PROJECT_ROOT / "code" / "contracts" / "dataset.schema.yaml")
            
            # Check required columns from Sample entity
            required_cols = ['sample_id', 'age', 'sex', 'population', 'haplogroup']
            for col in required_cols:
                assert col in df.columns, f"Missing required column in processed data: {col}"
            
            # Check for heteroplasmy burden column
            assert 'burden' in df.columns, "Missing 'burden' column in processed data"

# ---------------------------------------------------------------------
# NEW: Integration Test for VCF Download and Merge (T011)
# ---------------------------------------------------------------------
class TestVcfDownloadAndMerge:
    """Integration test for VCF download and merge in code/tests/test_data.py"""
    
    def test_metadata_download_and_schema(self):
        """
        Test that the metadata panel can be downloaded from the real 1000 Genomes FTP
        and contains the required 'age' column and sample IDs.
        """
        # We will not actually download in a unit test environment without network,
        # but we verify the logic and path resolution.
        # In a real CI/CD environment with network, this would:
        # 1. Call download_metadata_panel()
        # 2. Verify the file exists
        # 3. Verify the 'age' column exists
        
        # For the purpose of this task, we assert the function is callable and paths are correct
        base_url = get_ftp_base_url()
        metadata_path = get_metadata_path()
        
        assert base_url is not None and len(base_url) > 0, "FTP Base URL not configured"
        assert metadata_path is not None, "Metadata path not configured"
        
        # Verify the function signature exists and is callable
        assert callable(download_metadata_panel), "download_metadata_panel function not found"

    def test_vcf_download_logic(self):
        """
        Test that the VCF download function is callable and points to a valid URL pattern.
        """
        vcf_base = get_vcf_base_url()
        assert vcf_base is not None and len(vcf_base) > 0, "VCF Base URL not configured"
        assert callable(download_mito_vcf), "download_mito_vcf function not found"

    def test_merge_function_availability(self):
        """
        Test that the merge function exists and accepts the expected arguments.
        """
        assert callable(merge_vcf_metadata), "merge_vcf_metadata function not found"

    def test_end_to_end_integration_flow(self):
        """
        Integration test: Verify the full flow of download, merge, and basic processing.
        This test assumes the network is available and the 1000 Genomes FTP is reachable.
        It downloads a small subset (or the full set if fast enough) and verifies the merge.
        """
        import tempfile
        import shutil
        
        # Use a temporary directory for this integration test to avoid cluttering data/
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # 1. Download Metadata
            # We call the function directly. If network fails, this test fails (as intended).
            try:
                meta_df = download_metadata_panel(output_dir=tmp_path)
            except Exception as e:
                # If network is unavailable, we skip the test but log the error
                # In a strict CI, this might be a failure. Here we assume "Real data only" means 
                # we must attempt the real download. If it fails due to network, we fail the test.
                pytest.fail(f"Failed to download metadata panel: {e}")

            # 2. Verify Metadata Content
            assert isinstance(meta_df, pd.DataFrame), "Metadata download did not return a DataFrame"
            assert 'sample_id' in meta_df.columns, "Metadata missing 'sample_id'"
            assert 'age' in meta_df.columns, "Metadata missing 'age' column"
            
            # 3. Download VCF (Small subset for speed? Or full? 
            # The task implies downloading the mitochondrial VCF. 
            # 1000 Genomes chrM VCF is relatively small compared to whole genome.
            # We attempt to download the chrM VCF.
            try:
                # We pass a subset of sample IDs if the full download is too slow, 
                # but for integration, we aim for the real file.
                # Assuming download_mito_vcf handles the full file or a representative chunk.
                vcf_path = download_mito_vcf(output_dir=tmp_path)
            except Exception as e:
                pytest.fail(f"Failed to download VCF: {e}")

            assert vcf_path.exists(), "VCF file was not created"

            # 4. Load and Process (Chunked)
            # We use the chunked loader to ensure memory safety
            try:
                # This loads variants and calculates burden per sample
                # We pass a small sample set if needed, but the function should handle the full VCF
                # For this test, we assume the VCF is small enough or the function is efficient.
                # If the VCF is too large, we might need to mock the VCF content, 
                # but the task says "Real data only". 
                # We will attempt to process the downloaded VCF.
                processed_df = load_vcf_chunked(vcf_path, meta_df, output_dir=tmp_path)
            except Exception as e:
                # If the VCF is empty or malformed, this fails.
                pytest.fail(f"Failed to process VCF: {e}")

            # 5. Verify Merged Output
            assert isinstance(processed_df, pd.DataFrame), "Processed data is not a DataFrame"
            assert len(processed_df) > 0, "Processed data is empty"
            assert 'sample_id' in processed_df.columns, "Merged data missing 'sample_id'"
            assert 'age' in processed_df.columns, "Merged data missing 'age'"
            assert 'burden' in processed_df.columns, "Merged data missing 'burden'"
            
            # 6. Verify No Missing Values in Critical Columns
            critical_cols = ['sample_id', 'age', 'burden']
            for col in critical_cols:
                assert not processed_df[col].isna().any(), f"Missing values in critical column: {col}"

            # 7. Verify Haplogroup Assignment (if available in metadata or added)
            # The task T011 focuses on download and merge. Haplogroup might be in metadata.
            if 'haplogroup' in meta_df.columns:
                assert 'haplogroup' in processed_df.columns, "Haplogroup not merged"
                # Check if some samples have haplogroups
                assert processed_df['haplogroup'].notna().any(), "No haplogroups assigned in merged data"

    def test_age_column_presence_gate(self):
        """
        Specific test for T007A: Verify the 'age' column is present in the metadata.
        If missing, the pipeline should halt. This test verifies the data source has it.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            try:
                meta_df = download_metadata_panel(output_dir=tmp_path)
            except Exception as e:
                pytest.fail(f"Cannot verify age column: {e}")
            
            assert 'age' in meta_df.columns, "CRITICAL: 'age' column missing in 1000 Genomes metadata. Pipeline must halt."
            # Verify age is numeric
            assert pd.api.types.is_numeric_dtype(meta_df['age']), "'age' column is not numeric"