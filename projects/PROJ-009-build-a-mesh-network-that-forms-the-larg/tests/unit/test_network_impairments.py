import unittest
from unittest.mock import MagicMock, patch
from orchestrator.network_impairments import (
    NetworkImpairments,
    ImpairmentConfig,
    ImpairmentResult
)
from orchestrator.node_manager import NodeManager, SSHConnection


class TestNetworkImpairments(unittest.TestCase):

    def setUp(self):
        self.mock_node_manager = MagicMock(spec=NodeManager)
        self.impairments = NetworkImpairments(self.mock_node_manager)

    def test_build_tc_netem_command_latency_only(self):
        config = ImpairmentConfig(latency_ms=100)
        cmd = self.impairments._build_tc_netem_command("eth0", config)
        expected = "tc qdisc add dev eth0 root netem delay 100ms"
        self.assertEqual(cmd, expected)

    def test_build_tc_netem_command_latency_jitter(self):
        config = ImpairmentConfig(latency_ms=100, jitter_ms=10)
        cmd = self.impairments._build_tc_netem_command("eth0", config)
        expected = "tc qdisc add dev eth0 root netem delay 100ms 10ms"
        self.assertEqual(cmd, expected)

    def test_build_tc_netem_command_loss(self):
        config = ImpairmentConfig(packet_loss_pct=1.5)
        cmd = self.impairments._build_tc_netem_command("eth0", config)
        expected = "tc qdisc add dev eth0 root netem loss 1.5%"
        self.assertEqual(cmd, expected)

    def test_build_tc_netem_command_bandwidth(self):
        config = ImpairmentConfig(bandwidth_mbps=10)
        cmd = self.impairments._build_tc_netem_command("eth0", config)
        expected = "tc qdisc add dev eth0 root netem rate 10mbit"
        self.assertEqual(cmd, expected)

    def test_build_tc_netem_command_combined(self):
        config = ImpairmentConfig(
            latency_ms=100,
            jitter_ms=10,
            packet_loss_pct=1.5,
            bandwidth_mbps=10
        )
        cmd = self.impairments._build_tc_netem_command("eth0", config)
        # Order might vary slightly depending on implementation, but all parts must be present
        self.assertIn("delay 100ms 10ms", cmd)
        self.assertIn("loss 1.5%", cmd)
        self.assertIn("rate 10mbit", cmd)

    def test_build_tc_netem_command_clear(self):
        config = None
        cmd = self.impairments._build_tc_netem_command("eth0", config)
        expected = "tc qdisc del dev eth0 root 2>/dev/null || true"
        self.assertEqual(cmd, expected)

    @patch.object(SSHConnection, 'exec_command')
    def test_inject_impairment_success(self, mock_exec):
        mock_conn = MagicMock(spec=SSHConnection)
        mock_conn.is_connected.return_value = True
        mock_exec.return_value = ("", "", 0)  # stdout, stderr, exit_code
        self.mock_node_manager.get_connection.return_value = mock_conn

        config = ImpairmentConfig(latency_ms=100)
        result = self.impairments.inject_impairment("node-1", config)

        self.assertTrue(result.success)
        self.assertEqual(result.node_id, "node-1")
        mock_exec.assert_called_once_with("sudo tc qdisc add dev eth0 root netem delay 100ms")

    @patch.object(SSHConnection, 'exec_command')
    def test_inject_impairment_failure(self, mock_exec):
        mock_conn = MagicMock(spec=SSHConnection)
        mock_conn.is_connected.return_value = True
        mock_exec.return_value = ("", "Permission denied", 1)
        self.mock_node_manager.get_connection.return_value = mock_conn

        config = ImpairmentConfig(latency_ms=100)
        result = self.impairments.inject_impairment("node-1", config)

        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "Permission denied")

    def test_inject_impairment_no_connection(self):
        self.mock_node_manager.get_connection.return_value = None

        config = ImpairmentConfig(latency_ms=100)
        result = self.impairments.inject_impairment("node-1", config)

        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "SSH connection not available")

    def test_clear_impairments(self):
        mock_conn = MagicMock(spec=SSHConnection)
        mock_conn.is_connected.return_value = True
        mock_conn.exec_command.return_value = ("", "", 0)
        self.mock_node_manager.get_connection.return_value = mock_conn

        result = self.impairments.clear_impairments("node-1")

        self.assertTrue(result.success)
        mock_conn.exec_command.assert_called_with(
            "sudo tc qdisc del dev eth0 root 2>/dev/null || true"
        )

    def test_apply_impairments_to_nodes(self):
        mock_conn = MagicMock(spec=SSHConnection)
        mock_conn.is_connected.return_value = True
        mock_conn.exec_command.return_value = ("", "", 0)
        self.mock_node_manager.get_connection.return_value = mock_conn

        config = ImpairmentConfig(latency_ms=50)
        results = self.impairments.apply_impairments_to_nodes(
            ["node-1", "node-2"], config
        )

        self.assertEqual(len(results), 2)
        self.assertTrue(all(r.success for r in results))
        self.assertEqual(self.mock_node_manager.get_connection.call_count, 2)


if __name__ == "__main__":
    unittest.main()