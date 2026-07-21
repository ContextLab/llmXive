"""
Unit tests for the Rule Generator (T023).

Tests the generation of `extracted_rules.json` ensuring:
1. The file is created.
2. The structure matches the expected schema.
3. Checksums are generated if requested.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# We need to mock the extractor and validator to avoid heavy dependencies
# in this unit test, focusing on the generator logic.
from rules.generator import generate_rules_artifact

@pytest.fixture
def temp_dirs():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        # Create mock input files
        traces_file = tmp_path / "cot_traces.json"
        traces_file.write_text(json.dumps({
            "traces": [
                {"id": "t1", "steps": [{"action": "move", "target": "A"}]}
            ]
        }))
        
        oracle_file = tmp_path / "oracle_graph.json"
        oracle_file.write_text(json.dumps({"nodes": [], "edges": []}))
        
        yield {
            "traces": traces_file,
            "oracle": oracle_file,
            "output": tmp_path / "extracted_rules.json",
            "manifest": tmp_path / "manifest.json",
            "base": tmp_path
        }

@patch('rules.generator.RuleExtractor')
@patch('rules.generator.RuleValidator')
def test_generate_rules_creates_file(MockValidator, MockExtractor, temp_dirs):
    """Test that the generator creates the output file."""
    # Setup mocks
    mock_extractor_instance = MagicMock()
    mock_extractor_instance.extract.return_value = [] # Return empty for simplicity
    MockExtractor.return_value = mock_extractor_instance
    
    mock_validator_instance = MagicMock()
    mock_validator_instance.validate.return_value = MagicMock(is_valid=True, confidence=1.0)
    MockValidator.return_value = mock_validator_instance

    # Run
    result = generate_rules_artifact(
        input_traces_path=temp_dirs["traces"],
        oracle_graph_path=temp_dirs["oracle"],
        output_path=temp_dirs["output"],
        checksum_manifest_path=temp_dirs["manifest"]
    )

    # Assert
    assert result["status"] == "success"
    assert temp_dirs["output"].exists()
    assert temp_dirs["manifest"].exists()

    # Verify content structure
    with open(temp_dirs["output"], "r") as f:
        content = json.load(f)
    
    assert "metadata" in content
    assert "rules" in content
    assert content["metadata"]["total_rules_extracted"] == 0

@patch('rules.generator.RuleExtractor')
@patch('rules.generator.RuleValidator')
def test_generate_rules_with_data(MockValidator, MockExtractor, temp_dirs):
    """Test generator with simulated extracted rules."""
    # Setup mocks to return a rule
    from rules.extractor import ExtractedRule
    
    mock_rule = ExtractedRule(
        rule_id="R001",
        condition="agent_at(A)",
        action="move_to(B)",
        consequence="agent_at(B)",
        confidence=0.95
    )
    
    mock_extractor_instance = MagicMock()
    mock_extractor_instance.extract.return_value = [mock_rule]
    MockExtractor.return_value = mock_extractor_instance
    
    mock_validator_instance = MagicMock()
    mock_validator_instance.validate.return_value = MagicMock(is_valid=True, confidence=0.95)
    MockValidator.return_value = mock_validator_instance

    # Run
    result = generate_rules_artifact(
        input_traces_path=temp_dirs["traces"],
        oracle_graph_path=temp_dirs["oracle"],
        output_path=temp_dirs["output"],
        checksum_manifest_path=temp_dirs["manifest"]
    )

    # Assert
    assert result["rules_count"] == 1
    
    with open(temp_dirs["output"], "r") as f:
        content = json.load(f)
    
    assert len(content["rules"]) == 1
    assert content["rules"][0]["rule_id"] == "R001"
    assert content["rules"][0]["validation_status"] == "valid"

@patch('rules.generator.RuleExtractor')
@patch('rules.generator.RuleValidator')
def test_file_not_found(MockValidator, MockExtractor, temp_dirs):
    """Test that the generator fails loudly if inputs are missing."""
    MockExtractor.return_value = MagicMock()
    MockValidator.return_value = MagicMock()

    with pytest.raises(FileNotFoundError):
        generate_rules_artifact(
            input_traces_path=Path("/nonexistent/path.json"),
            oracle_graph_path=temp_dirs["oracle"],
            output_path=temp_dirs["output"]
        )

    with pytest.raises(FileNotFoundError):
        generate_rules_artifact(
            input_traces_path=temp_dirs["traces"],
            oracle_graph_path=Path("/nonexistent/oracle.json"),
            output_path=temp_dirs["output"]
        )