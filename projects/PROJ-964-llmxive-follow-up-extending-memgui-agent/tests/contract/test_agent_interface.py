"""
Contract tests for agent interface compliance.

Ensures that all agents implement the required RunnerProtocol interface.
"""
import pytest
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

# Import the ExecutionLog data model used by the protocol
from utils.execution_log import ExecutionLog, TrajectoryExecutionLog

class RunnerProtocol(ABC):
    """
    Contract interface for agent execution runners.
    
    All agents (baseline, recall-enhanced) must implement this interface
    to ensure consistent execution and logging behavior.
    """
    
    @abstractmethod
    def run_trajectory(self, trajectory: Dict[str, Any]) -> TrajectoryExecutionLog:
        """
        Run a single trajectory and return execution logs.
        
        Args:
            trajectory: A dictionary containing the trajectory data
                       (steps, states, actions, dependencies).
        
        Returns:
            TrajectoryExecutionLog: Structured log of the execution,
                                   including success/failure, steps taken,
                                   and any errors encountered.
        """
        pass
    
    @abstractmethod
    def get_logs(self) -> List[TrajectoryExecutionLog]:
        """
        Return all execution logs from the current run.
        
        Returns:
            List[TrajectoryExecutionLog]: List of logs for all trajectories
                                         processed by this runner instance.
        """
        pass

class MockAgent:
    """
    Mock agent implementation for testing interface compliance.
    Used to verify that the protocol definition is correct without
    requiring a real model or hardware.
    """
    
    def __init__(self):
        self._logs: List[TrajectoryExecutionLog] = []
    
    def run_trajectory(self, trajectory: Dict[str, Any]) -> TrajectoryExecutionLog:
        """Simulate running a trajectory and return a mock log."""
        # Create a minimal valid log entry
        log_entry = TrajectoryExecutionLog(
            trajectory_id=trajectory.get("id", "mock_001"),
            status="success",
            steps_executed=len(trajectory.get("steps", [])),
            latency_ms=10.0,
            memory_peak_mb=50.0,
            error_message=None
        )
        self._logs.append(log_entry)
        return log_entry
    
    def get_logs(self) -> List[TrajectoryExecutionLog]:
        """Return the accumulated logs."""
        return self._logs

class NonCompliantAgent:
    """
    Agent that deliberately fails to implement the interface correctly.
    Used to test that the contract tests catch missing methods.
    """
    
    def run_trajectory(self, trajectory):
        # Missing return type and proper log structure
        return {"status": "incomplete"}
    
    # Missing get_logs method entirely

def test_agent_implements_interface():
    """
    Verify that agents implement the required interface methods.
    
    This test ensures that any agent class intended for use in the pipeline
    has the necessary `run_trajectory` and `get_logs` methods.
    """
    agent = MockAgent()
    
    # Check for method existence
    assert hasattr(agent, 'run_trajectory'), "Agent must have run_trajectory method"
    assert hasattr(agent, 'get_logs'), "Agent must have get_logs method"
    
    # Check that methods are callable
    assert callable(agent.run_trajectory), "run_trajectory must be callable"
    assert callable(agent.get_logs), "get_logs must be callable"
    
    # Check return types (basic structural check)
    result = agent.run_trajectory({"id": "test", "steps": [1, 2, 3]})
    assert isinstance(result, TrajectoryExecutionLog), "run_trajectory must return TrajectoryExecutionLog"
    
    logs = agent.get_logs()
    assert isinstance(logs, list), "get_logs must return a list"
    assert len(logs) > 0, "get_logs must return non-empty list after run"
    assert all(isinstance(log, TrajectoryExecutionLog) for log in logs), "All logs must be TrajectoryExecutionLog instances"

def test_protocol_compliance():
    """
    Verify that the protocol class defines required methods correctly.
    
    This test ensures the abstract base class is properly defined
    with the correct signatures.
    """
    # Check that the protocol has the required abstract methods
    assert hasattr(RunnerProtocol, 'run_trajectory'), "RunnerProtocol must define run_trajectory"
    assert hasattr(RunnerProtocol, 'get_logs'), "RunnerProtocol must define get_logs"
    
    # Check that they are abstract methods
    import inspect
    assert RunnerProtocol.run_trajectory in RunnerProtocol.__abstractmethods__, "run_trajectory must be abstract"
    assert RunnerProtocol.get_logs in RunnerProtocol.__abstractmethods__, "get_logs must be abstract"
    
    # Verify method signatures using inspect
    sig_run = inspect.signature(RunnerProtocol.run_trajectory)
    sig_get = inspect.signature(RunnerProtocol.get_logs)
    
    # run_trajectory should accept self and trajectory
    assert len(sig_run.parameters) == 2, "run_trajectory should have 2 parameters (self, trajectory)"
    assert 'trajectory' in sig_run.parameters, "run_trajectory must accept trajectory parameter"
    
    # get_logs should accept only self
    assert len(sig_get.parameters) == 1, "get_logs should have 1 parameter (self)"

def test_mock_agent_compliance():
    """
    Test that the MockAgent fully complies with the RunnerProtocol.
    
    This ensures our mock can be used interchangeably with real agents
    in contract testing scenarios.
    """
    agent = MockAgent()
    
    # Try to instantiate the protocol with the mock (should fail if not compliant)
    # Note: We can't directly instantiate an ABC, but we can check if it satisfies the interface
    try:
        # This would fail at runtime if the agent didn't implement the protocol
        # We simulate this by checking if the methods exist and return correct types
        trajectory = {
            "id": "contract_test_001",
            "steps": [
                {"step": 1, "action": "click", "target": "button1"},
                {"step": 2, "action": "type", "text": "hello"}
            ],
            "dependencies": []
        }
        
        log = agent.run_trajectory(trajectory)
        
        # Verify the log contains expected fields
        assert log.trajectory_id == "contract_test_001"
        assert log.status in ["success", "failure", "error"]
        assert log.steps_executed == 2
        assert log.latency_ms >= 0
        assert log.memory_peak_mb >= 0
        
        # Verify get_logs returns the log we just created
        logs = agent.get_logs()
        assert len(logs) == 1
        assert logs[0].trajectory_id == "contract_test_001"
        
    except Exception as e:
        pytest.fail(f"MockAgent failed contract test: {str(e)}")

def test_non_compliant_agent_fails():
    """
    Verify that agents not implementing the interface are caught.
    
    This test ensures our contract testing would fail for non-compliant agents.
    """
    agent = NonCompliantAgent()
    
    # Should have run_trajectory
    assert hasattr(agent, 'run_trajectory')
    
    # Should NOT have get_logs (this is the failure case)
    assert not hasattr(agent, 'get_logs'), "NonCompliantAgent should not have get_logs"
    
    # Running this would cause an AttributeError in real usage
    with pytest.raises(AttributeError):
        agent.get_logs()