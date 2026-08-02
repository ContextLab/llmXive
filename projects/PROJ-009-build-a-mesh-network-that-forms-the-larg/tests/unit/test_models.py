"""
Unit tests for the base data models.

Validates Pydantic models: PhysicalNode, TaskChunk, ExecutionRun.
"""
import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from code.orchestrator.models import (
    PhysicalNode,
    TaskChunk,
    ExecutionRun,
    NodeStatus,
    TaskStatus,
    ExecutionStatus
)


class TestPhysicalNode:
    def test_create_valid_node(self):
        node = PhysicalNode(
            node_id="node-001",
            hostname="192.168.1.10",
            username="researcher",
            hardware_spec={"cpu_arch": "x86_64", "ram_gb": 16, "cores": 8}
        )
        assert node.node_id == "node-001"
        assert node.status == NodeStatus.IDLE
        assert node.port == 22
        assert node.hardware_spec["cpu_arch"] == "x86_64"

    def test_invalid_port(self):
        with pytest.raises(ValidationError):
            PhysicalNode(
                node_id="node-002",
                hostname="192.168.1.11",
                username="researcher",
                port=70000
            )

    def test_negative_latency(self):
        with pytest.raises(ValidationError):
            PhysicalNode(
                node_id="node-003",
                hostname="192.168.1.12",
                username="researcher",
                latency_ms=-5.0
            )

    def test_negative_bandwidth(self):
        with pytest.raises(ValidationError):
            PhysicalNode(
                node_id="node-004",
                hostname="192.168.1.13",
                username="researcher",
                bandwidth_mbps=-100.0
            )

    def test_hardware_spec_must_be_dict(self):
        with pytest.raises(ValidationError):
            PhysicalNode(
                node_id="node-005",
                hostname="192.168.1.14",
                username="researcher",
                hardware_spec="not a dict"
            )


class TestTaskChunk:
    def test_create_valid_chunk(self):
        chunk = TaskChunk(
            chunk_id="chunk-001",
            task_type="monte_carlo",
            payload={"iterations": 10000, "seed": 42},
            expected_duration_sec=5.0
        )
        assert chunk.chunk_id == "chunk-001"
        assert chunk.status == TaskStatus.PENDING
        assert chunk.payload["iterations"] == 10000

    def test_invalid_duration(self):
        with pytest.raises(ValidationError):
            TaskChunk(
                chunk_id="chunk-002",
                task_type="monte_carlo",
                expected_duration_sec=-1.0
            )

    def test_payload_must_be_dict(self):
        with pytest.raises(ValidationError):
            TaskChunk(
                chunk_id="chunk-003",
                task_type="monte_carlo",
                payload="not a dict"
            )

    def test_end_time_before_start_time(self):
        with pytest.raises(ValidationError):
            TaskChunk(
                chunk_id="chunk-004",
                task_type="monte_carlo",
                start_time=datetime(2024, 1, 1, 12, 0, 0),
                end_time=datetime(2024, 1, 1, 11, 0, 0)
            )


class TestExecutionRun:
    def test_create_valid_run(self):
        run = ExecutionRun(
            run_id="run-001",
            node_ids=["node-001", "node-002"],
            config_snapshot={"granularity": "medium"}
        )
        assert run.run_id == "run-001"
        assert run.status == ExecutionStatus.PLANNED
        assert len(run.node_ids) == 2

    def test_duplicate_node_ids(self):
        with pytest.raises(ValidationError):
            ExecutionRun(
                run_id="run-002",
                node_ids=["node-001", "node-001"]
            )

    def test_duplicate_chunk_ids(self):
        chunk1 = TaskChunk(chunk_id="c1", task_type="test")
        chunk2 = TaskChunk(chunk_id="c1", task_type="test")  # Duplicate ID
        with pytest.raises(ValidationError):
            ExecutionRun(
                run_id="run-003",
                task_chunks=[chunk1, chunk2]
            )

    def test_end_time_before_start_time(self):
        with pytest.raises(ValidationError):
            ExecutionRun(
                run_id="run-004",
                start_time=datetime(2024, 1, 1, 12, 0, 0),
                end_time=datetime(2024, 1, 1, 11, 0, 0)
            )

    def test_completed_run_must_have_end_time(self):
        with pytest.raises(ValidationError):
            ExecutionRun(
                run_id="run-005",
                status=ExecutionStatus.COMPLETED
            )

    def test_completed_run_cannot_have_error_code(self):
        with pytest.raises(ValidationError):
            ExecutionRun(
                run_id="run-006",
                status=ExecutionStatus.COMPLETED,
                end_time=datetime(2024, 1, 1, 13, 0, 0),
                error_code="TIMEOUT"
            )

    def test_auto_calculate_wall_clock_time(self):
        start = datetime(2024, 1, 1, 12, 0, 0)
        end = datetime(2024, 1, 1, 12, 1, 30)
        run = ExecutionRun(
            run_id="run-007",
            start_time=start,
            end_time=end
        )
        assert run.total_wall_clock_time_sec == 90.0

    def test_coordination_overhead_ratio_bounds(self):
        # Valid range
        run = ExecutionRun(
            run_id="run-008",
            coordination_overhead_ratio=0.5
        )
        assert run.coordination_overhead_ratio == 0.5

        # Invalid: > 1.0
        with pytest.raises(ValidationError):
            ExecutionRun(
                run_id="run-009",
                coordination_overhead_ratio=1.5
            )

        # Invalid: < 0
        with pytest.raises(ValidationError):
            ExecutionRun(
                run_id="run-010",
                coordination_overhead_ratio=-0.1
            )

    def test_model_serialization(self):
        node = PhysicalNode(
            node_id="node-001",
            hostname="192.168.1.10",
            username="researcher"
        )
        chunk = TaskChunk(
            chunk_id="chunk-001",
            task_type="monte_carlo",
            payload={"iterations": 1000}
        )
        run = ExecutionRun(
            run_id="run-001",
            node_ids=["node-001"],
            task_chunks=[chunk],
            config_snapshot={"param": "value"}
        )

        # Test dict serialization
        run_dict = run.model_dump()
        assert run_dict["run_id"] == "run-001"
        assert len(run_dict["task_chunks"]) == 1

        # Test JSON serialization
        run_json = run.model_dump_json()
        assert "run-001" in run_json
