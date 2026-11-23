"""
Tests for T024: Strict two-group pairing validation.

Verifies that the pairing logic correctly enforces the constraint:
For every problem_id, exactly one 'pattern-guided' and one 'baseline' proposal must exist.
"""
import pytest
import json
import tempfile
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.error_handling import ValidationError
from code_04_pairing_and_output import (
    load_generated_proposals,
    validate_two_group_pairing,
    strip_metadata_for_evaluation,
    VALID_GROUPS
)

# Alias the module for cleaner test names
import code_04_pairing_and_output as pairing_module

def create_test_proposals(problem_ids, groups_map):
    """
    Helper to generate test proposal data.
    
    Args:
        problem_ids: List of problem IDs.
        groups_map: Dict mapping problem_id -> list of groups (e.g., {"p1": ["pattern-guided", "baseline"]}).
        
    Returns:
        List of proposal dicts.
    """
    proposals = []
    prop_counter = 0
    for pid in problem_ids:
        if pid in groups_map:
            for group in groups_map[pid]:
                prop_counter += 1
                proposals.append({
                    "proposal_id": f"prop_{prop_counter}",
                    "problem_id": pid,
                    "group": group,
                    "proposal_text": f"Test proposal for {pid} ({group})",
                    "internal_id": f"int_{prop_counter}",
                    "generation_timestamp": "2023-01-01T00:00:00Z"
                })
    return proposals

class TestTwoGroupPairingValidation:
    
    def test_valid_pairing_single_problem(self):
        """Test that a single problem with exactly one of each group passes."""
        proposals = create_test_proposals(
            ["prob_001"], 
            {"prob_001": ["pattern-guided", "baseline"]}
        )
        # Should not raise
        validate_two_group_pairing(proposals)

    def test_valid_pairing_multiple_problems(self):
        """Test that multiple problems with valid pairing pass."""
        proposals = create_test_proposals(
            ["prob_001", "prob_002", "prob_003"],
            {
                "prob_001": ["pattern-guided", "baseline"],
                "prob_002": ["pattern-guided", "baseline"],
                "prob_003": ["pattern-guided", "baseline"]
            }
        )
        validate_two_group_pairing(proposals)

    def test_missing_baseline_raises(self):
        """Test that missing baseline proposal raises ValidationError."""
        proposals = create_test_proposals(
            ["prob_001"],
            {"prob_001": ["pattern-guided"]}
        )
        with pytest.raises(ValidationError) as exc_info:
            validate_two_group_pairing(proposals)
        assert "baseline" in str(exc_info.value).lower()

    def test_missing_pattern_guided_raises(self):
        """Test that missing pattern-guided proposal raises ValidationError."""
        proposals = create_test_proposals(
            ["prob_001"],
            {"prob_001": ["baseline"]}
        )
        with pytest.raises(ValidationError) as exc_info:
            validate_two_group_pairing(proposals)
        assert "pattern-guided" in str(exc_info.value).lower()

    def test_duplicate_pattern_guided_raises(self):
        """Test that two pattern-guided proposals for one problem raises."""
        proposals = create_test_proposals(
            ["prob_001"],
            {"prob_001": ["pattern-guided", "pattern-guided"]}
        )
        with pytest.raises(ValidationError) as exc_info:
            validate_two_group_pairing(proposals)
        assert "pattern-guided" in str(exc_info.value).lower()

    def test_invalid_group_raises(self):
        """Test that an invalid group name raises ValidationError."""
        proposals = create_test_proposals(
            ["prob_001"],
            {"prob_001": ["pattern-guided", "random-pattern"]}
        )
        with pytest.raises(ValidationError) as exc_info:
            validate_two_group_pairing(proposals)
        assert "random-pattern" in str(exc_info.value)

    def test_missing_problem_id_raises(self):
        """Test that a proposal missing problem_id raises ValidationError."""
        proposals = [
            {
                "proposal_id": "prop_1",
                # "problem_id": "prob_001",  # Missing
                "group": "pattern-guided",
                "proposal_text": "Test"
            }
        ]
        with pytest.raises(ValidationError) as exc_info:
            validate_two_group_pairing(proposals)
        assert "problem_id" in str(exc_info.value).lower()

class TestStripMetadata:
    
    def test_strips_internal_fields(self):
        """Test that internal metadata fields are removed."""
        proposals = [
            {
                "proposal_id": "p1",
                "problem_id": "prob_001",
                "group": "pattern-guided",
                "proposal_text": "Test",
                "internal_id": "int_123",
                "generation_timestamp": "2023-01-01",
                "model_version": "v1.0",
                "prompt_template_id": "pt_1",
                "raw_generation_log": "log data"
            }
        ]
        cleaned = strip_metadata_for_evaluation(proposals)
        
        assert len(cleaned) == 1
        cleaned_prop = cleaned[0]
        
        # Check removed fields
        assert "internal_id" not in cleaned_prop
        assert "generation_timestamp" not in cleaned_prop
        assert "model_version" not in cleaned_prop
        assert "prompt_template_id" not in cleaned_prop
        assert "raw_generation_log" not in cleaned_prop
        
        # Check preserved fields
        assert cleaned_prop["proposal_id"] == "p1"
        assert cleaned_prop["problem_id"] == "prob_001"
        assert cleaned_prop["group"] == "pattern-guided"
        assert cleaned_prop["proposal_text"] == "Test"

    def test_preserves_unknown_fields(self):
        """Test that fields not in the strip list are preserved."""
        proposals = [
            {
                "proposal_id": "p1",
                "problem_id": "prob_001",
                "group": "pattern-guided",
                "proposal_text": "Test",
                "custom_field": "should_keep"
            }
        ]
        cleaned = strip_metadata_for_evaluation(proposals)
        assert cleaned[0]["custom_field"] == "should_keep"

class TestLoadGeneratedProposals:
    
    def test_loads_valid_jsonl(self):
        """Test loading a valid JSONL file."""
        data = [
            {"proposal_id": "1", "problem_id": "p1", "group": "baseline", "proposal_text": "A"},
            {"proposal_id": "2", "problem_id": "p1", "group": "pattern-guided", "proposal_text": "B"}
        ]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for item in data:
                f.write(json.dumps(item) + '\n')
            temp_path = Path(f.name)
        
        try:
            loaded = load_generated_proposals(temp_path)
            assert len(loaded) == 2
            assert loaded[0]["proposal_id"] == "1"
        finally:
            temp_path.unlink()

    def test_raises_on_missing_file(self):
        """Test that FileNotFoundError is raised for missing input."""
        with pytest.raises(FileNotFoundError):
            load_generated_proposals(Path("nonexistent_file.jsonl"))

    def test_raises_on_invalid_json(self):
        """Test that JSONDecodeError is raised for invalid JSON lines."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"valid": true}\n')
            f.write('invalid json line\n')
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(json.JSONDecodeError):
                load_generated_proposals(temp_path)
        finally:
            temp_path.unlink()
