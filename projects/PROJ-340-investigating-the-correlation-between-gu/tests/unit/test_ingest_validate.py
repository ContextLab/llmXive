import pytest
import pandas as pd
import os
import sys
from pathlib import Path
import json
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from ingest import validate_variables, save_variable_metrics, MissingDataError, load_required_variables

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    tmp = tempfile.mkdtemp()
    yield tmp
    shutil.rmtree(tmp)

@pytest.fixture
def sample_df_complete():
    """Create a sample DataFrame with all required variables."""
    # Load required vars to know what to generate
    try:
        req = load_required_variables()
    except FileNotFoundError:
        # Fallback if config missing
        req = {
            'predictors': ['Taxon_0', 'Taxon_1'],
            'outcomes': ['total_sleep_time', 'sws_duration']
        }
    
    data = {}
    for col in req['predictors'] + req['outcomes']:
        data[col] = [1.0, 2.0, 3.0]
    
    return pd.DataFrame(data)

@pytest.fixture
def sample_df_missing():
    """Create a sample DataFrame with missing variables."""
    try:
        req = load_required_variables()
    except FileNotFoundError:
        req = {
            'predictors': ['Taxon_0', 'Taxon_1'],
            'outcomes': ['total_sleep_time', 'sws_duration']
        }
    
    # Include only predictors, missing outcomes
    data = {}
    for col in req['predictors']:
        data[col] = [1.0, 2.0, 3.0]
    
    return pd.DataFrame(data)

def test_validate_variables_complete(sample_df_complete):
    """Test validation when all variables are present."""
    result = validate_variables(sample_df_complete, None)
    
    assert result['status'] == 'PASS'
    assert result['missing_variables'] == []
    assert result['percentage_loaded'] == 100.0
    assert result['loaded_count'] == result['total_required']

def test_validate_variables_missing(sample_df_missing):
    """Test validation when some variables are missing."""
    result = validate_variables(sample_df_missing, None)
    
    assert result['status'] == 'FAIL'
    assert len(result['missing_variables']) > 0
    assert result['percentage_loaded'] < 100.0
    assert result['loaded_count'] < result['total_required']

def test_save_variable_metrics(temp_dir):
    """Test saving metrics to a JSON file."""
    metrics = {
        'total_required': 10,
        'loaded_count': 5,
        'percentage_loaded': 50.0,
        'missing_variables': ['var1', 'var2'],
        'status': 'FAIL'
    }
    
    output_path = os.path.join(temp_dir, 'test_metrics.json')
    saved_path = save_variable_metrics(metrics, output_path)
    
    assert saved_path == output_path
    assert os.path.exists(output_path)
    
    with open(output_path, 'r') as f:
        loaded = json.load(f)
    
    assert loaded == metrics

def test_validate_variables_empty_config():
    """Test validation with empty required variables config."""
    df = pd.DataFrame({'A': [1, 2, 3]})
    result = validate_variables(df, {'predictors': [], 'outcomes': []})
    
    assert result['status'] == 'PASS'
    assert result['total_required'] == 0
    assert result['percentage_loaded'] == 100.0
