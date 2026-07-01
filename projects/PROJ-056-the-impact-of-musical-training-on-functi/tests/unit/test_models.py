"""
Unit tests for code/data/models.py
"""
import pytest
import numpy as np
from pathlib import Path
import tempfile
import os

from code.data.models import Subject, ConnectivityMatrix, ValidationError, create_subject_from_dict


class TestSubject:
    """Tests for the Subject data model."""
    
    def test_valid_subject_creation(self):
        """Test creation of a valid Subject instance."""
        subject = Subject(
            subject_id="ABC-1234",
            group="musician",
            years_of_training=5.5,
            age=16.0,
            sex="M",
            motion_score=0.12,
            ses_score=0.75
        )
        
        assert subject.subject_id == "ABC-1234"
        assert subject.group == "musician"
        assert subject.years_of_training == 5.5
        assert subject.age == 16.0
        assert subject.sex == "M"
        assert subject.motion_score == 0.12
        assert subject.ses_score == 0.75
        assert subject._validated is True
    
    def test_invalid_subject_id_format(self):
        """Test that invalid subject_id raises ValidationError."""
        with pytest.raises(ValidationError):
            Subject(
                subject_id="invalid",
                group="musician",
                years_of_training=5.0,
                age=16.0,
                sex="M",
                motion_score=0.1,
                ses_score=0.5
            )
    
    def test_invalid_group(self):
        """Test that invalid group raises ValidationError."""
        with pytest.raises(ValidationError):
            Subject(
                subject_id="ABC-1234",
                group="invalid_group",
                years_of_training=5.0,
                age=16.0,
                sex="M",
                motion_score=0.1,
                ses_score=0.5
            )
    
    def test_invalid_sex(self):
        """Test that invalid sex raises ValidationError."""
        with pytest.raises(ValidationError):
            Subject(
                subject_id="ABC-1234",
                group="musician",
                years_of_training=5.0,
                age=16.0,
                sex="X",
                motion_score=0.1,
                ses_score=0.5
            )
    
    def test_age_out_of_range(self):
        """Test that age out of range raises ValidationError."""
        with pytest.raises(ValidationError):
            Subject(
                subject_id="ABC-1234",
                group="musician",
                years_of_training=5.0,
                age=30.0,  # Out of range
                sex="M",
                motion_score=0.1,
                ses_score=0.5
            )
    
    def test_negative_training_years(self):
        """Test that negative training years raises ValidationError."""
        with pytest.raises(ValidationError):
            Subject(
                subject_id="ABC-1234",
                group="musician",
                years_of_training=-1.0,
                age=16.0,
                sex="M",
                motion_score=0.1,
                ses_score=0.5
            )
    
    def test_ses_score_out_of_range(self):
        """Test that SES score out of range raises ValidationError."""
        with pytest.raises(ValidationError):
            Subject(
                subject_id="ABC-1234",
                group="musician",
                years_of_training=5.0,
                age=16.0,
                sex="M",
                motion_score=0.1,
                ses_score=1.5  # Out of range
            )
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        subject = Subject(
            subject_id="XYZ-5678",
            group="non_musician",
            years_of_training=0.0,
            age=14.5,
            sex="F",
            motion_score=0.25,
            ses_score=0.4
        )
        
        data = subject.to_dict()
        
        assert data["subject_id"] == "XYZ-5678"
        assert data["group"] == "non_musician"
        assert data["years_of_training"] == 0.0
        assert data["age"] == 14.5
        assert data["sex"] == "F"
        assert data["motion_score"] == 0.25
        assert data["ses_score"] == 0.4
    
    def test_create_subject_from_dict(self):
        """Test factory function for creating Subject from dict."""
        data = {
            "subject_id": "DEF-9999",
            "group": "musician",
            "years_of_training": 10.0,
            "age": 18.0,
            "sex": "F",
            "motion_score": 0.15,
            "ses_score": 0.8
        }
        
        subject = create_subject_from_dict(data)
        
        assert isinstance(subject, Subject)
        assert subject.subject_id == "DEF-9999"
        assert subject.group == "musician"
        assert subject.years_of_training == 10.0
    
    def test_create_subject_from_dict_missing_keys(self):
        """Test that missing keys raise KeyError."""
        data = {
            "subject_id": "DEF-9999",
            "group": "musician",
            # Missing other required keys
        }
        
        with pytest.raises(KeyError):
            create_subject_from_dict(data)

class TestConnectivityMatrix:
    """Tests for the ConnectivityMatrix data model."""
    
    def test_valid_matrix_creation(self):
        """Test creation of a valid ConnectivityMatrix."""
        matrix = np.array([
            [1.0, 0.5, 0.3],
            [0.5, 1.0, 0.6],
            [0.3, 0.6, 1.0]
        ])
        
        conn = ConnectivityMatrix(
            subject_id="ABC-1234",
            matrix=matrix,
            atlas="AAL",
            roi_labels=["ROI1", "ROI2", "ROI3"]
        )
        
        assert conn.subject_id == "ABC-1234"
        assert conn.atlas == "AAL"
        assert conn.roi_labels == ["ROI1", "ROI2", "ROI3"]
    
    def test_non_square_matrix_raises_error(self):
        """Test that non-square matrix raises ValueError."""
        matrix = np.array([
            [1.0, 0.5],
            [0.5, 1.0],
            [0.3, 0.6]
        ])
        
        with pytest.raises(ValueError):
            ConnectivityMatrix(
                subject_id="ABC-1234",
                matrix=matrix
            )
    
    def test_non_symmetric_matrix_raises_error(self):
        """Test that non-symmetric matrix raises ValueError."""
        matrix = np.array([
            [1.0, 0.5, 0.3],
            [0.6, 1.0, 0.4],
            [0.3, 0.6, 1.0]
        ])
        
        with pytest.raises(ValueError):
            ConnectivityMatrix(
                subject_id="ABC-1234",
                matrix=matrix
            )
    
    def test_roi_labels_length_mismatch(self):
        """Test that mismatched ROI labels raise ValueError."""
        matrix = np.array([
            [1.0, 0.5],
            [0.5, 1.0]
        ])
        
        with pytest.raises(ValueError):
            ConnectivityMatrix(
                subject_id="ABC-1234",
                matrix=matrix,
                roi_labels=["ROI1", "ROI2", "ROI3"]  # Too many
            )
    
    def test_get_edge_list(self):
        """Test conversion to edge list."""
        matrix = np.array([
            [1.0, 0.5, 0.3],
            [0.5, 1.0, 0.6],
            [0.3, 0.6, 1.0]
        ])
        
        conn = ConnectivityMatrix(
            subject_id="ABC-1234",
            matrix=matrix,
            roi_labels=["A", "B", "C"]
        )
        
        edges = conn.get_edge_list()
        
        assert len(edges) == 3
        assert edges[0]["roi_i"] == "A"
        assert edges[0]["roi_j"] == "B"
        assert edges[0]["strength"] == 0.5
        assert edges[1]["roi_i"] == "A"
        assert edges[1]["roi_j"] == "C"
        assert edges[2]["roi_i"] == "B"
        assert edges[2]["roi_j"] == "C"
    
    def test_default_roi_labels(self):
        """Test that default ROI labels are generated if not provided."""
        matrix = np.array([
            [1.0, 0.5],
            [0.5, 1.0]
        ])
        
        conn = ConnectivityMatrix(
            subject_id="ABC-1234",
            matrix=matrix
        )
        
        edges = conn.get_edge_list()
        
        assert edges[0]["roi_i"] == "ROI_0"
        assert edges[0]["roi_j"] == "ROI_1"