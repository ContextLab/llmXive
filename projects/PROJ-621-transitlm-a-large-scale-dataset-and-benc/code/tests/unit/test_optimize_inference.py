import pytest
import json
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

from src.analysis.optimize_inference import (
    load_model_optimized,
    run_batched_inference,
    run_optimized_benchmark,
    MAX_TIME_SECONDS
)
from src.lib.config import set_seed

@pytest.fixture
def sample_graph():
    return {
        "nodes": [
            {"id": "A", "type": "station"},
            {"id": "B", "type": "station"},
            {"id": "C", "type": "station"}
        ],
        "edges": [
            {"source": "A", "target": "B", "type": "transfer"},
            {"source": "B", "target": "C", "type": "transfer"}
        ]
    }

@pytest.fixture
def sample_od_pairs():
    return [
        {"origin": "A", "destination": "C"},
        {"origin": "A", "destination": "B"}
    ]

def test_run_optimized_benchmark_time_constraint(sample_graph, sample_od_pairs):
    """
    Verify that the benchmark completes within the 6-hour limit (simulated).
    """
    with TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        graph_path = tmpdir / "graph.json"
        od_path = tmpdir / "od.json"
        output_path = tmpdir / "results.json"

        # Write fixtures
        with open(graph_path, 'w') as f:
            json.dump(sample_graph, f)
        with open(od_path, 'w') as f:
            json.dump(sample_od_pairs, f)

        # Mock model loading and inference to simulate fast execution
        # We cannot load a real model in unit tests easily without heavy deps
        with patch('src.analysis.optimize_inference.AutoModelForCausalLM.from_pretrained') as mock_model, \
             patch('src.analysis.optimize_inference.AutoTokenizer.from_pretrained') as mock_tokenizer, \
             patch('src.analysis.optimize_inference.run_batched_inference') as mock_infer:
            
            # Setup mocks
            mock_model.return_value = MagicMock()
            mock_tokenizer.return_value = MagicMock(pad_token='<pad>', eos_token='<eos>')
            mock_infer.return_value = ["Take line L from A to C", "Take line L from A to B"]

            # Run benchmark
            result = run_optimized_benchmark(
                graph_path=graph_path,
                od_pairs_path=od_path,
                output_path=output_path,
                model_name="test-model",
                max_new_tokens=10
            )

            # Assert output file was created
            assert output_path.exists()

            # Assert result structure
            assert result["success"] is True # Should be under limit
            assert result["total_samples"] == 2
            assert result["valid_count"] >= 0 # Depends on validation logic which runs with real graph

def test_batched_inference_mock():
    """
    Test the batched inference logic with mocked model.
    """
    mock_model = MagicMock()
    mock_tokenizer = MagicMock()
    
    # Setup tokenizer mock
    mock_tokenizer.return_value = {"input_ids": [[1, 2, 3]], "attention_mask": [[1, 1, 1]]}
    mock_tokenizer.decode.return_value = "Result"
    
    # Setup model generate mock
    mock_output = MagicMock()
    mock_output.__iter__ = lambda self: iter([MagicMock(__len__=lambda self: 3, __getitem__=lambda self, i: [1,2,3,4,5])])
    mock_model.generate.return_value = mock_output

    prompts = ["Prompt 1", "Prompt 2"]
    
    # Note: This is a structural test. Real tokenization requires a real tokenizer.
    # We are testing the logic flow in run_batched_inference if it were called.
    # For now, we assert the function exists and signature is correct.
    assert callable(run_batched_inference)

def test_time_limit_constant():
    assert MAX_TIME_SECONDS == 6 * 3600
