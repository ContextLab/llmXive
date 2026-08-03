"""
Unit tests for RemoteInstrumentor.

These tests verify the instrumentation logic without requiring
actual SSH connections to remote nodes.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from orchestrator.instrumentor_remote import RemoteInstrumentor, create_instrumentor
from orchestrator.models import PhysicalNode, NodeStatus
from orchestrator.node_manager import NodeManager


class TestRemoteInstrumentor:
    """Test suite for RemoteInstrumentor class."""

    @pytest.fixture
    def mock_node_manager(self):
        """Create a mock NodeManager for testing."""
        manager = Mock(spec=NodeManager)
        return manager

    @pytest.fixture
    def mock_node(self):
        """Create a mock PhysicalNode for testing."""
        node = PhysicalNode(
            node_id="test-node-001",
            hostname="192.168.1.100",
            username="testuser",
            status=NodeStatus.ONLINE,
            cpu_cores=4,
            memory_gb=8,
            network_interface="eth0"
        )
        return node

    @pytest.fixture
    def instrumentor(self, mock_node_manager):
        """Create a RemoteInstrumentor with a mock NodeManager."""
        return RemoteInstrumentor(mock_node_manager)

    def test_init(self, mock_node_manager):
        """Test initialization of RemoteInstrumentor."""
        instrumentor = RemoteInstrumentor(mock_node_manager)
        assert instrumentor.node_manager == mock_node_manager
        assert instrumentor.logger is not None

    def test_create_instrumentor_factory(self, mock_node_manager):
        """Test factory function for creating instrumentor."""
        instrumentor = create_instrumentor(mock_node_manager)
        assert isinstance(instrumentor, RemoteInstrumentor)
        assert instrumentor.node_manager == mock_node_manager

    @patch('re.search')
    def test_execute_tcpdump_success(self, mock_search, instrumentor, mock_node):
        """Test successful tcpdump execution."""
        # Mock the result
        mock_result = Mock()
        mock_result.exit_code = 0
        mock_result.stdout = "12345 packets captured\n12345 packets received by filter"
        mock_result.stderr = ""
        
        instrumentor.node_manager.execute_command.return_value = mock_result
        mock_search.return_value = Mock(group=lambda x: "12345" if x == 1 else None)
        
        result = instrumentor.execute_tcpdump(mock_node, duration=10)
        
        assert result["success"] is True
        assert result["packet_count"] == 12345
        assert result["node_id"] == "test-node-001"
        assert result["interface"] == "eth0"
        assert "timestamp" in result

    def test_execute_tcpdump_permission_error(self, instrumentor, mock_node):
        """Test tcpdump execution with permission error."""
        # Mock the result with permission error
        mock_result = Mock()
        mock_result.exit_code = 1
        mock_result.stdout = ""
        mock_result.stderr = "tcpdump: can't create raw socket: Permission denied"
        
        instrumentor.node_manager.execute_command.side_effect = [
            mock_result,  # First attempt fails
            Mock(exit_code=0, stdout="100 packets captured\n", stderr="")  # Retry succeeds
        ]
        
        result = instrumentor.execute_tcpdump(mock_node, duration=10)
        
        # Should succeed after retry
        assert result["success"] is True
        assert instrumentor.node_manager.execute_command.call_count == 2

    def test_execute_tcpdump_failure(self, instrumentor, mock_node):
        """Test tcpdump execution that fails completely."""
        mock_result = Mock()
        mock_result.exit_code = 1
        mock_result.stdout = ""
        mock_result.stderr = "tcpdump: interface eth0 does not exist"
        
        instrumentor.node_manager.execute_command.return_value = mock_result
        
        result = instrumentor.execute_tcpdump(mock_node, duration=10)
        
        assert result["success"] is False
        assert "error" in result

    @patch('re.search')
    def test_execute_mpstat_success(self, mock_search, instrumentor, mock_node):
        """Test successful mpstat execution."""
        # Mock the result
        mock_result = Mock()
        mock_result.exit_code = 0
        mock_result.stdout = """
        Linux 5.4.0-42-generic (test-node) 	09/15/2023 	_x86_64_	(4 CPU)

        12:34:56  CPU    %usr   %nice    %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle
        12:34:57  all    1.00    0.00    0.50    0.00    0.00    0.00    0.00    0.00    0.00   98.50
        12:34:58  all    2.00    0.00    1.00    0.00    0.00    0.00    0.00    0.00    0.00   97.00
        Average:  all    1.50    0.00    0.75    0.00    0.00    0.00    0.00    0.00    0.00   97.75
        """
        instrumentor.node_manager.execute_command.return_value = mock_result
        
        result = instrumentor.execute_mpstat(mock_node, interval=1.0, count=2)
        
        assert result["success"] is True
        assert result["cpu_utilization_pct"] > 0  # Should be around 2.25%
        assert len(result["samples"]) == 2
        assert result["node_id"] == "test-node-001"

    def test_execute_mpstat_failure(self, instrumentor, mock_node):
        """Test mpstat execution that fails."""
        mock_result = Mock()
        mock_result.exit_code = 1
        mock_result.stdout = ""
        mock_result.stderr = "mpstat: command not found"
        
        instrumentor.node_manager.execute_command.return_value = mock_result
        
        result = instrumentor.execute_mpstat(mock_node)
        
        assert result["success"] is False
        assert "error" in result

    @patch('re.search')
    def test_check_network_saturation_normal(self, mock_search, instrumentor, mock_node):
        """Test network saturation check with normal conditions."""
        mock_result = Mock()
        mock_result.exit_code = 0
        mock_result.stdout = "100 packets transmitted, 100 received, 0% packet loss"
        mock_search.return_value = Mock(group=lambda x: "0" if x == 1 else None)
        
        instrumentor.node_manager.execute_command.return_value = mock_result
        
        result = instrumentor.check_network_saturation(mock_node, duration=10, threshold=0.20)
        
        assert result["success"] is True
        assert result["packet_loss_rate"] == 0.0
        assert result["saturated"] is False

    @patch('re.search')
    def test_check_network_saturation_high_loss(self, mock_search, instrumentor, mock_node):
        """Test network saturation check with high packet loss."""
        mock_result = Mock()
        mock_result.exit_code = 0
        mock_result.stdout = "100 packets transmitted, 80 received, 20% packet loss"
        mock_search.return_value = Mock(group=lambda x: "20" if x == 1 else None)
        
        instrumentor.node_manager.execute_command.return_value = mock_result
        
        result = instrumentor.check_network_saturation(mock_node, duration=10, threshold=0.15)
        
        assert result["success"] is True
        assert result["packet_loss_rate"] == 0.20
        assert result["saturated"] is True

    def test_capture_unmodeled_vars_success(self, instrumentor, mock_node):
        """Test capturing unmodeled variables."""
        # Mock thermal result
        thermal_result = Mock()
        thermal_result.exit_code = 0
        thermal_result.stdout = "45000"  # 45.0 C
        
        # Mock load result
        load_result = Mock()
        load_result.exit_code = 0
        load_result.stdout = " 12:34:56 up 10 days,  1:23,  2 users,  load average: 0.50, 0.40, 0.30"
        
        # Mock interrupt result
        interrupt_result = Mock()
        interrupt_result.exit_code = 0
        interrupt_result.stdout = "intr 12345678"
        
        instrumentor.node_manager.execute_command.side_effect = [
            thermal_result,
            load_result,
            interrupt_result
        ]
        
        result = instrumentor.capture_unmodeled_vars(mock_node)
        
        assert result["success"] is True
        assert "temperature_celsius" in result["os_noise_metrics"]
        assert result["os_noise_metrics"]["temperature_celsius"] == 45.0
        assert result["thermal_throttling"] is False  # Below 80C threshold

    def test_capture_unmodeled_vars_thermal_throttling(self, instrumentor, mock_node):
        """Test capturing unmodeled variables with thermal throttling."""
        # Mock thermal result with high temperature
        thermal_result = Mock()
        thermal_result.exit_code = 0
        thermal_result.stdout = "85000"  # 85.0 C
        
        instrumentor.node_manager.execute_command.return_value = thermal_result
        
        result = instrumentor.capture_unmodeled_vars(mock_node)
        
        assert result["success"] is True
        assert result["thermal_throttling"] is True

    def test_instrument_node_full_cycle(self, instrumentor, mock_node):
        """Test full instrumentation cycle."""
        # Mock all command results
        tcpdump_result = Mock(exit_code=0, stdout="100 packets captured\n", stderr="")
        mpstat_result = Mock(exit_code=0, stdout="12:34:56  all    1.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00    0.00   99.00\n", stderr="")
        thermal_result = Mock(exit_code=0, stdout="45000", stderr="")
        load_result = Mock(exit_code=0, stdout="load average: 0.50, 0.40, 0.30", stderr="")
        interrupt_result = Mock(exit_code=0, stdout="intr 12345678", stderr="")
        ping_result = Mock(exit_code=0, stdout="100 packets transmitted, 100 received, 0% packet loss", stderr="")
        
        instrumentor.node_manager.execute_command.side_effect = [
            tcpdump_result,   # tcpdump
            mpstat_result,    # mpstat
            thermal_result,   # thermal
            load_result,      # load
            interrupt_result, # interrupt
            ping_result       # ping for saturation
        ]
        
        result = instrumentor.instrument_node(mock_node, capture_duration=10)
        
        assert result["node_id"] == "test-node-001"
        assert "tcpdump" in result
        assert "mpstat" in result
        assert "unmodeled_vars" in result
        assert "network_saturation" in result
        assert "timestamp" in result