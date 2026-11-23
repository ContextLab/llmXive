import os
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil

# Import the functions to test
from generate_moderate_tier import (
    load_instructional_units,
    normalize_text,
    generate_moderate_tier,
    save_moderate_tiers
)

class TestNormalizeText:
    def test_strip_whitespace(self):
        text = "   Hello World   "
        expected = "Hello World"
        assert normalize_text(text) == expected

    def test_multiple_spaces(self):
        text = "Hello   World    Test"
        expected = "Hello World Test"
        assert normalize_text(text) == expected

    def test_line_breaks(self):
        text = "Hello\n\n\nWorld"
        expected = "Hello\n\nWorld"
        assert normalize_text(text) == expected

    def test_non_string_input(self):
        assert normalize_text(123) == "123"
        assert normalize_text(None) == ""

class TestGenerateModerateTier:
    def test_basic_generation(self):
        unit = {'unit_id': '1', 'text': 'Test text'}
        result = generate_moderate_tier(unit)
        
        assert result['unit_id'] == '1'
        assert result['original_text'] == 'Test text'
        assert result['moderate_text'] == 'Test text'
        assert result['tier'] == 'moderate'

    def test_text_normalization(self):
        unit = {'unit_id': '2', 'text': '   Spaced   Text   '}
        result = generate_moderate_tier(unit)
        
        assert result['moderate_text'] == 'Spaced Text'

class TestLoadInstructionalUnits:
    def test_load_valid_csv(self, tmp_path):
        csv_path = tmp_path / "test_units.csv"
        df = pd.DataFrame({
            'unit_id': ['1', '2'],
            'text': ['Text 1', 'Text 2']
        })
        df.to_csv(csv_path, index=False)
        
        units = load_instructional_units(str(csv_path))
        
        assert len(units) == 2
        assert units[0]['unit_id'] == '1'
        assert units[1]['text'] == 'Text 2'

    def test_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_instructional_units(str(tmp_path / "nonexistent.csv"))

    def test_empty_file(self, tmp_path):
        csv_path = tmp_path / "empty.csv"
        csv_path.touch()
        with pytest.raises(ValueError):
            load_instructional_units(str(csv_path))

    def test_missing_columns(self, tmp_path):
        csv_path = tmp_path / "missing_cols.csv"
        df = pd.DataFrame({'id': ['1'], 'content': ['text']})
        df.to_csv(csv_path, index=False)
        with pytest.raises(ValueError):
            load_instructional_units(str(csv_path))

class TestSaveModerateTiers:
    def test_save_success(self, tmp_path):
        tiers = [
            {'unit_id': '1', 'original_text': 'A', 'moderate_text': 'A', 'tier': 'moderate'},
            {'unit_id': '2', 'original_text': 'B', 'moderate_text': 'B', 'tier': 'moderate'}
        ]
        output_path = tmp_path / "output.csv"
        
        save_moderate_tiers(tiers, str(output_path))
        
        assert output_path.exists()
        df = pd.read_csv(output_path)
        assert len(df) == 2
        assert list(df.columns) == ['unit_id', 'original_text', 'moderate_text', 'tier']

    def test_empty_tiers(self, tmp_path):
        with pytest.raises(ValueError):
            save_moderate_tiers([], str(tmp_path / "output.csv"))

class TestModerateTierIntegration:
    def test_full_pipeline(self, tmp_path):
        # Create input file
        input_path = tmp_path / "instructional_units.csv"
        df = pd.DataFrame({
            'unit_id': ['101', '102', '103'],
            'text': [
                '   Simple   Text   ',
                'Normal text here',
                'Complex\n\n\nText\n\n\nHere'
            ]
        })
        df.to_csv(input_path, index=False)
        
        # Create output directory
        output_dir = tmp_path / "tiers"
        output_dir.mkdir()
        output_path = output_dir / "moderate.csv"
        
        # Run pipeline
        units = load_instructional_units(str(input_path))
        tiers = [generate_moderate_tier(u) for u in units]
        save_moderate_tiers(tiers, str(output_path))
        
        # Verify output
        result_df = pd.read_csv(output_path)
        assert len(result_df) == 3
        assert result_df.iloc[0]['moderate_text'] == 'Simple Text'
        assert result_df.iloc[2]['moderate_text'] == 'Complex\n\nText\n\nHere'
        assert all(result_df['tier'] == 'moderate')