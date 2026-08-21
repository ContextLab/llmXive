from typing import Union, List, Dict, Any
from .schemas import Message, AnalysisResult
import logging

logger = logging.getLogger(__name__)

def validate_message(data: Union[Dict, Message]) -> Message:
    """
    Validates and returns a Message object.
    
    Args:
        data: Either a dictionary of raw data or an existing Message object.
        
    Returns:
        A validated Message object.
        
    Raises:
        ValueError: If the data cannot be validated into a Message.
    """
    if isinstance(data, Message):
        return data
    
    try:
        # Ensure required fields exist if dict
        if isinstance(data, dict):
            if 'message_id' not in data:
                raise ValueError("Missing required field: message_id")
            if 'text' not in data:
                raise ValueError("Missing required field: text")
        
        return Message(**data)
    except Exception as e:
        logger.error(f"Failed to validate message: {e}")
        raise ValueError(f"Invalid message data: {e}")

def validate_analysis_result(data: Union[Dict, AnalysisResult]) -> AnalysisResult:
    """
    Validates and returns an AnalysisResult object.
    
    Args:
        data: Either a dictionary of raw data or an existing AnalysisResult object.
        
    Returns:
        A validated AnalysisResult object.
        
    Raises:
        ValueError: If the data cannot be validated into an AnalysisResult.
    """
    if isinstance(data, AnalysisResult):
        return data
    
    try:
        if isinstance(data, dict):
            required = ['analysis_id', 'metric_name', 'effect_size', 'p_value', 'sample_size']
            missing = [k for k in required if k not in data]
            if missing:
                raise ValueError(f"Missing required fields: {missing}")
        
        return AnalysisResult(**data)
    except Exception as e:
        logger.error(f"Failed to validate analysis result: {e}")
        raise ValueError(f"Invalid analysis result data: {e}")
