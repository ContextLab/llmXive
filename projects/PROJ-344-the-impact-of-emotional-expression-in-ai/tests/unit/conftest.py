"""
Pytest configuration and fixtures for unit tests.
"""
import pytest
import numpy as np
import pandas as pd
import os
import sys

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

@pytest.fixture
def sample_metadata():
    """
    Create a sample metadata DataFrame for testing.
    
    Returns:
        tuple: (X_features, y_trust)
    """
    np.random.seed(42)
    n_samples = 100
    
    consistency_score = np.random.uniform(0, 1, n_samples)
    avatar_type = np.random.choice(['emotional', 'neutral', 'expressive'], n_samples)
    duration = np.random.uniform(30, 300, n_samples)
    difficulty = np.random.choice([1, 2, 3, 4, 5], n_samples)
    
    # Generate ordinal trust scores with some correlation to consistency
    base_trust = 3 + 2 * consistency_score
    noise = np.random.normal(0, 0.8, n_samples)
    raw_trust = base_trust + noise + (difficulty * 0.1)
    trust_scores = np.clip(raw_trust, 1, 5).astype(int)
    
    X = pd.DataFrame({
        'consistency_score': consistency_score,
        'avatar_type': avatar_type,
        'duration': duration,
        'difficulty': difficulty
    })
    
    y = pd.Series(trust_scores, name='trust_score')
    
    return X, y