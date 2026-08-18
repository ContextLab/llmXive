"""
Unit tests for T036: Dataset Statistics Validation
"""

import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.dataset.validate_dataset_statistics import (
    ValidationResult,
    validate_type_distribution,
    load_dataset_metadata
)

class TestValidateTypeDistribution:
    def test_balanced_distribution(self):
        """Test that a balanced 50/50 distribution passes."""
        puzzles = [
            {'type': 'sudoku', 'complexity': 10},
            {'type': 'sudoku', 'complexity': 50},
            {'type': 'pathfinding', 'complexity': 100},
            {'type': 'pathfinding', 'complexity': 200},
            {'type': 'sudoku', 'complexity': 500},
            {'type': 'pathfinding', 'complexity': 500},
            {'type': 'sudoku', 'complexity': 10},
            {'type': 'pathfinding', 'complexity': 50},
            {'type': 'sudoku', 'complexity': 100},
            {'type': 'pathfinding', 'complexity': 200},
        ]
        
        result = validate_type_distribution(puzzles, (0.5, 0.5))
        
        assert result.is_valid is True
        assert result.total_puzzles == 10
        assert result.type_distribution['sudoku'] == 5
        assert result.type_distribution['pathfinding'] == 5
        assert len(result.issues) == 0

    def test_unbalanced_distribution_fails(self):
        """Test that a significantly unbalanced distribution fails."""
        puzzles = [
            {'type': 'sudoku', 'complexity': 10},
            {'type': 'sudoku', 'complexity': 50},
            {'type': 'sudoku', 'complexity': 100},
            {'type': 'sudoku', 'complexity': 200},
            {'type': 'sudoku', 'complexity': 500},
            {'type': 'sudoku', 'complexity': 500},
            {'type': 'sudoku', 'complexity': 10},
            {'type': 'sudoku', 'complexity': 50},
            {'type': 'sudoku', 'complexity': 100},
            {'type': 'sudoku', 'complexity': 200},
        ]
        
        result = validate_type_distribution(puzzles, (0.5, 0.5))
        
        assert result.is_valid is False
        assert 'sudoku' in result.issues[0] or 'Pathfinding' in result.issues[0]

    def test_missing_complexity_levels(self):
        """Test that missing complexity levels are detected."""
        puzzles = [
            {'type': 'sudoku', 'complexity': 10},
            {'type': 'pathfinding', 'complexity': 500},
        ]
        
        result = validate_type_distribution(puzzles, (0.5, 0.5))
        
        assert result.is_valid is False
        assert 50 in result.missing_complexity_levels
        assert 100 in result.missing_complexity_levels
        assert 200 in result.missing_complexity_levels

    def test_sample_size_warning(self):
        """Test that small sample sizes generate warnings but don't fail validation."""
        puzzles = [
            {'type': 'sudoku', 'complexity': 10},
            {'type': 'pathfinding', 'complexity': 50},
        ]
        
        result = validate_type_distribution(puzzles, (0.5, 0.5))
        
        assert result.sample_size_adequate is False
        assert any('Sample size' in issue for issue in result.issues)

    def test_empty_dataset(self):
        """Test that an empty dataset fails validation."""
        puzzles = []
        
        result = validate_type_distribution(puzzles, (0.5, 0.5))
        
        assert result.is_valid is False
        assert result.total_puzzles == 0
        assert "No puzzles found" in result.issues[0]

class TestLoadDatasetMetadata:
    def test_load_valid_json_files(self, tmp_path):
        """Test loading metadata from valid JSON files."""
        # Create test data directory
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        
        # Create valid puzzle files
        puzzle1 = {
            "type": "sudoku",
            "complexity": 10,
            "constraints": {},
            "initial_state": {}
        }
        puzzle2 = {
            "type": "pathfinding",
            "complexity": 50,
            "constraints": {},
            "initial_state": {}
        }
        
        with open(raw_dir / "puzzle1.json", 'w') as f:
            json.dump(puzzle1, f)
        with open(raw_dir / "puzzle2.json", 'w') as f:
            json.dump(puzzle2, f)
        
        # Load metadata
        puzzles = load_dataset_metadata(tmp_path)
        
        assert len(puzzles) == 2
        types = [p['type'] for p in puzzles]
        assert 'sudoku' in types
        assert 'pathfinding' in types
        complexities = [p['complexity'] for p in puzzles]
        assert 10 in complexities
        assert 50 in complexities

    def test_handles_invalid_json(self, tmp_path):
        """Test that invalid JSON files are skipped with a warning."""
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        
        # Create a valid file
        puzzle1 = {"type": "sudoku", "complexity": 10}
        with open(raw_dir / "valid.json", 'w') as f:
            json.dump(puzzle1, f)
        
        # Create an invalid file
        with open(raw_dir / "invalid.json", 'w') as f:
            f.write("{ invalid json }")
        
        # Load metadata (should not raise, just skip invalid)
        puzzles = load_dataset_metadata(tmp_path)
        
        assert len(puzzles) == 1
        assert puzzles[0]['file'] == 'valid.json'

    def test_missing_directory(self, tmp_path):
        """Test that missing data directory raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_dataset_metadata(tmp_path / "nonexistent")