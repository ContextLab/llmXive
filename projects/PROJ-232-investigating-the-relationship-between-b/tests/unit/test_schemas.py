"""
Unit tests for the Pydantic schemas defined in src/models/schemas.py.

Validates that the models correctly enforce data constraints and
reject invalid input as expected.
"""

import pytest
import numpy as np
from src.models.schemas import Subject, ConnectivityMatrix, NetworkMetrics, BehavioralScore

# --- Subject Tests ---

def test_subject_valid():
    """Test creation of a valid Subject."""
    sub = Subject(subject_id="sub-001", age=25, sex="M", handedness="R")
    assert sub.subject_id == "sub-001"
    assert sub.age == 25
    assert sub.sex == "M"

def test_subject_invalid_sex():
    """Test rejection of invalid sex value."""
    with pytest.raises(ValueError):
        Subject(subject_id="sub-001", age=25, sex="X", handedness="R")

def test_subject_empty_id():
    """Test rejection of empty subject ID."""
    with pytest.raises(ValueError):
        Subject(subject_id="  ", age=25, sex="M")

def test_subject_age_out_of_range():
    """Test rejection of age outside valid range."""
    with pytest.raises(ValueError):
        Subject(subject_id="sub-001", age=-1, sex="M")
    with pytest.raises(ValueError):
        Subject(subject_id="sub-001", age=150, sex="M")

# --- ConnectivityMatrix Tests ---

def make_valid_matrix(n=3):
    """Helper to create a valid symmetric correlation matrix."""
    mat = np.eye(n)
    # Add some off-diagonal values in [-1, 1]
    for i in range(n):
        for j in range(i + 1, n):
            val = np.random.uniform(-0.8, 0.8)
            mat[i, j] = val
            mat[j, i] = val
    return mat.tolist()

def test_connectivity_valid():
    """Test creation of a valid ConnectivityMatrix."""
    mat = make_valid_matrix(3)
    cm = ConnectivityMatrix(
        subject_id="sub-001",
        matrix=mat,
        atlas_name="Schaefer200",
        n_nodes=3,
        method="pearson"
    )
    assert cm.subject_id == "sub-001"
    assert cm.n_nodes == 3

def test_connectivity_non_square():
    """Test rejection of non-square matrix."""
    mat = [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]] # 3x2
    with pytest.raises(ValueError):
        ConnectivityMatrix(
            subject_id="sub-001",
            matrix=mat,
            atlas_name="Test",
            n_nodes=3
        )

def test_connectivity_asymmetric():
    """Test rejection of asymmetric matrix."""
    mat = [[1.0, 0.5], [0.6, 1.0]] # Not symmetric
    with pytest.raises(ValueError):
        ConnectivityMatrix(
            subject_id="sub-001",
            matrix=mat,
            atlas_name="Test",
            n_nodes=2
        )

def test_connectivity_diagonal_not_one():
    """Test rejection if diagonal is not 1.0."""
    mat = [[0.9, 0.5], [0.5, 1.0]]
    with pytest.raises(ValueError):
        ConnectivityMatrix(
            subject_id="sub-001",
            matrix=mat,
            atlas_name="Test",
            n_nodes=2
        )

def test_connectivity_out_of_range():
    """Test rejection if values are outside [-1, 1]."""
    mat = [[1.0, 1.5], [1.5, 1.0]]
    with pytest.raises(ValueError):
        ConnectivityMatrix(
            subject_id="sub-001",
            matrix=mat,
            atlas_name="Test",
            n_nodes=2
        )

def test_connectivity_n_nodes_mismatch():
    """Test rejection if n_nodes does not match matrix shape."""
    mat = [[1.0, 0.5], [0.5, 1.0]]
    with pytest.raises(ValueError):
        ConnectivityMatrix(
            subject_id="sub-001",
            matrix=mat,
            atlas_name="Test",
            n_nodes=5 # Mismatch
        )

# --- NetworkMetrics Tests ---

def test_network_metrics_valid():
    """Test creation of valid NetworkMetrics."""
    nm = NetworkMetrics(
        subject_id="sub-001",
        global_efficiency=0.45,
        modularity=0.32,
        participation_coefficient=0.15,
        network_efficiency={"DMN": 0.40, "VIS": 0.38}
    )
    assert nm.global_efficiency == 0.45

def test_network_metrics_nan():
    """Test rejection of NaN values."""
    with pytest.raises(ValueError):
        NetworkMetrics(
            subject_id="sub-001",
            global_efficiency=float('nan'),
            modularity=0.32,
            participation_coefficient=0.15
        )

def test_network_metrics_negative_efficiency():
    """Test rejection of negative global efficiency."""
    with pytest.raises(ValueError):
        NetworkMetrics(
            subject_id="sub-001",
            global_efficiency=-0.1,
            modularity=0.32,
            participation_coefficient=0.15
        )

# --- BehavioralScore Tests ---

def test_behavioral_score_valid():
    """Test creation of valid BehavioralScore."""
    bs = BehavioralScore(
        subject_id="sub-001",
        bmrq_total=120.5,
        bmrq_subscores={"Appreciation": 30.0, "Emotion": 25.0},
        music_training_years=5.0
    )
    assert bs.bmrq_total == 120.5

def test_behavioral_score_nan():
    """Test rejection of NaN BMRQ total."""
    with pytest.raises(ValueError):
        BehavioralScore(
            subject_id="sub-001",
            bmrq_total=float('nan')
        )