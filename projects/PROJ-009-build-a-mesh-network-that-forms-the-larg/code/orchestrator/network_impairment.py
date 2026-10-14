"""
Network impairment utilities for the mesh‑network orchestrator.

This module provides a thin wrapper around the Linux ``tc`` command
(traffic control) to inject latency and packet‑loss on a set of
network interfaces.  It is deliberately minimal – the real testbed
will run the commands on the target nodes via SSH; in CI we simply
verify that the ``tc`` binary exists and raise an informative error
if it does not.
"""

import subprocess
import shutil
from typing import List

class NetworkImpairmentRequiredError(RuntimeError):
    """Raised when the required ``tc`` binary is unavailable."""

def _check_tc_available() -> bool:
    """Return ``True`` if the ``tc`` executable can be found in PATH."""
    return shutil.which("tc") is not None

def apply_impairments(
    *,
    node_ips: List[str],
    latency_ms: int,
    packet_loss_pct: float,
    iface: str = "eth0",
) -> None:
    """
    Apply network impairments using ``tc netem`` on the given nodes.

    Parameters
    ----------
    node_ips:
        List of node IP addresses to which the impairment should be applied.
        In the real testbed this list is used to SSH into each node and
        execute the ``tc`` command.  For the CI mock implementation the
        function merely verifies that ``tc`` exists locally.
    latency_ms:
        Desired one‑way latency in milliseconds.  ``0`` means no latency
        injection.
    packet_loss_pct:
        Desired packet‑loss percentage (0‑100).  ``0`` means no loss.
    iface:
        Network interface on which to apply the netem rule.  Defaults to
        ``eth0`` which is common on many Linux testbeds.

    Raises
    ------
    NetworkImpairmentRequiredError
        If the ``tc`` binary cannot be located.
    subprocess.CalledProcessError
        If the ``tc`` command itself fails (e.g., insufficient privileges).
    """
    if not _check_tc_available():
        raise NetworkImpairmentRequiredError(
            "The required 'tc' command is not available on this system."
        )

    # Build the netem argument string
    netem_args = []
    if latency_ms > 0:
        netem_args.append(f"delay {latency_ms}ms")
    if packet_loss_pct > 0:
        netem_args.append(f"loss {packet_loss_pct}%")
    if not netem_args:
        # Nothing to apply – caller should have avoided this case.
        return

    netem_rule = " ".join(netem_args)

    # In a real environment we would SSH to each node and run the command.
    # For CI we simply execute locally to prove the command is syntactically
    # valid.  The caller is responsible for ensuring appropriate privileges.
    cmd = ["tc", "qdisc", "add", "dev", iface, "root", "netem"] + netem_args
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Failed to apply netem rule '{netem_rule}' on interface {iface}: {e.stderr}"
        ) from e
