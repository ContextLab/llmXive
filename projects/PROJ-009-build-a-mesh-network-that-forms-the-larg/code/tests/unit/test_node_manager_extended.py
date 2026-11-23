"""
Extended unit tests for the NodeManager implementation (task T002).

These tests focus on the metadata collection path:
- Verification that required remote tools are checked.
- CPU profiling, radio metric (SNR & bandwidth) extraction.
- Thermal check (non‑fatal) and packet / CPU utilization parsing.
- Correct JSON file creation under ``data/raw/physical_node_<ip>.json``.
- Validation against the PhysicalNode JSON schema.
"""

import json
import os
import re
from pathlib import Path

import pytest
from unittest.mock import MagicMock, patch

from orchestrator.node_manager import (
    NodeManager,
    ToolMissingError,
    InstrumentationError,
    create_node_manager,
)
from llmxive_toolkit import paths

# Helper to build a deterministic fake iperf3 JSON output
def _fake_iperf3_output(bps: float = 1e9) -> str:
    return json.dumps({
        "end": {
            "sum_sent": {
                "bits_per_second": bps
            }
        }
    })

@pytest.fixture
def manager():
    # Use a short timeout to keep tests fast
    cfg = {"ssh_timeout": 2, "ssh_port": 22, "username": "test_user"}
    return create_node_manager(cfg)

def _setup_exec_mock(manager: NodeManager, ip: str):
    """
    Patch ``_exec_remote`` to return deterministic outputs for the
    sequence of commands used by ``collect_and_write_metadata``.
    """
    # Mapping of command substrings to fake outputs
    def exec_side_effect(target_ip, command, timeout=None):
        assert target_ip == ip, "Unexpected IP in exec_remote"

        # CPU profile via lscpu
        if command.startswith("lscpu"):
            return "Model,CPU_MHz\nIntel-Xeon,2400\n"
        # Fallback cpuinfo if lscpu fails – not exercised here
        if command.startswith("cat /proc/cpuinfo"):
            return "model name\t: Intel Xeon\ncpu MHz\t\t: 2400.000\n"
        # SNR via iwconfig
        if "iwconfig" in command:
            return "Signal level=-45 dBm  Noise level=-95 dBm"
        # SNR fallback via /proc/net/wireless
        if "cat /proc/net/wireless" in command:
            return "wlan0: 0000   70   0   0   0   0   0   0   0   0"
        # Bandwidth via iperf3
        if "iperf3" in command:
            return _fake_iperf3_output(bps=2e9)  # 2 Gbps → 2000 Mbps
        # mpstat for CPU utilization
        if "mpstat" in command:
            return (
                "Linux 5.15.0 (mock)  03/20/2024  _x86_64_  (4 CPU)\n"
                "03:45:12 PM     CPU     %usr     %nice      %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle\n"
                "03:45:13 PM     all     15.00      0.00      2.00      0.50      0.00      0.10      0.00      0.00      0.00    82.40\n"
            )
        # tcpdump packet capture
        if "tcpdump" in command:
            # Simulate exactly the requested number of packet lines
            m = re.search(r"-c (\d+)", command)
            count = int(m.group(1)) if m else 5
            return "\n".join([f"packet {i}" for i in range(count)]) + "\n"
        # Thermal check – return a safe temperature
        if "cat /sys/class/thermal/thermal_zone0/temp" in command:
            return "45000\n"  # 45 °C
        # Any other command – empty output
        return ""

    manager._exec_remote = MagicMock(side_effect=exec_side_effect)

def test_verify_remote_tools_success(manager):
    ip = "192.168.1.10"
    # Patch exec to simulate ``which`` returning a path
    manager._exec_remote = MagicMock(return_value="/usr/bin/iperf3\n")
    # Should not raise
    manager.verify_remote_tools(ip, ["iperf3", "tcpdump", "mpstat"])

def test_verify_remote_tools_missing(manager):
    ip = "192.168.1.10"
    # ``which`` returns empty string → missing tool
    manager._exec_remote = MagicMock(return_value="\n")
    with pytest.raises(ToolMissingError) as exc:
        manager.verify_remote_tools(ip, ["nonexistenttool"])
    assert exc.value.tool == "nonexistenttool"
    assert exc.value.ip == ip

