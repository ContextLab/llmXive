"""
Contract test for feature extraction output schema.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from src.data.models import FeatureVector

def test_feature_extraction_schema():
    """Test that feature extraction produces correct schema."""
    # Create a mock FeatureVector
    features = FeatureVector(
        clip_id="test_001",
        features=np.array([1.0, 2.0, 3.0]),
        feature_names=["optical_flow_mean", "optical_flow_var", "spectral_centroid_mean"],
        extraction_time=0.5,
        metadata={"source": "test.mp4"}
    )
    
    # Verify schema
    assert hasattr(features, "clip_id")
    assert hasattr(features, "features")
    assert hasattr(features, "feature_names")
    assert hasattr(features, "extraction_time")
    assert hasattr(features, "metadata")
    
    assert isinstance(features.clip_id, str)
    assert isinstance(features.features, np.ndarray)
    assert isinstance(features.feature_names, list)
    assert isinstance(features.extraction_time, float)
    assert isinstance(features.metadata, dict)
