"""
Verification script for T008.
Ensures that the data classes defined in code/entities.py can be imported
and instantiated without syntax errors.
"""
import sys
import os

# Ensure the code directory is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

def test_entities_import():
    """Test that all required entities can be imported."""
    try:
        from entities import (
            EEGRecording,
            MicrostateSegmentation,
            MicrostateFeatures,
            AffectiveScores,
            CorrelationResult
        )
        print("SUCCESS: All entities imported successfully.")
    except ImportError as e:
        print(f"FAILED: Import error - {e}")
        raise

def test_entities_instantiation():
    """Test that entities can be instantiated with basic data."""
    import numpy as np
    from datetime import datetime

    from entities import (
        EEGRecording,
        MicrostateSegmentation,
        MicrostateFeatures,
        AffectiveScores,
        CorrelationResult
    )

    # Test EEGRecording
    eeg = EEGRecording(
        subject_id="sub-001",
        session_id="ses-01",
        task="rest",
        sampling_frequency=250.0,
        channel_count=64,
        data=np.zeros((64, 1000)),
        channel_names=[f"EEG{i:03d}" for i in range(64)]
    )
    assert eeg.subject_id == "sub-001"

    # Test MicrostateSegmentation
    seg = MicrostateSegmentation(
        subject_id="sub-001",
        session_id="ses-01",
        segment_labels=np.array([0, 1, 2, 3, 0]),
        global_explained_variance=0.85
    )
    assert seg.global_explained_variance == 0.85

    # Test MicrostateFeatures
    features = MicrostateFeatures(
        subject_id="sub-001",
        session_id="ses-01",
        mean_duration={"A": 80.0, "B": 75.0, "C": 90.0, "D": 85.0},
        occurrence_rate={"A": 3.0, "B": 2.5, "C": 3.2, "D": 2.8},
        coverage={"A": 0.25, "B": 0.20, "C": 0.30, "D": 0.25},
        transition_probabilities={"A": {"B": 0.5, "C": 0.5}}
    )
    assert "A" in features.mean_duration

    # Test AffectiveScores
    affective = AffectiveScores(
        subject_id="sub-001",
        session_id="ses-01",
        instrument_type="PANAS",
        scores={"positive": 22.0, "negative": 14.0},
        response_rate=1.0
    )
    assert affective.scores["positive"] == 22.0

    # Test CorrelationResult
    corr = CorrelationResult(
        feature_name="mean_duration",
        feature_class="A",
        affective_dimension="positive",
        correlation_coefficient=0.45,
        p_value=0.03,
        method="pearson",
        n_subjects=15
    )
    assert corr.is_significant == False  # p > 0.01 threshold (example)

    print("SUCCESS: All entities instantiated successfully.")

if __name__ == "__main__":
    test_entities_import()
    test_entities_instantiation()
    print("All T008 verification checks passed.")