def test_collect_and_write_metadata_success(manager, tmp_path, monkeypatch):
    """
    End‑to‑end test of ``collect_and_write_metadata``.
    It checks that:
    - All required fields are present in the written JSON.
    - The JSON validates against the PhysicalNode schema.
    - The file is written under ``data/raw/`` with the correct naming convention.
    """
    ip = "192.168.1.42"
    _setup_exec_mock(manager, ip)

    # Ensure the data directory is inside a temporary location to avoid polluting the repo
    # Monkey‑patch the paths.data function to point inside the tmp_path.
    def fake_data(*parts):
        p = Path(tmp_path, *parts)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p
    monkeypatch.setattr(paths, "data", fake_data)

    # Run the collection
    out_path = manager.collect_and_write_metadata(ip)

    # Verify the file location and name
    expected_name = f"physical_node_{ip.replace('.', '_')}.json"
    assert out_path.name == expected_name
    assert out_path.parent == Path(tmp_path, "raw")

    # Load and inspect JSON contents
    with out_path.open() as f:
        data = json.load(f)

    # Required fields from the schema
    required_fields = {
        "ip_address",
        "hardware_spec",
        "baseline_bandwidth_Mbps",
        "baseline_snr_db",
        "current_latency",
        "packet_loss_rate",
        "cpu_utilization",
    }
    assert required_fields.issubset(data.keys())

    # Check that values are of expected types / ranges
    assert isinstance(data["ip_address"], str) and data["ip_address"] == ip
    assert isinstance(data["hardware_spec"], str) and "Intel-Xeon" in data["hardware_spec"]
    assert data["baseline_bandwidth_Mbps"] == pytest.approx(2000.0)  # 2 Gbps → 2000 Mbps
    assert data["baseline_snr_db"] == pytest.approx(50.0)  # -45 - (-95)
    assert data["cpu_utilization"] == pytest.approx(17.6)   # 100 - 82.4 idle

    # ``current_latency`` and ``packet_loss_rate`` are placeholders (0.0)
    assert data["current_latency"] == 0.0
    assert data["packet_loss_rate"] == 0.0

    # Schema validation is performed inside ``collect_and_write_metadata``.
    # If we reach this point without an exception, validation succeeded.

def test_collect_and_write_metadata_schema_failure(manager, tmp_path, monkeypatch):
    """
    Force a schema validation failure by returning an invalid value
    (negative bandwidth). The method should raise ``InstrumentationError``.
    """
    ip = "192.168.1.99"

    # Mock exec to return a negative bandwidth value via iperf3 JSON.
    def exec_side_effect(target_ip, command, timeout=None):
        if "lscpu" in command:
            return "Model,CPU_MHz\nIntel-Xeon,2400\n"
        if "iwconfig" in command:
            return "Signal level=-45 dBm  Noise level=-95 dBm"
        if "iperf3" in command:
            # Negative bits_per_second to break the schema (minimum 0)
            return json.dumps({"end": {"sum_sent": {"bits_per_second": -1}}})
        if "mpstat" in command:
            return (
                "Linux 5.15.0 (mock)  03/20/2024  _x86_64_  (4 CPU)\n"
                "03:45:12 PM     CPU     %usr     %nice      %sys %iowait    %irq   %soft  %steal  %guest  %gnice   %idle\n"
                "03:45:13 PM     all     15.00      0.00      2.00      0.50      0.00      0.10      0.00      0.00      0.00    82.40\n"
            )
        if "tcpdump" in command:
            return "\n".join(["packet"] * 5) + "\n"
        if "cat /sys/class/thermal/thermal_zone0/temp" in command:
            return "45000\n"
        return ""

    manager._exec_remote = MagicMock(side_effect=exec_side_effect)

    # Redirect data writes to a temporary directory
    def fake_data(*parts):
        p = Path(tmp_path, *parts)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p
    monkeypatch.setattr(paths, "data", fake_data)

    with pytest.raises(InstrumentationError) as exc:
        manager.collect_and_write_metadata(ip)

    # The error message should mention schema validation
    assert "Schema validation failed" in str(exc.value)