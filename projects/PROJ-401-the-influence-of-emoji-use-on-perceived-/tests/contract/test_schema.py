"""
Contract tests for schema validation.

These tests ensure that data structures conform to the expected schemas
defined in src/data/contracts/.
"""
import pytest
from src.data.contracts.schemas import Message, AnalysisResult

def test_message_schema_valid():
    """Test that a valid message conforms to the Message schema."""
    valid_data = {
        "message_id": "msg_123",
        "text": "Hello world! 😊",
        "emoji_present": True,
        "emoji_count": 1,
        "emoji_types": ["smiling face"],
        "text_length": 17,
        "punctuation_count": 2
    }
    
    # Instantiate the Pydantic model; this will raise ValidationError if invalid
    message = Message(**valid_data)
    
    assert message.message_id == "msg_123"
    assert message.text == "Hello world! 😊"
    assert message.emoji_present is True
    assert message.emoji_count == 1
    assert message.emoji_types == ["smiling face"]
    assert message.text_length == 17
    assert message.punctuation_count == 2

def test_message_schema_invalid_type():
    """Test that invalid types are caught by Pydantic validation."""
    invalid_data = {
        "message_id": 123,  # Should be string
        "text": "Hello",
        "emoji_present": True,
        "emoji_count": 1,
        "emoji_types": [],
        "text_length": 5,
        "punctuation_count": 0
    }
    
    with pytest.raises(Exception):  # Pydantic raises ValidationError
        Message(**invalid_data)

def test_message_schema_missing_field():
    """Test that missing required fields are detected."""
    incomplete_data = {
        "message_id": "msg_456",
        "text": "Test",
        "emoji_present": False,
        "emoji_count": 0,
        "emoji_types": [],
        # Missing text_length and punctuation_count
    }
    
    with pytest.raises(Exception):
        Message(**incomplete_data)

def test_analysis_result_schema_valid():
    """Test that a valid analysis result conforms to the AnalysisResult schema."""
    valid_data = {
        "analysis_id": "analysis_001",
        "correlation_pearson": 0.45,
        "correlation_spearman": 0.42,
        "regression_beta": 0.35,
        "p_value": 0.001,
        "significant": True,
        "sample_size": 500
    }
    
    result = AnalysisResult(**valid_data)
    
    assert result.analysis_id == "analysis_001"
    assert result.correlation_pearson == 0.45
    assert result.correlation_spearman == 0.42
    assert result.regression_beta == 0.35
    assert result.p_value == 0.001
    assert result.significant is True
    assert result.sample_size == 500

def test_analysis_result_schema_invalid_type():
    """Test that invalid types in AnalysisResult are caught."""
    invalid_data = {
        "analysis_id": "analysis_001",
        "correlation_pearson": "not_a_number",  # Should be float
        "correlation_spearman": 0.42,
        "regression_beta": 0.35,
        "p_value": 0.001,
        "significant": True,
        "sample_size": 500
    }
    
    with pytest.raises(Exception):
        AnalysisResult(**invalid_data)

def test_analysis_result_schema_missing_field():
    """Test that missing required fields in AnalysisResult are detected."""
    incomplete_data = {
        "analysis_id": "analysis_001",
        "correlation_pearson": 0.45
        # Missing other required fields
    }
    
    with pytest.raises(Exception):
        AnalysisResult(**incomplete_data)