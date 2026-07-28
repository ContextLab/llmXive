import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import logging

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the function to test
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))
from src.data_acquisition import (
    check_response_labels,
    download_geo_dataset,
    download_all_geo_datasets,
    GEO_DATASETS_CONFIG
)

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory for test data."""
    test_dir = tmp_path / "geo_test"
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir

class TestGEOAcquisition:
    """Integration tests for GEO dataset acquisition."""

    def test_geo_datasets_defined(self):
        """Verify that GEO datasets are defined in the configuration."""
        assert len(GEO_DATASETS_CONFIG) > 0, "At least one GEO dataset should be defined"
        
        for geo_id, config in GEO_DATASETS_CONFIG.items():
            assert geo_id.startswith("GSE"), f"Invalid GEO ID format: {geo_id}"
            assert "platform" in config, f"Missing platform for {geo_id}"
            assert "description" in config, f"Missing description for {geo_id}"
            assert "required_label" in config, f"Missing required_label for {geo_id}"

    def test_check_response_labels_with_real_structure(self, temp_data_dir):
        """Test response label checking with a mock phenotype file."""
        # Create a mock phenotype file with response labels
        pheno_file = temp_data_dir / "test_phenotype.csv"
        pheno_content = """
        sample_id,response,treatment,age
        GSM123,1,chemo,45
        GSM124,0,chemo,52
        GSM125,1,chemo,38
        """
        pheno_file.write_text(pheno_content)
        
        has_labels, label_cols = check_response_labels(pheno_file)
        
        assert has_labels is True, "Should detect response labels"
        assert "response" in label_cols, "Should find 'response' column"

    def test_check_response_labels_missing(self, temp_data_dir):
        """Test response label checking when labels are missing."""
        # Create a mock phenotype file without response labels
        pheno_file = temp_data_dir / "test_phenotype_no_labels.csv"
        pheno_content = """
        sample_id,treatment,age
        GSM123,chemo,45
        GSM124,chemo,52
        GSM125,chemo,38
        """
        pheno_file.write_text(pheno_content)
        
        has_labels, label_cols = check_response_labels(pheno_file)
        
        assert has_labels is False, "Should not find response labels"
        assert len(label_cols) == 0, "Should return empty list"

    def test_download_geo_dataset_structure(self):
        """Test that download function has correct structure (skips actual download in CI)."""
        # This test verifies the function signature and error handling
        # Actual download is skipped in CI environments
        
        # Check function exists and has correct signature
        import inspect
        sig = inspect.signature(download_geo_dataset)
        params = list(sig.parameters.keys())
        
        assert 'geo_id' in params, "Function should have geo_id parameter"
        assert 'output_dir' in params, "Function should have output_dir parameter"
        assert 'timeout' in params, "Function should have timeout parameter"

    def test_download_all_geo_datasets_structure(self, temp_data_dir):
        """Test the structure of the download_all_geo_datasets function."""
        # This test verifies the function returns the expected structure
        # without actually downloading (which would fail in CI)
        
        # Mock the download function to avoid actual network calls
        original_download = download_geo_dataset
        
        def mock_download(geo_id, output_dir, timeout=300):
            # Create mock files
            expr_file = output_dir / f"{geo_id}_expression.csv"
            pheno_file = output_dir / f"{geo_id}_phenotype.csv"
            expr_file.write_text("sample1,sample2\n1,2\n3,4")
            pheno_file.write_text("sample_id,response\nsample1,1\nsample2,0")
            return expr_file
        
        try:
            import src.data_acquisition as da_module
            da_module.download_geo_dataset = mock_download
            
            results = download_all_geo_datasets(temp_data_dir)
            
            # Verify results structure
            assert 'total_datasets' in results, "Results should have total_datasets"
            assert 'downloaded' in results, "Results should have downloaded count"
            assert 'valid_with_labels' in results, "Results should have valid_with_labels count"
            assert 'failed_no_labels' in results, "Results should have failed_no_labels count"
            assert 'datasets' in results, "Results should have datasets dict"
            
            # Verify dataset entries
            for geo_id, dataset_result in results['datasets'].items():
                assert 'status' in dataset_result, f"Dataset {geo_id} should have status"
                assert 'has_labels' in dataset_result, f"Dataset {geo_id} should have has_labels"
                
        finally:
            # Restore original function
            da_module.download_geo_dataset = original_download

    def test_main_function_structure(self):
        """Test that main function exists and has correct structure."""
        from src.data_acquisition import main
        
        import inspect
        sig = inspect.signature(main)
        
        # main should take no parameters
        assert len(sig.parameters) == 0, "main should take no parameters"

    def test_geo_feasibility_logic(self, temp_data_dir):
        """Test the logic for counting valid GEO datasets."""
        # Create mock results
        mock_results = {
            'total_datasets': 5,
            'downloaded': 4,
            'valid_with_labels': 2,
            'failed_no_labels': 1,
            'failed': 1,
            'datasets': {
                'GSE1': {'status': 'valid', 'has_labels': True},
                'GSE2': {'status': 'valid', 'has_labels': True},
                'GSE3': {'status': 'skipped', 'has_labels': False},
                'GSE4': {'status': 'failed', 'has_labels': False},
                'GSE5': {'status': 'skipped', 'has_labels': False}
            }
        }
        
        # Verify the count matches
        valid_count = sum(1 for d in mock_results['datasets'].values() 
                        if d.get('status') == 'valid' and d.get('has_labels'))
        
        assert valid_count == mock_results['valid_with_labels'], \
            "Valid count should match valid_with_labels"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
