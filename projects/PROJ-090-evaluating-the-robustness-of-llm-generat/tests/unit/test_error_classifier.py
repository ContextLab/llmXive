import pytest
import json
import random
from pathlib import Path
from unittest.mock import patch, MagicMock

from analysis.error_classifier import (
    load_execution_results,
    filter_failures,
    stratify_by_perturbation_type,
    sample_stratified,
    classify_error,
    create_error_classification_report,
    save_report,
    main
)

@pytest.fixture
def sample_results():
    """Fixture providing sample execution results for testing."""
    return [
        {'task_id': 'task1', 'perturbation_type': 'synonym', 'status': 'pass', 'error_tag': None},
        {'task_id': 'task2', 'perturbation_type': 'typo', 'status': 'fail', 'error_tag': 'syntax', 'message': 'SyntaxError: invalid syntax'},
        {'task_id': 'task3', 'perturbation_type': 'rephrase', 'status': 'fail', 'error_tag': 'logic', 'message': 'AssertionError: expected 5, got 3'},
        {'task_id': 'task4', 'perturbation_type': 'synonym', 'status': 'timeout', 'error_tag': 'timeout', 'message': 'Execution timed out'},
        {'task_id': 'task5', 'perturbation_type': 'typo', 'status': 'fail', 'error_tag': None, 'message': 'IndentationError: unexpected indent'},
        {'task_id': 'task6', 'perturbation_type': 'rephrase', 'status': 'pass', 'error_tag': None},
    ]

@pytest.fixture
def sample_failures(sample_results):
    """Fixture providing sample failures."""
    return filter_failures(sample_results)

def test_filter_failures(sample_results):
    """Test that filter_failures correctly identifies failed executions."""
    failures = filter_failures(sample_results)
    assert len(failures) == 4
    task_ids = [f['task_id'] for f in failures]
    assert 'task1' not in task_ids
    assert 'task6' not in task_ids
    assert 'task2' in task_ids
    assert 'task3' in task_ids
    assert 'task4' in task_ids
    assert 'task5' in task_ids

def test_stratify_by_perturbation_type(sample_failures):
    """Test stratification by perturbation type."""
    stratified = stratify_by_perturbation_type(sample_failures)
    
    assert 'synonym' in stratified
    assert 'typo' in stratified
    assert 'rephrase' in stratified
    
    assert len(stratified['synonym']) == 1
    assert len(stratified['typo']) == 2
    assert len(stratified['rephrase']) == 1

def test_sample_stratified_all(sample_failures):
    """Test sampling when total failures <= max_total."""
    sampled = sample_stratified(stratify_by_perturbation_type(sample_failures), max_total=100, seed=42)
    assert len(sampled) == len(sample_failures)

def test_sample_stratified_limited(sample_failures):
    """Test sampling when total failures > max_total."""
    # Create more failures to test limiting
    many_failures = sample_failures * 20  # 80 failures
    stratified = stratify_by_perturbation_type(many_failures)
    
    sampled = sample_stratified(stratified, max_total=50, seed=42)
    assert len(sampled) <= 50
    
    # Verify stratification is maintained (all types present)
    types_present = set(f['perturbation_type'] for f in sampled)
    assert len(types_present) >= 2  # Should have at least 2 types

def test_sample_stratified_deterministic(sample_failures):
    """Test that sampling is deterministic with same seed."""
    stratified = stratify_by_perturbation_type(sample_failures)
    
    sampled1 = sample_stratified(stratified, max_total=50, seed=42)
    sampled2 = sample_stratified(stratified, max_total=50, seed=42)
    
    assert len(sampled1) == len(sampled2)
    assert [f['task_id'] for f in sampled1] == [f['task_id'] for f in sampled2]

def test_classify_error_syntax():
    """Test syntax error classification."""
    result = {'error_tag': 'syntax', 'message': 'SyntaxError: invalid syntax'}
    assert classify_error(result) == 'syntax'
    
    result = {'status': 'syntax_error', 'message': 'unexpected indent'}
    assert classify_error(result) == 'syntax'
    
    result = {'message': 'IndentationError: unexpected indent'}
    assert classify_error(result) == 'syntax'

def test_classify_error_logic():
    """Test logic error classification."""
    result = {'error_tag': 'logic', 'message': 'AssertionError'}
    assert classify_error(result) == 'logic'
    
    result = {'status': 'fail', 'message': 'AssertionError: expected 5, got 3'}
    assert classify_error(result) == 'logic'
    
    result = {'status': 'timeout', 'message': 'Execution timed out'}
    assert classify_error(result) == 'logic'

def test_classify_error_unknown():
    """Test unknown error classification."""
    result = {'status': 'unknown', 'message': ''}
    assert classify_error(result) == 'unknown'

def test_create_error_classification_report(sample_failures):
    """Test report creation."""
    report = create_error_classification_report(sample_failures)
    
    assert len(report) == len(sample_failures)
    
    for entry in report:
        assert 'task_id' in entry
        assert 'perturbation_type' in entry
        assert 'classification' in entry
        assert entry['classification'] in ['syntax', 'logic', 'unknown']

def test_save_report(tmp_path):
    """Test saving report to file."""
    report = [{'task_id': 'test', 'perturbation_type': 'synonym', 'classification': 'syntax'}]
    output_file = tmp_path / 'test_report.json'
    
    save_report(report, str(output_file))
    
    assert output_file.exists()
    with open(output_file) as f:
        loaded = json.load(f)
    assert len(loaded) == 1
    assert loaded[0]['task_id'] == 'test'

def test_main_integration(tmp_path, sample_results):
    """Test the main function integration."""
    # Mock the execution results file
    results_file = tmp_path / 'execution_results.json'
    with open(results_file, 'w') as f:
        json.dump(sample_results, f)
    
    output_file = tmp_path / 'error_classification_report.json'
    
    # Patch the functions to use our temp paths
    with patch('analysis.error_classifier.load_execution_results') as mock_load, \
         patch('analysis.error_classifier.save_report') as mock_save, \
         patch('analysis.error_classifier.get_config_dict') as mock_config:
         
         mock_config.return_value = {'data_dir': str(tmp_path)}
         mock_load.return_value = sample_results
         
         main()
         
         # Verify save_report was called
         assert mock_save.called
         call_args = mock_save.call_args[0]
         assert len(call_args[0]) <= 50
         assert all('perturbation_type' in entry for entry in call_args[0])

def test_sample_stratified_empty():
    """Test sampling with no failures."""
    sampled = sample_stratified({}, max_total=50, seed=42)
    assert len(sampled) == 0

def test_sample_stratified_single_group():
    """Test sampling with a single perturbation type."""
    failures = [{'task_id': f't{i}', 'perturbation_type': 'synonym'} for i in range(100)]
    stratified = {'synonym': failures}
    
    sampled = sample_stratified(stratified, max_total=50, seed=42)
    assert len(sampled) == 50
    assert all(f['perturbation_type'] == 'synonym' for f in sampled)
