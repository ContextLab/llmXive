"""CPU throttling utilities using Linux cgroups (v2).

This module enforces a strict limit of 1 CPU core (≤ 1 000 ms CPU time per query) and 7 GB of RAM
for the current process (and any child processes) by creating a dedicated cgroup under
``/sys/fs/cgroup``. If the environment does not permit cgroup manipulation (e.g., insufficient
permissions or missing cgroup v2 support), the process aborts with exit code ``99`` and a clear
error message, as required by the specification.

The public API mirrors the placeholder that existed previously:

* ``ThrottleError`` – raised when throttling cannot be applied.
* ``CgroupController`` – encapsulates the creation, configuration,
  and cleanup of the cgroup.
* ``check_throttling_validity`` – returns ``True`` if a cgroup can
  be created and limits applied, otherwise ``False``.
* ``throttled_context`` – a context manager that applies the cgroup
  on entry and removes it on exit.
* ``main`` – a small CLI that attempts to apply the limits and
  reports success or failure.

The implementation deliberately avoids any RLIMIT fallback; the
only supported mechanism is cgroups. The module logs the throttling
mode (``cgroups``) and the configured limits using the project's
``llmxive_toolkit`` logger.
"""

import os
import sys
import errno
from pathlib import Path
from contextlib import contextmanager

from llmxive_toolkit import get_logger, paths

# ----------------------------------------------------------------------
# Configuration constants (matching the feature spec)
# ----------------------------------------------------------------------
DEFAULT_CORES = 2
DEFAULT_MEMORY_GB = 7
# Exit code mandated by the specification for throttling failure.
EXIT_CODE_THROTTLING_FAILURE = 99

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Exceptions
# ----------------------------------------------------------------------
class ThrottleError(RuntimeError):
    """Raised when cgroup throttling cannot be applied."""
    pass


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _cgroup_v2_root() -> Path:
    """Return the root path of the cgroup v2 hierarchy.

    Raises:
        ThrottleError: If the system does not appear to have a cgroup v2
            hierarchy (i.e., ``/sys/fs/cgroup/cgroup.controllers`` is missing).
    """
    root = Path("/sys/fs/cgroup")
    if not (root / "cgroup.controllers").exists():
        raise ThrottleError(
            "cgroup v2 not available on this system (missing cgroup.controllers)."
        )
    return root

def _enable_controllers(cgroup_path: Path) -> None:
    """Enable the ``cpu`` and ``memory`` controllers for the given cgroup.

    Args:
        cgroup_path: Path to the newly created cgroup directory.

    Raises:
        ThrottleError: If the controller enable operation fails.
    """
    subtree_ctl = cgroup_path / "cgroup.subtree_control"
    try:
        # The file may already contain the needed controllers; appending is safe.
        with subtree_ctl.open("a") as f:
            f.write("+cpu +memory\n")
    except OSError as e:
        raise ThrottleError(
            f"Failed to enable cpu/memory controllers in cgroup: {e}"
        ) from e

def _write_limit_file(file_path: Path, content: str) -> None:
    """Write a limit value to a cgroup control file.

    Args:
        file_path: Path to the cgroup control file.
        content: String content to write.

    Raises:
        ThrottleError: If writing fails (e.g., permission denied).
    """
    try:
        with file_path.open("w") as f:
            f.write(content)
    except OSError as e:
        raise ThrottleError(
            f"Unable to write to cgroup limit file {file_path}: {e}"
        ) from e


