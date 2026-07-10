import os
import json
import tempfile
from extraction import extract_perspective_features, calculate_pronoun_density

def test_neutral_omniscient_flagging():
    """
    T017 Validation: Verify that texts with 0.0 first-person pronoun density
    are correctly flagged as 'is_neutral_omniscient'.
    """
    # Create a temporary file with a third-person only text
    third_person_text = """
    He walked down the street. She watched from the window. They decided to meet later.
    The cat sat on the mat. It was a sunny day. The birds sang in the trees.
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(third_person_text)
        temp_path = f.name
        
    try:
        features = extract_perspective_features(temp_path)
        
        assert features is not None, "Features should be extracted"
        assert features["pronoun_density_1st"] == 0.0, "First-person density should be 0.0"
        assert features["is_neutral_omniscient"] == True, "Should be flagged as neutral/omniscient"
        
    finally:
        os.unlink(temp_path)

def test_first_person_not_flagged():
    """
    T017 Validation: Verify that texts with non-zero first-person density
    are NOT flagged as 'is_neutral_omniscient'.
    """
    first_person_text = """
    I walked down the street. I saw her from the window. We decided to meet later.
    My cat sat on the mat. It was a sunny day. I heard the birds singing.
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(first_person_text)
        temp_path = f.name
        
    try:
        features = extract_perspective_features(temp_path)
        
        assert features is not None, "Features should be extracted"
        assert features["pronoun_density_1st"] > 0.0, "First-person density should be > 0.0"
        assert features["is_neutral_omniscient"] == False, "Should NOT be flagged as neutral/omniscient"
        
    finally:
        os.unlink(temp_path)

def test_mixed_pronouns_not_flagged():
    """
    T017 Validation: Verify that texts with mixed pronouns
    are NOT flagged as 'is_neutral_omniscient'.
    """
    mixed_text = """
    I walked down the street. He watched from the window. They decided to meet later.
    My cat sat on the mat. It was a sunny day. I heard the birds singing.
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(mixed_text)
        temp_path = f.name
        
    try:
        features = extract_perspective_features(temp_path)
        
        assert features is not None, "Features should be extracted"
        assert features["pronoun_density_1st"] > 0.0, "First-person density should be > 0.0"
        assert features["is_neutral_omniscient"] == False, "Should NOT be flagged as neutral/omniscient"
        
    finally:
        os.unlink(temp_path)