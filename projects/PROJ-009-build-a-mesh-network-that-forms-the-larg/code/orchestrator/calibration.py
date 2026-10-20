"""
Calibration utilities for the mesh‑network orchestrator.

This module provides two calibration steps required before any sweep
execution:

1. **Network calibration** – runs ``iperf3`` between ``localhost`` three
   times, parses the JSON output, and stores the average throughput
   (bits per second) together with the per‑run values.

2. **CPU calibration** – runs ``sysbench cpu`` (single‑thread) once,
   parses the ``events per second`` value (a proxy for CPU work rate),
   and stores the result.

Both calibration results are written to ``data/raw/network_calibration.json``
and ``data/raw/cpu_calibration.json`` respectively.  The functions raise
on any error (missing binary, non‑zero return code, or unexpected output)
so that the CLI fails loudly if real measurements cannot be obtained.
"""

import json
import subprocess
import time
from pathlib import Path
from typing import List, Dict

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _run_subprocess(cmd: List[str]) -> subprocess.CompletedProcess:
    """
    Execute *cmd* and return the completed process.

    ``check=True`` ensures a non‑zero exit status raises a ``CalledProcessError``.
    """
    log.debug("Running command: %s", " ".join(cmd))
    return subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )

# ----------------------------------------------------------------------
# Network calibration
# ----------------------------------------------------------------------
def _run_iperf3_once() -> float:
    """
    Run a single ``iperf3`` client against ``localhost`` and return the
    measured bits‑per‑second value.

    The command uses the ``-J`` flag to produce JSON output, which makes
    parsing reliable across iperf3 versions.
    """
    # ``-t 1`` limits the test to 1 second – sufficient for a quick
    # measurement on the CI runner.
    result = _run_subprocess(["iperf3", "-c", "127.0.0.1", "-t", "1", "-J"])
    data = json.loads(result.stdout)

    # The JSON schema (iperf3 3.x) stores the aggregate throughput under:
    #   data["end"]["sum"]["bits_per_second"]
    try:
        bps = float(data["end"]["sum"]["bits_per_second"])
        log.debug("iperf3 measured throughput: %.2f bps", bps)
        return bps
    except (KeyError, TypeError) as exc:
        raise RuntimeError(f"Unexpected iperf3 JSON structure: {exc}") from exc

def calibrate_network() -> Dict[str, any]:
    """
    Perform three iperf3 runs, compute the average throughput and write the
    calibration file.

    Returns the calibration dictionary (also written to disk).
    """
    throughputs: List[float] = []
    for i in range(3):
        bps = _run_iperf3_once()
        throughputs.append(bps)
        # Small pause to avoid hammering the loopback interface.
        time.sleep(0.2)

    avg_bps = sum(throughputs) / len(throughputs)

    calibration = {
        "runs_bps": throughputs,
        "average_throughput_bps": avg_bps,
    }

    out_path = paths.data("raw", "network_calibration.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(calibration, indent=2), encoding="utf-8")
    log.info("Network calibration written to %s", out_path)

    return calibration

# ----------------------------------------------------------------------
# CPU calibration
# ----------------------------------------------------------------------
def _run_sysbench_cpu_once() -> float:
    """
    Execute ``sysbench cpu`` (single‑thread) and return the ``events per
    second`` metric, which represents how many CPU‑bound operations were
    performed per second.

    The output is plain text; we extract the line starting with
    ``events per second:``.
    """
    # ``--time=5`` limits the benchmark to 5 seconds – enough for a stable
    # measurement while staying well within CI limits.
    result = _run_subprocess(
        ["sysbench", "cpu", "--threads=1", "--time=5", "run"]
    )
    for line in result.stdout.splitlines():
        if "events per second:" in line:
            # Example line: "events per second:  1234.56 (250.00 per thread)"
            parts = line.split(":")
            if len(parts) >= 2:
                try:
                    eps = float(parts[1].strip().split()[0])
                    log.debug("sysbench measured EPS: %.2f", eps)
                    return eps
                except ValueError:
                    continue
    raise RuntimeError("Could not parse sysbench output for events per second")

def calibrate_cpu() -> Dict[str, any]:
    """
    Run a single sysbench CPU benchmark, store the measured operations per
    second and write the calibration file.

    Returns the calibration dictionary (also written to disk).
    """
    eps = _run_sysbench_cpu_once()
    # Derive a simple linear conversion factor: we assume 100 % CPU utilisation
    # corresponds to the measured EPS.  The factor therefore converts a
    # ``mpstat`` %util value into an estimated EPS.
    conversion_factor = eps / 100.0

    calibration = {
        "events_per_second": eps,
        "conversion_factor_eps_per_cpu_util_pct": conversion_factor,
    }

    out_path = paths.data("raw", "cpu_calibration.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(calibration, indent=2), encoding="utf-8")
    log.info("CPU calibration written to %s", out_path)

    return calibration

# ----------------------------------------------------------------------
# Public entry point
# ----------------------------------------------------------------------
def perform_calibration() -> None:
    """
    Execute both network and CPU calibration steps.

    Any exception propagates to the caller – the CLI treats this as a
    failure and exits with a non‑zero status, satisfying the requirement
    that missing or invalid calibration aborts downstream pipelines.
    """
    log.info("Starting calibration procedures")
    calibrate_network()
    calibrate_cpu()
    log.info("Calibration completed successfully")
