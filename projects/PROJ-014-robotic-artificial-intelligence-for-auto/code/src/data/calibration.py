"""
Calibration module for extrinsic parameter validation and coordinate transformation.

This module provides:
- ExtrinsicParams: Dataclass for storing rotation and translation matrices.
- CalibrationReport: Dataclass for storing validation results.
- CalibrationValidator: Class to perform validation checks.
- validate_calibration: Function to execute validation and return a report.
- create_calibration_validator: Factory function for the validator.
"""
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class ExtrinsicParams:
    """
    Stores extrinsic calibration parameters for sensor coordinate transformations.
    
    Attributes:
        rotation_matrix: 3x3 or 4x4 rotation matrix (numpy array)
        translation_vector: 3x1 or 4x1 translation vector (numpy array)
        source_frame: Name of the source coordinate frame
        target_frame: Name of the target coordinate frame
    """
    rotation_matrix: np.ndarray = None
    translation_vector: np.ndarray = None
    source_frame: str = "sensor"
    target_frame: "world"

    def __post_init__(self):
        if self.rotation_matrix is None:
            self.rotation_matrix = np.eye(3)
        elif isinstance(self.rotation_matrix, list):
            self.rotation_matrix = np.array(self.rotation_matrix)
        
        if self.translation_vector is None:
            self.translation_vector = np.zeros(3)
        elif isinstance(self.translation_vector, list):
            self.translation_vector = np.array(self.translation_vector)

        # Ensure types are numpy arrays
        self.rotation_matrix = np.asarray(self.rotation_matrix, dtype=np.float64)
        self.translation_vector = np.asarray(self.translation_vector, dtype=np.float64)

    def transform_point(self, point: np.ndarray) -> np.ndarray:
        """
        Transform a point from source frame to target frame.
        
        Args:
            point: Input point in source frame (3,) or (4,) homogeneous
          
        Returns:
            Transformed point in target frame
        """
        if point.shape == (3,):
            # Use 3x3 rotation and 3x1 translation
            return self.rotation_matrix @ point + self.translation_vector
        elif point.shape == (4,):
            # Assume homogeneous coordinates
            R = self.rotation_matrix
            t = self.translation_vector
            # Construct 4x4 matrix
            T = np.eye(4)
            T[:3, :3] = R
            T[:3, 3] = t
            return T @ point
        else:
            raise ValueError(f"Point must be 3D or 4D, got {point.shape}")

    def is_valid(self) -> Tuple[bool, str]:
        """
        Check if the extrinsic parameters are numerically valid.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if self.rotation_matrix.shape not in [(3, 3), (4, 4)]:
            return False, f"Invalid rotation matrix shape: {self.rotation_matrix.shape}"
        
        if self.translation_vector.shape not in [(3,), (4,)]:
            return False, f"Invalid translation vector shape: {self.translation_vector.shape}"
        
        # Check for NaN or Inf
        if np.any(np.isnan(self.rotation_matrix)) or np.any(np.isinf(self.rotation_matrix)):
            return False, "Rotation matrix contains NaN or Inf values"
        
        if np.any(np.isnan(self.translation_vector)) or np.any(np.isinf(self.translation_vector)):
            return False, "Translation vector contains NaN or Inf values"

        # Check rotation matrix orthogonality (for 3x3)
        if self.rotation_matrix.shape == (3, 3):
            det = np.linalg.det(self.rotation_matrix)
            if not np.isclose(det, 1.0, atol=1e-6):
                return False, f"Rotation matrix determinant is {det}, expected ~1.0"
            
            # Check orthogonality: R * R^T should be I
            ortho_check = self.rotation_matrix @ self.rotation_matrix.T
            if not np.allclose(ortho_check, np.eye(3), atol=1e-6):
                return False, "Rotation matrix is not orthogonal"

        return True, ""

@dataclass
class CalibrationReport:
    """
    Stores the result of a calibration validation.
    
    Attributes:
        status: "passed", "failed", or "warning"
        validation_passed: Boolean flag
        error_message: Description of failure if any
        metrics: Dictionary of validation metrics (e.g., reprojection error)
        timestamp: ISO format timestamp of validation
    """
    status: str = "unknown"
    validation_passed: bool = False
    error_message: Optional[str] = None
    metrics: Dict[str, float] = None
    timestamp: Optional[str] = None

    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {}

class CalibrationValidator:
    """
    Performs validation checks on extrinsic calibration parameters.
    
    This class encapsulates the logic for checking:
    - Parameter validity (NaN, Inf, dimensions)
    - Orthogonality of rotation matrices
    - Determinant of rotation matrix
    - Threshold checks on derived metrics (e.g., reprojection error)
    """
    def __init__(self, extrinsic_params: ExtrinsicParams, thresholds: Optional[Dict[str, float]] = None):
        self.params = extrinsic_params
        self.thresholds = thresholds or {
            "ortho_tolerance": 1e-6,
            "det_tolerance": 1e-6,
            "reprojection_error_max": 0.1
        }
        self.logger = logging.getLogger(__name__)

    def check_orthogonality(self) -> Tuple[bool, float]:
        """
        Check if rotation matrix is orthogonal.
        
        Returns:
            Tuple of (is_valid, error_value)
        """
        if self.params.rotation_matrix.shape != (3, 3):
            return False, float('inf')
        
        R = self.params.rotation_matrix
        identity = np.eye(3)
        error = np.linalg.norm(R @ R.T - identity)
        is_valid = error < self.thresholds["ortho_tolerance"]
        return is_valid, error

    def check_determinant(self) -> Tuple[bool, float]:
        """
        Check if rotation matrix determinant is close to 1.
        
        Returns:
            Tuple of (is_valid, error_value)
        """
        if self.params.rotation_matrix.shape != (3, 3):
            return False, float('inf')
        
        det = np.linalg.det(self.params.rotation_matrix)
        error = abs(det - 1.0)
        is_valid = error < self.thresholds["det_tolerance"]
        return is_valid, error

    def check_numerical_stability(self) -> Tuple[bool, str]:
        """
        Check for NaN or Inf in parameters.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if np.any(np.isnan(self.params.rotation_matrix)) or np.any(np.isinf(self.params.rotation_matrix)):
            return False, "Rotation matrix contains NaN or Inf"
        if np.any(np.isnan(self.params.translation_vector)) or np.any(np.isinf(self.params.translation_vector)):
            return False, "Translation vector contains NaN or Inf"
        return True, ""

    def validate(self) -> CalibrationReport:
        """
        Run all validation checks and return a report.
        
        Returns:
            CalibrationReport with status and metrics
        """
        import datetime
        report = CalibrationReport(
            status="unknown",
            validation_passed=False,
            metrics={}
        )
        
        # Check numerical stability
        stable, err_msg = self.check_numerical_stability()
        if not stable:
            report.status = "failed"
            report.error_message = err_msg
            return report

        # Check orthogonality
        ortho_valid, ortho_err = self.check_orthogonality()
        report.metrics["ortho_error"] = float(ortho_err)
        
        # Check determinant
        det_valid, det_err = self.check_determinant()
        report.metrics["det_error"] = float(det_err)

        # Aggregate results
        all_valid = ortho_valid and det_valid
        
        if all_valid:
            report.status = "passed"
            report.validation_passed = True
        else:
            report.status = "failed"
            report.validation_passed = False
            errors = []
            if not ortho_valid:
                errors.append(f"Orthogonality error {ortho_err:.2e} > threshold {self.thresholds['ortho_tolerance']}")
            if not det_valid:
                errors.append(f"Determinant error {det_err:.2e} > threshold {self.thresholds['det_tolerance']}")
            report.error_message = "; ".join(errors)

        report.timestamp = datetime.datetime.now().isoformat()
        return report

def create_calibration_validator(extrinsic_params: ExtrinsicParams, thresholds: Optional[Dict[str, float]] = None) -> CalibrationValidator:
    """
    Factory function to create a CalibrationValidator.
    
    Args:
        extrinsic_params: The calibration parameters to validate
        thresholds: Optional dictionary of validation thresholds
        
    Returns:
        CalibrationValidator instance
    """
    return CalibrationValidator(extrinsic_params, thresholds)

def validate_calibration(validator: CalibrationValidator, extrinsic_params: ExtrinsicParams) -> CalibrationReport:
    """
    Execute calibration validation using the provided validator.
    
    Args:
        validator: The CalibrationValidator instance
        extrinsic_params: The parameters being validated (for redundancy/override)
        
    Returns:
        CalibrationReport with validation results
    """
    # The validator already holds the params, but we ensure consistency
    if not np.allclose(validator.params.rotation_matrix, extrinsic_params.rotation_matrix):
        logger.warning("Validator params differ from input params. Using validator params.")
    
    return validator.validate()