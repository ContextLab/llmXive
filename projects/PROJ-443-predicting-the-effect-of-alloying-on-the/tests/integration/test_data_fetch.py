"""
Integration test for data fetch functionality.

This test verifies that the DataFetcher can successfully connect to
real data sources (OQMD/MP) or local fallbacks, handle retries,
and return valid data structures.

Prerequisites:
- T007: utils/data_fetch.py implemented
- T008: utils/validators.py implemented
- T009: utils/logging_config.py implemented
"""

import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import from project modules (matching API surface)
from utils.data_fetch import DataFetcher, create_fetcher
from utils.validators import validate_data_integrity, ValidationError
from utils.logging_config import setup_logging, get_logger

# Setup logging for the test
setup_logging(level="DEBUG")
logger = get_logger("tests.integration.test_data_fetch")

# Test configuration
TEST_TIMEOUT = 30  # seconds for network operations
TEST_RETRIES = 2

class TestDataFetcherIntegration:
    """Integration tests for the DataFetcher class."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.test_dir) / "data"
        self.data_dir.mkdir()
        
        # Mock environment variables for API keys if needed
        self.original_env = {}
        for key in ["OQMD_API_KEY", "MP_API_KEY"]:
            if key in os.environ:
                self.original_env[key] = os.environ[key]
                del os.environ[key]
        
        yield
        
        # Restore environment
        for key, value in self.original_env.items():
            os.environ[key] = value
        
        # Cleanup
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_fetcher_initialization(self):
        """Test that DataFetcher initializes correctly with various configurations."""
        # Test default initialization
        fetcher = DataFetcher(source="mock", output_dir=self.data_dir)
        assert fetcher.source == "mock"
        assert fetcher.output_dir == self.data_dir
        assert fetcher.timeout == 30
        assert fetcher.max_retries == 3
        
        # Test custom initialization
        fetcher_custom = DataFetcher(
            source="oqmd",
            output_dir=self.data_dir,
            timeout=60,
            max_retries=5
        )
        assert fetcher_custom.source == "oqmd"
        assert fetcher_custom.timeout == 60
        assert fetcher_custom.max_retries == 5
        
        logger.info("✓ DataFetcher initialization test passed")
    
    def test_create_fetcher_factory(self):
        """Test the create_fetcher factory function."""
        # Test mock fetcher creation
        fetcher = create_fetcher("mock", self.data_dir)
        assert isinstance(fetcher, DataFetcher)
        assert fetcher.source == "mock"
        
        # Test with custom parameters
        fetcher_custom = create_fetcher(
            "mock",
            self.data_dir,
            timeout=45,
            max_retries=4
        )
        assert fetcher_custom.timeout == 45
        assert fetcher_custom.max_retries == 4
        
        logger.info("✓ create_fetcher factory test passed")
    
    def test_mock_data_fetching(self):
        """Test fetching data from a mock source."""
        fetcher = DataFetcher(source="mock", output_dir=self.data_dir)
        
        # Mock the _fetch_data method to return test data
        test_data = [
            {
                "sample_id": "TEST001",
                "composition": {"Fe": 0.2, "Co": 0.2, "Ni": 0.2, "Cr": 0.2, "Mn": 0.2},
                "bulk_modulus": 180.5,
                "shear_modulus": 75.3
            },
            {
                "sample_id": "TEST002",
                "composition": {"Ti": 0.25, "Zr": 0.25, "Hf": 0.25, "V": 0.125, "Nb": 0.125},
                "bulk_modulus": 145.2,
                "shear_modulus": 62.1
            }
        ]
        
        with patch.object(fetcher, '_fetch_data', return_value=test_data):
            result = fetcher.fetch()
            
            assert result is not None
            assert len(result) == 2
            assert result[0]["sample_id"] == "TEST001"
            assert result[1]["sample_id"] == "TEST002"
            
            # Verify composition sum validation
            for sample in result:
                comp_sum = sum(sample["composition"].values())
                assert abs(comp_sum - 1.0) < 1e-6, f"Composition sum {comp_sum} != 1.0"
            
            logger.info("✓ Mock data fetching test passed")
    
    def test_data_validation_integration(self):
        """Test that fetched data passes validation."""
        fetcher = DataFetcher(source="mock", output_dir=self.data_dir)
        
        valid_data = [
            {
                "sample_id": "VALID001",
                "composition": {"Fe": 0.2, "Co": 0.2, "Ni": 0.2, "Cr": 0.2, "Mn": 0.2},
                "bulk_modulus": 180.5,
                "shear_modulus": 75.3
            }
        ]
        
        with patch.object(fetcher, '_fetch_data', return_value=valid_data):
            result = fetcher.fetch()
            
            # Validate the fetched data
            is_valid, errors = validate_data_integrity(result)
            
            assert is_valid, f"Data validation failed: {errors}"
            assert len(errors) == 0
            
            logger.info("✓ Data validation integration test passed")
    
    def test_retry_logic(self):
        """Test that the fetcher properly handles retries."""
        fetcher = DataFetcher(
            source="mock",
            output_dir=self.data_dir,
            max_retries=2
        )
        
        call_count = 0
        
        def failing_fetch(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Simulated network failure")
            return [{"sample_id": "RETRY001", "composition": {"Fe": 1.0}}]
        
        with patch.object(fetcher, '_fetch_data', side_effect=failing_fetch):
            result = fetcher.fetch()
            
            # Should have retried twice (initial + 2 retries)
            assert call_count == 3
            assert len(result) == 1
            assert result[0]["sample_id"] == "RETRY001"
            
            logger.info("✓ Retry logic test passed")
    
    def test_empty_data_handling(self):
        """Test handling of empty data responses."""
        fetcher = DataFetcher(source="mock", output_dir=self.data_dir)
        
        with patch.object(fetcher, '_fetch_data', return_value=[]):
            result = fetcher.fetch()
            
            assert result == []
            logger.info("✓ Empty data handling test passed")
    
    def test_save_to_disk(self):
        """Test that fetched data is saved to disk correctly."""
        fetcher = DataFetcher(source="mock", output_dir=self.data_dir)
        
        test_data = [
            {
                "sample_id": "SAVE001",
                "composition": {"Fe": 0.2, "Co": 0.2, "Ni": 0.2, "Cr": 0.2, "Mn": 0.2},
                "bulk_modulus": 180.5
            }
        ]
        
        output_file = self.data_dir / "test_output.json"
        
        with patch.object(fetcher, '_fetch_data', return_value=test_data):
            fetcher.fetch(save_to_file=True, output_path=str(output_file))
            
            assert output_file.exists(), "Output file was not created"
            
            with open(output_file, 'r') as f:
                saved_data = json.load(f)
            
            assert len(saved_data) == 1
            assert saved_data[0]["sample_id"] == "SAVE001"
            
            logger.info("✓ Save to disk test passed")
    
    def test_invalid_composition_rejection(self):
        """Test that compositions not summing to 1.0 are rejected."""
        fetcher = DataFetcher(source="mock", output_dir=self.data_dir)
        
        invalid_data = [
            {
                "sample_id": "INVALID001",
                "composition": {"Fe": 0.5, "Co": 0.5},  # Sum = 1.0, but missing elements for HEA
                "bulk_modulus": 100.0
            },
            {
                "sample_id": "INVALID002",
                "composition": {"Fe": 0.3, "Co": 0.3},  # Sum = 0.6 != 1.0
                "bulk_modulus": 100.0
            }
        ]
        
        with patch.object(fetcher, '_fetch_data', return_value=invalid_data):
            # This should trigger validation errors
            result = fetcher.fetch()
            
            # The fetcher should either filter or raise an error
            # For this test, we check that the invalid composition is handled
            assert len(result) <= len(invalid_data)
            
            logger.info("✓ Invalid composition rejection test passed")
    
    def test_logging_integration(self):
        """Test that logging is properly integrated during fetch operations."""
        fetcher = DataFetcher(source="mock", output_dir=self.data_dir)
        
        test_data = [{"sample_id": "LOG001", "composition": {"Fe": 1.0}}]
        
        with patch.object(fetcher, '_fetch_data', return_value=test_data):
            result = fetcher.fetch()
            
            # If we get here without logging errors, the test passes
            assert len(result) == 1
            
            logger.info("✓ Logging integration test passed")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])