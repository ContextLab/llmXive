"""
Integration test for evaluate_static.py

This test verifies that the evaluation script:
1. Can load the merged dataset
2. Can find and load trained models
3. Can compute evaluation metrics (precision, recall, F1, accuracy)
4. Produces a valid JSON output file with the expected schema
"""

import os
import json
import tempfile
import pytest
import numpy as np
import pandas as pd
import joblib
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression

# Import the main function from the module under test
from code.models.evaluate_static import main, evaluate_model, prepare_features_and_labels


@pytest.fixture
def temp_dirs():
    """Create temporary directories for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_merged_dataset(temp_dirs):
    """Create a sample merged dataset CSV."""
    data = {
        'doc_id': [f'doc_{i}' for i in range(100)],
        'token_id': list(range(100)),
        'position': list(range(100)),
        'entropy': np.random.rand(100) * 10,
        'pos_tag': np.random.choice(['NOUN', 'VERB', 'ADJ', 'ADV'], 100),
        'kenlm_perplexity': np.random.rand(100) * 100,
        'rtpurbo_label': np.random.choice([0, 1], 100)
    }
    df = pd.DataFrame(data)
    filepath = os.path.join(temp_dirs, 'merged_dataset.csv')
    df.to_csv(filepath, index=False)
    return filepath


@pytest.fixture
def sample_models(temp_dirs):
    """Create sample trained models."""
    seeds_dir = os.path.join(temp_dirs, 'models', 'seeds')
    os.makedirs(seeds_dir, exist_ok=True)
    
    # Create 3 sample models
    feature_cols = ['entropy', 'kenlm_perplexity']
    X = np.random.rand(80, 2)
    y = np.random.choice([0, 1], 80)
    
    for i in range(3):
        if i == 0:
            model = DecisionTreeClassifier(max_depth=3, random_state=i)
        else:
            model = LogisticRegression(random_state=i, max_iter=1000)
        
        model.fit(X, y)
        model_path = os.path.join(seeds_dir, f'model_seed_{i}.pkl')
        joblib.dump(model, model_path)
    
    return seeds_dir


def test_evaluate_model_function():
    """Test the evaluate_model function directly."""
    # Create a simple model
    model = DecisionTreeClassifier(max_depth=2, random_state=42)
    X_train = np.random.rand(50, 2)
    y_train = np.random.choice([0, 1], 50)
    model.fit(X_train, y_train)
    
    X_test = np.random.rand(20, 2)
    y_test = np.random.choice([0, 1], 20)
    
    metrics = evaluate_model(model, X_test, y_test)
    
    assert 'precision' in metrics
    assert 'recall' in metrics
    assert 'f1' in metrics
    assert 'accuracy' in metrics
    assert 0 <= metrics['precision'] <= 1
    assert 0 <= metrics['recall'] <= 1
    assert 0 <= metrics['f1'] <= 1
    assert 0 <= metrics['accuracy'] <= 1


def test_prepare_features_and_labels():
    """Test the prepare_features_and_labels function."""
    data = {
        'doc_id': [f'doc_{i}' for i in range(100)],
        'token_id': list(range(100)),
        'position': list(range(100)),
        'entropy': np.random.rand(100) * 10,
        'kenlm_perplexity': np.random.rand(100) * 100,
        'rtpurbo_label': np.random.choice([0, 1], 100)
    }
    df = pd.DataFrame(data)
    
    feature_cols = ['entropy', 'kenlm_perplexity']
    X_test, y_test = prepare_features_and_labels(df, feature_cols)
    
    assert X_test is not None
    assert y_test is not None
    assert len(X_test) > 0
    assert len(y_test) > 0
    assert X_test.shape[0] == y_test.shape[0]


def test_main_integration(temp_dirs, sample_merged_dataset, sample_models):
    """Test the full main function end-to-end."""
    output_path = os.path.join(temp_dirs, 'static_eval_scores.json')
    
    # Run the main function
    result = main({
        'merged_dataset': sample_merged_dataset,
        'seeds_dir': sample_models,
        'output': output_path
    })
    
    # Verify output file exists
    assert os.path.exists(output_path)
    
    # Verify JSON structure
    with open(output_path, 'r') as f:
        output_data = json.load(f)
    
    assert 'num_models_evaluated' in output_data
    assert 'test_set_size' in output_data
    assert 'evaluations' in output_data
    assert len(output_data['evaluations']) == 3  # We created 3 models
    
    # Verify each evaluation has required fields
    for eval_result in output_data['evaluations']:
        assert 'seed' in eval_result
        assert 'model_file' in eval_result
        assert 'precision' in eval_result
        assert 'recall' in eval_result
        assert 'f1' in eval_result
        assert 'accuracy' in eval_result
        
        # Verify metrics are valid numbers (not NaN or None for successful evaluations)
        if eval_result.get('error') is None:
            assert isinstance(eval_result['precision'], float)
            assert isinstance(eval_result['recall'], float)
            assert isinstance(eval_result['f1'], float)
            assert isinstance(eval_result['accuracy'], float)
            assert 0 <= eval_result['precision'] <= 1
            assert 0 <= eval_result['recall'] <= 1
            assert 0 <= eval_result['f1'] <= 1
            assert 0 <= eval_result['accuracy'] <= 1


def test_main_with_missing_dataset(temp_dirs):
    """Test that main raises FileNotFoundError for missing dataset."""
    output_path = os.path.join(temp_dirs, 'static_eval_scores.json')
    
    with pytest.raises(FileNotFoundError):
        main({
            'merged_dataset': os.path.join(temp_dirs, 'nonexistent.csv'),
            'seeds_dir': temp_dirs,
            'output': output_path
        })


def test_main_with_missing_models(temp_dirs, sample_merged_dataset):
    """Test that main raises FileNotFoundError for missing models directory."""
    output_path = os.path.join(temp_dirs, 'static_eval_scores.json')
    
    with pytest.raises(FileNotFoundError):
        main({
            'merged_dataset': sample_merged_dataset,
            'seeds_dir': os.path.join(temp_dirs, 'nonexistent_models'),
            'output': output_path
        })
