"""
Unit tests for the calibration module.

Tests FR-009: Extrinsic calibration and coordinate transformation validation.
"""
import numpy as np
import pytest
import json
import tempfile
from pathlib import Path
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from src.data.calibration import (
    ExtrinsicParams, 
    CalibrationValidator, 
    validate_calibration,
    create_calibration_validator
)

class TestExtrinsicParams:
    def test_to_matrix_rotation_identity(self):
        """Test that zero rotation and translation produces identity matrix."""
        params = ExtrinsicParams(
            translation=[0.0, 0.0, 0.0],
            rotation=[0.0, 0.0, 0.0],
            sensor_type="lidar",
            frame_id="test_frame"
        )
        T = params.to_matrix()
        
        assert np.allclose(T, np.eye(4))
        
    def test_to_matrix_translation_only(self):
        """Test translation component of transformation matrix."""
        tx, ty, tz = 1.0, 2.0, 3.0
        params = ExtrinsicParams(
            translation=[tx, ty, tz],
            rotation=[0.0, 0.0, 0.0],
            sensor_type="camera",
            frame_id="cam_frame"
        )
        T = params.to_matrix()
        
        assert np.allclose(T[:3, 3], [tx, ty, tz])
        assert np.allclose(T[:3, :3], np.eye(3))

class TestCalibrationValidator:
    @pytest.fixture
    def validator(self):
        return CalibrationValidator(tolerance_translation=0.1, tolerance_rotation_deg=5.0)
    
    def test_validate_transformation_consistency_identity(self, validator):
        """Test that identity matrix passes validation."""
        T = np.eye(4)
        is_valid, rot_err, trans_err = validator.validate_transformation_consistency(T)
        
        assert is_valid
        assert rot_err == 0.0
        assert trans_err == 0.0
        
    def test_validate_transformation_consistency_invalid_rotation(self, validator):
        """Test that non-orthogonal matrix fails validation."""
        T = np.eye(4)
        T[:3, :3] = np.array([[1.0, 0.1, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
        
        is_valid, rot_err, trans_err = validator.validate_transformation_consistency(T)
        
        assert not is_valid
        assert rot_err > 1e-6
        
    def test_validate_calibration_against_ground_truth(self, validator):
        """Test full calibration validation with synthetic ground truth."""
        # Create a known transformation
        T_gt = np.eye(4)
        T_gt[:3, 3] = [0.5, 0.5, 0.5]
        
        # Create a point cloud
        points = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0]
        ])
        
        # Create params that match ground truth
        params = ExtrinsicParams(
            translation=[0.5, 0.5, 0.5],
            rotation=[0.0, 0.0, 0.0],
            sensor_type="lidar",
            frame_id="sensor"
        )
        
        report = validator.validate_calibration_against_ground_truth(
            params, points, points, T_gt
        )
        
        assert report.is_valid
        assert report.max_translation_error < 1e-6
        assert report.max_rotation_error_deg < 1e-6

class TestValidateCalibrationFunction:
    def test_validate_calibration_with_temp_config(self):
        """Test the main validate_calibration function with a temporary config file."""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config = {
                "translation": [0.1, 0.2, 0.3],
                "rotation": [0.0, 0.0, 0.0],
                "sensor_type": "test_sensor",
                "frame_id": "test_frame"
            }
            json.dump(config, f)
            config_path = Path(f.name)
        
        try:
            # Create temporary ground truth points
            with tempfile.NamedTemporaryFile(suffix='.npy', delete=False) as f:
                points = np.random.rand(10, 3)
                np.save(f.name, points)
                gt_path = Path(f.name)
            
            # Create temporary output path
            with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
                output_path = Path(f.name)
            
            try:
                report = validate_calibration(
                    extrinsic_config_path=config_path,
                    ground_truth_points_path=gt_path,
                    output_report_path=output_path
                )
                
                assert report is not None
                assert report.sensor_frame == "test_frame"
                assert output_path.exists()
                
                # Verify report content
                with open(output_path, 'r') as f:
                    saved_report = json.load(f)
                
                assert 'is_valid' in saved_report
                assert 'max_translation_error' in saved_report
                
            finally:
                output_path.unlink()
                gt_path.unlink()
                
        finally:
            config_path.unlink()

class TestCreateCalibrationValidator:
    def test_factory_function(self):
        """Test the factory function creates a validator with correct tolerances."""
        validator = create_calibration_validator(
            tolerance_translation=0.05,
            tolerance_rotation_deg=1.0
        )
        
        assert validator.tolerance_translation == 0.05
        assert validator.tolerance_rotation_deg == 1.0
        assert validator.tolerance_rotation_rad == np.deg2rad(1.0)