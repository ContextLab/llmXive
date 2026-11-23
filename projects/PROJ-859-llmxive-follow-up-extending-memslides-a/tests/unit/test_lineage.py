"""
Unit tests for code/utils/lineage.py (T063).
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code to path
code_root = Path(__file__).resolve().parent.parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from utils.lineage import (
    load_state_file,
    load_exclusion_log,
    build_dag,
    generate_dot_file,
    LineageError
)

def test_load_state_file_valid():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "state.json"
        data = {"artifacts": {"test": "value"}, "generation_stats": {}}
        with open(state_path, 'w') as f:
            json.dump(data, f)
        
        result = load_state_file(state_path)
        assert result == data

def test_load_state_file_missing():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "missing.json"
        try:
            load_state_file(state_path)
            assert False, "Should have raised LineageError"
        except LineageError:
            pass

def test_load_exclusion_log_valid():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "exclusion_log.json"
        data = [
            json.dumps({"trace_id": "1", "reason": "bad"}),
            json.dumps({"trace_id": "2", "reason": "empty"})
        ]
        with open(log_path, 'w') as f:
            f.write("\n".join(data))
        
        result = load_exclusion_log(log_path)
        assert len(result) == 2
        assert result[0]["trace_id"] == "1"

def test_load_exclusion_log_missing():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "missing.json"
        result = load_exclusion_log(log_path)
        assert result == []

def test_build_dag_structure():
    # Minimal mock state and exclusion log
    state = {
        "artifacts": {
            "feature_matrix.csv": {"hash": "abc"}
        },
        "generation_stats": {}
    }
    exclusion_log = []
    
    # We need to mock the filesystem or provide a config that points to temp dirs
    # For this unit test, we assume the function logic is correct if it returns a dict
    # with nodes and edges. The actual file scanning is dependent on real files.
    # To test strictly, we would need to create the directory structure.
    # Here we test the structure of the return value assuming files exist.
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create dummy files to satisfy the scan
        data_dir = Path(tmpdir) / "data"
        training_dir = data_dir / "training"
        processed_dir = data_dir / "processed"
        rules_dir = processed_dir / "rules"
        
        training_dir.mkdir(parents=True)
        processed_dir.mkdir(parents=True)
        rules_dir.mkdir(parents=True)
        
        # Create dummy trace
        (training_dir / "session_1.json").write_text("{}")
        # Create dummy processed artifacts
        (processed_dir / "feature_matrix.csv").write_text("col1,col2\n1,2")
        (processed_dir / "rules" / "global_rules.json").write_text("[]")
        (processed_dir / "benchmark_results.json").write_text("[]")
        (processed_dir / "accuracy_deltas.csv").write_text("col1,col2\n1,2")
        (processed_dir / "statistical_analysis.json").write_text("{}")
        (processed_dir / "exclusion_summary.md").write_text("# Report")
        (processed_dir / "exclusion_log.json").write_text("")
        (processed_dir / "per_trace_scores.csv").write_text("col1,col2\n1,2")
        
        # Mock get_config to return our temp dir
        with patch('utils.lineage.get_config') as mock_config:
            mock_config.return_value.data_dir = str(data_dir)
            mock_config.return_value.project_root = tmpdir
            
            dag = build_dag(state, exclusion_log)
            
            assert "nodes" in dag
            assert "edges" in dag
            assert "metadata" in dag
            assert len(dag["nodes"]) > 0
            # Verify some edges exist
            edge_sources = [e["source"] for e in dag["edges"]]
            # feature_matrix should depend on training trace
            assert any("training" in s for s in edge_sources)

def test_generate_dot_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        dag = {
            "nodes": [
                {"id": "file:data/raw/1.json", "type": "raw_data", "path": "data/raw/1.json"},
                {"id": "file:data/processed/1.csv", "type": "processed_data", "path": "data/processed/1.csv"}
            ],
            "edges": [
                {"source": "file:data/raw/1.json", "target": "file:data/processed/1.csv", "transformation": "extract"}
            ]
        }
        
        dot_path = Path(tmpdir) / "test.dot"
        generate_dot_file(dag, dot_path)
        
        assert dot_path.exists()
        content = dot_path.read_text()
        assert "digraph DataLineage" in content
        assert "data_raw_1_json" in content
        assert "data_processed_1_csv" in content
        assert "->" in content
