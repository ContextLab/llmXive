import json
import tempfile
from pathlib import Path
import pytest
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from evaluation.measure_retrieval_latency import RetrievalLatencyMeasurer
from config import get_config


@pytest.fixture
def sample_trace():
    return {
        "trace_id": "test-001",
        "tool_sequence": ["edit_slide", "insert_text", "format_text"],
        "arguments": [
            {"slide_id": 1, "content": "Hello"},
            {"text": "World"},
            {"style": "bold"}
        ],
        "final_state": {"slide_count": 1, "total_chars": 5}
    }


@pytest.fixture
def sample_rules():
    return {
        "rules": [
            {"id": 1, "pattern": "edit_slide", "action": "compress"},
            {"id": 2, "pattern": "insert_text", "action": "keep"}
        ],
        "metadata": {"version": "1.0"}
    }


@pytest.fixture
def temp_dirs():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        held_out_dir = tmpdir / "held_out"
        held_out_dir.mkdir()
        
        # Create a sample trace file
        trace_file = held_out_dir / "session_test-001.json"
        with open(trace_file, 'w') as f:
            json.dump({"trace_id": "test-001", "tool_sequence": ["edit"]}, f)
        
        # Create rules file
        rules_file = tmpdir / "global_rules.json"
        with open(rules_file, 'w') as f:
            json.dump({"rules": []}, f)
        
        yield {
            "held_out_dir": held_out_dir,
            "rules_path": rules_file,
            "output_path": tmpdir / "latency_results.json"
        }


def test_measure_baseline_latency(sample_trace):
    config = get_config()
    measurer = RetrievalLatencyMeasurer(config)
    
    latency = measurer.measure_baseline_latency(sample_trace)
    
    assert isinstance(latency, float)
    assert latency >= 0.0
    assert latency < 1.0  # Should be very fast


def test_measure_compressed_latency(sample_trace, sample_rules, temp_dirs):
    config = get_config()
    measurer = RetrievalLatencyMeasurer(config)
    
    # Write sample rules to temp file
    with open(temp_dirs["rules_path"], 'w') as f:
        json.dump(sample_rules, f)
    
    latency = measurer.measure_compressed_latency(sample_trace, temp_dirs["rules_path"])
    
    assert isinstance(latency, float)
    assert latency >= 0.0
    assert latency < 1.0


def test_run_measurement(sample_trace, sample_rules, temp_dirs):
    config = get_config()
    measurer = RetrievalLatencyMeasurer(config)
    
    # Write sample rules
    with open(temp_dirs["rules_path"], 'w') as f:
        json.dump(sample_rules, f)
    
    result = measurer.run_measurement("test-001", sample_trace, temp_dirs["rules_path"])
    
    assert "trace_id" in result
    assert "baseline_latency" in result
    assert "compressed_latency" in result
    assert result["trace_id"] == "test-001"
    assert isinstance(result["baseline_latency"], float)
    assert isinstance(result["compressed_latency"], float)


def test_calculate_retrieval_latencies(temp_dirs):
    config = get_config()
    measurer = RetrievalLatencyMeasurer(config)
    
    results = measurer.calculate_retrieval_latencies(
        temp_dirs["held_out_dir"], 
        temp_dirs["rules_path"]
    )
    
    assert isinstance(results, list)
    assert len(results) == 1  # We created one trace file
    assert results[0]["trace_id"] == "session_test-001"
    assert "baseline_latency" in results[0]
    assert "compressed_latency" in results[0]


def test_save_results(temp_dirs):
    config = get_config()
    measurer = RetrievalLatencyMeasurer(config)
    
    # Manually set results
    measurer.latency_results = [
        {
            "trace_id": "test-001",
            "baseline_latency": 0.001,
            "compressed_latency": 0.0005
        }
    ]
    
    measurer.save_results(temp_dirs["output_path"])
    
    assert temp_dirs["output_path"].exists()
    
    with open(temp_dirs["output_path"], 'r') as f:
        saved_data = json.load(f)
    
    assert len(saved_data) == 1
    assert saved_data[0]["trace_id"] == "test-001"


def test_missing_held_out_directory():
    config = get_config()
    measurer = RetrievalLatencyMeasurer(config)
    
    with pytest.raises(FileNotFoundError):
        measurer.calculate_retrieval_latencies(
            Path("/nonexistent/path"), 
            Path("/nonexistent/rules.json")
        )


def test_missing_rules_file(temp_dirs):
    config = get_config()
    measurer = RetrievalLatencyMeasurer(config)
    
    with pytest.raises(FileNotFoundError):
        measurer.calculate_retrieval_latencies(
            temp_dirs["held_out_dir"], 
            Path("/nonexistent/rules.json")
        )