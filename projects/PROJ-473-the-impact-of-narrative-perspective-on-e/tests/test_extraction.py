import pytest
import os
import tempfile
import json
from extraction import extract_perspective_features, calculate_pronoun_density

def test_neutral_omniscient_flagging():
    """
    T017 Test: Verify that texts with 0.0 first-person density are flagged as 'is_neutral_omniscient'.
    """
    # Create a temporary file with a third-person heavy text (omniscient style)
    third_person_text = """
    The old man walked down the street. He looked at the sky. The sky was blue. 
    She watched him from the window. It was a cold day. They did not speak to each other.
    The dog barked at the mailman. It was a lonely afternoon in the city.
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(third_person_text)
        temp_path = f.name

    try:
        result = extract_perspective_features(temp_path)
        
        assert result is not None, "Extraction should not return None for valid English text"
        assert result['pronoun_density_1st'] == 0.0, "First person density should be 0.0 for this text"
        assert result['is_neutral_omniscient'] is True, "Text with 0.0 first-person density must be flagged as neutral/omniscient"
        assert result['pronoun_density_3rd'] > 0.0, "Third person density should be > 0.0"
    finally:
        os.unlink(temp_path)

def test_first_person_not_flagged():
    """
    T017 Test: Verify that texts with non-zero first-person density are NOT flagged.
    """
    first_person_text = """
    I walked down the street. I looked at the sky. The sky was blue. 
    I watched the man from the window. It was a cold day. I did not speak to him.
    My dog barked at the mailman. It was a lonely afternoon for me.
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(first_person_text)
        temp_path = f.name

    try:
        result = extract_perspective_features(temp_path)
        
        assert result is not None, "Extraction should not return None for valid English text"
        assert result['pronoun_density_1st'] > 0.0, "First person density should be > 0.0"
        assert result['is_neutral_omniscient'] is False, "Text with > 0.0 first-person density must NOT be flagged"
    finally:
        os.unlink(temp_path)

def test_edge_case_empty_text():
    """
    T017 Test: Verify behavior on empty text.
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("")
        temp_path = f.name

    try:
        result = extract_perspective_features(temp_path)
        assert result is None, "Empty text should return None"
    finally:
        os.unlink(temp_path)

def test_language_detection_skip():
    """
    T017 Test: Verify non-English text is skipped.
    """
    spanish_text = "Hola, cómo estás? El cielo está azul."
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(spanish_text)
        temp_path = f.name

    try:
        result = extract_perspective_features(temp_path)
        assert result is None, "Non-English text should return None"
    finally:
        os.unlink(temp_path)
