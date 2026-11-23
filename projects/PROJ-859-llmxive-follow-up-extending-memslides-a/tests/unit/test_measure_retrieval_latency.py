import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from evaluation.measure_retrieval_latency import (
    RetrievalLatencyMeasurer,
    calculate_retrieval_latencies
)
from config import get_config

@pytest.fixture
def mock_config():
    return {
        "held_out_dir": "data/held_out",
        "latency_output_path": "data/processed/retrieval_latencies.json",
        "seed": 42
    }

@pytest.fixture
def temp_trace_dir(tmp_path):
    # Create a temporary directory with mock trace files
    trace_dir = tmp_path / "held_out"
    trace_dir.mkdir()
    
    trace1 = {
        "trace_id": "trace_001",
        "tool_sequence": ["tool_a", "tool_b"],
        "final_state": {"slide": "A"}
    }
    trace2 = {
        "trace_id": "trace_002",
        "tool_sequence": ["tool_c"],
        "final_state": {"slide": "B"}
    }

    (trace_dir / "trace_001.json").write_text(json.dumps(trace1))
    (trace_dir / "trace_002.json").write_text(json.dumps(trace2))
    
    return str(trace_dir)

@pytest.fixture
def mock_agents():
    with patch('evaluation.measure_retrieval_latency.BaselineAgent') as mock_base, \
         patch('evaluation.measure_retrieval_latency.CompressedAgent') as mock_comp:
        
        mock_base_inst = MagicMock()
        mock_base_inst.prepare_context = MagicMock(return_value=None)
        mock_base.return_value = mock_base_inst

        mock_comp_inst = MagicMock()
        mock_comp_inst.prepare_context = MagicMock(return_value=None)
        mock_comp.return_value = mock_comp_inst

        yield mock_base, mock_comp, mock_base_inst, mock_comp_inst

def test_retrieval_latency_measurer_init(mock_config):
    measurer = RetrievalLatencyMeasurer(mock_config)
    assert measurer.config == mock_config
    assert hasattr(measurer, 'measure_baseline_latency')
    assert hasattr(measurer, 'measure_compressed_latency')

def test_measure_baseline_latency(mock_config, mock_agents):
    mock_base, _, mock_base_inst, _ = mock_agents
    measurer = RetrievalLatencyMeasurer(mock_config)
    
    trace = {"trace_id": "test", "data": "value"}
    latency = measurer.measure_baseline_latency(trace)
    
    mock_base.assert_called_once()
    mock_base_inst.prepare_context.assert_called_once_with(trace)
    assert latency >= 0

def test_measure_compressed_latency(mock_config, mock_agents):
    _, mock_comp, _, mock_comp_inst = mock_agents
    measurer = RetrievalLatencyMeasurer(mock_config)
    
    trace = {"trace_id": "test", "data": "value"}
    latency = measurer.measure_compressed_latency(trace)
    
    mock_comp.assert_called_once()
    mock_comp_inst.prepare_context.assert_called_once_with(trace)
    assert latency >= 0

def test_process_trace(mock_config, mock_agents):
    mock_base, _, mock_base_inst, mock_comp_inst = mock_agents
    # Mock time to ensure deterministic results
    with patch('evaluation.measure_retrieval_latency.time.perf_counter') as mock_time:
        mock_time.side_effect = [0.0, 0.1, 0.1, 0.2] # Base: 0.1, Comp: 0.1
        
        measurer = RetrievalLatencyMeasurer(mock_config)
        trace = {"trace_id": "test", "data": "value"}
        
        result = measurer.process_trace("test_id", trace)
        
        assert result["trace_id"] == "test_id"
        assert result["baseline_latency"] == 0.1
        assert result["compressed_latency"] == 0.1
        assert result["latency_delta"] == 0.0

def test_calculate_retrieval_latencies(mock_config, temp_trace_dir, mock_agents):
    output_path = str(Path(temp_trace_dir).parent / "output_latencies.json")
    
    with patch('evaluation.measure_retrieval_latency.time.perf_counter') as mock_time:
        mock_time.side_effect = [0.0, 0.05, 0.05, 0.15,  # Trace 1: Base 0.05, Comp 0.1
                                 0.0, 0.05, 0.05, 0.15] # Trace 2: Base 0.05, Comp 0.1
        
        results = calculate_retrieval_latencies(temp_trace_dir, output_path, mock_config)
        
        assert len(results) == 2
        assert results[0]["trace_id"] == "trace_001"
        assert results[1]["trace_id"] == "trace_002"
        
        # Verify output file was created
        assert Path(output_path).exists()
        
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        
        assert len(saved_data) == 2

def test_calculate_retrieval_latencies_missing_dir(mock_config):
    with pytest.raises(FileNotFoundError):
        calculate_retrieval_latencies("non_existent_dir", "output.json", mock_config)

def test_calculate_retrieval_latencies_no_files(mock_config, tmp_path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    
    with pytest.raises(ValueError):
        calculate_retrieval_latencies(str(empty_dir), "output.json", mock_config)
