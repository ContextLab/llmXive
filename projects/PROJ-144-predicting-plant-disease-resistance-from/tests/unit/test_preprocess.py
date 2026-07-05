import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from code.data.preprocess import (
    _log_transform_and_filter,
    _align_metabolites,
    _residualize_covariates,
    _apply_combat,
    preprocess_metabolomics
)
from utils.constants import DATA_PROCESSED_DIR

@pytest.fixture
def sample_data():
    """Create a mock dataframe for testing."""
    data = {
        'sample_id': ['S1', 'S2', 'S3', 'S4'],
        'study_id': ['A', 'A', 'B', 'B'],
        'metabolite_1': [100.0, 200.0, 150.0, 300.0],
        'metabolite_2': [50.0, 0.0, np.nan, 100.0], # 25% missing in B? No, 1/4 total.
        'resistance_label': [1, 0, 1, 0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sparse_data():
    """Data with >30% missing to test filtering."""
    data = {
        'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
        'metabolite_good': [10.0, 20.0, 30.0, 40.0, 50.0],
        'metabolite_bad': [1.0, np.nan, np.nan, np.nan, np.nan], # 80% missing
        'resistance_label': [1, 0, 1, 0, 1]
    }
    return pd.DataFrame(data)

def test_log_transform_and_filter(sample_data, sparse_data):
    """Test log transform and missing value filtering."""
    # Test log transform
    result = _log_transform_and_filter(sample_data, threshold=0.5)
    assert 'metabolite_1' in result.columns
    assert 'metabolite_2' in result.columns
    # Check log transformation (log1p(100) ~ 4.6)
    assert result['metabolite_1'].iloc[0] > 4.0
    
    # Test filtering
    result_sparse = _log_transform_and_filter(sparse_data, threshold=0.30)
    assert 'metabolite_good' in result_sparse.columns
    assert 'metabolite_bad' not in result_sparse.columns

def test_align_metabolites():
    """Test alignment of metabolites across studies."""
    df1 = pd.DataFrame({
        'sample_id': ['S1', 'S2'],
        'study_id': ['A', 'A'],
        'metA': [10.0, 20.0],
        'metC': [30.0, 40.0]
    })
    df2 = pd.DataFrame({
        'sample_id': ['S3', 'S4'],
        'study_id': ['B', 'B'],
        'metB': [50.0, 60.0],
        'metC': [70.0, 80.0]
    })
    
    batches = [
        {'study_id': 'A', 'df': df1},
        {'study_id': 'B', 'df': df2}
    ]
    
    aligned = _align_metabolites(batches)
    
    # Should have union of columns
    assert 'metA' in aligned.columns
    assert 'metB' in aligned.columns
    assert 'metC' in aligned.columns
    # Check NaN filling (we fill with 0 in implementation)
    assert aligned.loc[aligned['sample_id'] == 'S1', 'metB'].iloc[0] == 0.0
    assert aligned.loc[aligned['sample_id'] == 'S3', 'metA'].iloc[0] == 0.0

def test_residualize_covariates(sample_data):
    """Test covariate residualization."""
    # Add a strong confounder effect
    df = sample_data.copy()
    df['study_id'] = ['A', 'A', 'B', 'B']
    df['metabolite_1'] = df['study_id'].map({'A': 100.0, 'B': 1000.0}) # Strong batch effect
    
    result = _residualize_covariates(df)
    # The variance due to study_id should be reduced in the residuals
    # We can't easily assert exact values without sklearn, but we check it runs
    assert 'metabolite_1' in result.columns
    assert not result['metabolite_1'].isna().any()

def test_apply_combat_no_batch(sample_data):
    """Test ComBat with only one study."""
    df = sample_data.copy()
    df['study_id'] = 'A' # Single study
    result = _apply_combat(df)
    # Should return unchanged or warn
    assert result.shape == df.shape

def test_preprocess_metabolomics_integration(monkeypatch, tmp_path):
    """
    Integration test: Mock file system and run full pipeline.
    """
    # Setup mock data files in a temp directory
    mock_processed_dir = tmp_path / "data" / "processed"
    mock_processed_dir.mkdir(parents=True)
    
    # Create mock harmonized files
    df1 = pd.DataFrame({
        'sample_id': ['S1', 'S2'],
        'study_id': ['A', 'A'],
        'met1': [100.0, 200.0],
        'met2': [50.0, 150.0],
        'resistance_label': [1, 0]
    })
    df2 = pd.DataFrame({
        'sample_id': ['S3', 'S4'],
        'study_id': ['B', 'B'],
        'met1': [120.0, 220.0],
        'met3': [300.0, 400.0], # Different metabolite
        'resistance_label': [1, 0]
    })
    
    df1.to_csv(mock_processed_dir / "harmonized_study_A.csv", index=False)
    df2.to_csv(mock_processed_dir / "harmonized_study_B.csv", index=False)
    
    # Mock constants
    from utils import constants
    original_dir = constants.DATA_PROCESSED_DIR
    constants.DATA_PROCESSED_DIR = str(mock_processed_dir)
    
    try:
        # Run
        success = preprocess_metabolomics()
        assert success is True
        
        # Check outputs
        assert (mock_processed_dir / "batch_corrected_matrix.csv").exists()
        assert (mock_processed_dir / "labels.csv").exists()
        
        # Verify content
        matrix = pd.read_csv(mock_processed_dir / "batch_corrected_matrix.csv")
        assert 'met1' in matrix.columns
        assert 'met2' in matrix.columns
        assert 'met3' in matrix.columns
        # Check log transform happened (values should be log1p of original)
        assert matrix['met1'].iloc[0] > 4.0 # log1p(100)
        
    finally:
        constants.DATA_PROCESSED_DIR = original_dir

if __name__ == "__main__":
    pytest.main([__file__, "-v"])