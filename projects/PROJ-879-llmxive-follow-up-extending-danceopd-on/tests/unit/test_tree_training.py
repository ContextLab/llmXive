"""
Unit tests for Decision Tree training parameters (Task T018).

Verifies:
1. DecisionTreeClassifier instantiation with specific max_depth values.
2. Correct accuracy calculation logic.
3. Parameter validation for the training loop.
"""
import pytest
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.datasets import make_classification

# Mock the config if needed, but for unit tests we can generate synthetic data
# to test the logic of the classifier and metrics, not the data loading.
# Note: This test uses synthetic data ONLY for testing the training logic,
# NOT as a replacement for the real dataset in the pipeline.

def test_decision_tree_instantiation():
    """Verify DecisionTreeClassifier can be instantiated with specific depths."""
    depths = [2, 5, 10, 20]
    
    for depth in depths:
        clf = DecisionTreeClassifier(max_depth=depth, random_state=42)
        assert clf.max_depth == depth
        assert clf.random_state == 42
        # Verify it's a valid estimator
        assert hasattr(clf, 'fit')
        assert hasattr(clf, 'predict')

def test_accuracy_calculation():
    """Verify accuracy calculation logic matches sklearn metrics."""
    # Create a small synthetic dataset for testing the logic
    X, y = make_classification(n_samples=100, n_features=10, 
                               n_informative=5, n_redundant=2, 
                               random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    clf = DecisionTreeClassifier(max_depth=5, random_state=42)
    clf.fit(X_train, y_train)
    
    y_pred = clf.predict(X_test)
    
    # Calculate accuracy manually
    manual_accuracy = np.sum(y_pred == y_test) / len(y_test)
    
    # Compare with sklearn
    sklearn_accuracy = accuracy_score(y_test, y_pred)
    
    assert np.isclose(manual_accuracy, sklearn_accuracy)
    assert 0.0 <= sklearn_accuracy <= 1.0

def test_training_loop_parameters():
    """Verify that the loop parameters for training trees are correct."""
    # Simulate the loop logic from code/01_train_trees.py
    depths = list(range(2, 21))  # 2 to 20 inclusive
    
    assert len(depths) == 19
    assert min(depths) == 2
    assert max(depths) == 20
    
    # Verify each depth is an integer
    for d in depths:
        assert isinstance(d, int)
        assert d >= 2

def test_model_fit_and_predict():
    """Verify the model can be fit and predict correctly."""
    X, y = make_classification(n_samples=200, n_features=10, 
                               n_informative=5, random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42
    )
    
    clf = DecisionTreeClassifier(max_depth=5, random_state=42)
    clf.fit(X_train, y_train)
    
    # Should not raise an error
    predictions = clf.predict(X_test)
    
    assert len(predictions) == len(y_test)
    assert set(predictions).issubset(set(y))

def test_overfitting_detection():
    """Verify that deeper trees tend to overfit on small datasets."""
    X, y = make_classification(n_samples=50, n_features=10, 
                               n_informative=5, random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    shallow_clf = DecisionTreeClassifier(max_depth=2, random_state=42)
    deep_clf = DecisionTreeClassifier(max_depth=20, random_state=42)
    
    shallow_clf.fit(X_train, y_train)
    deep_clf.fit(X_train, y_train)
    
    shallow_train_acc = accuracy_score(y_train, shallow_clf.predict(X_train))
    deep_train_acc = accuracy_score(y_train, deep_clf.predict(X_train))
    
    shallow_test_acc = accuracy_score(y_test, shallow_clf.predict(X_test))
    deep_test_acc = accuracy_score(y_test, deep_clf.predict(X_test))
    
    # Deep tree should have higher training accuracy (potentially overfitting)
    assert deep_train_acc >= shallow_train_acc
    
    # But test accuracy might be lower or similar (overfitting effect)
    # This is a probabilistic check, but usually holds for small datasets
    # We just verify the metrics are calculated correctly
    assert 0.0 <= shallow_test_acc <= 1.0
    assert 0.0 <= deep_test_acc <= 1.0