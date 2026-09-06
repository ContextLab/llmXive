import os
import sys
import pytest
from pathlib import Path
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from generate_moderate_tier import load_instructional_units, normalize_text, generate_moderate_tier, save_moderate_tiers

class TestModerateTierContract:
    """
    Contract tests for the Moderate Tier generation (T022b).
    Ensures the script reads the correct input, processes it, and writes the correct output.
    """

    def test_load_instructional_units_file_exists(self, tmp_path):
        """Test that the loader raises an error if input file is missing."""
        fake_path = tmp_path / "missing.csv"
        with pytest.raises(FileNotFoundError):
            load_instructional_units(fake_path)

    def test_normalize_text_whitespace(self):
        """Test that normalize_text handles excessive whitespace."""
        raw = "This  is   a    test   text   ."
        expected = "This is a test text ."
        # Note: The regex in normalize_text removes trailing space before punctuation
        # So "text ." becomes "text."
        expected = "This is a test text."
        assert normalize_text(raw) == expected

    def test_normalize_text_punctuation_spacing(self):
        """Test that normalize_text fixes punctuation spacing."""
        raw = "Hello , world ."
        expected = "Hello, world."
        assert normalize_text(raw) == expected

    def test_generate_moderate_tier_preserves_content(self, tmp_path):
        """Test that the moderate tier preserves the core content of the original."""
        original = "The quick brown fox jumps over the lazy dog."
        moderate = generate_moderate_tier(original)
        # Should be identical after normalization (no extra changes)
        assert "quick brown fox" in moderate
        assert "lazy dog" in moderate
        assert moderate == original  # No extra spaces in this simple case

    def test_save_moderate_tiers_creates_file(self, tmp_path):
        """Test that save_moderate_tiers creates the output file with correct schema."""
        units = [
            {'interaction_id': '1', 'original_text': 'Test text 1', 'source': 'test'},
            {'interaction_id': '2', 'original_text': 'Test text 2', 'source': 'test'}
        ]
        output_path = tmp_path / "moderate_tiers.csv"

        save_moderate_tiers(units, output_path)

        assert output_path.exists()
        df = pd.read_csv(output_path)

        # Check schema
        required_cols = ['interaction_id', 'tier', 'text', 'source']
        assert all(col in df.columns for col in required_cols)

        # Check content
        assert len(df) == 2
        assert all(df['tier'] == 'moderate')
        assert df.iloc[0]['interaction_id'] == '1'
        assert 'Test text 1' in df.iloc[0]['text']

    def test_full_pipeline_integration(self, tmp_path):
        """
        End-to-end test: Create input file -> Run loader -> Generate -> Save -> Verify.
        """
        input_path = tmp_path / "instructional_units.csv"
        output_path = tmp_path / "moderate_tiers.csv"

        # Create mock input
        input_data = [
            {'interaction_id': 'A1', 'skill_description': 'Simple sentence.'},
            {'interaction_id': 'A2', 'skill_description': 'Complex   sentence   with   extra   spaces .'}
        ]
        pd.DataFrame(input_data).to_csv(input_path, index=False)

        # Load
        units = load_instructional_units(input_path)
        assert len(units) == 2

        # Save
        save_moderate_tiers(units, output_path)

        # Verify
        assert output_path.exists()
        df = pd.read_csv(output_path)
        assert df.iloc[0]['tier'] == 'moderate'
        assert df.iloc[1]['text'] == 'Complex sentence with extra spaces.' # Normalized