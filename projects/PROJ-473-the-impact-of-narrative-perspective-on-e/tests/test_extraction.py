import pytest
from extraction import calculate_pronoun_density, calculate_narrator_distance_score, extract_perspective_features
import os
import tempfile
import logging

# Configure logging to capture warnings during tests
logging.basicConfig(level=logging.WARNING)

def test_pronoun_density_first_person():
    text = "I went to the store. I bought milk. I was happy."
    result = calculate_pronoun_density(text)
    assert result['pronoun_density_1st'] > 0.0
    assert result['pronoun_density_3rd'] == 0.0

def test_pronoun_density_third_person():
    text = "He went to the store. He bought milk. He was happy."
    result = calculate_pronoun_density(text)
    assert result['pronoun_density_3rd'] > 0.0
    assert result['pronoun_density_1st'] == 0.0

def test_narrator_distance():
    text_1st = "I walked. I saw. I did."
    text_3rd = "He walked. He saw. He did."
    
    score_1st = calculate_narrator_distance_score(text_1st)
    score_3rd = calculate_narrator_distance_score(text_3rd)
    
    assert score_1st < score_3rd

def test_language_detection_skips_non_english():
    """
    Unit test verifying that extract_perspective_features correctly skips
    non-English text and logs a warning.
    """
    # Create a temporary file with non-English text (Spanish)
    non_english_text = "Hola, me llamo Juan. Voy a la tienda."
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(non_english_text)
        temp_path = f.name

    try:
        # Capture log output
        import io
        log_stream = io.StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.WARNING)
        
        # Get the logger used by extraction module
        logger = logging.getLogger('extraction')
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)
        
        # Call the function - it should skip and return None or raise a specific error
        # Based on T015 logic, it should skip and log
        result = extract_perspective_features(temp_path)
        
        # The function should return None or an empty dict for non-English text
        assert result is None, "Non-English text should be skipped and return None"
        
        # Verify warning was logged
        log_contents = log_stream.getvalue()
        assert "non-English" in log_contents.lower() or "langdetect" in log_contents.lower(), \
            f"Expected language detection warning in logs, got: {log_contents}"
            
    finally:
        # Cleanup
        os.unlink(temp_path)
        logger.removeHandler(handler)

def test_short_text_skipping():
    """
    Unit test verifying that extract_perspective_features correctly skips
    text shorter than 50 words and logs a warning.
    """
    short_text = "This is a very short text."  # Definitely < 50 words
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(short_text)
        temp_path = f.name

    try:
        # Capture log output
        import io
        log_stream = io.StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.WARNING)
        
        logger = logging.getLogger('extraction')
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)
        
        result = extract_perspective_features(temp_path)
        
        assert result is None, "Short text (<50 words) should be skipped and return None"
        
        log_contents = log_stream.getvalue()
        assert "insufficient" in log_contents.lower() or "50 words" in log_contents.lower(), \
            f"Expected data quality warning in logs, got: {log_contents}"
            
    finally:
        os.unlink(temp_path)
        logger.removeHandler(handler)