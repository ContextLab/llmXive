"""
Unit tests for the dataset validation script.
"""
import pytest
import json
import tempfile
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.validate_dataset import (
    validate_dataset,
    validate_logic_proofs,
    validate_grid_worlds,
    VALIDITY_THRESHOLD
)
from src.utils.config import Config


class TestValidateDataset:
    """Tests for the dataset validation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.data_dir = self.temp_dir / "data"
        self.data_dir.mkdir()
        
        # Create test config
        self.config = Config(seed=42, logic_count=10, grid_count=10)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_validate_missing_data(self):
        """Test validation fails when data files are missing."""
        with pytest.raises(FileNotFoundError):
            validate_dataset(self.data_dir, self.config)
    
    def test_validate_empty_datasets(self):
        """Test validation with empty datasets."""
        # Create empty data files
        logic_file = self.data_dir / "logic_proofs.json"
        grid_file = self.data_dir / "grid_worlds.json"
        
        with open(logic_file, 'w') as f:
            json.dump([], f)
        
        with open(grid_file, 'w') as f:
            json.dump([], f)
        
        # Should pass validation (no data to fail)
        result = validate_dataset(self.data_dir, self.config)
        assert result is True
    
    def test_validate_logic_proofs_function(self):
        """Test the logic proof validation function."""
        # Create valid proof data
        valid_proofs = [
            {
                "premises": ["A", "A -> B"],
                "conclusion": "B",
                "valid": True,
                "proof_steps": ["Modus Ponens"]
            },
            {
                "premises": ["X", "X -> Y"],
                "conclusion": "Y",
                "valid": True,
                "proof_steps": ["Modus Ponens"]
            }
        ]
        
        from src.generators.logic_generator import LogicProofGenerator
        generator = LogicProofGenerator(seed=42)
        
        valid_count, total_count = validate_logic_proofs(valid_proofs, generator)
        
        assert total_count == 2
        assert valid_count == 2
    
    def test_validate_grid_worlds_function(self):
        """Test the grid world validation function."""
        # Create solvable grid data
        solvable_grids = [
            {
                "grid": [
                    ['.', '.', '.'],
                    ['.', '.', '.'],
                    ['.', '.', '.']
                ],
                "start": [0, 0],
                "end": [2, 2],
                "rules": ["avoid_red"]
            },
            {
                "grid": [
                    ['.', 'X', '.'],
                    ['.', '.', '.'],
                    ['.', '.', '.']
                ],
                "start": [0, 0],
                "end": [2, 2],
                "rules": ["diagonal_paths"]
            }
        ]
        
        from src.generators.grid_generator import GridWorldGenerator
        generator = GridWorldGenerator(seed=42)
        
        solvable_count, total_count = validate_grid_worlds(solvable_grids, generator)
        
        assert total_count == 2
        assert solvable_count == 2
    
    def test_validate_invalid_logic_rate(self):
        """Test validation fails when logic validity is below threshold."""
        # Create data with low validity
        logic_data = [
            {"premises": [], "conclusion": "X", "valid": False},
            {"premises": [], "conclusion": "Y", "valid": False},
            {"premises": [], "conclusion": "Z", "valid": True},
        ]
        
        grid_data = [
            {
                "grid": [['.', '.', '.'], ['.', '.', '.'], ['.', '.', '.']],
                "start": [0, 0],
                "end": [2, 2],
                "rules": []
            }
        ]
        
        # Write files
        with open(self.data_dir / "logic_proofs.json", 'w') as f:
            json.dump(logic_data, f)
        
        with open(self.data_dir / "grid_worlds.json", 'w') as f:
            json.dump(grid_data, f)
        
        # This should fail because logic validity is 33% < 99%
        result = validate_dataset(self.data_dir, self.config)
        assert result is False
    
    def test_validate_invalid_grid_rate(self):
        """Test validation fails when grid solvability is below threshold."""
        # Create data with low solvability
        logic_data = [
            {"premises": ["A"], "conclusion": "A", "valid": True},
        ]
        
        # Create unsolvable grids
        grid_data = [
            {
                "grid": [
                    ['.', 'X', '.'],
                    ['X', 'X', 'X'],
                    ['.', 'X', '.']
                ],
                "start": [0, 0],
                "end": [2, 2],
                "rules": []
            },
            {
                "grid": [
                    ['.', 'X', '.'],
                    ['X', 'X', 'X'],
                    ['.', 'X', '.']
                ],
                "start": [0, 0],
                "end": [2, 2],
                "rules": []
            },
            {
                "grid": [
                    ['.', '.', '.'],
                    ['.', '.', '.'],
                    ['.', '.', '.']
                ],
                "start": [0, 0],
                "end": [2, 2],
                "rules": []
            }
        ]
        
        # Write files
        with open(self.data_dir / "logic_proofs.json", 'w') as f:
            json.dump(logic_data, f)
        
        with open(self.data_dir / "grid_worlds.json", 'w') as f:
            json.dump(grid_data, f)
        
        # This should fail because grid solvability is 33% < 99%
        result = validate_dataset(self.data_dir, self.config)
        assert result is False
    
    def test_validate_high_validity(self):
        """Test validation passes when validity is above threshold."""
        # Create high validity data
        logic_data = [
            {"premises": ["A"], "conclusion": "A", "valid": True},
            {"premises": ["B"], "conclusion": "B", "valid": True},
            {"premises": ["C"], "conclusion": "C", "valid": True},
        ]
        
        grid_data = [
            {
                "grid": [['.', '.', '.'], ['.', '.', '.'], ['.', '.', '.']],
                "start": [0, 0],
                "end": [2, 2],
                "rules": []
            },
            {
                "grid": [['.', '.', '.'], ['.', '.', '.'], ['.', '.', '.']],
                "start": [0, 0],
                "end": [2, 2],
                "rules": []
            },
            {
                "grid": [['.', '.', '.'], ['.', '.', '.'], ['.', '.', '.']],
                "start": [0, 0],
                "end": [2, 2],
                "rules": []
            }
        ]
        
        # Write files
        with open(self.data_dir / "logic_proofs.json", 'w') as f:
            json.dump(logic_data, f)
        
        with open(self.data_dir / "grid_worlds.json", 'w') as f:
            json.dump(grid_data, f)
        
        # This should pass (100% validity)
        result = validate_dataset(self.data_dir, self.config)
        assert result is True