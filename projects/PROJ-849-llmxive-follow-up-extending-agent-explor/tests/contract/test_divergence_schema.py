"""
Contract tests for divergence output schema.
"""
import pytest
import json
from pathlib import Path
from typing import Dict, Any, List

def validate_divergence_record(record: Dict[str, Any]) -> bool:
    """
    Validate a single divergence record against the expected schema.
    
    Args:
        record: Dictionary to validate
    
    Returns:
        True if valid, False otherwise
    """
    required_fields = [
        'problem_id',
        'thinking_embedding',
        'tool_centroid_embedding',
        'cosine_similarity',
        'semantic_divergence_score'
    ]
    
    # Check required fields
    for field in required_fields:
        if field not in record:
            return False
    
    # Validate types
    if not isinstance(record['problem_id'], str):
        return False
    
    if not isinstance(record['thinking_embedding'], list):
        return False
    
    if record['tool_centroid_embedding'] is not None and not isinstance(record['tool_centroid_embedding'], list):
        return False
    
    if not isinstance(record['cosine_similarity'], (int, float)):
        return False
    
    if not isinstance(record['semantic_divergence_score'], (int, float)):
        return False
    
    # Validate ranges
    if not (0.0 <= record['cosine_similarity'] <= 1.0):
        return False
    
    if not (0.0 <= record['semantic_divergence_score'] <= 2.0):
        return False
    
    return True

def test_divergence_output_schema():
    """Test that a valid divergence record passes validation."""
    valid_record = {
        'problem_id': 'test_001',
        'thinking_embedding': [0.1] * 768,
        'tool_centroid_embedding': [0.2] * 768,
        'cosine_similarity': 0.85,
        'semantic_divergence_score': 0.15
    }
    
    assert validate_divergence_record(valid_record) is True

def test_divergence_output_invalid_missing_field():
    """Test that a record with missing field fails validation."""
    invalid_record = {
        'problem_id': 'test_001',
        'thinking_embedding': [0.1] * 768,
        # Missing tool_centroid_embedding
        'cosine_similarity': 0.85,
        'semantic_divergence_score': 0.15
    }
    
    assert validate_divergence_record(invalid_record) is False

def test_divergence_output_invalid_range():
    """Test that a record with invalid range fails validation."""
    invalid_record = {
        'problem_id': 'test_001',
        'thinking_embedding': [0.1] * 768,
        'tool_centroid_embedding': [0.2] * 768,
        'cosine_similarity': 1.5,  # Invalid: > 1.0
        'semantic_divergence_score': 0.15
    }
    
    assert validate_divergence_record(invalid_record) is False
