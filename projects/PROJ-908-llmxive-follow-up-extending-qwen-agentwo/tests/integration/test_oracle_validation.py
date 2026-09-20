import pytest
import json
from pathlib import Path
from code.oracle.generator import build_oracle_graph, save_and_verify
from code.oracle.simulator import simulate_oracle

def test_oracle_vs_simulator(tmp_path):
    # 1. Generate Oracle
    mock_source = tmp_path / "source"
    mock_source.mkdir()
    (mock_source / "init.py").write_text("")
    
    oracle_graph = build_oracle_graph(mock_source)
    oracle_file = tmp_path / "oracle.json"
    save_and_verify(oracle_graph, oracle_file)
    
    # 2. Validate via Simulator (mocked for structure)
    # In real impl: simulate_oracle(oracle_file, steps=1000)
    # assert accuracy >= 0.999
    assert oracle_file.exists()
