"""
Unit tests for BaselineOrchestrator.

These tests verify that the orchestrator correctly:
1. Iterates through seed sequences
2. Handles stable and unstable seeds
3. Implements retry logic
4. Generates the required number of valid manifests
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.llmxive.baseline_orchestrator import BaselineOrchestrator
from src.llmxive.exceptions import DATA_INTEGRITY_ERROR, ERR_SEED_UNSTABLE


class TestBaselineOrchestrator:
    """Test cases for BaselineOrchestrator class."""

    @pytest.fixture
    def mock_manifest_dir(self, tmp_path):
        """Create a temporary manifest directory."""
        manifest_dir = tmp_path / "baseline_manifests"
        manifest_dir.mkdir()
        return manifest_dir

    @pytest.fixture
    def orchestrator(self, mock_manifest_dir):
        """Create a BaselineOrchestrator instance with mocked paths."""
        with patch.object(BaselineOrchestrator, '__init__', lambda x, **kwargs: None):
            orch = BaselineOrchestrator.__new__(BaselineOrchestrator)
            orch.model_id = "phi2"
            orch.num_valid_seeds = 3
            orch.max_attempts_per_seed = None
            orch.manifest_dir = mock_manifest_dir
            orch.seed_manager = MagicMock()
            return orch

    def test_orchestrator_initialization(self, mock_manifest_dir):
        """Test that orchestrator initializes correctly."""
        orch = BaselineOrchestrator(
            model_id="phi2",
            num_valid_seeds=5,
            max_attempts_per_seed=10
        )
        
        assert orch.model_id == "phi2"
        assert orch.num_valid_seeds == 5
        assert orch.max_attempts_per_seed == 10
        assert orch.manifest_dir.exists()

    def test_orchestrate_success(self, orchestrator):
        """Test successful orchestration with stable seeds."""
        # Mock generate_baseline_manifest to return stable manifests
        stable_manifest = {
            'seed_id': 1,
            'status': 'STABLE',
            'mean_reward': 0.8,
            'mean_grad_norm': 0.1,
            'variance': 0.01
        }
        
        with patch('src.llmxive.baseline_orchestrator.generate_baseline_manifest', 
                  return_value=stable_manifest):
            with patch.object(orchestrator, '_get_manifest_path') as mock_path:
                mock_path.return_value = orchestrator.manifest_dir / "phi2_1.json"
                
                manifests = orchestrator.orchestrate(seed_sequence=[1, 2, 3])
                
                assert len(manifests) == 3
                assert all(m['status'] == 'STABLE' for m in manifests)

    def test_orchestrate_with_unstable_seeds(self, orchestrator):
        """Test orchestration handles unstable seeds correctly."""
        # First call returns unstable, second call returns stable
        call_count = [0]
        
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                manifest = {
                    'seed_id': 1,
                    'status': 'UNSTABLE',
                    'mean_reward': 0.8,
                    'mean_grad_norm': 0.1,
                    'variance': 0.1
                }
                raise ERR_SEED_UNSTABLE("Seed unstable")
            else:
                return {
                    'seed_id': 1,
                    'status': 'STABLE',
                    'mean_reward': 0.8,
                    'mean_grad_norm': 0.1,
                    'variance': 0.01
                }
        
        with patch('src.llmxive.baseline_orchestrator.generate_baseline_manifest', 
                  side_effect=side_effect):
            with patch.object(orchestrator, '_get_manifest_path') as mock_path:
                mock_path.return_value = orchestrator.manifest_dir / "phi2_1.json"
                
                # Should retry on unstable seed and succeed
                manifests = orchestrator.orchestrate(seed_sequence=[1, 2, 3])
                
                assert len(manifests) == 3
                assert all(m['status'] == 'STABLE' for m in manifests)

    def test_orchestrate_max_attempts(self, orchestrator):
        """Test orchestration respects max attempts limit."""
        orchestrator.max_attempts_per_seed = 2
        
        # Always return unstable
        def always_unstable(*args, **kwargs):
            raise ERR_SEED_UNSTABLE("Seed unstable")
        
        with patch('src.llmxive.baseline_orchestrator.generate_baseline_manifest', 
                  side_effect=always_unstable):
            # Should eventually fail if not enough stable seeds found
            with pytest.raises(DATA_INTEGRITY_ERROR):
                orchestrator.orchestrate(seed_sequence=[1, 2, 3, 4, 5])

    def test_orchestrate_data_integrity_error(self, orchestrator):
        """Test orchestration handles data integrity errors."""
        def raise_integrity_error(*args, **kwargs):
            raise DATA_INTEGRITY_ERROR("Data integrity failed")
        
        with patch('src.llmxive.baseline_orchestrator.generate_baseline_manifest', 
                  side_effect=raise_integrity_error):
            with pytest.raises(DATA_INTEGRITY_ERROR):
                orchestrator.orchestrate(seed_sequence=[1, 2, 3])

    def test_get_manifest_path(self, orchestrator, mock_manifest_dir):
        """Test manifest path generation."""
        path = orchestrator._get_manifest_path(123)
        expected = mock_manifest_dir / "phi2_123.json"
        assert path == expected

    def test_get_generated_manifests(self, orchestrator, mock_manifest_dir):
        """Test retrieval of generated manifest paths."""
        # Create some fake manifest files
        for seed in [1, 2, 3]:
            manifest_file = mock_manifest_dir / f"phi2_{seed}.json"
            manifest_file.write_text('{"seed_id": 1}')
        
        manifests = orchestrator.get_generated_manifests()
        assert len(manifests) == 3
        assert all(str(m).endswith('.json') for m in manifests)
        assert all('phi2_' in str(m) for m in manifests)