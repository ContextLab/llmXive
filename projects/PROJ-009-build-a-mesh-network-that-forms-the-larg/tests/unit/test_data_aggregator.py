import csv
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from orchestrator.data_aggregator import DataAggregator, AggregatedExecutionLog

@pytest.fixture
def temp_data_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_dir = Path(tmpdir) / "raw"
        raw_dir.mkdir()
        processed_dir = Path(tmpdir) / "processed"
        processed_dir.mkdir()
        
        # Mock config file
        config_content = {
            "project": {
                "raw_data_dir": str(raw_dir),
                "processed_data_dir": str(processed_dir)
            },
            "nodes": {}
        }
        config_path = Path(tmpdir) / "config.yaml"
        with open(config_path, 'w') as f:
            import yaml
            yaml.dump(config_content, f)
        
        yield str(config_path)
        # Cleanup handled by TemporaryDirectory

@pytest.fixture
def mock_network_metrics(temp_data_dir):
    raw_dir = Path(temp_data_dir).parent / "raw"
    metrics_file = raw_dir / "network_metrics.csv"
    with open(metrics_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['node_id', 'bandwidth_Mbps', 'snr_db'])
        writer.writeheader()
        writer.writerow({'node_id': 'node_1', 'bandwidth_Mbps': 100.5, 'snr_db': 25.0})
        writer.writerow({'node_id': 'node_2', 'bandwidth_Mbps': 95.0, 'snr_db': 22.5})

@pytest.fixture
def mock_instrumentor_logs(temp_data_dir, mock_network_metrics):
    raw_dir = Path(temp_data_dir).parent / "raw"
    
    # Create log for node_1
    log1 = raw_dir / "node_1_instrumentor.log"
    with open(log1, 'w') as f:
        f.write(json.dumps({
            "node_id": "node_1",
            "wall_clock_time": 12.5,
            "cpu_utilization_pct": 45.0,
            "packet_count": 1000,
            "status": "completed",
            "current_latency": 15.0
        }) + "\n")
    
    # Create log for node_2
    log2 = raw_dir / "node_2_instrumentor.log"
    with open(log2, 'w') as f:
        f.write(json.dumps({
            "node_id": "node_2",
            "wall_clock_time": 15.0,
            "cpu_utilization_pct": 60.0,
            "packet_count": 1200,
            "status": "completed",
            "current_latency": 20.0
        }) + "\n")

@pytest.fixture
def mock_no_saturation(temp_data_dir):
    raw_dir = Path(temp_data_dir).parent / "raw"
    # No saturation flag file created
    pass

@pytest.fixture
def mock_saturation(temp_data_dir):
    raw_dir = Path(temp_data_dir).parent / "raw"
    status_file = raw_dir / "run_status.json"
    with open(status_file, 'w') as f:
        json.dump({"status": "network_saturation"}, f)

def test_aggregation_success(temp_data_dir, mock_network_metrics, mock_instrumentor_logs, mock_no_saturation):
    """Test successful aggregation of logs."""
    aggregator = DataAggregator(temp_data_dir)
    
    logs = aggregator.aggregate()
    
    assert len(logs) == 2
    
    # Check node_1
    node1_log = next((l for l in logs if l.node_id == "node_1"), None)
    assert node1_log is not None
    assert node1_log.wall_clock_time == 12.5
    assert node1_log.cpu_utilization_pct == 45.0
    assert node1_log.packet_count == 1000
    assert node1_log.bandwidth_Mbps == 100.5
    assert node1_log.snr_db == 25.0
    
    # Check node_2
    node2_log = next((l for l in logs if l.node_id == "node_2"), None)
    assert node2_log is not None
    assert node2_log.wall_clock_time == 15.0
    assert node2_log.cpu_utilization_pct == 60.0
    assert node2_log.bandwidth_Mbps == 95.0
    
    # Verify CSV file exists
    output_file = Path(temp_data_dir).parent / "raw" / "execution_logs.csv"
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert 'node_id' in rows[0]
        assert 'bandwidth_Mbps' in rows[0]

def test_saturation_aborts(temp_data_dir, mock_network_metrics, mock_instrumentor_logs, mock_saturation):
    """Test that aggregation aborts if T043 detects saturation."""
    aggregator = DataAggregator(temp_data_dir)
    
    with pytest.raises(RuntimeError, match="Network saturation detected"):
        aggregator.aggregate()

def test_missing_network_metrics(temp_data_dir, mock_instrumentor_logs, mock_no_saturation):
    """Test error when network metrics file is missing."""
    # Remove the mock network metrics
    raw_dir = Path(temp_data_dir).parent / "raw"
    metrics_file = raw_dir / "network_metrics.csv"
    if metrics_file.exists():
        metrics_file.unlink()
    
    aggregator = DataAggregator(temp_data_dir)
    
    with pytest.raises(FileNotFoundError, match="Network metrics file not found"):
        aggregator.aggregate()

def test_missing_instrumentor_logs(temp_data_dir, mock_network_metrics, mock_no_saturation):
    """Test handling when no instrumentor logs are found."""
    # Remove log files
    raw_dir = Path(temp_data_dir).parent / "raw"
    for f in raw_dir.glob("node_*_instrumentor.log"):
        f.unlink()
    
    aggregator = DataAggregator(temp_data_dir)
    
    logs = aggregator.aggregate()
    assert len(logs) == 0
    
    # Verify empty CSV is created
    output_file = raw_dir / "execution_logs.csv"
    assert output_file.exists()
    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 0

def test_aggregated_execution_log_to_dict():
    """Test the to_dict method of AggregatedExecutionLog."""
    log = AggregatedExecutionLog(
        node_id="test_node",
        wall_clock_time=10.0,
        cpu_utilization_pct=50.0,
        packet_count=500,
        status="completed",
        hardware_spec='{"cpu": "test"}',
        current_latency=5.0,
        bandwidth_Mbps=100.0,
        snr_db=30.0
    )
    
    d = log.to_dict()
    assert d["node_id"] == "test_node"
    assert d["wall_clock_time"] == 10.0
    assert d["hardware_spec"] == '{"cpu": "test"}'
    assert isinstance(d["hardware_spec"], str)
