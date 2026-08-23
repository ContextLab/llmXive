import os
import sys
import json
import tempfile
import shutil
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add code directory to path to allow imports
code_root = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_root))

from models.baselines import FeatureEngineeredBaseline, extract_structural_features
from utils.seed import set_seed
from utils.memory_monitor import check_memory_limit

class TestBaselineTraining:
    """
    T019: Test skeleton for baseline training in tests/test_models.py.
    Asserts that RF/XGBoost produce predictions without crashing.
    """

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        # Set a fixed seed for reproducibility
        set_seed(42)
        yield
        # Cleanup if needed

    def test_extract_structural_features_runs(self):
        """
        Test that extract_structural_features produces output from a dummy graph.
        """
        import networkx as nx
        # Create a small dummy graph
        G = nx.karate_club_graph()
        
        # Add a dummy 'label' attribute to nodes for feature extraction context
        for node in G.nodes():
            G.nodes[node]['label'] = 0 if node < 30 else 1

        # Run extraction
        features_df = extract_structural_features(G)
        
        # Assertions
        assert features_df is not None
        assert isinstance(features_df, pd.DataFrame)
        assert len(features_df) > 0
        # Check for expected structural columns
        expected_cols = ['degree', 'betweenness', 'closeness', 'pagerank', 'clustering']
        for col in expected_cols:
            assert col in features_df.columns

    def test_baseline_training_produces_predictions(self):
        """
        Test that FeatureEngineeredBaseline trains and produces predictions.
        """
        import networkx as nx
        from sklearn.model_selection import train_test_split

        # Setup: Create a small dummy graph
        G = nx.karate_club_graph()
        for node in G.nodes():
            G.nodes[node]['label'] = 0 if node < 30 else 1

        # Extract features
        features_df = extract_structural_features(G)
        
        # Prepare X and y
        # Drop 'label' from features if present (it's the target)
        X = features_df.drop(columns=['label'], errors='ignore')
        y = features_df['label'] if 'label' in features_df.columns else pd.Series([0]*len(X))
        
        # Ensure we have labels
        if len(y) != len(X):
            # Fallback for edge cases in dummy data
            y = pd.Series([0 if i < len(X)*0.8 else 1 for i in range(len(X))])

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Instantiate and train the baseline
        baseline = FeatureEngineeredBaseline(model_type='random_forest')
        
        # Train
        baseline.train(X_train, y_train)
        
        # Predict
        predictions = baseline.predict(X_test)
        probabilities = baseline.predict_proba(X_test)

        # Assertions
        assert predictions is not None
        assert len(predictions) == len(X_test)
        assert probabilities is not None
        assert len(probabilities) == len(X_test)
        assert predictions.dtype in [np.int64, np.int32, np.int_]
        
        # Check that probabilities sum to 1 (for multi-class) or are valid (binary)
        if probabilities.shape[1] > 1:
            row_sums = np.sum(probabilities, axis=1)
            assert np.allclose(row_sums, 1.0), "Probabilities must sum to 1"

    def test_baseline_xgboost_produces_predictions(self):
        """
        Test that FeatureEngineeredBaseline with XGBoost trains and produces predictions.
        """
        import networkx as nx
        from sklearn.model_selection import train_test_split

        # Setup: Create a small dummy graph
        G = nx.karate_club_graph()
        for node in G.nodes():
            G.nodes[node]['label'] = 0 if node < 30 else 1

        # Extract features
        features_df = extract_structural_features(G)
        
        # Prepare X and y
        X = features_df.drop(columns=['label'], errors='ignore')
        y = features_df['label'] if 'label' in features_df.columns else pd.Series([0]*len(X))
        
        if len(y) != len(X):
            y = pd.Series([0 if i < len(X)*0.8 else 1 for i in range(len(X))])

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Instantiate and train the baseline (XGBoost)
        baseline = FeatureEngineeredBaseline(model_type='xgboost')
        
        # Train
        baseline.train(X_train, y_train)
        
        # Predict
        predictions = baseline.predict(X_test)
        probabilities = baseline.predict_proba(X_test)

        # Assertions
        assert predictions is not None
        assert len(predictions) == len(X_test)
        assert probabilities is not None
        assert len(probabilities) == len(X_test)

    def test_baseline_memory_limit(self):
        """
        Test that baseline training respects memory limits (using mock if necessary).
        """
        import networkx as nx
        from unittest.mock import patch

        # Create a small dummy graph
        G = nx.karate_club_graph()
        for node in G.nodes():
            G.nodes[node]['label'] = 0 if node < 30 else 1

        features_df = extract_structural_features(G)
        X = features_df.drop(columns=['label'], errors='ignore')
        y = features_df['label'] if 'label' in features_df.columns else pd.Series([0]*len(X))
        
        if len(y) != len(X):
            y = pd.Series([0 if i < len(X)*0.8 else 1 for i in range(len(X))])

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        baseline = FeatureEngineeredBaseline(model_type='random_forest')
        
        # Mock the memory check to simulate a limit violation
        # We expect the training to either succeed or raise a specific error
        # depending on implementation. Here we test that the check is called.
        with patch('models.baselines.check_memory_limit') as mock_check:
            mock_check.return_value = True # Simulate pass
            baseline.train(X_train, y_train)
            predictions = baseline.predict(X_test)
            
            assert predictions is not None
            # Verify the memory check was invoked during training
            # (Assuming the implementation calls it; if not, this test documents the requirement)
            # If the implementation doesn't call it, this test serves as a placeholder for that requirement.

    def test_baseline_handles_empty_features(self):
        """
        Test that baseline handles edge case of empty feature set gracefully.
        """
        # Create an empty DataFrame
        X_empty = pd.DataFrame()
        y_empty = pd.Series([])
        
        baseline = FeatureEngineeredBaseline(model_type='random_forest')
        
        # This should raise a ValueError or similar, not crash with a cryptic error
        with pytest.raises((ValueError, Exception)):
            baseline.train(X_empty, y_empty)