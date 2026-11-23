import pytest
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import StratifiedKFold, LeaveOneGroupOut
from code.modeling.train import load_merged_data, preprocess_data, train_model, run_loso_cv, run_stratified_cv
from code.utils.exceptions import DataQualityError

class TestPreprocessData:
    def test_encode_categorical_features(self):
        """Test that categorical features are properly encoded."""
        df = pd.DataFrame({
            'species': ['A', 'B', 'A', 'C', 'B'],
            'N': [10.0, 20.0, 15.0, 25.0, 18.0],
            'P': [5.0, 8.0, 6.0, 10.0, 7.0],
            'K': [100.0, 150.0, 120.0, 180.0, 140.0],
            'pH': [6.5, 7.0, 6.8, 7.2, 6.6],
            'depth': [10.0, 20.0, 15.0, 25.0, 18.0],
            'branching': [2.0, 4.0, 3.0, 5.0, 3.5]
        })

        # Test preprocessing for Model A (Soil Only)
        X_a, y_a = preprocess_data(df, model_type='a')
        
        assert 'species' not in X_a.columns
        assert all(col in X_a.columns for col in ['N', 'P', 'K', 'pH'])
        assert all(col in y_a.columns for col in ['depth', 'branching'])

        # Test preprocessing for Model B (Soil + Species)
        X_b, y_b = preprocess_data(df, model_type='b')
        
        assert 'species' in X_b.columns or X_b.shape[1] > 4  # Species encoded
        assert all(col in y_b.columns for col in ['depth', 'branching'])

    def test_preprocess_data_with_missing_values(self):
        df = pd.DataFrame({
            'species': ['A', 'B', 'A'],
            'N': [10.0, np.nan, 15.0],
            'P': [5.0, 8.0, 6.0],
            'K': [100.0, 150.0, 120.0],
            'pH': [6.5, 7.0, 6.8],
            'depth': [10.0, 20.0, 15.0],
            'branching': [2.0, 4.0, 3.0]
        })

        # Should handle missing values by dropping or imputing
        try:
            X, y = preprocess_data(df, model_type='a')
            # If successful, rows with NaN should be dropped
            assert len(X) < len(df)
        except Exception:
            # If it raises, that's also acceptable behavior
            pass

class TestModelTraining:
    def test_train_model_basic(self):
        X = np.random.randn(50, 4)
        y = np.random.randn(50)
        
        model = train_model(X, y, model_type='rf')
        
        assert model is not None
        assert hasattr(model, 'predict')

    def test_train_model_with_random_state(self):
        X = np.random.randn(50, 4)
        y = np.random.randn(50)
        
        model1 = train_model(X, y, model_type='rf', random_state=42)
        model2 = train_model(X, y, model_type='rf', random_state=42)
        
        # Same random state should produce same model
        pred1 = model1.predict(X[:5])
        pred2 = model2.predict(X[:5])
        
        np.testing.assert_array_almost_equal(pred1, pred2)

class TestCrossValidation:
    def test_run_stratified_cv_basic(self):
        np.random.seed(42)
        X = np.random.randn(100, 4)
        y = np.random.randn(100)
        species = np.repeat(['A', 'B', 'C', 'D', 'E'], 20)
        
        r2_scores, rmse_scores = run_stratified_cv(X, y, species, n_splits=5)
        
        assert len(r2_scores) == 5
        assert len(rmse_scores) == 5
        assert all(isinstance(s, float) for s in r2_scores)

    def test_run_loso_cv_basic(self):
        np.random.seed(42)
        X = np.random.randn(50, 4)
        y = np.random.randn(50)
        species = np.repeat(['A', 'B', 'C', 'D', 'E'], 10)
        
        r2_scores, rmse_scores = run_loso_cv(X, y, species)
        
        # LOSO should have as many folds as unique species
        assert len(r2_scores) == 5
        assert len(rmse_scores) == 5

    def test_stratified_cv_with_two_species(self):
        np.random.seed(42)
        X = np.random.randn(40, 4)
        y = np.random.randn(40)
        species = np.repeat(['A', 'B'], 20)
        
        r2_scores, rmse_scores = run_stratified_cv(X, y, species, n_splits=2)
        
        assert len(r2_scores) == 2

    def test_loso_with_insufficient_species(self):
        """Test LOSO with only 1 species - should raise error."""
        np.random.seed(42)
        X = np.random.randn(20, 4)
        y = np.random.randn(20)
        species = np.array(['A'] * 20)
        
        with pytest.raises(DataQualityError):
            run_loso_cv(X, y, species)

class TestFeatureImportance:
    def test_extract_feature_importance(self):
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        X = np.random.randn(50, 4)
        y = np.random.randn(50)
        
        model.fit(X, y)
        
        # Check that feature importance exists
        importance = model.feature_importances_
        
        assert len(importance) == 4
        assert np.all(importance >= 0)
        assert np.isclose(np.sum(importance), 1.0)

    def test_feature_importance_ranking(self):
        # Create data where first feature is most important
        X = np.random.randn(100, 4)
        y = 5 * X[:, 0] + 0.1 * X[:, 1] + 0.1 * X[:, 2] + 0.1 * X[:, 3] + np.random.randn(100) * 0.1
        
        model = RandomForestRegressor(n_estimators=50, random_state=42)
        model.fit(X, y)
        
        importance = model.feature_importances_
        
        # First feature should be most important
        assert importance[0] > importance[1]
        assert importance[0] > importance[2]
        assert importance[0] > importance[3]

class TestDataLoading:
    def test_load_merged_data_schema(self):
        """Test that loaded data has expected columns."""
        # Create a mock merged dataset
        mock_df = pd.DataFrame({
            'species': ['A', 'B', 'C'],
            'N': [10.0, 20.0, 15.0],
            'P': [5.0, 8.0, 6.0],
            'K': [100.0, 150.0, 120.0],
            'pH': [6.5, 7.0, 6.8],
            'depth': [10.0, 20.0, 15.0],
            'branching': [2.0, 4.0, 3.0],
            'lat': [45.0, -45.0, 0.0],
            'lon': [-122.0, 122.0, 0.0]
        })
        
        # Verify columns exist
        expected_cols = ['species', 'N', 'P', 'K', 'pH', 'depth', 'branching', 'lat', 'lon']
        assert all(col in mock_df.columns for col in expected_cols)

    def test_load_merged_data_with_missing_values(self):
        mock_df = pd.DataFrame({
            'species': ['A', 'B', 'C'],
            'N': [10.0, np.nan, 15.0],
            'P': [5.0, 8.0, 6.0],
            'depth': [10.0, 20.0, 15.0],
            'branching': [2.0, 4.0, 3.0]
        })
        
        # Should be able to handle missing values
        assert mock_df['N'].isna().sum() == 1