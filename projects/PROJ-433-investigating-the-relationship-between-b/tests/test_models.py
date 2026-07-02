"""
Tests for the Subject entity model.
"""
import os
import tempfile
import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from models import Subject


class TestSubjectInit:
    """Tests for Subject initialization."""

    def test_minimal_initialization(self):
        """Test creating a subject with minimal required fields."""
        subject = Subject(id="sub-001", fMRI_path="/fake/path.nii")
        assert subject.id == "sub-001"
        assert subject.fMRI_path == "/fake/path.nii"
        assert subject.DSST_score is None
        assert subject.qc_metrics == {}

    def test_full_initialization(self):
        """Test creating a subject with all fields."""
        subject = Subject(
            id="sub-002",
            fMRI_path="/fake/path2.nii",
            DSST_score=85.5,
            qc_metrics={"fd": 0.2, "t1": "pass"}
        )
        assert subject.id == "sub-002"
        assert subject.fMRI_path == "/fake/path2.nii"
        assert subject.DSST_score == 85.5
        assert subject.qc_metrics == {"fd": 0.2, "t1": "pass"}

    def test_explicit_none_dsst(self):
        """Test that DSST_score can be explicitly None."""
        subject = Subject(id="sub-003", fMRI_path="/fake.nii", DSST_score=None)
        assert subject.DSST_score is None


class TestSubjectHasValidData:
    """Tests for the has_valid_data() method."""

    def test_valid_data_returns_true(self):
        """Test that valid data (file exists + score present) returns True."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".nii") as tmp:
            tmp_path = tmp.name

        try:
            subject = Subject(
                id="sub-valid",
                fMRI_path=tmp_path,
                DSST_score=90.0
            )
            assert subject.has_valid_data() is True
        finally:
            os.unlink(tmp_path)

    def test_missing_file_returns_false(self):
        """Test that missing fMRI file returns False."""
        subject = Subject(
            id="sub-missing",
            fMRI_path="/nonexistent/path.nii",
            DSST_score=90.0
        )
        assert subject.has_valid_data() is False

    def test_missing_dsst_returns_false(self):
        """Test that missing DSST score returns False even if file exists."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".nii") as tmp:
            tmp_path = tmp.name

        try:
            subject = Subject(
                id="sub-no-score",
                fMRI_path=tmp_path,
                DSST_score=None
            )
            assert subject.has_valid_data() is False
        finally:
            os.unlink(tmp_path)

    def test_both_missing_returns_false(self):
        """Test that missing both file and score returns False."""
        subject = Subject(
            id="sub-bad",
            fMRI_path="/nonexistent.nii",
            DSST_score=None
        )
        assert subject.has_valid_data() is False

    def test_empty_path_returns_false(self):
        """Test that empty fMRI_path returns False."""
        subject = Subject(
            id="sub-empty",
            fMRI_path="",
            DSST_score=50.0
        )
        assert subject.has_valid_data() is False


class TestSubjectSerialization:
    """Tests for dictionary conversion methods."""

    def test_to_dict(self):
        """Test converting subject to dictionary."""
        subject = Subject(
            id="sub-001",
            fMRI_path="/data/sub-001.nii",
            DSST_score=75.5,
            qc_metrics={"fd": 0.3}
        )
        data = subject.to_dict()
        
        assert data['id'] == "sub-001"
        assert data['fMRI_path'] == "/data/sub-001.nii"
        assert data['DSST_score'] == 75.5
        assert data['qc_metrics'] == {"fd": 0.3}

    def test_from_dict(self):
        """Test creating subject from dictionary."""
        data = {
            'id': 'sub-002',
            'fMRI_path': '/data/sub-002.nii',
            'DSST_score': 88.0,
            'qc_metrics': {'fd': 0.1}
        }
        subject = Subject.from_dict(data)
        
        assert subject.id == "sub-002"
        assert subject.fMRI_path == "/data/sub-002.nii"
        assert subject.DSST_score == 88.0
        assert subject.qc_metrics == {'fd': 0.1}

    def test_from_dict_missing_optional(self):
        """Test creating subject from dict with missing optional fields."""
        data = {
            'id': 'sub-003',
            'fMRI_path': '/data/sub-003.nii'
        }
        subject = Subject.from_dict(data)
        
        assert subject.id == "sub-003"
        assert subject.fMRI_path == "/data/sub-003.nii"
        assert subject.DSST_score is None
        assert subject.qc_metrics == {}

    def test_round_trip(self):
        """Test that to_dict -> from_dict preserves data."""
        original = Subject(
            id="sub-round",
            fMRI_path="/data/round.nii",
            DSST_score=60.0,
            qc_metrics={"fd": 0.4, "status": "ok"}
        )
        data = original.to_dict()
        reconstructed = Subject.from_dict(data)
        
        assert reconstructed.id == original.id
        assert reconstructed.fMRI_path == original.fMRI_path
        assert reconstructed.DSST_score == original.DSST_score
        assert reconstructed.qc_metrics == original.qc_metrics


class TestSubjectRepr:
    """Tests for string representation."""

    def test_repr_format(self):
        """Test that __repr__ returns a valid representation."""
        subject = Subject(
            id="sub-001",
            fMRI_path="/data/test.nii",
            DSST_score=100.0,
            qc_metrics={"fd": 0.2}
        )
        rep = repr(subject)
        
        assert "Subject" in rep
        assert "sub-001" in rep
        assert "/data/test.nii" in rep
        assert "100.0" in rep