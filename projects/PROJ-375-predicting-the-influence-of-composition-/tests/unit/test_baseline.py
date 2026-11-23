import numpy as np
import pytest
from modeling.train import NullModel


def test_null_model_predicts_mean():
    """
    Verify that NullModel predicts the mean of the training target variable.
    
    Assert: NullModel().predict(X) == y_train.mean()
    """
    # Create dummy training data
    X_train = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0], [7.0, 8.0]])
    y_train = np.array([10.0, 20.0, 30.0, 40.0])
    
    # Instantiate the null model
    model = NullModel()
    
    # Fit the model (this should store the mean of y_train)
    model.fit(X_train, y_train)
    
    # Predict on a new feature matrix (values shouldn't matter for NullModel)
    X_test = np.array([[9.0, 10.0], [11.0, 12.0]])
    predictions = model.predict(X_test)
    
    # Assert that predictions are all equal to the mean of y_train
    expected_mean = y_train.mean()
    expected_predictions = np.full_like(predictions, expected_mean, dtype=float)
    
    np.testing.assert_array_equal(predictions, expected_predictions)
    
    # Also verify the mean value is correct
    assert predictions[0] == expected_mean
    assert len(np.unique(predictions)) == 1  # All predictions should be identical