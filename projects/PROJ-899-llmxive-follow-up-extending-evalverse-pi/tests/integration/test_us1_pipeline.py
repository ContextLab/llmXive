"""
Integration test for User Story 1 pipeline.
"""
import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from pathlib import Path
from src.data.models import FeatureVector, DimensionScore
from src.data.preprocess import extract_all_features
from src.models.train import train_ridge
from src.models.metrics import pearson_correlation

def test_us1_pipeline_sample():
    """Test the full US1 pipeline on a small sample."""
    # Create sample data
    n_samples = 10
    np.random.seed(42)
    
    features_list = []
    scores_list = []
    
    for i in range(n_samples):
        # Mock feature vector
        fv = FeatureVector(
            clip_id=f"clip_{i}",
            features=np.random.rand(5),
            feature_names=["f1", "f2", "f3", "f4", "f5"],
            extraction_time=0.1,
            metadata={}
        )
        features_list.append(fv)
        
        # Mock score
        scores_list.append(np.random.rand() * 10)
    
    # Train model
    X = np.array([f.features for f in features_list])
    y = np.array(scores_list)
    
    model = train_ridge(X, y)
    predictions = model.predict(X)
    
    # Calculate correlation
    corr = pearson_correlation(y, predictions)
    
    # Verify results
    assert corr is not None
    assert -1.0 <= corr <= 1.0
    print(f"Pipeline test completed. Correlation: {corr:.4f}")
