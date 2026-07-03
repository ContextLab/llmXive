import pytest
import logging
from code.utils import DataInsufficiencyError, raise_data_insufficiency

def test_data_insufficiency_error_message_no_missing_features():
    """Test error message when no specific missing features are provided."""
    with pytest.raises(DataInsufficiencyError) as exc_info:
        raise_data_insufficiency(100, 500)
    
    assert "Data Insufficiency: Retrieved 100 < 500" in str(exc_info.value)
    assert exc_info.value.retrieved_count == 100
    assert exc_info.value.required_count == 500
    assert exc_info.value.missing_features == []

def test_data_insufficiency_error_message_with_missing_features():
    """Test error message includes missing features list."""
    missing = ['boundary plane normal', 'Σ value']
    with pytest.raises(DataInsufficiencyError) as exc_info:
        raise_data_insufficiency(400, 500, missing_features=missing)
    
    assert "Data Insufficiency: Retrieved 400 < 500" in str(exc_info.value)
    assert "boundary plane normal" in str(exc_info.value)
    assert "Σ value" in str(exc_info.value)
    assert exc_info.value.missing_features == missing

def test_raise_data_insufficiency_logs_error():
    """Test that the function logs the error before raising."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.ERROR)
    
    with pytest.raises(DataInsufficiencyError):
        raise_data_insufficiency(50, 500, missing_features=['test_feature'])