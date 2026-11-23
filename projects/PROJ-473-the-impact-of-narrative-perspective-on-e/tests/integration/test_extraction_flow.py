import pytest
import json
import os
from pathlib import Path
from extraction import extract_perspective_features

def test_full_extraction_flow():
    # Ensure sample data exists
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    sample_file = raw_dir / "test_story.txt"
    sample_content = "I walked down the street. I saw a dog. It was happy. I petted the dog."
    sample_file.write_text(sample_content)
    
    try:
        result = extract_perspective_features(str(sample_file))
        assert result is not None
        assert 'story_id' in result
        assert 'pronoun_density_1st' in result
        assert result['pronoun_density_1st'] > 0.0
    finally:
        if sample_file.exists():
            sample_file.unlink()
