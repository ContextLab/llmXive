"""
Unit tests for the factorial stimulus generator (T013).
"""
import csv
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.config import get_project_root, get_raw_data_dir
from code import generate_stimuli, verify_stimuli, count_emojis, save_stimuli


class TestCountEmojis:
    def test_count_zero_emojis(self):
        text = "Hello world."
        assert count_emojis(text) == 0

    def test_count_one_emoji(self):
        text = "Hello 🙂"
        assert count_emojis(text) == 1

    def test_count_two_emojis(self):
        text = "Hello 🙂 👍"
        assert count_emojis(text) == 2


class TestGenerateStimuli:
    def test_total_count(self):
        # 5 scenarios * 3 emoji counts * 4 punctuation types * 3 length categories = 180
        stimuli = generate_stimuli(seed=42)
        assert len(stimuli) == 180

    def test_unique_ids(self):
        stimuli = generate_stimuli(seed=42)
        ids = [s["id"] for s in stimuli]
        assert len(ids) == len(set(ids))

    def test_required_columns(self):
        stimuli = generate_stimuli(seed=42)
        required_cols = {"id", "text", "emoji_count", "punctuation_type", "length_category", "scenario_id"}
        for s in stimuli:
            assert set(s.keys()) == required_cols

    def test_deterministic_generation(self):
        s1 = generate_stimuli(seed=42)
        s2 = generate_stimuli(seed=42)
        assert s1 == s2
        
        s3 = generate_stimuli(seed=99)
        assert s1 != s3


class TestVerifyStimuli:
    def test_verify_success(self):
        stimuli = generate_stimuli(seed=42)
        assert verify_stimuli(stimuli) is True

    def test_verify_duplicate_id_fails(self):
        stimuli = generate_stimuli(seed=42)
        stimuli[0]["id"] = stimuli[1]["id"]
        assert verify_stimuli(stimuli) is False

    def test_verify_duplicate_combo_fails(self):
        stimuli = generate_stimuli(seed=42)
        # Force a duplicate combination
        stimuli[0]["emoji_count"] = stimuli[1]["emoji_count"]
        stimuli[0]["punctuation_type"] = stimuli[1]["punctuation_type"]
        stimuli[0]["length_category"] = stimuli[1]["length_category"]
        stimuli[0]["scenario_id"] = stimuli[1]["scenario_id"]
        assert verify_stimuli(stimuli) is False


class TestSaveAndLoad:
    def test_save_and_load_csv(self):
        stimuli = generate_stimuli(seed=42)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_stimuli.csv")
            save_stimuli(stimuli, output_path)
            
            # Verify file exists
            assert os.path.exists(output_path)
            
            # Read back
            with open(output_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 180
            assert rows[0]["id"] == stimuli[0]["id"]
            assert rows[0]["text"] == stimuli[0]["text"]
            assert int(rows[0]["emoji_count"]) == stimuli[0]["emoji_count"]
            assert rows[0]["punctuation_type"] == stimuli[0]["punctuation_type"]
            assert rows[0]["length_category"] == stimuli[0]["length_category"]
            assert rows[0]["scenario_id"] == stimuli[0]["scenario_id"]
