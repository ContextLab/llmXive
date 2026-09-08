"""
Contract tests for agent interface compliance.

Ensures that all agents implement the required RunnerProtocol interface.
"""
import pytest
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

# Placeholder for RunnerProtocol definition which will be implemented in T022b
class RunnerProtocol(ABC):
    @abstractmethod
    def run_trajectory(self, trajectory: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single trajectory and return execution logs."""
        pass
    
    @abstractmethod
    def get_logs(self) -> List[Dict[str, Any]]:
        """Return all execution logs from the current run."""
        pass

class MockAgent:
    """Mock agent to test interface compliance."""
    def run_trajectory(self, trajectory):
        return {"status": "mock"}
    
    def get_logs(self):
        return []

def test_agent_implements_interface():
    """Verify that agents implement the required interface methods."""
    agent = MockAgent()
    assert hasattr(agent, 'run_trajectory')
    assert hasattr(agent, 'get_logs')
    assert callable(agent.run_trajectory)
    assert callable(agent.get_logs)

def test_protocol_compliance():
    """Verify that the protocol class defines required methods."""
    assert hasattr(RunnerProtocol, 'run_trajectory')
    assert hasattr(RunnerProtocol, 'get_logs')
