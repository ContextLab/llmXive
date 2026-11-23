import os
import sys
import csv
import pytest
from pathlib import Path
import json

# Add project root to path if running from tests/
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root / "code"))

from data.download_diverse_prompts import fetch_diverse_prompts, load_coco_captions, merge_and_deduplicate
from config import Config

def test_fetch_diverse_prompts_real_source():
    """
    Integration test: Verify that fetch_diverse_prompts actually retrieves data
    from the real HuggingFace dataset and returns non-empty, structured results.
    """
    prompts = fetch_diverse_prompts()
    
    assert len(prompts) > 0, "No prompts were fetched from the dataset."
    assert isinstance(prompts, list), "Prompts should be a list."
    
    # Check structure of a sample item
    sample = prompts[0]
    assert 'prompt' in sample, "Missing 'prompt' key in result."
    assert 'source' in sample, "Missing 'source' key in result."
    assert isinstance(sample['prompt'], str), "Prompt must be a string."
    assert len(sample['prompt']) > 0, "Prompt string cannot be empty."
    assert sample['source'] == 'nlpconnect/vit-gpt2-image-captioning', "Source mismatch."

def test_load_coco_captions_integration(tmp_path):
    """
    Integration test: Verify loading of COCO captions from a generated CSV.
    This simulates the output of T006b.
    """
    config = Config()
    # Override data path to use temp dir for this test
    test_data_dir = tmp_path / "data" / "processed"
    test_data_dir.mkdir(parents=True)
    
    # Create a fake prompts_test.csv
    test_csv = test_data_dir / "prompts_test.csv"
    with open(test_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['caption', 'id'])
        writer.writeheader()
        writer.writerow({'caption': 'A cat sitting on a mat', 'id': '1'})
        writer.writerow({'caption': 'A dog running in the park', 'id': '2'})
    
    # Temporarily patch config
    original_path = config.data_path
    config.data_path = tmp_path / "data"
    
    try:
        prompts = load_coco_captions(config)
        assert len(prompts) == 2, f"Expected 2 prompts, got {len(prompts)}"
        assert prompts[0]['prompt'] == 'A cat sitting on a mat'
        assert prompts[0]['source'] == 'ms-coco-validation'
    finally:
        config.data_path = original_path

def test_merge_and_deduplicate_logic():
    """
    Unit/Integration test: Verify deduplication logic works correctly.
    """
    list_a = [{'prompt': 'Hello World', 'source': 'A'}, {'prompt': 'Good Morning', 'source': 'A'}]
    list_b = [{'prompt': 'Hello World', 'source': 'B'}, {'prompt': 'Good Day', 'source': 'B'}]
    
    result = merge_and_deduplicate(list_a, list_b)
    
    # 'Hello World' appears in both, should be 1 entry
    # 'Good Morning' and 'Good Day' are unique
    assert len(result) == 3, f"Expected 3 unique prompts, got {len(result)}: {[p['prompt'] for p in result]}"
    
    # Verify 'Hello World' is present only once
    hello_count = sum(1 for p in result if p['prompt'] == 'Hello World')
    assert hello_count == 1, "Deduplication failed: 'Hello World' appears more than once."

def test_end_to_end_csv_generation(tmp_path):
    """
    End-to-end test: Run the full pipeline to generate a CSV and verify file content.
    """
    config = Config()
    output_path = tmp_path / "diverse_prompts.csv"
    
    # Mock data for the test to avoid long network calls in CI
    mock_diverse = [{'prompt': 'Test Prompt 1', 'source': 'mock'}]
    mock_coco = [{'prompt': 'Test Prompt 2', 'source': 'mock'}]
    
    final_prompts = merge_and_deduplicate(mock_coco, mock_diverse)
    
    # Write using the actual function logic (simplified for test)
    from data.download_diverse_prompts import write_merged_csv
    write_merged_csv(final_prompts, output_path)
    
    assert output_path.exists(), "Output CSV file was not created."
    
    # Verify content
    with open(output_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    assert len(rows) == 2, "CSV should contain 2 rows."
    assert rows[0]['prompt'] in ['Test Prompt 1', 'Test Prompt 2']
    assert rows[1]['prompt'] in ['Test Prompt 1', 'Test Prompt 2']
    assert 'source' in rows[0].keys(), "Missing 'source' column in CSV."