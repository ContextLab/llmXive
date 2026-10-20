import os
import math
import yaml
from pathlib import Path

# Import the functions from the power_analysis module
from code.power_analysis import (
    calculate_sample_size,
    write_power_analysis_file,
    read_power_analysis_file,
    update_research_md,
    update_state_file,
    RESULT_PATH,
    RESEARCH_MD_PATH,
    STATE_YAML_PATH,
)

def test_calculate_sample_size():
    # Using the default parameters, the sample size should be a positive integer
    n = calculate_sample_size()
    assert isinstance(n, int)
    assert n > 0

def test_write_and_read_back(tmp_path):
    # Use a temporary file to avoid interfering with actual results
    temp_file = tmp_path / "temp_power.txt"
    sample = 1234
    write_power_analysis_file(sample, path=temp_file)
    read_back = read_power_analysis_file(path=temp_file)
    assert read_back == sample

def test_update_research_md(tmp_path):
    temp_md = tmp_path / "research.md"
    # Create a dummy file with some other content
    temp_md.write_text("Some intro line\\nAnother line\\n")
    update_research_md(2000, path=temp_md)
    content = temp_md.read_text()
    assert "Required sample size: 2000" in content

def test_update_state_file(tmp_path):
    temp_yaml = tmp_path / "state.yaml"
    update_state_file(2500, path=temp_yaml)
    with open(temp_yaml, "r") as f:
        data = yaml.safe_load(f)
    assert data.get("required_sample_size") == 2500

def test_end_to_end(tmp_path, monkeypatch):
    # Redirect paths to temporary locations for isolation
    monkeypatch.setattr("code.power_analysis.RESULT_PATH", tmp_path / "power.txt")
    monkeypatch.setattr("code.power_analysis.RESEARCH_MD_PATH", tmp_path / "research.md")
    monkeypatch.setattr("code.power_analysis.STATE_YAML_PATH", tmp_path / "state.yaml")

    # Run main workflow
    from code import power_analysis
    power_analysis.main()

    # Verify outputs exist and contain matching values
    assert (tmp_path / "power.txt").exists()
    assert (tmp_path / "research.md").exists()
    assert (tmp_path / "state.yaml").exists()

    # Load and compare values
    with open(tmp_path / "power.txt", "r") as f:
        val = int(f.readline().strip())
    with open(tmp_path / "state.yaml", "r") as f:
        state = yaml.safe_load(f)
    assert state["required_sample_size"] == val
    md_content = (tmp_path / "research.md").read_text()
    assert f"Required sample size: {val}" in md_content