"""
Unit tests for the data model classes in code/models/.
Verifies dataclass initialization, validation, and basic properties.
"""
import pytest
import numpy as np
from dataclasses import fields

from models.subject import Subject, SubjectStatus
from models.connectivity import ConnectivityMatrix
from models.topology import TopologyMetrics
from models.behavioral import IllusionScore


class TestSubject:
    def test_subject_creation(self):
        """Test basic Subject creation."""
        sub = Subject(subject_id="sub-01")
        assert sub.subject_id == "sub-01"
        assert sub.status == SubjectStatus.PENDING
        assert sub.is_excluded() is False

    def test_subject_exclusion(self):
        """Test subject exclusion logic."""
        sub = Subject(subject_id="sub-02")
        sub.set_excluded("High motion")
        assert sub.status == SubjectStatus.EXCLUDED
        assert sub.exclusion_reason == "High motion"
        assert sub.is_excluded() is True

    def test_subject_fd_recording(self):
        """Test that FD can be recorded before exclusion."""
        sub = Subject(subject_id="sub-03")
        sub.mean_fd = 0.6
        sub.set_excluded("Mean FD > 0.5")
        assert sub.mean_fd == 0.6
        assert sub.is_excluded() is True


class TestConnectivityMatrix:
    def test_matrix_creation(self):
        """Test ConnectivityMatrix creation with valid data."""
        n = 200
        mat = np.random.rand(n, n)
        mat = (mat + mat.T) / 2  # Make symmetric
        np.fill_diagonal(mat, 1.0)
        
        cm = ConnectivityMatrix(subject_id="sub-01", matrix=mat)
        assert cm.n_regions == 200
        assert cm.is_symmetric
        assert cm.is_weighted
        assert cm.is_binary is False

    def test_matrix_validation_shape(self):
        """Test that non-square matrices raise errors."""
        with pytest.raises(ValueError):
            ConnectivityMatrix(subject_id="sub-01", matrix=np.random.rand(10, 20))

    def test_matrix_validation_ndim(self):
        """Test that non-2D matrices raise errors."""
        with pytest.raises(ValueError):
            ConnectivityMatrix(subject_id="sub-01", matrix=np.array([1, 2, 3]))

    def test_upper_triangle_extraction(self):
        """Test extracting upper triangle."""
        mat = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]], dtype=float)
        cm = ConnectivityMatrix(subject_id="sub-01", matrix=mat)
        
        upper = cm.get_upper_triangle(include_diag=False)
        # Expected: (0,1), (0,2), (1,2) -> 2, 3, 6
        expected = np.array([2.0, 3.0, 6.0])
        np.testing.assert_array_equal(upper, expected)


class TestTopologyMetrics:
    def test_metrics_creation(self):
        """Test TopologyMetrics creation."""
        tm = TopologyMetrics(
            subject_id="sub-01",
            modularity=0.45,
            characteristic_path_length=2.1,
            clustering_coefficient=0.35,
            global_efficiency=0.48,
            small_worldness=1.2
        )
        assert tm.modularity == 0.45
        assert tm.validate() is True

    def test_metrics_modularity_bounds(self):
        """Test modularity out of bounds detection."""
        tm = TopologyMetrics(subject_id="sub-01", modularity=1.5)
        assert tm.validate() is False
        assert 'modularity_out_of_bounds' in tm.flags

    def test_metrics_path_length_bounds(self):
        """Test path length non-positive detection."""
        tm = TopologyMetrics(subject_id="sub-01", characteristic_path_length=-0.1)
        assert tm.validate() is False
        assert 'path_length_non_positive' in tm.flags

    def test_metrics_efficiency_bounds(self):
        """Test global efficiency > 1.0 detection."""
        tm = TopologyMetrics(subject_id="sub-01", global_efficiency=1.5)
        assert tm.validate() is False
        assert 'efficiency_out_of_bounds' in tm.flags


class TestIllusionScore:
    def test_score_creation(self):
        """Test IllusionScore creation."""
        score = IllusionScore(
            subject_id="sub-01",
            muller_lyer_score=12.5,
            ponzo_score=8.3
        )
        assert score.muller_lyer_score == 12.5
        assert score.ponzo_score == 8.3
        assert score.is_complete() is True

    def test_score_incomplete(self):
        """Test is_complete when one score is missing."""
        score = IllusionScore(
            subject_id="sub-01",
            muller_lyer_score=12.5,
            ponzo_score=None
        )
        assert score.is_complete() is False

    def test_average_score(self):
        """Test average calculation."""
        score = IllusionScore(
            subject_id="sub-01",
            muller_lyer_score=10.0,
            ponzo_score=20.0
        )
        assert score.average_illusion_score() == 15.0

    def test_average_score_incomplete(self):
        """Test average returns None if incomplete."""
        score = IllusionScore(
            subject_id="sub-01",
            muller_lyer_score=10.0,
            ponzo_score=None
        )
        assert score.average_illusion_score() is None
