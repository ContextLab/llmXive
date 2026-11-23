import os
import json
import pytest
from pathlib import Path
import tempfile
import shutil

# We will mock the Config import if it fails in test environment
try:
    from validate.vlm_trace_auditor import audit_vlm_traces, load_jsonl, load_json
except ImportError:
    # Fallback for direct test execution if path setup is weird
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
    from validate.vlm_trace_auditor import audit_vlm_traces, load_jsonl, load_json

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)

def test_audit_pass_no_leaks(temp_dir):
    """Test audit passes when IDs match and no tool traces are present."""
    # Setup files
    scenes_file = temp_dir / "sampled_scenes.jsonl"
    vlm_file = temp_dir / "vlm_baseline.jsonl"
    constraints_file = temp_dir / "constraints.jsonl"
    output_file = temp_dir / "audit_result.json"

    scene_data = [
        {"scene_id": "scene_001", "geometry": {"objects": []}},
        {"scene_id": "scene_002", "geometry": {"objects": []}}
    ]
    vlm_data = [
        {"scene_id": "scene_001", "prediction": 5},
        {"scene_id": "scene_002", "prediction": 3}
    ]
    constraint_data = [
        {"scene_id": "scene_001", "constraints": [{"type": "left_of"}]},
        {"scene_id": "scene_002", "constraints": [{"type": "above"}]}
    ]

    with open(scenes_file, 'w') as f:
        f.write('\n'.join(json.dumps(x) for x in scene_data))
    with open(vlm_file, 'w') as f:
        f.write('\n'.join(json.dumps(x) for x in vlm_data))
    with open(constraints_file, 'w') as f:
        f.write('\n'.join(json.dumps(x) for x in constraint_data))

    result = audit_vlm_traces(scenes_file, vlm_file, constraints_file, output_file)

    assert result["status"] == "pass"
    assert result["discrepancies"] == []
    assert output_file.exists()

    with open(output_file) as f:
        saved = json.load(f)
    assert saved["status"] == "pass"

def test_audit_fail_missing_vlm_ids(temp_dir):
    """Test audit fails when VLM baseline is missing some scene IDs."""
    scenes_file = temp_dir / "sampled_scenes.jsonl"
    vlm_file = temp_dir / "vlm_baseline.jsonl"
    constraints_file = temp_dir / "constraints.jsonl"
    output_file = temp_dir / "audit_result.json"

    scene_data = [
        {"scene_id": "scene_001", "geometry": {}},
        {"scene_id": "scene_002", "geometry": {}},
        {"scene_id": "scene_003", "geometry": {}}
    ]
    # Only has scene_001 and scene_002
    vlm_data = [
        {"scene_id": "scene_001", "prediction": 5},
        {"scene_id": "scene_002", "prediction": 3}
    ]
    constraint_data = [
        {"scene_id": "scene_001", "constraints": []},
        {"scene_id": "scene_002", "constraints": []},
        {"scene_id": "scene_003", "constraints": []}
    ]

    with open(scenes_file, 'w') as f:
        f.write('\n'.join(json.dumps(x) for x in scene_data))
    with open(vlm_file, 'w') as f:
        f.write('\n'.join(json.dumps(x) for x in vlm_data))
    with open(constraints_file, 'w') as f:
        f.write('\n'.join(json.dumps(x) for x in constraint_data))

    result = audit_vlm_traces(scenes_file, vlm_file, constraints_file, output_file)

    assert result["status"] == "fail"
    assert len(result["discrepancies"]) > 0
    assert any(d["type"] == "missing_vlm_baseline" for d in result["discrepancies"])

def test_audit_fail_tool_trace_leak(temp_dir):
    """Test audit fails when tool-call traces are detected in constraints."""
    scenes_file = temp_dir / "sampled_scenes.jsonl"
    vlm_file = temp_dir / "vlm_baseline.jsonl"
    constraints_file = temp_dir / "constraints.jsonl"
    output_file = temp_dir / "audit_result.json"

    scene_data = [{"scene_id": "scene_001", "geometry": {}}]
    vlm_data = [{"scene_id": "scene_001", "prediction": 5}]
    # Contains 'tool_call' key which is a leak
    constraint_data = [
        {"scene_id": "scene_001", "constraints": [], "tool_call": "some_tool"}
    ]

    with open(scenes_file, 'w') as f:
        f.write('\n'.join(json.dumps(x) for x in scene_data))
    with open(vlm_file, 'w') as f:
        f.write('\n'.join(json.dumps(x) for x in vlm_data))
    with open(constraints_file, 'w') as f:
        f.write('\n'.join(json.dumps(x) for x in constraint_data))

    result = audit_vlm_traces(scenes_file, vlm_file, constraints_file, output_file)

    assert result["status"] == "fail"
    assert any(d["type"] == "tool_trace_leak" for d in result["discrepancies"])

def test_audit_fail_extra_vlm_ids(temp_dir):
    """Test audit fails when VLM baseline has extra IDs not in sampled scenes."""
    scenes_file = temp_dir / "sampled_scenes.jsonl"
    vlm_file = temp_dir / "vlm_baseline.jsonl"
    constraints_file = temp_dir / "constraints.jsonl"
    output_file = temp_dir / "audit_result.json"

    scene_data = [{"scene_id": "scene_001", "geometry": {}}]
    # Has extra scene_002
    vlm_data = [
        {"scene_id": "scene_001", "prediction": 5},
        {"scene_id": "scene_002", "prediction": 3}
    ]
    constraint_data = [{"scene_id": "scene_001", "constraints": []}]

    with open(scenes_file, 'w') as f:
        f.write('\n'.join(json.dumps(x) for x in scene_data))
    with open(vlm_file, 'w') as f:
        f.write('\n'.join(json.dumps(x) for x in vlm_data))
    with open(constraints_file, 'w') as f:
        f.write('\n'.join(json.dumps(x) for x in constraint_data))

    result = audit_vlm_traces(scenes_file, vlm_file, constraints_file, output_file)

    assert result["status"] == "fail"
    assert any(d["type"] == "extra_vlm_baseline" for d in result["discrepancies"])

def test_audit_file_not_found(temp_dir):
    """Test audit handles missing input files gracefully."""
    scenes_file = temp_dir / "sampled_scenes.jsonl"
    vlm_file = temp_dir / "vlm_baseline.jsonl"
    constraints_file = temp_dir / "constraints.jsonl"
    output_file = temp_dir / "audit_result.json"

    # Write scenes only
    with open(scenes_file, 'w') as f:
        f.write(json.dumps({"scene_id": "scene_001"}))

    result = audit_vlm_traces(scenes_file, vlm_file, constraints_file, output_file)

    assert result["status"] == "fail"
    assert "error" in result or "discrepancies" in result