import json
import os
import pytest
from pathlib import Path

def test_method_selection_log_has_raw_pvalues():
    """Test that method_selection_log.json contains raw p-values from Shapiro-Wilk."""
    log_path = Path('data/metadata/method_selection_log.json')
    if not log_path.exists():
        pytest.skip("Method selection log not generated yet")

    with open(log_path, 'r') as f:
        log_data = json.load(f)

    # Check structure
    assert 'checks_performed' in log_data, "checks_performed missing from log"
    assert 'decisions' in log_data, "decisions missing from log"
    assert 'final_method' in log_data, "final_method missing from log"

    # Check for raw p-values in checks
    checks = log_data['checks_performed']
    has_shapiro = any('shapiro' in str(c).lower() for c in checks)
    assert has_shapiro, "Shapiro-Wilk test results not found in checks_performed"

def test_method_selection_log_has_zero_proportion():
    """Test that method_selection_log.json contains exact zero proportions."""
    log_path = Path('data/metadata/method_selection_log.json')
    if not log_path.exists():
        pytest.skip("Method selection log not generated yet")

    with open(log_path, 'r') as f:
        log_data = json.load(f)

    # Check for zero proportion data
    checks = log_data.get('checks_performed', [])
    has_zero_prop = any('zero' in str(c).lower() or 'prop' in str(c).lower() for c in checks)
    assert has_zero_prop, "Zero proportion data not found in checks_performed"

def test_method_selection_log_has_decision_path():
    """Test that method_selection_log.json documents the decision path."""
    log_path = Path('data/metadata/method_selection_log.json')
    if not log_path.exists():
        pytest.skip("Method selection log not generated yet")

    with open(log_path, 'r') as f:
        log_data = json.load(f)

    decisions = log_data.get('decisions', [])
    assert len(decisions) > 0, "No decisions recorded in log"

    for decision in decisions:
        assert 'method' in decision, "Method not specified in decision"
        assert 'reason' in decision, "Reason not specified in decision"