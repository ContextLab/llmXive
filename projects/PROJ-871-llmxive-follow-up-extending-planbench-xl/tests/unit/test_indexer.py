import json
from pathlib import Path
from dataset.indexer import extract_failure_signatures

def test_static_json_index_creation():
    """Verify static JSON index creation with consistent schema."""
    # Sample injected data
    injected_data = [
        {
            'id': 1,
            'injected_error_pattern': True,
            'injected_error_type': 'ERROR: silent_tool_failure'
        },
        {
            'id': 2,
            'injected_error_pattern': True,
            'injected_error_type': 'ERROR: tool_timeout'
        }
    ]
    
    signatures = extract_failure_signatures(injected_data)
    
    # Verify schema
    assert len(signatures) > 0
    for sig in signatures:
        assert 'tool_id' in sig
        assert 'pattern_string' in sig
        assert 'recovery_strategy' in sig
        assert sig['recovery_strategy'] == 'replan'
