"""
Unit tests for aspect ratio validation logic.
"""
import pytest
import json
import tempfile
from pathlib import Path
import numpy as np

from analysis.validation import (
    calculate_aspect_ratio,
    validate_aspect_ratio_against_ground_truth,
    validate_sequence,
    run_aspect_ratio_validation,
    ASPECT_RATIO_TOLERANCE
)


class TestAspectRatioCalculation:
    """Tests for aspect ratio calculation."""
    
    def test_calculate_aspect_ratio_basic(self):
        """Test basic aspect ratio calculation."""
        result = calculate_aspect_ratio(2.0, 1.0, 1.0)
        
        assert result["width_height"] == 2.0
        assert result["width_depth"] == 2.0
        assert result["height_depth"] == 1.0
    
    def test_calculate_aspect_ratio_non_square(self):
        """Test with non-square dimensions."""
        result = calculate_aspect_ratio(4.0, 2.0, 1.0)
        
        assert result["width_height"] == 2.0
        assert result["width_depth"] == 4.0
        assert result["height_depth"] == 2.0
    
    def test_calculate_aspect_ratio_zero_prevention(self):
        """Test that zero dimensions don't cause division by zero."""
        # Very small values should be handled gracefully
        result = calculate_aspect_ratio(1.0, 1e-7, 1e-7)
        
        assert result["width_height"] > 0
        assert result["width_depth"] > 0
        assert result["height_depth"] > 0


class TestValidationAgainstGroundTruth:
    """Tests for validation against ground truth."""
    
    def test_perfect_match(self):
        """Test validation with perfect match."""
        estimated = {"width": 2.0, "height": 1.0, "depth": 1.0}
        ground_truth = {"width": 2.0, "height": 1.0, "depth": 1.0}
        
        is_valid, errors, valid_ratios = validate_aspect_ratio_against_ground_truth(
            estimated, ground_truth, tolerance=0.05
        )
        
        assert is_valid is True
        assert all(v == 0.0 for v in errors.values())
        assert all(v is True for v in valid_ratios.values())
    
    def test_within_tolerance(self):
        """Test validation with small error within tolerance."""
        estimated = {"width": 2.05, "height": 1.0, "depth": 1.0}
        ground_truth = {"width": 2.0, "height": 1.0, "depth": 1.0}
        
        is_valid, errors, valid_ratios = validate_aspect_ratio_against_ground_truth(
            estimated, ground_truth, tolerance=0.05
        )
        
        # 2.5% error should be within 5% tolerance
        assert is_valid is True
        assert errors["width_height"] <= 0.05
    
    def test_outside_tolerance(self):
        """Test validation with error outside tolerance."""
        estimated = {"width": 2.15, "height": 1.0, "depth": 1.0}
        ground_truth = {"width": 2.0, "height": 1.0, "depth": 1.0}
        
        is_valid, errors, valid_ratios = validate_aspect_ratio_against_ground_truth(
            estimated, ground_truth, tolerance=0.05
        )
        
        # 15% error should be outside 5% tolerance
        assert is_valid is False
        assert errors["width_height"] > 0.05
    
    def test_partial_validity(self):
        """Test when some aspect ratios are valid and others are not."""
        estimated = {"width": 2.05, "height": 1.0, "depth": 1.2}
        ground_truth = {"width": 2.0, "height": 1.0, "depth": 1.0}
        
        is_valid, errors, valid_ratios = validate_aspect_ratio_against_ground_truth(
            estimated, ground_truth, tolerance=0.05
        )
        
        assert is_valid is False  # Overall should be invalid
        assert valid_ratios["width_height"] is True  # This one is valid
        assert valid_ratios["width_depth"] is False  # This one is invalid
        assert valid_ratios["height_depth"] is False  # This one is invalid


class TestSequenceValidation:
    """Tests for individual sequence validation."""
    
    def test_validate_sequence_with_reconstructed_box(self):
        """Test validation with reconstructed_box structure."""
        sequence = {
            "sequence_id": "seq_001",
            "reconstructed_box": {
                "width": 2.0,
                "height": 1.0,
                "depth": 1.0
            }
        }
        ground_truth = {"width": 2.0, "height": 1.0, "depth": 1.0}
        
        result = validate_sequence(sequence, ground_truth)
        
        assert result["sequence_id"] == "seq_001"
        assert result["valid"] is True
    
    def test_validate_sequence_with_dimensions(self):
        """Test validation with dimensions structure."""
        sequence = {
            "sequence_id": "seq_002",
            "dimensions": {
                "width": 2.0,
                "height": 1.0,
                "depth": 1.0
            }
        }
        ground_truth = {"width": 2.0, "height": 1.0, "depth": 1.0}
        
        result = validate_sequence(sequence, ground_truth)
        
        assert result["sequence_id"] == "seq_002"
        assert result["valid"] is True
    
    def test_validate_sequence_without_ground_truth(self):
        """Test validation when no ground truth is provided."""
        sequence = {
            "sequence_id": "seq_003",
            "reconstructed_box": {
                "width": 2.0,
                "height": 1.0,
                "depth": 1.0
            }
        }
        
        result = validate_sequence(sequence, None)
        
        assert result["sequence_id"] == "seq_003"
        assert result["valid"] is None
        assert "No ground truth" in result["message"]


