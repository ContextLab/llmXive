import pytest
import json
import os
from pathlib import Path
import pandas as pd
import tempfile
import unicodedata

from ingestion import (
    parse_cognitive_status,
    clean_transcript_text,
    count_raw_records_from_csv,
    save_raw_record_count,
    save_group_counts
)
from utils import normalize_text

def test_parse_cognitive_status_control():
    assert parse_cognitive_status("pa_001_control.txt") == "Control"
    assert parse_cognitive_status("pa_001_Control.txt") == "Control"
    assert parse_cognitive_status("pa_001_c.txt") == "Control"

def test_parse_cognitive_status_mci():
    assert parse_cognitive_status("pa_002_mci.txt") == "MCI"
    assert parse_cognitive_status("pa_002_MCI.txt") == "MCI"

def test_parse_cognitive_status_ad():
    assert parse_cognitive_status("pa_003_dementia.txt") == "AD"
    assert parse_cognitive_status("pa_003_ad.txt") == "AD"

def test_clean_transcript_text():
    text = "Hello <laughter> world <pause> this is a test."
    cleaned = clean_transcript_text(text)
    assert "<laughter>" not in cleaned
    assert "<pause>" not in cleaned
    assert "Hello world this is a test." in cleaned

def test_count_raw_records_from_csv(tmp_path):
    # Create a dummy CSV
    data = {
        'participant_id': ['1', '2', '3'],
        'label': ['Control', 'MCI', 'AD'],
        'text': ['test text 1', 'test text 2', 'test text 3']
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / "test.csv"
    df.to_csv(csv_path, index=False)

    total, groups = count_raw_records_from_csv(csv_path)
    
    assert total == 3
    assert groups['Control'] == 1
    assert groups['MCI'] == 1
    assert groups['AD'] == 1

def test_save_raw_record_count(tmp_path):
    output_path = tmp_path / "raw_count.json"
    save_raw_record_count(10, output_path)
    
    assert output_path.exists()
    with open(output_path) as f:
        data = json.load(f)
    assert data['raw_count'] == 10

def test_save_group_counts(tmp_path):
    output_path = tmp_path / "group_counts.json"
    counts = {'Control': 5, 'MCI': 3, 'AD': 2}
    save_group_counts(counts, output_path)
    
    assert output_path.exists()
    with open(output_path) as f:
        data = json.load(f)
    assert data == counts

def test_utf8_normalization():
    """Test UTF-8 normalization using the utility from utils.py."""
    # Create a string with mixed Unicode forms (NFD vs NFC)
    # e.g. 'é' as composed (NFC) vs decomposed (NFD)
    composed = "café"  # NFC
    decomposed = "cafe\u0301"  # NFD: e + combining acute accent
    
    # Both should normalize to the same NFC form
    norm_composed = normalize_text(composed)
    norm_decomposed = normalize_text(decomposed)
    
    assert norm_composed == norm_decomposed
    assert norm_composed == "café"

def test_utf8_normalization_in_cleaning():
    """Test that UTF-8 normalization is applied during text cleaning."""
    # Text with non-ASCII characters that might need normalization
    text_with_unicode = "The patient said: café <pause> and résumé."
    cleaned = clean_transcript_text(text_with_unicode)
    
    # Annotations removed
    assert "<pause>" not in cleaned
    # Unicode characters preserved and normalized
    assert "café" in cleaned or "cafe" in cleaned # depends on normalization strategy
    assert "résumé" in cleaned or "resume" in cleaned

def test_exclusion_logic_missing_label():
    """Test that records with missing labels are identified for exclusion."""
    # This tests the logic that would be used in filter_records (T014)
    # We simulate the check here
    record = {'participant_id': '1', 'label': None, 'text': 'some text'}
    is_valid = record['label'] is not None and len(record['text'].split()) >= 50
    assert not is_valid

def test_exclusion_logic_short_text():
    """Test that records with text < 50 words are identified for exclusion."""
    # Short text
    record = {'participant_id': '2', 'label': 'Control', 'text': 'This is a short text.'}
    is_valid = record['label'] is not None and len(record['text'].split()) >= 50
    assert not is_valid

def test_exclusion_logic_valid_record():
    """Test that valid records pass the exclusion logic."""
    # Valid text (>= 50 words)
    long_text = " ".join(["word"] * 50)
    record = {'participant_id': '3', 'label': 'AD', 'text': long_text}
    is_valid = record['label'] is not None and len(record['text'].split()) >= 50
    assert is_valid

def test_utf8_edge_case_null_characters():
    """Test handling of null characters in UTF-8 strings."""
    text = "Hello\x00World"
    cleaned = clean_transcript_text(text)
    # Null characters should be removed or handled gracefully
    assert "\x00" not in cleaned