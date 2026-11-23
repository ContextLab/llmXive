import os
import csv
import json
import tempfile
from pathlib import Path
import pytest

from evaluation.latency_monitor import measure_inference_latency, save_latency_results, collect_latency_stats
from evaluation.runner import run_evaluation, load_repopeftbench_data

# Mock data for testing
MOCK_DATA = [
    {
        "task_id": "mock_task_1",
        "prompt": "def add(a, b):\n    return a + b",
        "expected_output": "def add(a, b):\n    return a + b"
    },
    {
        "task_id": "mock_task_2",
        "prompt": "def sub(a, b):\n    return a - b",
        "expected_output": "def sub(a, b):\n    return a - b"
    }
]

class MockModel:
    def generate(self, **kwargs):
        # Return a dummy tensor
        import torch
        return torch.tensor([[1, 2, 3]])

class MockTokenizer:
    def __call__(self, text, **kwargs):
        return {"input_ids": [[1, 2, 3]], "attention_mask": [[1, 1, 1]]}
    def decode(self, tokens, **kwargs):
        return "mock_output"

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_measure_inference_latency_success():
    def dummy_inference():
        time.sleep(0.01) # Sleep for 10ms
        return "result"

    result = measure_inference_latency("test_1", dummy_inference)
    assert result["task_id"] == "test_1"
    assert result["status"] == "success"
    assert result["latency_ms"] >= 10.0 # Should be at least 10ms


def test_save_latency_results(temp_dir):
    results = [
        {"task_id": "t1", "latency_ms": 10.5, "status": "success"},
        {"task_id": "t2", "latency_ms": 20.3, "status": "success"}
    ]
    output_path = temp_dir / "latency.csv"
    save_latency_results(results, str(output_path))

    assert output_path.exists()
    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 2
    assert rows[0]["task_id"] == "t1"
    assert float(rows[0]["latency_ms"]) == 10.5


def test_collect_latency_stats():
    results = [
        {"task_id": "t1", "latency_ms": 10.0, "status": "success"},
        {"task_id": "t2", "latency_ms": 20.0, "status": "success"},
        {"task_id": "t3", "latency_ms": 30.0, "status": "success"},
        {"task_id": "t4", "latency_ms": 5.0, "status": "error"} # Should be ignored
    ]
    stats = collect_latency_stats(results)
    assert stats["count"] == 3
    assert stats["min"] == 10.0
    assert stats["max"] == 30.0
    assert stats["mean"] == 20.0
    assert stats["median"] == 20.0


def test_integration_latency_in_runner(temp_dir):
    # Create a mock data file
    data_file = temp_dir / "data.csv"
    with open(data_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["task_id", "prompt", "expected_output"])
        writer.writeheader()
        for item in MOCK_DATA:
            writer.writerow(item)

    # Mock model and tokenizer
    model = MockModel()
    tokenizer = MockTokenizer()

    scores_path = temp_dir / "scores.csv"
    latency_path = temp_dir / "latency.csv"

    summary = run_evaluation(
        MOCK_DATA,
        model,
        tokenizer,
        str(scores_path),
        str(latency_path),
        max_samples=2
    )

    assert scores_path.exists()
    assert latency_path.exists()

    # Verify latency file has content
    with open(latency_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 2
    assert "latency_ms" in rows[0]
    assert float(rows[0]["latency_ms"]) > 0