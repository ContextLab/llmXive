"""
Integration test for T032: Generate Cluster Results.

This test verifies that the `generate_cluster_results.py` script:
1. Correctly reads the intermediate data produced by T030.
2. Aggregates the Cluster Label Alignment Score and intra-cluster similarity.
3. Writes a valid JSON file to `data/processed/cluster_results.json`.
4. Updates the project state file with the new artifact hash.
"""
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path to allow imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.analysis.generate_cluster_results import (
    load_json_safe,
    aggregate_cluster_results,
    update_state_file,
    main,
    DATA_PROCESSED_DIR,
    CLUSTER_INTERMEDIATE_PATH,
    CLUSTER_RESULTS_PATH,
    STATE_FILE
)


class TestGenerateClusterResults:
    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_dir = Path(self.temp_dir) / "data" / "processed"
        self.test_data_dir.mkdir(parents=True)
        
        # Mock paths
        self.mock_intermediate_path = self.test_data_dir / "cluster_intermediate.json"
        self.mock_results_path = self.test_data_dir / "cluster_results.json"
        self.mock_state_path = Path(self.temp_dir) / "state" / "projects" / "test_state.yaml"
        
        # Ensure state directory exists
        self.mock_state_path.parent.mkdir(parents=True)

    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_load_json_safe_exists(self):
        """Test loading an existing JSON file."""
        test_data = {"key": "value"}
        with open(self.mock_intermediate_path, 'w') as f:
            json.dump(test_data, f)
        
        result = load_json_safe(self.mock_intermediate_path)
        assert result == test_data

    def test_load_json_safe_missing(self):
        """Test loading a non-existent JSON file."""
        result = load_json_safe(Path("non_existent.json"))
        assert result is None

    def test_aggregate_cluster_results_success(self):
        """Test successful aggregation of cluster results."""
        # Prepare mock intermediate data
        mock_data = {
            "cluster_label_alignment_score": 0.85,
            "intra_cluster_similarity_coefficient": 0.72,
            "clusters": [
                {"tags": ["python", "django"], "id": 1},
                {"tags": ["javascript", "react"], "id": 2}
            ],
            "generated_at": "2023-10-01T00:00:00Z",
            "taxonomy_source": "survey_2023",
            "methodology": {"test": "fuzzy_match"}
        }
        
        with open(self.mock_intermediate_path, 'w') as f:
            json.dump(mock_data, f)

        # Patch the paths to use our test directory
        with patch('code.analysis.generate_cluster_results.CLUSTER_INTERMEDIATE_PATH', self.mock_intermediate_path):
            results = aggregate_cluster_results()

        assert results is not None
        assert results["metrics"]["cluster_label_alignment_score"] == 0.85
        assert results["metrics"]["intra_cluster_similarity_coefficient"] == 0.72
        assert results["clusters_summary"]["total_clusters"] == 2

    def test_aggregate_cluster_results_missing_metrics(self):
        """Test aggregation fails when metrics are missing."""
        mock_data = {
            "clusters": [],
            "generated_at": "2023-10-01"
            # Missing required metrics
        }
        
        with open(self.mock_intermediate_path, 'w') as f:
            json.dump(mock_data, f)

        with patch('code.analysis.generate_cluster_results.CLUSTER_INTERMEDIATE_PATH', self.mock_intermediate_path):
            results = aggregate_cluster_results()

        assert results is None

    def test_update_state_file(self):
        """Test updating the state file with artifact checksum."""
        results = {
            "task_id": "T032",
            "metrics": {
                "cluster_label_alignment_score": 0.85,
                "intra_cluster_similarity_coefficient": 0.72
            }
        }

        # Initial state
        initial_state = {
            "artifacts": {},
            "checksums": {},
            "last_updated": "2023-01-01"
        }
        
        with open(self.mock_state_path, 'w') as f:
            import yaml
            yaml.dump(initial_state, f)

        # Mock load_state and save_state to use our temp files
        from code.utils import hygiene
        
        original_load = hygiene.load_state
        original_save = hygiene.save_state

        def mock_load(path):
            if path == self.mock_state_path:
                with open(path, 'r') as f:
                    return yaml.safe_load(f)
            return original_load(path)

        def mock_save(state, path):
            if path == self.mock_state_path:
                with open(path, 'w') as f:
                    yaml.dump(state, f)
                return True
            return original_save(state, path)

        with patch.object(hygiene, 'load_state', mock_load):
            with patch.object(hygiene, 'save_state', mock_save):
                # Patch STATE_FILE
                with patch('code.analysis.generate_cluster_results.STATE_FILE', self.mock_state_path):
                    success = update_state_file(results, self.mock_results_path)

        assert success is True
        
        # Verify state was updated
        with open(self.mock_state_path, 'r') as f:
            final_state = yaml.safe_load(f)
        
        assert "artifacts" in final_state
        assert len(final_state["artifacts"]) > 0

    def test_main_execution(self, capsys):
        """Test the main function execution end-to-end."""
        # Setup mock data
        mock_data = {
            "cluster_label_alignment_score": 0.90,
            "intra_cluster_similarity_coefficient": 0.80,
            "clusters": [{"tags": ["tag1"], "id": 1}],
            "generated_at": "2023-10-01",
            "taxonomy_source": "survey",
            "methodology": {}
        }
        
        # Ensure intermediate file exists in temp dir
        with open(self.mock_intermediate_path, 'w') as f:
            json.dump(mock_data, f)

        # Mock state file
        initial_state = {"artifacts": {}, "checksums": {}}
        with open(self.mock_state_path, 'w') as f:
            import yaml
            yaml.dump(initial_state, f)

        # Patch paths and hygiene functions
        from code.utils import hygiene
        original_load = hygiene.load_state
        original_save = hygiene.save_state

        def mock_load(path):
            if path == self.mock_state_path:
                with open(path, 'r') as f:
                    return yaml.safe_load(f)
            return original_load(path)

        def mock_save(state, path):
            if path == self.mock_state_path:
                with open(path, 'w') as f:
                    yaml.dump(state, f)
                return True
            return original_save(state, path)

        with patch('code.analysis.generate_cluster_results.CLUSTER_INTERMEDIATE_PATH', self.mock_intermediate_path):
            with patch('code.analysis.generate_cluster_results.CLUSTER_RESULTS_PATH', self.mock_results_path):
                with patch('code.analysis.generate_cluster_results.STATE_FILE', self.mock_state_path):
                    with patch.object(hygiene, 'load_state', mock_load):
                        with patch.object(hygiene, 'save_state', mock_save):
                            # Redirect stdout to capture print statements
                            try:
                                main()
                            except SystemExit as e:
                                # main() calls sys.exit(0) on success
                                assert e.code == 0

        # Verify output file exists and has content
        assert self.mock_results_path.exists()
        with open(self.mock_results_path, 'r') as f:
            output_data = json.load(f)
        
        assert output_data["metrics"]["cluster_label_alignment_score"] == 0.90
        assert "task_id" in output_data
        assert output_data["task_id"] == "T032"