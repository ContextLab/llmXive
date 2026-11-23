import os
import json
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.modeling import check_model_convergence

@pytest.fixture
def temp_log_file():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        f.write('[]')
        return f.name

@pytest.fixture
def mock_converged_model():
    class MockModel:
        converged = True
        mle_retvals = {'converged': True}
        bse = {'sentiment': 0.1}
        params = {'sentiment': 0.5}
        pvalues = {'sentiment': 0.01}
        mle_settings = {'maxiter': 100}
    return MockModel()

@pytest.fixture
def mock_failed_model():
    class MockModel:
        converged = False
        mle_retvals = {'converged': False, 'message': 'Maximum iterations reached'}
        bse = {}
        params = {}
        pvalues = {}
        mle_settings = {'maxiter': 100}
    return MockModel()

def test_check_convergence_success(mock_converged_model, temp_log_file):
    status, message = check_model_convergence(mock_converged_model, "test_thread_1", temp_log_file)
    assert status == "converged"
    assert "successfully" in message.lower()
    
    with open(temp_log_file, 'r') as f:
        logs = json.load(f)
    assert len(logs) == 1
    assert logs[0]['thread_id'] == 'test_thread_1'
    assert logs[0]['status'] == 'converged'

def test_check_convergence_failure(mock_failed_model, temp_log_file):
    status, message = check_model_convergence(mock_failed_model, "test_thread_2", temp_log_file)
    assert status == "failed"
    assert "did not converge" in message.lower()
    
    with open(temp_log_file, 'r') as f:
        logs = json.load(f)
    assert len(logs) == 1
    assert logs[0]['status'] == 'failed'

def test_check_convergence_no_attr(temp_log_file):
    class MockModelNoAttr:
        bse = {'sentiment': 0.1}
        params = {'sentiment': 0.5}
        pvalues = {'sentiment': 0.01}
    
    status, message = check_model_convergence(MockModelNoAttr(), "test_thread_3", temp_log_file)
    assert status == "converged" # Falls back to "parameters estimated"
    assert "assumed" in message.lower()

def test_check_convergence_exception(temp_log_file):
    class MockModelError:
        converged = False
        @property
        def bse(self):
            raise ValueError("Covariance estimation failed")
    
    status, message = check_model_convergence(MockModelError(), "test_thread_4", temp_log_file)
    assert status == "failed"
    assert "failed" in message.lower()

def test_log_file_append(temp_log_file):
    # Write initial log
    with open(temp_log_file, 'w') as f:
        json.dump([{"thread_id": "existing", "status": "converged"}], f)
    
    class MockModel:
        converged = True
        bse = {}
        params = {}
        pvalues = {}
        mle_settings = {}
    
    check_model_convergence(MockModel(), "new_thread", temp_log_file)
    
    with open(temp_log_file, 'r') as f:
        logs = json.load(f)
    
    assert len(logs) == 2
    assert logs[0]['thread_id'] == 'existing'
    assert logs[1]['thread_id'] == 'new_thread'
    assert logs[1]['status'] == 'converged'