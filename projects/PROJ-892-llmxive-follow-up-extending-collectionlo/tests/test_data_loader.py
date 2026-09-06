import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from data_loader import load_subspace_ranks, get_project_root, load_artifacts_state, save_artifacts_state

class TestLoadSubspaceRanks:
    """Tests for the load_subspace_ranks function (T009c)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.project_root = get_project_root()
        self.ranks_path = self.project_root / "data" / "subspace_ranks_merged.json"
        self.state_path = self.project_root / "state" / "artifacts.yaml"
        
        # Ensure directories exist
        self.ranks_path.parent.mkdir(parents=True, exist_ok=True)
        (self.project_root / "state").mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Clean up test fixtures."""
        # Remove test file if it exists
        if self.ranks_path.exists():
            self.ranks_path.unlink()
        
        # Reset state
        if self.state_path.exists():
            self.state_path.unlink()

    def test_load_subspace_ranks_success(self):
        """Test successful loading of subspace ranks."""
        # Create a valid test file
        test_data = {
            "tolerance": 1e-5,
            "effects": {
                "oil_painting": {"rank": 8, "key": "oil_painting"},
                "watercolor": {"rank": 12, "key": "watercolor"},
                "cyberpunk": {"rank": 10, "key": "cyberpunk"}
            }
        }
        
        with open(self.ranks_path, 'w') as f:
            json.dump(test_data, f)
        
        # Load and verify
        result = load_subspace_ranks()
        
        assert result == test_data
        assert result['tolerance'] == 1e-5
        assert len(result['effects']) == 3

    def test_load_subspace_ranks_file_not_found(self):
        """Test error when file does not exist."""
        with pytest.raises(FileNotFoundError, match="Subspace ranks file not found"):
            load_subspace_ranks()

    def test_load_subspace_ranks_missing_tolerance(self):
        """Test error when tolerance is missing."""
        test_data = {
            "effects": {
                "oil_painting": {"rank": 8}
            }
        }
        
        with open(self.ranks_path, 'w') as f:
            json.dump(test_data, f)
        
        with pytest.raises(ValueError, match="Tolerance threshold not found"):
            load_subspace_ranks()

    def test_load_subspace_ranks_invalid_tolerance(self):
        """Test error when tolerance is invalid."""
        test_data = {
            "tolerance": -1e-5,
            "effects": {
                "oil_painting": {"rank": 8}
            }
        }
        
        with open(self.ranks_path, 'w') as f:
            json.dump(test_data, f)
        
        with pytest.raises(ValueError, match="Invalid tolerance threshold"):
            load_subspace_ranks()

    def test_load_subspace_ranks_missing_effects(self):
        """Test error when effects data is missing."""
        test_data = {
            "tolerance": 1e-5
        }
        
        with open(self.ranks_path, 'w') as f:
            json.dump(test_data, f)
        
        with pytest.raises(ValueError, match="No 'effects' data found"):
            load_subspace_ranks()

    def test_load_subspace_ranks_empty_effects(self):
        """Test error when effects data is empty."""
        test_data = {
            "tolerance": 1e-5,
            "effects": {}
        }
        
        with open(self.ranks_path, 'w') as f:
            json.dump(test_data, f)
        
        with pytest.raises(ValueError, match="Effects data is empty"):
            load_subspace_ranks()

    def test_load_subspace_ranks_missing_rank(self):
        """Test error when rank is missing for an effect."""
        test_data = {
            "tolerance": 1e-5,
            "effects": {
                "oil_painting": {"key": "oil_painting"}
            }
        }
        
        with open(self.ranks_path, 'w') as f:
            json.dump(test_data, f)
        
        with pytest.raises(ValueError, match="Rank not found for effect"):
            load_subspace_ranks()

    def test_load_subspace_ranks_invalid_rank(self):
        """Test error when rank is invalid."""
        test_data = {
            "tolerance": 1e-5,
            "effects": {
                "oil_painting": {"rank": -5, "key": "oil_painting"}
            }
        }
        
        with open(self.ranks_path, 'w') as f:
            json.dump(test_data, f)
        
        with pytest.raises(ValueError, match="Invalid rank for effect"):
            load_subspace_ranks()

    def test_load_subspace_ranks_registers_in_state(self):
        """Test that the function registers the file in state if not present."""
        test_data = {
            "tolerance": 1e-5,
            "effects": {
                "oil_painting": {"rank": 8}
            }
        }
        
        with open(self.ranks_path, 'w') as f:
            json.dump(test_data, f)
        
        # Ensure state is empty
        save_artifacts_state({})
        
        # Load
        load_subspace_ranks()
        
        # Check state
        state = load_artifacts_state()
        assert 'subspace_ranks_merged' in state
        assert state['subspace_ranks_merged']['path'] == str(self.ranks_path.relative_to(self.project_root))
        assert 'hash' in state['subspace_ranks_merged']
        assert state['subspace_ranks_merged']['type'] == 'subspace_ranks'

    def test_load_subspace_ranks_updates_hash_mismatch(self):
        """Test that the function updates the hash if there's a mismatch."""
        test_data = {
            "tolerance": 1e-5,
            "effects": {
                "oil_painting": {"rank": 8}
            }
        }
        
        with open(self.ranks_path, 'w') as f:
            json.dump(test_data, f)
        
        # Set up state with wrong hash
        state = {
            'subspace_ranks_merged': {
                'path': str(self.ranks_path.relative_to(self.project_root)),
                'hash': 'wrong_hash',
                'type': 'subspace_ranks'
            }
        }
        save_artifacts_state(state)
        
        # Load
        load_subspace_ranks()
        
        # Check state was updated
        state = load_artifacts_state()
        assert state['subspace_ranks_merged']['hash'] != 'wrong_hash'
        assert len(state['subspace_ranks_merged']['hash']) == 64  # SHA256 hex length

    def test_load_subspace_ranks_validates_multiple_effects(self):
        """Test loading with multiple effects."""
        test_data = {
            "tolerance": 1e-5,
            "effects": {
                "oil_painting": {"rank": 8, "key": "oil_painting"},
                "watercolor": {"rank": 12, "key": "watercolor"},
                "cyberpunk": {"rank": 10, "key": "cyberpunk"},
                "pencil_sketch": {"rank": 6, "key": "pencil_sketch"},
                "ink_wash": {"rank": 9, "key": "ink_wash"}
            }
        }
        
        with open(self.ranks_path, 'w') as f:
            json.dump(test_data, f)
        
        result = load_subspace_ranks()
        
        assert len(result['effects']) == 5
        for effect_name, effect_data in result['effects'].items():
            assert 'rank' in effect_data
            assert effect_data['rank'] > 0
            assert 'key' in effect_data
            assert effect_data['key'] == effect_name
