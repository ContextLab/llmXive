import pytest
from pathlib import Path
from code.oracle.parser import parse_qwen_agentworld

def test_schema_alignment(tmp_path):
    # Create a mock source file
    mock_file = tmp_path / "mock_source.py"
    mock_file.write_text("# Mock Qwen Agent World Source")
    
    result = parse_qwen_agentworld(mock_file)
    
    assert "source" in result
    assert "entities" in result
    assert "transitions" in result
