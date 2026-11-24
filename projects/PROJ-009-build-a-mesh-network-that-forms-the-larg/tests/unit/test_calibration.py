"""
Unit tests for the calibration procedures.

The tests monkey‑patch ``subprocess.run`` to return deterministic output
for both ``iperf3`` and ``sysbench`` so that the calibration logic can be
exercised without requiring the real binaries to be present on the CI
runner.
"""

import json
from pathlib import Path

import pytest

from orchestrator.calibration import perform_calibration

# ----------------------------------------------------------------------
# Helper mock objects
# ----------------------------------------------------------------------
class MockCompletedProcess:
    def __init__(self, stdout: str):
        self.stdout = stdout
        self.stderr = ""
        self.returncode = 0

# Sample iperf3 JSON output (bits_per_second = 1 Gbps)
IPERF3_SAMPLE = json.dumps({
    "end": {
        "sum": {
            "bits_per_second": 1_000_000_000
        }
    }
})

# Sample sysbench output containing an ``events per second`` line
SYSBENCH_SAMPLE = """
sysbench 1.0.20 (using system LuaJIT 2.1.0)

Running the test with following options:
Number of threads: 1
Total time: 5 seconds

Number of events: 10000

Total time: 5.0000 seconds
events per second: 2000.00 (4000.00 per thread)
"""

# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------
def test_perform_calibration_writes_files(monkeypatch):
    """
    Verify that ``perform_calibration`` creates the two JSON files with
    the expected structure and values.
    """
    # Mock subprocess.run to return our canned outputs.
    def fake_run(cmd, stdout, stderr, text, check):
        if "iperf3" in cmd:
            return MockCompletedProcess(IPERF3_SAMPLE)
        if "sysbench" in cmd:
            return MockCompletedProcess(SYSBENCH_SAMPLE)
        raise RuntimeError("Unexpected command")

    monkeypatch.setattr("subprocess.run", fake_run)

    # Ensure a clean state – delete any previous artifacts.
    net_path = Path("data/raw/network_calibration.json")
    cpu_path = Path("data/raw/cpu_calibration.json")
    if net_path.is_file():
        net_path.unlink()
    if cpu_path.is_file():
        cpu_path.unlink()

    # Run calibration
    perform_calibration()

    # ------------------------------------------------------------------
    # Network calibration assertions
    # ------------------------------------------------------------------
    assert net_path.is_file(), "network_calibration.json was not created"
    net_data = json.loads(net_path.read_text(encoding="utf-8"))
    # Three runs, each 1 Gbps → average should also be 1 Gbps
    assert net_data["average_throughput_bps"] == 1_000_000_000
    assert len(net_data["runs_bps"]) == 3
    assert all(bps == 1_000_000_000 for bps in net_data["runs_bps"])

    # ------------------------------------------------------------------
    # CPU calibration assertions
    # ------------------------------------------------------------------
    assert cpu_path.is_file(), "cpu_calibration.json was not created"
    cpu_data = json.loads(cpu_path.read_text(encoding="utf-8"))
    # The sample reports 2000 EPS
    assert cpu_data["events_per_second"] == 2000.0
    # Conversion factor = EPS / 100 % CPU
    assert cpu_data["conversion_factor_eps_per_cpu_util_pct"] == 20.0

    # Clean up (optional – the temporary CI workspace is discarded anyway)
    net_path.unlink()
    cpu_path.unlink()