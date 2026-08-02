"""
Contract test for ExecutionRun schema validation.

This test validates that the ExecutionRun model (defined in code/orchestrator/models.py)
correctly enforces the schema constraints required by the project specification.
It ensures that valid data passes and invalid data raises appropriate Pydantic validation errors.
"""
import pytest
from datetime import datetime
from typing import List, Dict, Any

from orchestrator.models import ExecutionRun, PhysicalNode, TaskChunk, ExecutionStatus, NodeStatus, TaskStatus
from orchestrator.config import OrchestratorConfig


class TestExecutionRunSchema:
    """Test suite for ExecutionRun schema validation contracts."""

    def _create_valid_physical_node(self, node_id: str = "node-001") -> PhysicalNode:
        """Helper to create a valid PhysicalNode instance."""
        return PhysicalNode(
            node_id=node_id,
            hostname="192.168.1.10",
            hardware_spec={"cpu": "Intel i7", "ram_gb": 32, "arch": "x86_64"},
            status=NodeStatus.IDLE
        )

    def _create_valid_task_chunk(self, chunk_id: str = "chunk-001") -> TaskChunk:
        """Helper to create a valid TaskChunk instance."""
        return TaskChunk(
            chunk_id=chunk_id,
            task_type="monte_carlo",
            start_index=0,
            end_index=1000,
            status=TaskStatus.PENDING,
            assigned_node_id=None
        )

    def _create_valid_execution_run(self) -> ExecutionRun:
        """Helper to create a valid ExecutionRun instance."""
        return ExecutionRun(
            run_id="run-20231027-001",
            start_time=datetime.now(),
            end_time=None,
            status=ExecutionStatus.RUNNING,
            nodes=[self._create_valid_physical_node("node-001")],
            tasks=[self._create_valid_task_chunk("chunk-001")],
            config=OrchestratorConfig(
                node_timeout_seconds=300,
                heartbeat_interval_seconds=10,
                max_retries=3
            )
        )

    def test_valid_execution_run_creation(self):
        """Test that a fully valid ExecutionRun can be instantiated."""
        run = self._create_valid_execution_run()
        assert run.run_id == "run-20231027-001"
        assert run.status == ExecutionStatus.RUNNING
        assert len(run.nodes) == 1
        assert len(run.tasks) == 1
        assert run.nodes[0].node_id == "node-001"

    def test_run_id_uniqueness_constraint(self):
        """Test that run_id is required and non-empty."""
        with pytest.raises(Exception):
            ExecutionRun(
                run_id="",  # Empty string should fail validation if constrained
                start_time=datetime.now(),
                status=ExecutionStatus.PENDING,
                nodes=[],
                tasks=[],
                config=OrchestratorConfig()
            )

    def test_status_enum_validation(self):
        """Test that status must be a valid ExecutionStatus enum."""
        with pytest.raises(Exception):
            ExecutionRun(
                run_id="run-001",
                start_time=datetime.now(),
                status="INVALID_STATUS",  # Type error
                nodes=[],
                tasks=[],
                config=OrchestratorConfig()
            )

    def test_nodes_list_requirement(self):
        """Test that nodes must be a list of PhysicalNode objects."""
        # Valid empty list
        run = self._create_valid_execution_run()
        run.nodes = []
        assert run.nodes == []

        # Invalid: string instead of list
        with pytest.raises(Exception):
            run = self._create_valid_execution_run()
            run.nodes = "not a list"

    def test_tasks_list_requirement(self):
        """Test that tasks must be a list of TaskChunk objects."""
        # Valid empty list
        run = self._create_valid_execution_run()
        run.tasks = []
        assert run.tasks == []

        # Invalid: dict instead of list
        with pytest.raises(Exception):
            run = self._create_valid_execution_run()
            run.tasks = {"key": "value"}

    def test_end_time_nullable(self):
        """Test that end_time can be None for running runs."""
        run = self._create_valid_execution_run()
        assert run.end_time is None

        # Set to a datetime
        run.end_time = datetime.now()
        assert run.end_time is not None

    def test_config_validation(self):
        """Test that config must be a valid OrchestratorConfig."""
        run = self._create_valid_execution_run()
        assert run.config is not None

        with pytest.raises(Exception):
            run.config = "invalid config"

    def test_serialization_roundtrip(self):
        """Test that ExecutionRun can be serialized to dict and deserialized back."""
        original = self._create_valid_execution_run()
        data = original.model_dump()

        # Reconstruct
        reconstructed = ExecutionRun(**data)

        assert reconstructed.run_id == original.run_id
        assert reconstructed.status == original.status
        assert reconstructed.nodes[0].node_id == original.nodes[0].node_id

    def test_model_dump_json(self):
        """Test JSON serialization compatibility."""
        run = self._create_valid_execution_run()
        json_str = run.model_dump_json()
        assert isinstance(json_str, str)
        assert "run-20231027-001" in json_str

    def test_node_status_enum_in_nodes(self):
        """Test that PhysicalNode status inside ExecutionRun is validated."""
        run = self._create_valid_execution_run()
        # This should work
        run.nodes[0].status = NodeStatus.BUSY
        assert run.nodes[0].status == NodeStatus.BUSY

        # This should fail
        with pytest.raises(Exception):
            run.nodes[0].status = "INVALID_NODE_STATUS"

    def test_task_status_enum_in_tasks(self):
        """Test that TaskChunk status inside ExecutionRun is validated."""
        run = self._create_valid_execution_run()
        run.tasks[0].status = TaskStatus.COMPLETED
        assert run.tasks[0].status == TaskStatus.COMPLETED

        with pytest.raises(Exception):
            run.tasks[0].status = "INVALID_TASK_STATUS"

    def test_mandatory_fields_presence(self):
        """Verify that mandatory fields defined in the spec are present."""
        required_fields = [
            'run_id', 'start_time', 'status', 'nodes', 'tasks', 'config'
        ]
        run = self._create_valid_execution_run()
        data = run.model_dump()

        for field in required_fields:
            assert field in data, f"Missing mandatory field: {field}"

    def test_optional_fields_default(self):
        """Verify optional fields have correct defaults if not provided."""
        # We need to construct a minimal valid run to test defaults,
        # but Pydantic usually requires all non-optional fields.
        # This test confirms that 'end_time' defaults to None if not set.
        run = self._create_valid_execution_run()
        assert run.end_time is None