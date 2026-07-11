"""
Unit tests for the metadata schemas defined in code/metadata/schemas.py.
"""
import pytest
from code.metadata.schemas import Subject, ConnectivityMatrix, FeatureVector


class TestSubjectSchema:
    def test_valid_subject(self):
        """Test creation of a valid Subject instance."""
        sub = Subject(
            subject_id="sub-001",
            diagnosis="SZ",
            age=35.5,
            sex="M"
        )
        assert sub.subject_id == "sub-001"
        assert sub.diagnosis == "SZ"
        assert sub.motion_flag is False

    def test_invalid_subject_id_format(self):
        """Test that invalid subject ID format raises error."""
        with pytest.raises(ValueError):
            Subject(
                subject_id="subject-001", # Missing 'sub-' prefix
                diagnosis="HC",
                age=30.0,
                sex="F"
            )

    def test_invalid_age_range(self):
        """Test that age outside [18, 100] raises error."""
        with pytest.raises(ValueError):
            Subject(
                subject_id="sub-002",
                diagnosis="HC",
                age=15.0,
                sex="F"
            )

    def test_optional_fields(self):
        """Test that optional fields can be None."""
        sub = Subject(
            subject_id="sub-003",
            diagnosis="SZ",
            age=40.0,
            sex="M",
            medication_status=None,
            exclusion_reason=None
        )
        assert sub.medication_status is None


class TestConnectivityMatrixSchema:
    def test_valid_matrix(self):
        """Test creation of a valid ConnectivityMatrix instance."""
        matrix = ConnectivityMatrix(
            subject_id="sub-001",
            matrix_path="data/processed/sub-001_matrix.npy",
            dimension=90
        )
        assert matrix.atlas == "AAL"
        assert matrix.is_psd is False

    def test_invalid_matrix_path(self):
        """Test that invalid matrix path raises error."""
        with pytest.raises(ValueError):
            ConnectivityMatrix(
                subject_id="sub-001",
                matrix_path="raw_data/sub-001.npy", # Wrong directory
                dimension=90
            )

    def test_invalid_dimension(self):
        """Test that dimension <= 0 raises error."""
        with pytest.raises(ValueError):
            ConnectivityMatrix(
                subject_id="sub-001",
                matrix_path="data/processed/sub-001.npy",
                dimension=0
            )


class TestFeatureVectorSchema:
    def test_valid_features(self):
        """Test creation of a valid FeatureVector instance."""
        features = FeatureVector(
            subject_id="sub-001",
            global_efficiency=0.45,
            local_efficiency=0.60,
            modularity=0.35,
            betweenness_centrality_mean=0.02,
            prefrontal_centrality=0.05,
            hippocampal_centrality=0.04
        )
        assert features.global_efficiency == 0.45

    def test_efficiency_bounds(self):
        """Test that efficiency values must be in [0, 1]."""
        with pytest.raises(ValueError):
            FeatureVector(
                subject_id="sub-001",
                global_efficiency=1.5, # Out of bounds
                local_efficiency=0.60,
                modularity=0.35,
                betweenness_centrality_mean=0.02,
                prefrontal_centrality=0.05,
                hippocampal_centrality=0.04
            )

    def test_invalid_feature_path(self):
        """Test that invalid feature path raises error."""
        with pytest.raises(ValueError):
            FeatureVector(
                subject_id="sub-001",
                global_efficiency=0.45,
                local_efficiency=0.60,
                modularity=0.35,
                betweenness_centrality_mean=0.02,
                prefrontal_centrality=0.05,
                hippocampal_centrality=0.04,
                feature_vector_path="data/raw/features.csv" # Wrong directory
            )
