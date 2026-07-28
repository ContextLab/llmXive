import pytest
import os
import json
import tempfile
from extraction import extract_perspective_features, calculate_pronoun_density

def test_neutral_omniscient_flagging():
    """
    Test that texts with 0.0 first-person pronoun density are flagged as neutral/omniscient.
    """
    # Create a temporary file with third-person only text
    third_person_text = """
    He walked down the street. She was waiting for him. The cat sat on the wall.
    They watched the sun set. It was a beautiful evening. The birds flew away.
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(third_person_text)
        temp_path = f.name

    try:
        result = extract_perspective_features(temp_path)
        assert result is not None
        assert result["pronoun_density_1st"] == 0.0
        assert result["is_neutral_omniscient"] is True
    finally:
        os.unlink(temp_path)

def test_first_person_not_flagged():
    """
    Test that texts with non-zero first-person density are NOT flagged as neutral/omniscient.
    """
    first_person_text = """
    I walked down the street. I was waiting for my friend. My cat sat on my wall.
    We watched the sun set. It was a beautiful evening. I felt happy.
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(first_person_text)
        temp_path = f.name

    try:
        result = extract_perspective_features(temp_path)
        assert result is not None
        assert result["pronoun_density_1st"] > 0.0
        assert result["is_neutral_omniscient"] is False
    finally:
        os.unlink(temp_path)

def test_mixed_perspective_not_flagged():
    """
    Test that texts with mixed perspective are NOT flagged as neutral/omniscient.
    """
    mixed_text = """
    I walked down the street. He was waiting for me. The cat sat on the wall.
    We watched the sun set. She smiled at me. It was a beautiful evening.
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(mixed_text)
        temp_path = f.name

    try:
        result = extract_perspective_features(temp_path)
        assert result is not None
        assert result["pronoun_density_1st"] > 0.0
        assert result["is_neutral_omniscient"] is False
    finally:
        os.unlink(temp_path)
