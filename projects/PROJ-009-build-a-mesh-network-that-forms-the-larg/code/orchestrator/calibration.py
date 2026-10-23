"""
Calibration utilities for the mesh‑network orchestrator.

This module provides two calibration steps required before any sweep
execution:

1. **Network calibration** – measures the relationship between packet count
   and throughput (Mbps) on the local loop‑back interface.  The implementation
   avoids external dependencies (e.g. ``iperf3``) and instead uses a plain
   Python ``socket`` to send a known number of UDP packets to ``localhost``.
   Three different packet‑count levels are measured, a linear regression is
   fitted, and the slope (``packet_to_mbps_factor``) together with the
   coefficient of determination (``r_squared``) are written to
   ``data/raw/network_calibration.json``.

2. **CPU calibration** – measures the relationship between CPU utilisation
   (percent) and the number of operations per second.  The implementation
   performs a simple, CPU‑bound loop for three different operation counts,
   measures the elapsed wall‑clock time, computes operations‑per‑second,
   derives a synthetic utilisation percentage (relative to the maximum
   observed ops/s), fits a linear regression, and writes the slope
   (``percent_to_ops_factor``) and ``r_squared`` to
   ``data/raw/cpu_calibration.json``.

Both calibration steps raise on unexpected errors so that downstream
pipelines abort loudly if a real measurement cannot be obtained.
"""

import json
import socket
import time
from pathlib import Path
from typing import List, Dict

import numpy as np

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _run_udp_burst(packet_count: int, packet_size: int = 1500) -> float:
    """
    Send ``packet_count`` UDP packets of ``packet_size`` bytes to the
    local loop‑back interface and return the measured throughput in
    **bits per second**.

    The function creates a UDP socket bound to ``127.0.0.1`` and measures
    the elapsed time required to ``sendto`` all packets.  The throughput
    is calculated as ``(total_bytes * 8) / elapsed_seconds``.

    Args:
        packet_count: Number of packets to send.
        packet_size: Size of each packet in bytes (default 1500, a typical
                     Ethernet MTU).

    Returns:
        Throughput in bits per second (float).
    """
    log.debug("Running UDP burst: %d packets of %d bytes", packet_count, packet_size)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        payload = b"x" * packet_size
        start = time.perf_counter()
        for _ in range(packet_count):
            # ``sendto`` is non‑blocking for localhost; any error will raise.
            sock.sendto(payload, ("127.0.0.1", 9999))
        end = time.perf_counter()
    finally:
        sock.close()
    elapsed = max(end - start, 1e-9)  # avoid division by zero
    bits_sent = packet_count * packet_size * 8
    bps = bits_sent / elapsed
    log.debug("UDP burst completed in %.6f s → %.2f bps", elapsed, bps)
    return bps

def _fit_linear(x: np.ndarray, y: np.ndarray) -> Dict[str, float]:
    """
    Fit a simple linear model ``y = a * x + b`` and compute the
    coefficient of determination (R²).

    Args:
        x: Independent variable values.
        y: Dependent variable values.

    Returns:
        Dictionary with keys ``slope``, ``intercept``, and ``r_squared``.
    """
    if x.size != y.size or x.size < 2:
        raise ValueError("Need at least two data points for linear fit")
    # ``np.polyfit`` returns coefficients [a, b] for degree‑1 fit.
    a, b = np.polyfit(x, y, deg=1)
    y_pred = a * x + b
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - ss_res / ss_tot if ss_tot != 0 else 0.0
    log.debug(
        "Linear fit results – slope: %.6f, intercept: %.6f, R²: %.6f",
        a,
        b,
        r_squared,
    )
    return {"slope": a, "intercept": b, "r_squared": r_squared}

# ----------------------------------------------------------------------
# Network calibration
# ----------------------------------------------------------------------
def calibrate_network() -> Dict[str, any]:
    """
    Perform three UDP‑burst measurements with increasing packet counts,
    fit a linear model between *packet count* and *throughput in Mbps*,
    and write the calibration file.

    Returns:
        Calibration dictionary (also written to disk) with keys:
            - ``packet_to_mbps_factor``: slope of the linear model
              (Mbps per packet).
            - ``r_squared``: coefficient of determination of the fit.
    """
    packet_counts = np.array([1_000, 2_000, 3_000], dtype=float)
    throughputs_bps = np.empty_like(packet_counts)

    for idx, cnt in enumerate(packet_counts):
        throughputs_bps[idx] = _run_udp_burst(int(cnt))

    # Convert bits‑per‑second to megabits‑per‑second
    throughputs_mbps = throughputs_bps / 1_000_000.0

    fit = _fit_linear(packet_counts, throughputs_mbps)

    calibration = {
        "packet_to_mbps_factor": fit["slope"],
        "r_squared": fit["r_squared"],
        "measurement_details": {
            "packet_counts": packet_counts.tolist(),
            "throughputs_mbps": throughputs_mbps.tolist(),
        },
    }

    out_path = paths.data("raw", "network_calibration.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(calibration, indent=2), encoding="utf-8")
    log.info("Network calibration written to %s", out_path)

    return calibration

# ----------------------------------------------------------------------
# CPU calibration
# ----------------------------------------------------------------------
def _cpu_bound_work(iterations: int) -> None:
    """
    Execute a tight CPU‑bound loop for ``iterations`` steps.  The function
    does not return a value; its purpose is to consume CPU cycles so that
    the elapsed wall‑clock time can be measured.

    Args:
        iterations: Number of loop iterations (int).
    """
    # Use a local variable to avoid global look‑ups in the tight loop.
    i = 0
    while i < iterations:
        i += 1

def calibrate_cpu() -> Dict[str, any]:
    """
    Run three CPU‑bound workloads with increasing iteration counts,
    compute operations‑per‑second for each, derive a synthetic
    utilisation percentage (relative to the maximum observed ops/s),
    fit a linear model between *percent utilisation* and *ops/s*, and
    write the calibration file.

    Returns:
        Calibration dictionary (also written to disk) with keys:
            - ``percent_to_ops_factor``: slope of the linear model
              (operations per second per 1 % CPU utilisation).
            - ``r_squared``: coefficient of determination of the fit.
    """
    # Choose iteration counts that run quickly on CI but still give measurable
    # differences in elapsed time.
    iteration_counts = np.array([5_000_000, 10_000_000, 15_000_000], dtype=float)
    ops_per_sec = np.empty_like(iteration_counts)

    for idx, cnt in enumerate(iteration_counts):
        start = time.perf_counter()
        _cpu_bound_work(int(cnt))
        elapsed = max(time.perf_counter() - start, 1e-9)
        ops_per_sec[idx] = cnt / elapsed
        log.debug(
            "CPU work %d iterations → %.2f ops/s (elapsed %.6f s)",
            int(cnt),
            ops_per_sec[idx],
            elapsed,
        )

    # Synthetic utilisation: max ops/s corresponds to 100 % utilisation.
    max_ops = np.max(ops_per_sec)
    cpu_util_percent = (ops_per_sec / max_ops) * 100.0

    fit = _fit_linear(cpu_util_percent, ops_per_sec)

    calibration = {
        "percent_to_ops_factor": fit["slope"],
        "r_squared": fit["r_squared"],
        "measurement_details": {
            "iteration_counts": iteration_counts.tolist(),
            "ops_per_sec": ops_per_sec.tolist(),
            "cpu_util_percent": cpu_util_percent.tolist(),
        },
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