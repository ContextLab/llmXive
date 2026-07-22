import pytest
import pandas as pd
import json
import os
import tempfile
from pathlib import Path

# Import the functions to test
from token_reduction_verifier import (
    load_baseline_comparison,
    calculate_reduction,
    generate_verification_report,
    main
)

@pytest.fixture
def temp_csv_path():
    """Create a temporary CSV file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        # Create a mock baseline comparison
        # Static: 1000 tokens, Dynamic: 700 tokens -> 30% reduction
        f.write("condition,win_rate,avg_tokens,std_dev_tokens\n")
        f.write("Static,0.50,1000,50\n")
        f.write("Dynamic,0.55,700,40\n")
        f.write("Random,0.40,1100,60\n")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_csv_fail_path():
    """Create a temporary CSV file for testing failure case."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        # Create a mock baseline comparison
        # Static: 1000 tokens, Dynamic: 900 tokens -> 10% reduction (fail)
        f.write("condition,win_rate,avg_tokens,std_dev_tokens\n")
        f.write("Static,0.50,1000,50\n")
        f.write("Dynamic,0.55,900,40\n")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_load_baseline_comparison(temp_csv_path):
    """Test loading the baseline comparison CSV."""
    df = load_baseline_comparison(temp_csv_path)
    assert 'condition' in df.columns
    assert 'avg_tokens' in df.columns
    assert len(df) == 3
    assert df[df['condition'] == 'Static']['avg_tokens'].iloc[0] == 1000

def test_calculate_reduction_pass(temp_csv_path):
    """Test calculation of reduction when it passes the threshold."""
    df = load_baseline_comparison(temp_csv_path)
    reduction = calculate_reduction(df)
    # (1000 - 700) / 1000 = 0.30 -> 30%
    assert abs(reduction - 30.0) < 0.001

def test_calculate_reduction_fail(temp_csv_fail_path):
    """Test calculation of reduction when it fails the threshold."""
    df = load_baseline_comparison(temp_csv_fail_path)
    reduction = calculate_reduction(df)
    # (1000 - 900) / 1000 = 0.10 -> 10%
    assert abs(reduction - 10.0) < 0.001

def test_generate_verification_report():
    """Test generation of the verification report dictionary."""
    report = generate_verification_report(30.0, True)
    assert report['passed'] is True
    assert report['actual_reduction_percent'] == 30.0
    assert report['threshold_percent'] == 30.0

def test_main_success(temp_csv_path):
    """Test main function when reduction passes."""
    # We need to temporarily swap the global INPUT_FILE constant
    import token_reduction_verifier as module
    original_input = module.INPUT_FILE
    original_output = module.OUTPUT_FILE
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_input = os.path.join(tmpdir, "test_input.csv")
        test_output = os.path.join(tmpdir, "test_output.json")
        
        # Copy content of temp_csv_path to test_input
        with open(temp_csv_path, 'r') as src:
            with open(test_input, 'w') as dst:
                dst.write(src.read())
        
        module.INPUT_FILE = test_input
        module.OUTPUT_FILE = test_output
        
        try:
            result = main()
            assert result == 0
            assert os.path.exists(test_output)
            with open(test_output, 'r') as f:
                data = json.load(f)
                assert data['passed'] is True
                assert data['actual_reduction_percent'] == 30.0
        finally:
            module.INPUT_FILE = original_input
            module.OUTPUT_FILE = original_output

def test_main_failure(temp_csv_fail_path):
    """Test main function when reduction fails."""
    import token_reduction_verifier as module
    original_input = module.INPUT_FILE
    original_output = module.OUTPUT_FILE
    original_failure = module.FAILURE_FILE
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_input = os.path.join(tmpdir, "test_input.csv")
        test_output = os.path.join(tmpdir, "test_output.json")
        test_failure = os.path.join(tmpdir, "test_failure.json")
        
        # Copy content
        with open(temp_csv_fail_path, 'r') as src:
            with open(test_input, 'w') as dst:
                dst.write(src.read())
        
        module.INPUT_FILE = test_input
        module.OUTPUT_FILE = test_output
        module.FAILURE_FILE = test_failure
        
        try:
            result = main()
            assert result == 1
            assert os.path.exists(test_output)
            assert os.path.exists(test_failure)
            
            with open(test_output, 'r') as f:
                data = json.load(f)
                assert data['passed'] is False
            
            with open(test_failure, 'r') as f:
                fail_data = json.load(f)
                assert fail_data['status'] == "FAILED"
        finally:
            module.INPUT_FILE = original_input
            module.OUTPUT_FILE = original_output
            module.FAILURE_FILE = original_failure
