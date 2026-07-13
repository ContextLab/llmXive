"""
Unit tests for data preprocessing logic.
Specifically tests for Cycle-Agnostic fallback logic as per T018.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.data.preprocessing import fill_gaps, detect_cycle_boundaries, load_raw_data
from code.models.train_fallback import prepare_fallback_features, train_fallback_model
from code.config import ensure_directories


class TestCycleAgnosticFallbackLogic:
    """
    Unit tests for the Cycle-Agnostic fallback logic.
    This tests the core mechanism where a global model (no Cycle ID) is used
    to predict TSI for cycles not seen during training or for pre-satellite eras.
    """

    @pytest.fixture
    def mock_preprocessed_data(self):
        """
        Create a mock preprocessed dataset mimicking the output of run_preprocessing.
        Contains GSN, TSI, and Cycle ID for a few cycles.
        """
        dates = pd.date_range(start='2003-01-01', end='2023-12-31', freq='M')
        n = len(dates)
        
        # Simulate GSN data with noise
        gsn = 50 + 30 * np.sin(np.linspace(0, 4 * np.pi, n)) + np.random.normal(0, 5, n)
        
        # Simulate TSI data (correlated with GSN)
        tsi = 1361.5 + 0.001 * gsn + np.random.normal(0, 0.05, n)
        
        # Assign cycle IDs (simplified mapping for 2003-2023)
        # Cycle 23: ~2003-2008, Cycle 24: ~2009-2019, Cycle 25: ~2020-present
        cycle_ids = np.where(dates.year < 2009, 23, 
                             np.where(dates.year < 2020, 24, 25))
        
        df = pd.DataFrame({
            'date': dates,
            'gsn': gsn,
            'tsi': tsi,
            'cycle_id': cycle_ids
        })
        return df

    @pytest.fixture
    def mock_pre_satellite_data(self):
        """
        Create mock pre-satellite data (e.g., 1900-1950) with Cycle IDs
        that are NOT present in the training set (simulating unseen cycles).
        """
        dates = pd.date_range(start='1900-01-01', end='1950-12-31', freq='M')
        n = len(dates)
        
        # Simulate GSN data
        gsn = 40 + 25 * np.sin(np.linspace(0, 3 * np.pi, n)) + np.random.normal(0, 4, n)
        
        # Create a DataFrame without TSI (since we are testing prediction)
        # but with Cycle IDs that are distinct from the training set
        cycle_ids = np.full(n, 16) # Maunder minimum era or similar, distinct from 23/24/25
        
        df = pd.DataFrame({
            'date': dates,
            'gsn': gsn,
            'cycle_id': cycle_ids
        })
        return df

    def test_fallback_feature_preparation_excludes_cycle_id(self, mock_preprocessed_data):
        """
        Verify that prepare_fallback_features correctly drops 'cycle_id' 
        to ensure the model is Cycle-Agnostic.
        """
        X, y = prepare_fallback_features(mock_preprocessed_data)
        
        # Check that 'cycle_id' is NOT in the feature set
        assert 'cycle_id' not in X.columns, "Cycle-Agnostic model must not use cycle_id as a feature."
        
        # Check that 'gsn' IS present
        assert 'gsn' in X.columns, "GSN must be present as the primary feature."

    def test_fallback_model_training(self, mock_preprocessed_data):
        """
        Verify that the fallback model can be trained without cycle_id features.
        """
        X, y = prepare_fallback_features(mock_preprocessed_data)
        model = train_fallback_model(X, y)
        
        # Verify model is not None
        assert model is not None, "Fallback model training failed."
        
        # Verify the model can make predictions
        predictions = model.predict(X)
        assert len(predictions) == len(y), "Prediction length mismatch."

    def test_fallback_prediction_on_unseen_cycles(self, mock_preprocessed_data, mock_pre_satellite_data):
        """
        Test the core fallback logic: 
        1. Train on satellite era (Cycles 23, 24, 25).
        2. Predict on pre-satellite era (Cycle 16) which was NOT in training.
        3. Verify that predictions are generated without error.
        """
        # 1. Prepare and train on satellite data
        X_train, y_train = prepare_fallback_features(mock_preprocessed_data)
        model = train_fallback_model(X_train, y_train)
        
        # 2. Prepare pre-satellite data (ensure it has 'gsn' but NO 'tsi' target)
        # The pre-satellite data should only have GSN and Cycle ID (which is ignored)
        X_test = mock_pre_satellite_data[['gsn']]
        
        # 3. Execute prediction
        # This should work because the model only depends on 'gsn', not 'cycle_id'
        predictions = model.predict(X_test)
        
        # 4. Verify output
        assert len(predictions) == len(mock_pre_satellite_data), "Prediction count mismatch for unseen cycles."
        assert not np.any(np.isnan(predictions)), "Predictions contain NaN values."
        
        # 5. Verify logical consistency: 
        # If GSN is high, TSI should be higher than if GSN is low (positive correlation)
        high_gsn_idx = np.argmax(mock_pre_satellite_data['gsn'])
        low_gsn_idx = np.argmin(mock_pre_satellite_data['gsn'])
        
        assert predictions[high_gsn_idx] > predictions[low_gsn_idx], \
            "Fallback model should preserve positive GSN-TSI correlation."

    def test_fallback_vs_cycle_specific_behavior(self, mock_preprocessed_data):
        """
        Verify that the fallback model produces different results than a model 
        that explicitly uses cycle_id (conceptual check).
        
        We simulate this by checking that the fallback model's predictions
        for a specific GSN value are constant regardless of the 'cycle_id' 
        associated with that row in the input dataframe.
        """
        # Create two identical GSN rows with different cycle IDs
        base_row = pd.DataFrame({
            'date': [pd.Timestamp('2020-01-01'), pd.Timestamp('2020-01-01')],
            'gsn': [50.0, 50.0],
            'cycle_id': [24, 25] # Different cycles
        })
        
        X_test = base_row[['gsn']]
        y_dummy = base_row['gsn'] # Dummy target for training if needed, but we use pre-trained model logic
        
        # Train a fresh fallback model
        X_train, y_train = prepare_fallback_features(mock_preprocessed_data)
        model = train_fallback_model(X_train, y_train)
        
        # Predict
        preds = model.predict(X_test)
        
        # Since the model is Cycle-Agnostic, predictions for identical GSN must be identical
        assert np.isclose(preds[0], preds[1]), \
            "Cycle-Agnostic fallback must produce identical predictions for identical GSN, regardless of cycle_id."

    def test_integration_with_preprocessing_pipeline(self):
        """
        Integration test: Ensure the fallback logic works end-to-end with 
        the preprocessing pipeline's output structure.
        """
        # Ensure directories exist
        ensure_directories()
        
        # Load mock data (simulating what run_preprocessing would output)
        # In a real scenario, this would be data/processed/preprocessed_data.parquet
        # Here we use the fixture data
        dates = pd.date_range(start='1850-01-01', end='2023-12-31', freq='M')
        n = len(dates)
        gsn = 45 + 28 * np.sin(np.linspace(0, 6 * np.pi, n)) + np.random.normal(0, 6, n)
        
        # Simulate TSI only for satellite era (2003+)
        tsi = np.full(n, np.nan)
        satellite_mask = dates.year >= 2003
        tsi[satellite_mask] = 1361.5 + 0.001 * gsn[satellite_mask] + np.random.normal(0, 0.05, satellite_mask.sum())
        
        # Assign cycles
        cycle_ids = np.zeros(n, dtype=int)
        cycle_ids[dates.year < 1900] = 14 # Dalton
        cycle_ids[(dates.year >= 1900) & (dates.year < 1930)] = 15
        cycle_ids[(dates.year >= 1930) & (dates.year < 1960)] = 16
        cycle_ids[(dates.year >= 1960) & (dates.year < 1990)] = 17
        cycle_ids[(dates.year >= 1990) & (dates.year < 2008)] = 23
        cycle_ids[(dates.year >= 2008) & (dates.year < 2019)] = 24
        cycle_ids[dates.year >= 2019] = 25
        
        df = pd.DataFrame({
            'date': dates,
            'gsn': gsn,
            'tsi': tsi,
            'cycle_id': cycle_ids
        })
        
        # Split into train (satellite) and test (pre-satellite)
        train_df = df[df['tsi'].notna()].copy()
        test_df = df[df['tsi'].isna()].copy()
        
        # Train fallback
        X_train, y_train = prepare_fallback_features(train_df)
        model = train_fallback_model(X_train, y_train)
        
        # Predict on pre-satellite
        X_test = test_df[['gsn']]
        predictions = model.predict(X_test)
        
        assert len(predictions) == len(test_df), "Prediction count mismatch in integration test."
        assert not np.any(np.isnan(predictions)), "Integration test predictions contain NaN."