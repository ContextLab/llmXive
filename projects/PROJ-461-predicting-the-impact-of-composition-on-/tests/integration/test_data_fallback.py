"""
Integration test for download fallback logic (T011).

This test verifies that when network failures occur during data fetching
(simulated via mocking), the system correctly triggers the fallback to
synthetic data generation as defined in T013-ORCHESTRATE.

Dependencies:
- T013-ORCHESTRATE: Must have implemented the orchestration logic that
  checks for network failures and row counts to decide on synthetic fallback.
- code/data/download.py: Must implement check_and_fallback logic.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the orchestration and data generation logic
# Note: We are testing the integration of the fallback logic.
# The actual implementation of check_and_fallback is expected to be in code/data/download.py
# based on the API surface provided.
try:
    from code.data.download import check_and_fallback, generate_synthetic_data
except ImportError:
    # Fallback for execution environment where code structure might differ slightly
    # but the logic must exist. If this import fails, the test environment is invalid.
    pytest.fail("Required module code.data.download not found. Ensure T012/T013 are implemented.")


class TestDownloadFallbackLogic:
    """Tests for the fallback mechanism when real data sources are unavailable."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test artifacts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def mock_config(self, temp_dir):
        """Create a mock configuration pointing to the temp directory."""
        class MockConfig:
            data_dir = temp_dir
            seed = 42
        return MockConfig()

    def test_fallback_triggered_on_network_failure(self, temp_dir, mock_config):
        """
        Test that synthetic data is generated when network fetches fail.

        Scenario:
        1. Mock requests to Zenodo and Materials Cloud to raise exceptions.
        2. Call the orchestration/fallback logic.
        3. Verify that synthetic_data.csv is created.
        4. Verify that validation_log.json indicates 'SYNTHETIC_REQUIRED'.
        """
        # Ensure clean state
        raw_data_path = temp_dir / "raw_data.csv"
        clean_data_path = temp_dir / "clean_data.csv"
        synth_data_path = temp_dir / "synthetic_data.csv"
        log_path = temp_dir / "validation_log.json"

        if raw_data_path.exists(): raw_data_path.unlink()
        if clean_data_path.exists(): clean_data_path.unlink()
        if synth_data_path.exists(): synth_data_path.unlink()
        if log_path.exists(): log_path.unlink()

        # Mock the download functions to simulate failure
        # We assume check_and_fallback calls internal download logic or relies on
        # the state of raw_data.csv/clean_data.csv.
        # Based on T013-ORCHESTRATE description: "Check if *both* sources failed OR if clean_data.csv has < 50 rows."
        
        # Simulate the state where T012 and T014 failed to produce data
        # by ensuring raw_data.csv and clean_data.csv do not exist or are empty
        # and mocking the network calls if check_and_fallback attempts them.
        
        # However, the task description for T011 says: "Mock network failures to verify fallback".
        # This implies the test should trigger the network failure path within the orchestration logic.

        with patch('code.data.download.get_element_density') as mock_get_density, \
             patch('code.data.download.linear_mixing_rule') as mock_linear_rule:
            
            # Simulate network failure
            mock_get_density.side_effect = ConnectionError("Network unreachable")
            mock_linear_rule.side_effect = ConnectionError("Network unreachable")

            # We need to simulate the state where the primary/secondary sources fail.
            # Since check_and_fallback is the entry point for the logic in T013-ORCHESTRATE,
            # we call it. It should detect the lack of data or failure and trigger generation.
            
            # Note: The implementation of check_and_fallback must handle the logic:
            # 1. Try to fetch (mocked to fail)
            # 2. If fail, check if clean_data.csv exists and has >= 50 rows.
            # 3. If not, generate synthetic.
            
            # For this test, we assume check_and_fallback orchestrates the whole flow
            # or is called after the initial fetch attempts.
            # Given the API surface, check_and_fallback is the function to test.
            
            # To strictly test the "Network Failure -> Fallback" path:
            # We mock the download functions inside check_and_fallback or ensure
            # the state passed to it indicates failure.
            
            # Let's assume check_and_fallback attempts to fetch if raw_data.csv is missing.
            # We mock the fetch functions to raise errors.
            
            # We need to patch the specific functions that check_and_fallback uses to fetch data.
            # Based on T012, download.py uses requests.
            # Let's patch the main fetch logic.
            
            with patch('code.data.download.requests.get') as mock_requests_get:
                mock_requests_get.side_effect = ConnectionError("Simulated Network Failure")
                
                # Call the orchestration function
                # Note: We need to ensure the function signature matches.
                # If check_and_fallback expects specific paths, we pass them.
                try:
                    result = check_and_fallback(
                        raw_data_path=raw_data_path,
                        clean_data_path=clean_data_path,
                        synth_data_path=synth_data_path,
                        log_path=log_path,
                        seed=mock_config.seed
                    )
                except Exception as e:
                    # If the implementation doesn't catch the error and fallback, it fails.
                    # But the requirement is that it *does* fallback.
                    # If it raises, the test fails (verdict: failed).
                    # We expect it to return True or similar if fallback succeeded.
                    pytest.fail(f"Fallback logic did not handle network failure: {e}")

                # Assertions
                assert synth_data_path.exists(), "Synthetic data file was not created after network failure."
                
                # Verify content of synthetic data
                import pandas as pd
                df = pd.read_csv(synth_data_path)
                assert len(df) >= 100, f"Synthetic data has {len(df)} rows, expected >= 100."
                assert "composition" in df.columns, "Missing 'composition' column in synthetic data."
                assert "density" in df.columns, "Missing 'density' column in synthetic data."

                # Verify validation log
                assert log_path.exists(), "Validation log was not created."
                with open(log_path, 'r') as f:
                    log_data = json.load(f)
                
                assert log_data.get("status") == "SYNTHETIC_REQUIRED", \
                    f"Expected status 'SYNTHETIC_REQUIRED', got {log_data.get('status')}"
                assert log_data.get("source") == "synthetic", \
                    f"Expected source 'synthetic', got {log_data.get('source')}"

    def test_no_fallback_when_clean_data_sufficient(self, temp_dir, mock_config):
        """
        Test that synthetic data is NOT generated when clean_data.csv has >= 50 rows.
        
        This verifies the condition in T013-ORCHESTRATE: "if clean_data.csv has < 50 rows".
        """
        raw_data_path = temp_dir / "raw_data.csv"
        clean_data_path = temp_dir / "clean_data.csv"
        synth_data_path = temp_dir / "synthetic_data.csv"
        log_path = temp_dir / "validation_log.json"

        # Create a valid clean_data.csv with 50+ rows
        import pandas as pd
        data = {
            "composition": [f"{{'Fe': 0.5, 'Zr': 0.5}}" for _ in range(60)],
            "density": [5.0 + i * 0.1 for i in range(60)]
        }
        df = pd.DataFrame(data)
        df.to_csv(clean_data_path, index=False)

        # Mock network failure again to ensure it doesn't trigger fallback
        with patch('code.data.download.requests.get') as mock_requests_get:
            mock_requests_get.side_effect = ConnectionError("Simulated Network Failure")
            
            result = check_and_fallback(
                raw_data_path=raw_data_path,
                clean_data_path=clean_data_path,
                synth_data_path=synth_data_path,
                log_path=log_path,
                seed=mock_config.seed
            )

        # Assertions
        assert not synth_data_path.exists(), "Synthetic data should not be created when clean data is sufficient."
        
        assert log_path.exists()
        with open(log_path, 'r') as f:
            log_data = json.load(f)
        
        assert log_data.get("status") == "REAL_DATA_AVAILABLE", \
            f"Expected status 'REAL_DATA_AVAILABLE', got {log_data.get('status')}"

    def test_fallback_triggered_when_clean_data_insufficient(self, temp_dir, mock_config):
        """
        Test that synthetic data IS generated when clean_data.csv has < 50 rows.
        """
        raw_data_path = temp_dir / "raw_data.csv"
        clean_data_path = temp_dir / "clean_data.csv"
        synth_data_path = temp_dir / "synthetic_data.csv"
        log_path = temp_dir / "validation_log.json"

        # Create a clean_data.csv with only 10 rows
        import pandas as pd
        data = {
            "composition": [f"{{'Fe': 0.5, 'Zr': 0.5}}" for _ in range(10)],
            "density": [5.0 + i * 0.1 for i in range(10)]
        }
        df = pd.DataFrame(data)
        df.to_csv(clean_data_path, index=False)

        # Mock network failure
        with patch('code.data.download.requests.get') as mock_requests_get:
            mock_requests_get.side_effect = ConnectionError("Simulated Network Failure")
            
            result = check_and_fallback(
                raw_data_path=raw_data_path,
                clean_data_path=clean_data_path,
                synth_data_path=synth_data_path,
                log_path=log_path,
                seed=mock_config.seed
            )

        # Assertions
        assert synth_data_path.exists(), "Synthetic data should be created when clean data is insufficient (< 50 rows)."
        
        import pandas as pd
        df_synth = pd.read_csv(synth_data_path)
        assert len(df_synth) >= 100, f"Synthetic data has {len(df_synth)} rows, expected >= 100."

        assert log_path.exists()
        with open(log_path, 'r') as f:
            log_data = json.load(f)
        
        assert log_data.get("status") == "SYNTHETIC_REQUIRED"