class TestFullValidationPipeline:
    """Tests for the full validation pipeline."""
    
    def test_run_validation_with_data(self):
        """Test running validation with sample data."""
        # Create temporary files
        with tempfile.TemporaryDirectory() as tmpdir:
            poses_file = Path(tmpdir) / "poses.json"
            volumes_file = Path(tmpdir) / "volumes.json"
            output_file = Path(tmpdir) / "validation_results.json"
            
            # Create sample poses data
            poses_data = [
                {
                    "sequence_id": "seq_001",
                    "reconstructed_box": {
                        "width": 2.0,
                        "height": 1.0,
                        "depth": 1.0
                    }
                },
                {
                    "sequence_id": "seq_002",
                    "reconstructed_box": {
                        "width": 2.1,
                        "height": 1.0,
                        "depth": 1.0
                    }
                }
            ]
            
            with open(poses_file, 'w') as f:
                json.dump(poses_data, f)
            
            # Create ground truth volumes
            volumes_data = {
                "seq_001": {"width": 2.0, "height": 1.0, "depth": 1.0},
                "seq_002": {"width": 2.0, "height": 1.0, "depth": 1.0}
            }
            
            with open(volumes_file, 'w') as f:
                json.dump(volumes_data, f)
            
            # Run validation
            summary = run_aspect_ratio_validation(
                poses_file=str(poses_file),
                synthetic_volumes_file=str(volumes_file),
                output_file=str(output_file)
            )
            
            # Verify results
            assert summary["total_sequences"] == 2
            assert summary["validated_sequences"] == 2
            assert summary["valid_count"] == 1  # seq_001 is valid, seq_002 is not
            assert summary["invalid_count"] == 1
            
            # Verify output file was created
            assert output_file.exists()
            
            with open(output_file, 'r') as f:
                output_data = json.load(f)
            
            assert "validation_results" in output_data
            assert "summary" in output_data
    
    def test_run_validation_no_ground_truth(self):
        """Test validation when no ground truth file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            poses_file = Path(tmpdir) / "poses.json"
            output_file = Path(tmpdir) / "validation_results.json"
            
            # Create sample poses data
            poses_data = [
                {
                    "sequence_id": "seq_001",
                    "reconstructed_box": {
                        "width": 2.0,
                        "height": 1.0,
                        "depth": 1.0
                    }
                }
            ]
            
            with open(poses_file, 'w') as f:
                json.dump(poses_data, f)
            
            # Run validation with non-existent ground truth file
            summary = run_aspect_ratio_validation(
                poses_file=str(poses_file),
                synthetic_volumes_file=str(Path(tmpdir) / "nonexistent.json"),
                output_file=str(output_file)
            )
            
            # Should return empty summary
            assert summary["total_sequences"] == 0
            assert summary["validated_sequences"] == 0
            assert "No ground truth" in summary["message"]
    
    def test_tolerance_parameter(self):
        """Test that tolerance parameter is respected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            poses_file = Path(tmpdir) / "poses.json"
            volumes_file = Path(tmpdir) / "volumes.json"
            output_file = Path(tmpdir) / "validation_results.json"
            
            # Create data with 10% error
            poses_data = [
                {
                    "sequence_id": "seq_001",
                    "reconstructed_box": {
                        "width": 2.2,  # 10% error
                        "height": 1.0,
                        "depth": 1.0
                    }
                }
            ]
            
            with open(poses_file, 'w') as f:
                json.dump(poses_data, f)
            
            volumes_data = {
                "seq_001": {"width": 2.0, "height": 1.0, "depth": 1.0}
            }
            
            with open(volumes_file, 'w') as f:
                json.dump(volumes_data, f)
            
            # Run with 5% tolerance (should fail)
            summary_5 = run_aspect_ratio_validation(
                poses_file=str(poses_file),
                synthetic_volumes_file=str(volumes_file),
                output_file=str(output_file)
            )
            assert summary_5["valid_count"] == 0
            assert summary_5["invalid_count"] == 1
            
            # Run with 15% tolerance (should pass)
            # Note: This test would need a custom tolerance parameter
            # which is currently hardcoded in the function.
            # For now, we just verify the default behavior.