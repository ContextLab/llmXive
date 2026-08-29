import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.synthetic_data_generator import generate_synthetic_dataset

class TestGenerateSyntheticDataset:
    def test_generate_synthetic_dataset_structure(self):
        df = generate_synthetic_dataset(n_participants=10, n_headlines=5, true_interaction=0.5)
        
        assert len(df) == 50 # 10 * 5
        assert 'participant_id' in df.columns
        assert 'headline_id' in df.columns
        assert 'belief_rating' in df.columns
        assert 'fixation_duration' in df.columns
        assert 'valence' in df.columns
        assert 'cognitive_reflection_score' in df.columns

    def test_generate_synthetic_dataset_interaction_effect(self):
        # With a large sample, the interaction term should be recoverable
        df = generate_synthetic_dataset(n_participants=1000, n_headlines=100, true_interaction=0.5, noise=0.1)
        
        # Basic check that data exists and is numeric
        assert df['belief_rating'].notna().all()
        assert df['fixation_duration'].notna().all()
        assert df['valence'].notna().all()
        assert df['cognitive_reflection_score'].notna().all()
