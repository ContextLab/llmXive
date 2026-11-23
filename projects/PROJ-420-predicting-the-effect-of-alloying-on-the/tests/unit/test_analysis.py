import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from sklearn.ensemble import RandomForestRegressor
from compositional import ilr
import pickle

# Import the module to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))
from analysis import (
    run_perturbation_sensitivity_analysis,
    validate_framing,
    calculate_vif,
    rank_and_compare_importance
)

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    np.random.seed(42)
    n_samples = 100
    
    # Create synthetic composition data (Cu, Mg, Si, Zn, Mn)
    # These should sum to less than 1 to leave room for Al
    data = {
        'Cu': np.random.uniform(0.01, 0.1, n_samples),
        'Mg': np.random.uniform(0.01, 0.1, n_samples),
        'Si': np.random.uniform(0.01, 0.1, n_samples),
        'Zn': np.random.uniform(0.01, 0.1, n_samples),
        'Mn': np.random.uniform(0.01, 0.1, n_samples),
        'poisson_ratio': np.random.uniform(0.33, 0.36, n_samples)
    }
    
    # Ensure sum of elements < 1
    for i in range(n_samples):
        total = sum(data[col][i] for col in ['Cu', 'Mg', 'Si', 'Zn', 'Mn'])
        if total >= 1.0:
            # Scale down to ensure room for Al
            scale = 0.95 / total
            for col in ['Cu', 'Mg', 'Si', 'Zn', 'Mn']:
                data[col][i] *= scale
    
    return pd.DataFrame(data)

@pytest.fixture
def trained_model():
    """Create a simple trained model for testing."""
    # Create a dummy model that just returns the mean
    model = RandomForestRegressor(n_estimators=5, random_state=42, max_depth=3)
    return model

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_run_perturbation_sensitivity_analysis(sample_data, trained_model, temp_dir):
    """Test the perturbation sensitivity analysis implementation."""
    # Save sample data to parquet
    data_path = temp_dir / "test_clean_data.parquet"
    sample_data.to_parquet(data_path)
    
    # Save a simple trained model
    model_path = temp_dir / "test_model.pkl"
    trained_model.fit(sample_data[['Cu', 'Mg', 'Si', 'Zn', 'Mn']], sample_data['poisson_ratio'])
    with open(model_path, 'wb') as f:
        pickle.dump(trained_model, f)
    
    # Create output path
    output_path = temp_dir / "element_importance.csv"
    
    # Run the analysis
    run_perturbation_sensitivity_analysis(
        model=trained_model,
        raw_data_path=data_path,
        ilr_model_path=model_path,
        output_path=output_path,
        random_state=42
    )
    
    # Verify output file exists
    assert output_path.exists(), "Output CSV file was not created"
    
    # Verify output content
    result_df = pd.read_csv(output_path)
    
    # Check required columns
    assert 'element' in result_df.columns, "Missing 'element' column"
    assert 'importance_score' in result_df.columns, "Missing 'importance_score' column"
    assert 'std_dev' in result_df.columns, "Missing 'std_dev' column"
    
    # Check that all elements are present
    expected_elements = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
    assert sorted(result_df['element'].tolist()) == sorted(expected_elements), "Not all expected elements present"
    
    # Check that importance scores are non-negative
    assert all(result_df['importance_score'] >= 0), "Importance scores should be non-negative"
    
    # Check that results are sorted in descending order
    scores = result_df['importance_score'].tolist()
    assert scores == sorted(scores, reverse=True), "Results should be sorted in descending order"

def test_validate_framing(temp_dir):
    """Test the framing validation function."""
    # Create a report with required phrases
    report_content = """
    # Final Report
    
    ## 1. Executive Summary
    This study shows an associational relationship between alloy composition and Poisson's ratio.
    
    ## 2. Data Quality
    The data correlates with expected trends.
    
    ## 3. Model Performance
    The model is linked to the observed properties.
    """
    
    report_path = temp_dir / "test_report.md"
    report_path.write_text(report_content)
    
    # Test with required phrases
    required_phrases = [
        "associational relationship",
        "statistical association",
        "correlates with",
        "linked to",
        "associated with"
    ]
    
    result = validate_framing(report_path, required_phrases)
    
    assert result['framing_verified'] is True, "Framing should be verified"
    assert len(result['missing_phrases']) == 0, "No phrases should be missing"

def test_validate_framing_missing_phrases(temp_dir):
    """Test framing validation when phrases are missing."""
    # Create a report without required phrases
    report_content = """
    # Final Report
    
    ## 1. Executive Summary
    This study predicts Poisson's ratio from alloy composition.
    """
    
    report_path = temp_dir / "test_report.md"
    report_path.write_text(report_content)
    
    required_phrases = [
        "associational relationship",
        "correlates with"
    ]
    
    result = validate_framing(report_path, required_phrases)
    
    assert result['framing_verified'] is False, "Framing should not be verified"
    assert len(result['missing_phrases']) == 2, "Two phrases should be missing"
    assert "associational relationship" in result['missing_phrases']
    assert "correlates with" in result['missing_phrases']

def test_calculate_vif(sample_data):
    """Test VIF calculation."""
    X = sample_data[['Cu', 'Mg', 'Si', 'Zn', 'Mn']].values
    feature_names = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
    
    vif_scores = calculate_vif(X, feature_names)
    
    # Check that all features have VIF scores
    assert len(vif_scores) == 5, "Should have VIF scores for all 5 features"
    
    # Check that all scores are positive
    assert all(v > 0 for v in vif_scores.values()), "VIF scores should be positive"
    
    # Check that feature names match
    assert set(vif_scores.keys()) == set(feature_names), "Feature names should match"

def test_rank_and_compare_importance():
    """Test ranking and comparison of importance scores."""
    importance_dict = {
        'Cu': 0.45,
        'Mg': 0.30,
        'Si': 0.15,
        'Zn': 0.08,
        'Mn': 0.02
    }
    
    perm_scores = [0.42, 0.31, 0.14, 0.09, 0.03]
    feature_names = ['ilr_Cu', 'ilr_Mg', 'ilr_Si', 'ilr_Zn', 'ilr_Mn']
    
    result = rank_and_compare_importance(importance_dict, perm_scores, feature_names)
    
    # Check ranking
    assert result['ranked_elements'] == ['Cu', 'Mg', 'Si', 'Zn', 'Mn'], "Elements should be ranked in descending order"
    
    # Check importance scores
    assert result['importance_scores'] == [0.45, 0.30, 0.15, 0.08, 0.02], "Importance scores should match"
    
    # Check permutation scores
    assert result['permutation_scores'] == perm_scores, "Permutation scores should match"
    
    # Check descending order
    scores = result['importance_scores']
    assert scores == sorted(scores, reverse=True), "Scores should be in descending order"