"""
Unit tests for Data Provenance metadata (T066).
Tests that metadata is correctly injected and validated.
"""

import json
import tempfile
import os
import pytest
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.dataset.generator import PuzzleGenerator, PuzzleType
from code.dataset.verifier import PuzzleVerifier, ErrorCodes


class TestDataProvenance:
    """Tests for T066: Data Provenance metadata injection and validation"""

    def test_generator_injects_metadata(self):
        """Test that generator injects all required metadata fields"""
        generator = PuzzleGenerator(
            source_id="test_source_v1",
            seed=12345,
            version="1.0.0"
        )
        
        # Generate a single puzzle
        puzzles = generator.generate_sudoku(n=9, count=1)
        
        assert len(puzzles) == 1
        puzzle = puzzles[0]
        
        # Check metadata exists
        assert "metadata" in puzzle.to_dict()
        metadata = puzzle.metadata
        
        # Check required fields
        assert metadata["source_id"] == "test_source_v1"
        assert metadata["generation_seed"] == 12345
        assert "timestamp" in metadata
        assert metadata["generator_version"] == "1.0.0"
        
        # Check complexity_metric
        assert "complexity_metric" in metadata
        assert "constraint_count" in metadata["complexity_metric"]
        assert "variable_domain_size" in metadata["complexity_metric"]

    def test_verifier_accepts_valid_metadata(self):
        """Test that verifier accepts puzzles with valid metadata"""
        generator = PuzzleGenerator()
        verifier = PuzzleVerifier()
        
        # Generate a puzzle with valid metadata
        puzzles = generator.generate_sudoku(n=9, count=1)
        puzzle_dict = puzzles[0].to_dict()
        
        # Verify it passes metadata validation
        is_valid, error_msg = verifier.validate_metadata(puzzle_dict)
        assert is_valid is True
        assert error_msg is None

    def test_verifier_rejects_missing_metadata(self):
        """Test that verifier rejects puzzles without metadata (T066 requirement)"""
        verifier = PuzzleVerifier()
        
        # Create a puzzle dict without metadata
        invalid_puzzle = {
            "puzzle_type": "sudoku",
            "constraints": ["Test constraint"],
            "initial_state": {"grid": []},
            "target_state": {"solution": []}
            # Missing metadata field
        }
        
        is_valid, error_msg = verifier.validate_metadata(invalid_puzzle)
        assert is_valid is False
        assert error_msg == "Missing metadata field"

    def test_verifier_rejects_missing_complexity_metric(self):
        """Test that verifier rejects puzzles with missing complexity_metric"""
        verifier = PuzzleVerifier()
        
        # Create a puzzle with metadata but missing complexity_metric
        invalid_puzzle = {
            "puzzle_type": "sudoku",
            "constraints": ["Test constraint"],
            "initial_state": {"grid": []},
            "target_state": {"solution": []},
            "metadata": {
                "source_id": "test",
                "generation_seed": 123,
                "timestamp": "2024-01-01T00:00:00",
                "generator_version": "1.0.0"
                # Missing complexity_metric
            }
        }
        
        is_valid, error_msg = verifier.validate_metadata(invalid_puzzle)
        assert is_valid is False
        assert "complexity_metric" in error_msg

    def test_full_verification_pipeline_with_metadata(self):
        """Test full pipeline: generate -> verify with metadata"""
        generator = PuzzleGenerator(seed=42)
        verifier = PuzzleVerifier()
        
        # Generate puzzles
        puzzles = generator.generate_sudoku(n=9, count=5)
        
        # Verify each puzzle
        for puzzle in puzzles:
            puzzle_dict = puzzle.to_dict()
            
            # First validate metadata
            is_valid, error_msg = verifier.validate_metadata(puzzle_dict)
            assert is_valid is True, f"Metadata validation failed: {error_msg}"
            
            # Then verify solution
            result = verifier.verify_solution(puzzle_dict)
            assert result.is_valid is True
            assert result.error_code is None

    def test_metadata_header_in_json_output(self):
        """Test that JSON output includes provenance header"""
        generator = PuzzleGenerator(
            source_id="test_header_v1",
            seed=99999
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = generator.generate_puzzles(
                n_values=[9],
                count=2,
                puzzle_types=[PuzzleType.SUDOKU],
                output_dir=tmpdir
            )
            
            # Load and check header
            with open(output_file, 'r') as f:
                data = json.load(f)
            
            assert "header" in data
            header = data["header"]
            
            assert header["source_id"] == "test_header_v1"
            assert header["generation_seed"] == 99999
            assert "timestamp" in header
            assert header["generator_version"] == "1.0.0"
            assert "total_instances" in header
            assert header["total_instances"] == 2

    def test_verifier_rejects_puzzle_with_invalid_metadata(self):
        """Test that verifier rejects puzzle with invalid metadata fields"""
        verifier = PuzzleVerifier()
        
        # Create puzzle with incomplete metadata
        invalid_puzzle = {
            "puzzle_type": "sudoku",
            "constraints": ["Test"],
            "initial_state": {"grid": []},
            "target_state": {"solution": []},
            "metadata": {
                "source_id": "test",
                # Missing generation_seed, timestamp, generator_version
            }
        }
        
        is_valid, error_msg = verifier.validate_metadata(invalid_puzzle)
        assert is_valid is False
        assert "generation_seed" in error_msg or "timestamp" in error_msg or "generator_version" in error_msg

    def test_complexity_metric_validation(self):
        """Test that complexity_metric fields are validated correctly"""
        verifier = PuzzleVerifier()
        
        # Test missing constraint_count
        puzzle_missing_constraint = {
            "puzzle_type": "sudoku",
            "metadata": {
                "source_id": "test",
                "generation_seed": 123,
                "timestamp": "2024-01-01",
                "generator_version": "1.0.0",
                "complexity_metric": {
                    "variable_domain_size": 9
                    # Missing constraint_count
                }
            }
        }
        
        is_valid, error_msg = verifier.validate_metadata(puzzle_missing_constraint)
        assert is_valid is False
        assert "constraint_count" in error_msg

    def test_different_puzzle_types_have_metadata(self):
        """Test that all puzzle types generate metadata correctly"""
        generator = PuzzleGenerator(seed=42)
        verifier = PuzzleVerifier()
        
        puzzle_types = [
            (PuzzleType.SUDOKU, 9),
            (PuzzleType.PATHFINDING, 5),
            (PuzzleType.LOGIC_GRID, 3),
            (PuzzleType.ARITHMETIC, 3)
        ]
        
        for p_type, n in puzzle_types:
            if p_type == PuzzleType.SUDOKU:
                puzzles = generator.generate_sudoku(n, 1)
            elif p_type == PuzzleType.PATHFINDING:
                puzzles = generator.generate_pathfinding(n, 1)
            elif p_type == PuzzleType.LOGIC_GRID:
                puzzles = generator.generate_logic_grid(n, 1)
            elif p_type == PuzzleType.ARITHMETIC:
                puzzles = generator.generate_arithmetic(n, 1)
            
            assert len(puzzles) == 1
            puzzle_dict = puzzles[0].to_dict()
            
            # Verify metadata exists and is valid
            is_valid, error_msg = verifier.validate_metadata(puzzle_dict)
            assert is_valid is True, f"Failed for {p_type.value}: {error_msg}"
            
            # Verify metadata contains correct puzzle type
            assert puzzle_dict["metadata"]["puzzle_type"] == p_type.value

    def test_metadata_timestamp_format(self):
        """Test that timestamp is in ISO format"""
        generator = PuzzleGenerator()
        puzzles = generator.generate_sudoku(n=9, count=1)
        
        timestamp = puzzles[0].metadata["timestamp"]
        
        # Should be parseable as ISO format
        try:
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            pytest.fail(f"Timestamp not in ISO format: {timestamp}")