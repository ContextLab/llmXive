"""
Integration test for single-subject pipeline (US1).

This test verifies that the full pipeline (structural + functional)
can process a single subject's data end-to-end and produce valid
output metrics.

It runs the actual pipeline logic against real HCP data (or a single
subject subset if full cohort is too large) and asserts that:
1. Structural metrics (global efficiency, clustering, modularity) are computed.
2. Dynamic metrics (dwell time, visited states) are computed.
3. Output files are created in the expected locations.
4. All metric values are non-null and within plausible ranges.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from config import ensure_directories, get_config_dict
from preprocess.structural import process_subject_structural_metrics, run_structural_pipeline
from preprocess.functional import run_functional_pipeline, calculate_dynamic_metrics
from preprocess.loader import load_hcp_fmri, load_hcp_dmri
from main import log_subject_exclusion, save_exclusion_log, get_exclusion_log_path
from utils.cpu_optimization import set_random_seed

# Configuration
SET_RANDOM_SEED = 42
TEST_SUBJECT_ID = "100307"  # Example HCP subject ID

class TestSingleSubjectPipeline:
    """Integration tests for single subject processing."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up test environment and clean up after."""
        set_random_seed(SET_RANDOM_SEED)
        config = get_config_dict()
        ensure_directories()

        # Store original paths to restore later
        self.original_data_dir = config.get('DATA_DIR', 'data')
        self.original_processed_dir = config.get('PROCESSED_DIR', 'data/processed')
        self.original_logs_dir = config.get('LOGS_DIR', 'data/logs')

        # Create temporary directories for this test
        self.test_dir = tempfile.mkdtemp()
        test_data_dir = os.path.join(self.test_dir, 'data')
        test_processed_dir = os.path.join(test_data_dir, 'processed')
        test_logs_dir = os.path.join(test_data_dir, 'logs')

        os.makedirs(test_processed_dir, exist_ok=True)
        os.makedirs(test_logs_dir, exist_ok=True)

        # Temporarily override config paths
        os.environ['DATA_DIR'] = test_data_dir
        os.environ['PROCESSED_DIR'] = test_processed_dir
        os.environ['LOGS_DIR'] = test_logs_dir

        yield

        # Cleanup
        shutil.rmtree(self.test_dir, ignore_errors=True)
        # Restore original environment
        if 'DATA_DIR' in os.environ:
            del os.environ['DATA_DIR']
        if 'PROCESSED_DIR' in os.environ:
            del os.environ['PROCESSED_DIR']
        if 'LOGS_DIR' in os.environ:
            del os.environ['LOGS_DIR']

    def test_subject_structural_metrics(self):
        """Test structural metric calculation for a single subject."""
        # Try to load a single subject's dMRI data
        # If real data is not available, we expect the loader to fail loudly
        try:
            # Attempt to load real data - this will raise an error if data is not found
            fmri_data = load_hcp_fmri(subject_ids=[TEST_SUBJECT_ID])
            dmri_data = load_hcp_dmri(subject_ids=[TEST_SUBJECT_ID])
        except Exception as e:
            pytest.skip(f"Real HCP data not available for subject {TEST_SUBJECT_ID}: {str(e)}")

        # Process structural metrics
        structural_result = process_subject_structural_metrics(
            subject_id=TEST_SUBJECT_ID,
            dmri_data=dmri_data
        )

        # Verify structural metrics are computed
        assert structural_result is not None, "Structural metrics calculation returned None"
        assert 'global_efficiency' in structural_result, "Missing global_efficiency metric"
        assert 'average_clustering' in structural_result, "Missing average_clustering metric"
        assert 'modularity' in structural_result, "Missing modularity metric"

        # Verify metrics are non-null and within plausible ranges
        assert structural_result['global_efficiency'] is not None, "global_efficiency is None"
        assert structural_result['average_clustering'] is not None, "average_clustering is None"
        assert structural_result['modularity'] is not None, "modularity is None"

        # Check plausible ranges
        assert 0 < structural_result['global_efficiency'] <= 1, "global_efficiency out of range"
        assert 0 <= structural_result['average_clustering'] <= 1, "average_clustering out of range"
        assert 0 <= structural_result['modularity'] <= 1, "modularity out of range"

        # Verify output file was created
        config = get_config_dict()
        output_path = os.path.join(config['PROCESSED_DIR'], 'structural_metrics.csv')
        assert os.path.exists(output_path), f"Structural metrics CSV not created at {output_path}"

        # Verify CSV content
        df = pd.read_csv(output_path)
        assert len(df) >= 1, "Structural metrics CSV is empty"
        assert 'subject_id' in df.columns, "Missing subject_id column"
        assert 'global_efficiency' in df.columns, "Missing global_efficiency column"
        assert 'average_clustering' in df.columns, "Missing average_clustering column"
        assert 'modularity' in df.columns, "Missing modularity column"

    def test_subject_dynamic_metrics(self):
        """Test dynamic metric calculation for a single subject."""
        # Try to load a single subject's fMRI data
        try:
            fmri_data = load_hcp_fmri(subject_ids=[TEST_SUBJECT_ID])
        except Exception as e:
            pytest.skip(f"Real HCP data not available for subject {TEST_SUBJECT_ID}: {str(e)}")

        # Process functional metrics
        # Note: This requires LOO centroids, which need multiple subjects
        # For a single subject test, we'll test the calculation function directly
        # with synthetic but realistic data to verify the logic works

        # Generate synthetic but realistic windowed correlation matrices
        n_windows = 50
        n_regions = 200
        np.random.seed(SET_RANDOM_SEED)

        # Create realistic windowed correlation matrices (values between -1 and 1)
        windowed_correlations = np.random.rand(n_windows, n_regions, n_regions)
        windowed_correlations = (windowed_correlations * 2 - 1)  # Scale to [-1, 1]
        # Make symmetric
        for i in range(n_windows):
            windowed_correlations[i] = (windowed_correlations[i] + windowed_correlations[i].T) / 2

        # Test dynamic metrics calculation
        # We'll use a small set of centroids for testing
        n_centroids = 5
        centroids = np.random.rand(n_centroids, n_regions, n_regions)
        centroids = (centroids * 2 - 1)  # Scale to [-1, 1]
        for i in range(n_centroids):
            centroids[i] = (centroids[i] + centroids[i].T) / 2

        dynamic_metrics = calculate_dynamic_metrics(
            subject_id=TEST_SUBJECT_ID,
            windowed_correlations=windowed_correlations,
            centroids=centroids
        )

        # Verify dynamic metrics are computed
        assert dynamic_metrics is not None, "Dynamic metrics calculation returned None"
        assert 'mean_dwell_time' in dynamic_metrics, "Missing mean_dwell_time metric"
        assert 'num_visited_states' in dynamic_metrics, "Missing num_visited_states metric"

        # Verify metrics are non-null and within plausible ranges
        assert dynamic_metrics['mean_dwell_time'] is not None, "mean_dwell_time is None"
        assert dynamic_metrics['num_visited_states'] is not None, "num_visited_states is None"

        # Check plausible ranges
        assert dynamic_metrics['mean_dwell_time'] > 0, "mean_dwell_time must be positive"
        assert dynamic_metrics['num_visited_states'] > 0, "num_visited_states must be positive"
        assert dynamic_metrics['num_visited_states'] <= 5, "num_visited_states exceeds number of states"

        # Verify output file was created
        config = get_config_dict()
        output_path = os.path.join(config['PROCESSED_DIR'], 'dynamic_metrics.csv')
        assert os.path.exists(output_path), f"Dynamic metrics CSV not created at {output_path}"

        # Verify CSV content
        df = pd.read_csv(output_path)
        assert len(df) >= 1, "Dynamic metrics CSV is empty"
        assert 'subject_id' in df.columns, "Missing subject_id column"
        assert 'mean_dwell_time' in df.columns, "Missing mean_dwell_time column"
        assert 'num_visited_states' in df.columns, "Missing num_visited_states column"

    def test_exclusion_logging(self):
        """Test that exclusion logging works correctly."""
        config = get_config_dict()
        exclusion_log_path = get_exclusion_log_path()

        # Log a test exclusion
        log_subject_exclusion(
            subject_id="TEST_001",
            reason="test_exclusion_reason"
        )

        # Verify exclusion log was created
        assert os.path.exists(exclusion_log_path), f"Exclusion log not created at {exclusion_log_path}"

        # Verify exclusion log content
        with open(exclusion_log_path, 'r') as f:
            exclusion_log = json.load(f)

        assert isinstance(exclusion_log, list), "Exclusion log should be a list"
        assert len(exclusion_log) >= 1, "Exclusion log is empty"

        # Find our test entry
        test_entry = None
        for entry in exclusion_log:
            if entry.get('subject_id') == "TEST_001":
                test_entry = entry
                break

        assert test_entry is not None, "Test exclusion entry not found in log"
        assert test_entry['reason'] == "test_exclusion_reason", "Exclusion reason mismatch"
        assert 'timestamp' in test_entry, "Missing timestamp in exclusion entry"

    def test_full_pipeline_integration(self):
        """Test the full pipeline integration for a single subject."""
        # This test verifies that all components work together
        # We'll use the same approach as individual tests but combine them

        try:
            fmri_data = load_hcp_fmri(subject_ids=[TEST_SUBJECT_ID])
            dmri_data = load_hcp_dmri(subject_ids=[TEST_SUBJECT_ID])
        except Exception as e:
            pytest.skip(f"Real HCP data not available for subject {TEST_SUBJECT_ID}: {str(e)}")

        # Run structural pipeline
        structural_result = process_subject_structural_metrics(
            subject_id=TEST_SUBJECT_ID,
            dmri_data=dmri_data
        )

        # Run functional pipeline (with synthetic data for testing)
        n_windows = 50
        n_regions = 200
        np.random.seed(SET_RANDOM_SEED)

        windowed_correlations = np.random.rand(n_windows, n_regions, n_regions)
        windowed_correlations = (windowed_correlations * 2 - 1)
        for i in range(n_windows):
            windowed_correlations[i] = (windowed_correlations[i] + windowed_correlations[i].T) / 2

        n_centroids = 5
        centroids = np.random.rand(n_centroids, n_regions, n_regions)
        centroids = (centroids * 2 - 1)
        for i in range(n_centroids):
            centroids[i] = (centroids[i] + centroids[i].T) / 2

        dynamic_metrics = calculate_dynamic_metrics(
            subject_id=TEST_SUBJECT_ID,
            windowed_correlations=windowed_correlations,
            centroids=centroids
        )

        # Verify both structural and dynamic metrics are computed
        assert structural_result is not None, "Structural metrics not computed"
        assert dynamic_metrics is not None, "Dynamic metrics not computed"

        # Verify all required fields are present
        required_structural_fields = ['global_efficiency', 'average_clustering', 'modularity']
        required_dynamic_fields = ['mean_dwell_time', 'num_visited_states']

        for field in required_structural_fields:
            assert field in structural_result, f"Missing structural field: {field}"
            assert structural_result[field] is not None, f"structural {field} is None"

        for field in required_dynamic_fields:
            assert field in dynamic_metrics, f"Missing dynamic field: {field}"
            assert dynamic_metrics[field] is not None, f"dynamic {field} is None"

        # Verify output files exist
        config = get_config_dict()
        structural_output = os.path.join(config['PROCESSED_DIR'], 'structural_metrics.csv')
        dynamic_output = os.path.join(config['PROCESSED_DIR'], 'dynamic_metrics.csv')

        assert os.path.exists(structural_output), "Structural metrics output file missing"
        assert os.path.exists(dynamic_output), "Dynamic metrics output file missing"