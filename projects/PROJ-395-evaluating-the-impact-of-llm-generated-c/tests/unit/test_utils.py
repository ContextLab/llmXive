import os
import tempfile
import pytest
from utils import write_memory_measurements_csv, read_memory_measurements_csv, calculate_total_resource_cost

def test_write_and_read_csv():
    """Test that write_memory_measurements_csv writes and read_memory_measurements_csv reads correctly."""
    sample_data = [
        {
            "problem_id": "human_001",
            "source_type": "human",
            "peak_memory": 1024000000,
            "steady_state": 512000000,
            "status": "success",
            "total_resource_cost": 512000000000.0
        },
        {
            "problem_id": "llm_001",
            "source_type": "llm",
            "peak_memory": 2048000000,
            "steady_state": 1024000000,
            "status": "timeout",
            "total_resource_cost": 420000000000.0
        }
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "memory_measurements.csv")
        
        # Write
        write_memory_measurements_csv(sample_data, csv_path)
        
        # Verify file exists
        assert os.path.exists(csv_path)
        
        # Read back
        read_data = read_memory_measurements_csv(csv_path)
        
        # Verify content
        assert len(read_data) == len(sample_data)
        for i, row in enumerate(read_data):
            assert row["problem_id"] == sample_data[i]["problem_id"]
            assert row["source_type"] == sample_data[i]["source_type"]
            assert row["status"] == sample_data[i]["status"]
            # Numeric comparison for floats
            assert abs(float(row["peak_memory"]) - sample_data[i]["peak_memory"]) < 1e-6

def test_write_creates_directories():
    """Test that write_memory_measurements_csv creates parent directories if they don't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        nested_path = os.path.join(tmpdir, "deep", "nested", "data.csv")
        sample_data = [
            {
                "problem_id": "test_001",
                "source_type": "human",
                "peak_memory": 100,
                "steady_state": 50,
                "status": "success",
                "total_resource_cost": 5000.0
            }
        ]
        
        write_memory_measurements_csv(sample_data, nested_path)
        assert os.path.exists(nested_path)

def test_read_missing_file():
    """Test that read_memory_measurements_csv returns empty list for missing file."""
    result = read_memory_measurements_csv("non_existent_file.csv")
    assert result == []

def test_calculate_resource_cost_success():
    """Test cost calculation for successful execution."""
    mem = 1e9  # 1 GB
    time = 10.0
    cost = calculate_total_resource_cost(mem, time, is_failure=False)
    expected = mem * time
    assert cost == expected

def test_calculate_resource_cost_failure():
    """Test cost calculation includes penalty for failure."""
    mem = 1e9
    time = 10.0
    # Assuming config constants are 7GB and 60s
    penalty = 7 * (1024**3) * 60
    cost = calculate_total_resource_cost(mem, time, is_failure=True)
    expected = (mem * time) + penalty
    assert cost == expected
