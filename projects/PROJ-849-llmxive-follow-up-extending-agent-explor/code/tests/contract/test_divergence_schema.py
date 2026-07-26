import pytest
import json
from pathlib import Path
from typing import Dict, Any, List

def validate_divergence_record(record: Dict[str, Any]) -> bool:
    """Validate a single divergence record schema."""
    required_fields = [
        "problem_id", 
        "thinking_embedding", 
        "tool_centroid_embedding", 
        "cosine_similarity", 
        "semantic_divergence_score"
    ]
    
    for field in required_fields:
        if field not in record:
            return False
    
    # Type checks
    if not isinstance(record["problem_id"], str):
        return False
    if not isinstance(record["thinking_embedding"], list):
        return False
    if record["tool_centroid_embedding"] is not None and not isinstance(record["tool_centroid_embedding"], list):
        return False
    if not isinstance(record["cosine_similarity"], (int, float)):
        return False
    if not isinstance(record["semantic_divergence_score"], (int, float)):
        return False
    
    # Range checks
    if not (0.0 <= record["cosine_similarity"] <= 1.0):
        return False
    if not (0.0 <= record["semantic_divergence_score"] <= 2.0):
        return False
        
    return True

def test_divergence_output_schema():
    """Test that the output schema matches the specification."""
    # Sample valid record
    sample = {
        "problem_id": "test-123",
        "thinking_embedding": [0.1] * 768,
        "tool_centroid_embedding": [0.2] * 768,
        "cosine_similarity": 0.85,
        "semantic_divergence_score": 0.15
    }
    
    assert validate_divergence_record(sample) is True

def test_divergence_output_invalid_missing_field():
    """Test validation fails on missing field."""
    sample = {
        "problem_id": "test-123",
        "thinking_embedding": [0.1] * 768,
        "tool_centroid_embedding": [0.2] * 768,
        "cosine_similarity": 0.85
        # Missing semantic_divergence_score
    }
    
    assert validate_divergence_record(sample) is False

def test_divergence_output_invalid_range():
    """Test validation fails on out-of-range values."""
    sample = {
        "problem_id": "test-123",
        "thinking_embedding": [0.1] * 768,
        "tool_centroid_embedding": [0.2] * 768,
        "cosine_similarity": 1.5,  # Invalid range
        "semantic_divergence_score": 0.15
    }
    
    assert validate_divergence_record(sample) is False