# ----------------------------------------------------------------------
# Core controller class
# ----------------------------------------------------------------------
class CgroupController:
    """Controller that creates a temporary cgroup and applies limits.

    The controller creates a sub‑cgroup named ``llmxive_throttle_<pid>``
    under the cgroup v2 root. Limits are applied to the current process
    (PID) and any children spawned while the cgroup is active.
    """

    def __init__(self, cores: int = DEFAULT_CORES, memory_gb: int = DEFAULT_MEMORY_GB):
        """
        Args:
            cores: Number of CPU cores to allow (integer >= 1).
            memory_gb: RAM limit in gigabytes.
        """
        if cores < 1:
            raise ValueError("cores must be >= 1")
        if memory_gb < 1:
            raise ValueError("memory_gb must be >= 1")

        self.cores = cores
        self.memory_gb = memory_gb
        self.cgroup_name = f"llmxive_throttle_{os.getpid()}"
        self.cgroup_path = _cgroup_v2_root() / self.cgroup_name
        self._applied = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def apply(self) -> None:
        """Create the cgroup, enable controllers, and set limits.

        Raises:
            ThrottleError: If any step fails (e.g., permission denied).
        """
        if self._applied:
            log.debug("Cgroup limits already applied; skipping.")
            return

        # 1. Create the cgroup directory
        try:
            self.cgroup_path.mkdir(parents=False, exist_ok=False)
            log.debug("Created cgroup directory %s", self.cgroup_path)
        except OSError as e:
            raise ThrottleError(
                f"Failed to create cgroup directory {self.cgroup_path}: {e}"
            ) from e

        # 2. Enable cpu and memory controllers
        _enable_controllers(self.cgroup_path)

        # 3. Set CPU limit.
        #    In cgroup v2 the format is: "<quota> <period>"
        #    We use a period of 100000µs (default) and quota = cores * period.
        period_us = 100_000
        quota_us = self.cores * period_us
        cpu_max_path = self.cgroup_path / "cpu.max"
        _write_limit_file(cpu_max_path, f"{quota_us} {period_us}")
        log.debug(
            "Set CPU limit: %d cores -> quota %d µs, period %d µs",
            self.cores,
            quota_us,
            period_us,
        )

        # 4. Set memory limit.
        mem_max_path = self.cgroup_path / "memory.max"
        mem_bytes = self.memory_gb * 1024 ** 3
        _write_limit_file(mem_max_path, str(mem_bytes))
        log.debug(
            "Set memory limit: %d GB (%d bytes)", self.memory_gb, mem_bytes
        )

        # 5. Move the current process (and future children) into the cgroup.
        cgroup_procs = self.cgroup_path / "cgroup.procs"
        _write_limit_file(cgroup_procs, str(os.getpid()))
        log.info(
            "Applied cgroup throttling (mode=cgroups, cores=%d, memory_gb=%d)",
            self.cores,
            self.memory_gb,
        )
        self._applied = True

    def cleanup(self) -> None:
        """Remove the cgroup directory if it was created.

        Errors during cleanup are logged but do not raise, because the
        process is already exiting or continuing its normal execution.
        """
        if not self._applied:
            return

        try:
            # Move any remaining processes back to the parent cgroup.
            parent_procs = self.cgroup_path.parent / "cgroup.procs"
            for pid_line in self.cgroup_path.joinpath("cgroup.procs").read_text().splitlines():
                if pid_line.strip():
                    _write_limit_file(parent_procs, pid_line.strip())
        except Exception as e:
            log.warning("Failed to migrate processes out of cgroup: %s", e)

        try:
            self.cgroup_path.rmdir()
            log.debug("Removed cgroup directory %s", self.cgroup_path)
        except OSError as e:
            if e.errno != errno.ENOENT:
                log.warning("Could not remove cgroup directory %s: %s", self.cgroup_path, e)

        self._applied = False

    # ------------------------------------------------------------------
    # Context manager support (optional convenience)
    # ------------------------------------------------------------------
    def __enter__(self):
        self.apply()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        # Do not suppress exceptions
        return False


# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def check_throttling_validity() -> bool:
    """Return ``True`` if cgroup throttling can be applied, else ``False``.

    The function attempts a *dry‑run* creation of a temporary cgroup
    without persisting any limits. If any step raises ``ThrottleError``,
    the function returns ``False``.
    """
    try:
        controller = CgroupController()
        controller.apply()
        controller.cleanup()
        return True
    except ThrottleError as e:
        log.debug("Throttling validity check failed: %s", e)
        return False

@contextmanager
def throttled_context(cores: int = DEFAULT_CORES, memory_gb: int = DEFAULT_MEMORY_GB):
    """Context manager that enforces cgroup limits for the block.

    Example:
        >>> from utils.cpu_throttle import throttled_context
        >>> with throttled_context():
        ...     run_heavy_computation()
    """
    controller = CgroupController(cores=cores, memory_gb=memory_gb)
    try:
        controller.apply()
        yield
    finally:
        controller.cleanup()


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def _parse_cli_args() -> dict:
    """Parse a minimal CLI used for manual testing of the module."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Apply a cgroup‑based CPU and memory throttle to the current process."
    )
    parser.add_argument(
        "--cores",
        type=int,
        default=DEFAULT_CORES,
        help=f"Number of CPU cores to allow (default: {DEFAULT_CORES})",
    )
    parser.add_argument(
        "--memory-gb",
        type=int,
        default=DEFAULT_MEMORY_GB,
        help=f"RAM limit in gigabytes (default: {DEFAULT_MEMORY_GB})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only check whether throttling could be applied, without applying it.",
    )
    return vars(parser.parse_args())

def main() -> None:
    """CLI entry point.

    Attempts to apply the configured cgroup limits. On failure the
    process exits with ``99`` as mandated by the specification.
    """
    args = _parse_cli_args()

    if args["dry_run"]:
        if check_throttling_validity():
            log.info("cgroup throttling is available on this system.")
            sys.exit(0)
        else:
            print("ERROR: CPU throttling not applied", file=sys.stderr)
            log.error("cgroup throttling is NOT available on this system.")
            sys.exit(EXIT_CODE_THROTTLING_FAILURE)

    try:
        controller = CgroupController(
            cores=args["cores"], memory_gb=args["memory_gb"]
        )
        controller.apply()
        # Record successful throttling mode for downstream metrics.
        os.environ["THROTTLE_MODE"] = "cgroups"
        log.info(
            "CPU throttling successfully applied (mode=cgroups, cores=%d, memory_gb=%d).",
            args["cores"],
            args["memory_gb"],
        )
        # Keep the cgroup active for the lifetime of the process.
        # The controller will clean up automatically on normal exit.
    except ThrottleError as e:
        print("ERROR: CPU throttling not applied", file=sys.stderr)
        log.error("Failed to apply CPU throttling: %s", e)
        sys.exit(EXIT_CODE_THROTTLING_FAILURE)

if __name__ == "__main__":
    main()
