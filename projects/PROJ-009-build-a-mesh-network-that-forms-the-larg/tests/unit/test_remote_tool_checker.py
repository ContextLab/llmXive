"""
Unit tests for the RemoteToolChecker module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from orchestrator.remote_tool_checker import (
    RemoteToolChecker,
    ToolMissingError,
    ToolCheckResult,
    NodeToolCheckResult,
    create_tool_checker
)
from orchestrator.models import PhysicalNode, NodeStatus
from orchestrator.node_manager import NodeManager

@pytest.fixture
def mock_node_manager():
    manager = Mock(spec=NodeManager)
    manager.execute_remote_command = Mock()
    return manager

@pytest.fixture
def mock_node():
    return PhysicalNode(
        node_id="test-node-01",
        ip_address="192.168.1.100",
        status=NodeStatus.ACTIVE,
        username="root",
        password=""
    )

def test_tool_check_result_creation():
    """Test that ToolCheckResult is created correctly."""
    result = ToolCheckResult(tool_name="tcpdump", available=True, version_info="/usr/bin/tcpdump")
    assert result.tool_name == "tcpdump"
    assert result.available is True
    assert result.version_info == "/usr/bin/tcpdump"

def test_node_tool_check_result_creation(mock_node):
    """Test that NodeToolCheckResult is created correctly."""
    result = NodeToolCheckResult(node_ip="192.168.1.100", node_id="test-node-01")
    assert result.node_ip == "192.168.1.100"
    assert result.node_id == "test-node-01"
    assert result.is_available is True
    assert result.tools == []

def test_check_tool_on_node_success(mock_node_manager, mock_node):
    """Test checking a tool that exists."""
    mock_node_manager.execute_remote_command.return_value = (
        "/usr/bin/tcpdump\n", "", 0
    )

    checker = RemoteToolChecker(mock_node_manager)
    result = checker.check_tool_on_node(mock_node, "tcpdump")

    assert result.tool_name == "tcpdump"
    assert result.available is True
    assert result.version_info == "/usr/bin/tcpdump"

def test_check_tool_on_node_missing(mock_node_manager, mock_node):
    """Test checking a tool that does not exist."""
    mock_node_manager.execute_remote_command.return_value = ("", "which: no tcpdump in (/usr/bin:/bin)\n", 1)

    checker = RemoteToolChecker(mock_node_manager)
    result = checker.check_tool_on_node(mock_node, "tcpdump")

    assert result.tool_name == "tcpdump"
    assert result.available is False
    assert "no tcpdump" in result.error_message

def test_check_node_tools_all_present(mock_node_manager, mock_node):
    """Test checking all tools when they are present."""
    mock_node_manager.execute_remote_command.side_effect = [
        ("/usr/bin/tcpdump\n", "", 0),  # tcpdump
        ("/usr/bin/mpstat\n", "", 0)    # mpstat
    ]

    checker = RemoteToolChecker(mock_node_manager)
    result = checker.check_node_tools(mock_node)

    assert result.is_available is True
    assert len(result.tools) == 2
    assert all(t.available for t in result.tools)
    assert result.missing_critical_tools == []

def test_check_node_tools_missing_critical(mock_node_manager, mock_node):
    """Test checking tools when a critical one is missing."""
    # tcpdump exists, mpstat missing
    mock_node_manager.execute_remote_command.side_effect = [
        ("/usr/bin/tcpdump\n", "", 0),
        ("", "which: no mpstat in (/usr/bin:/bin)\n", 1)
    ]

    checker = RemoteToolChecker(mock_node_manager)
    result = checker.check_node_tools(mock_node)

    assert result.is_available is False
    assert "mpstat" in result.missing_critical_tools
    assert len(result.tools) == 2
    assert any(not t.available for t in result.tools)

def test_create_tool_checker_factory(mock_node_manager):
    """Test the factory function."""
    checker = create_tool_checker(mock_node_manager)
    assert isinstance(checker, RemoteToolChecker)
    assert checker.node_manager == mock_node_manager