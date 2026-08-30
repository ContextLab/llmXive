import pytest
import json
import os
import tempfile
from pathlib import Path

# Import the module under test
from ablation import load_trajectories, generate_ablation_config, simulate_ablation_engine, run_ablation_study

def test_load_trajectories_empty_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write("")
        f.flush()
        with pytest.raises(ValueError):
            load_trajectories(f.name)
    os.unlink(f.name)

def test_load_trajectories_valid():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write('{"trajectory_id": "1", "layer_1": "data"}\n')
        f.write('{"trajectory_id": "2", "layer_1": "more data"}\n')
        f.flush()
        data = load_trajectories(f.name)
        assert len(data) == 2
        assert data[0]['trajectory_id'] == '1'
    os.unlink(f.name)

def test_generate_ablation_config_no_layers():
    # Schema with no layers defined
    schema = {"properties": {}}
    trajectories = [{"trajectory_id": "1"}]
    configs = generate_ablation_config(trajectories, schema)
    # Should fall back to defaults or empty list depending on implementation
    # In our implementation, it falls back to defaults if no layers found in schema
    assert len(configs) > 0

def test_simulate_ablation_engine_missing_layer():
    traj = {"trajectory_id": "1", "layer_1": "data"}
    delta = simulate_ablation_engine(traj, "layer_2", {})
    assert delta == 0.0

def test_simulate_ablation_engine_present_layer():
    traj = {"trajectory_id": "1", "layer_1": "some data content here"}
    delta = simulate_ablation_engine(traj, "layer_1", {})
    # Should be negative based on token count logic
    assert delta < 0.0

def test_run_ablation_study_integration():
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_path = os.path.join(tmpdir, "raw.jsonl")
        schema_path = os.path.join(tmpdir, "schema.json")
        out_path = os.path.join(tmpdir, "results.json")
        
        # Create raw data
        with open(raw_path, 'w') as f:
            f.write('{"trajectory_id": "t1", "layer_1": "data"}\n')
            f.write('{"trajectory_id": "t2", "layer_1": "more data"}\n')
        
        # Create simple schema
        with open(schema_path, 'w') as f:
            json.dump({"properties": {"layers": {"items": {"enum": ["layer_1"]}}}}, f)
        
        # Run study
        results = run_ablation_study(
            load_trajectories(raw_path),
            json.load(open(schema_path)),
            out_path
        )
        
        assert os.path.exists(out_path)
        assert len(results) > 0
        # Check structure
        assert 'trajectory_id' in results[0]
        assert 'utility_delta' in results[0]
