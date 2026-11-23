"""
Integration test for the preprocessing pipeline.
Verifies end-to-end flow: filtering -> splitting -> output files.
"""
import pytest
import json
import tempfile
import os
from pathlib import Path

from data.preprocess import filter_prompts_with_min_traces, simulate_context_split, process_and_split_dataset

def test_integration_filter_and_split(tmp_path):
    """Integration test: Filter and split a sample dataset."""
    # Prepare test data
    sample_data = [
        {"id": "1", "prompt": "P1", "rationales": ["r1", "r2", "r3", "r4", "r5"]},
        {"id": "2", "prompt": "P2", "rationales": ["r1", "r2", "r3"]}, # Should be filtered out
        {"id": "3", "prompt": "P3", "rationales": ["r1", "r2", "r3", "r4"]},
        {"id": "4", "prompt": "P4", "rationales": ["r1"]}, # Should be filtered out
    ]
    
    input_file = tmp_path / "input.json"
    with open(input_file, 'w') as f:
        json.dump(sample_data, f)
        
    output_splits = tmp_path / "context_splits.json"
    output_stats = tmp_path / "stats.json"
    
    # Run processing
    process_and_split_dataset(
        input_path=str(input_file),
        output_splits_path=str(output_splits),
        output_stats_path=str(output_stats),
        min_traces=4,
        seed=42
    )
    
    # Verify outputs exist
    assert output_splits.exists()
    assert output_stats.exists()
    
    # Verify splits content
    with open(output_splits, 'r') as f:
        splits = json.load(f)
    
    assert len(splits) == 2
    # Check that P2 and P4 are not in splits
    prompts_in_splits = [s["prompt_id"] for s in splits]
    assert "2" not in prompts_in_splits
    assert "4" not in prompts_in_splits
    assert "1" in prompts_in_splits
    assert "3" in prompts_in_splits
    
    # Verify each split has privileged context and target rationales
    for s in splits:
        assert "privileged_context" in s
        assert "target_rationales" in s
        assert len(s["target_rationales"]) >= 3 # Since min was 4, remaining is >= 3
        assert s["privileged_context"] in s["original_rationale_count"] or len(s["target_rationales"]) + 1 == s["original_rationale_count"]
        
    # Verify stats
    with open(output_stats, 'r') as f:
        stats = json.load(f)
    
    assert stats["total_prompts_processed"] == 2
    assert stats["total_splits_generated"] == 2
    assert stats["min_traces_threshold"] == 4

def test_integration_empty_after_filter(tmp_path):
    """Integration test: Handle case where no prompts pass filter."""
    sample_data = [
        {"id": "1", "prompt": "P1", "rationales": ["r1", "r2"]},
    ]
    
    input_file = tmp_path / "input.json"
    with open(input_file, 'w') as f:
        json.dump(sample_data, f)
        
    output_splits = tmp_path / "context_splits.json"
    output_stats = tmp_path / "stats.json"
    
    with pytest.raises(ValueError, match="No prompts found"):
        process_and_split_dataset(
            input_path=str(input_file),
            output_splits_path=str(output_splits),
            output_stats_path=str(output_stats),
            min_traces=4
        )

if __name__ == "__main__":
    pytest.main([__file__, "-v"])