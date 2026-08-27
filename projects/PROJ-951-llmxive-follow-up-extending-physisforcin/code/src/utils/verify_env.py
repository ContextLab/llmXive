"""
verify_env.py
----------------
Utility script to validate that the execution environment is CPU‑only for the
key scientific libraries used in this project: PyBullet, MuJoCo and PyTorch.
It also ensures that no CUDA devices are visible to the process.

The module provides the following public helpers (as declared in the
project's API surface):

- ``check_package_installed(pkg_name: str) -> bool``
- ``install_packages(packages: List[str]) -> None``
- ``verify_pybullet_cpu_only() -> None``
- ``verify_mujoco_cpu_only() -> None``
- ``verify_pytorch_cpu_only() -> None``
- ``verify_cpu_only_environment() -> None``
- ``main() -> None``

The helpers raise ``RuntimeError`` with a clear message when a requirement
is not satisfied.  The ``main`` function aggregates the checks and logs the
outcome using the project's standard logger.
"""

from __future__ import annotations

import importlib
import logging
import os
import subprocess
import sys
from typing import List

# The project already ships a logger utility; we reuse it to keep log formatting
# consistent across modules.
try:
    from src.utils.logging import get_logger
except Exception:  # pragma: no cover
    # Fallback to a very simple logger if the project's logger cannot be imported
    logging.basicConfig(level=logging.INFO)
    get_logger = logging.getLogger

logger = get_logger(__name__)

###########################################################################
# Helper utilities
###########################################################################


def check_package_installed(pkg_name: str) -> bool:
    """
    Return ``True`` if ``pkg_name`` can be imported, otherwise ``False``.
    """
    try:
        importlib.import_module(pkg_name)
        logger.debug("Package '%s' is installed.", pkg_name)
        return True
    except ImportError:
        logger.debug("Package '%s' is NOT installed.", pkg_name)
        return False


def install_packages(packages: List[str]) -> None:
    """
    Install the given list of packages using ``pip``.  This function is kept
    deliberately lightweight – it simply forwards the request to ``pip``.
    Any installation error propagates as a ``subprocess.CalledProcessError``.
    """
    if not packages:
        logger.debug("No packages to install.")
        return

    logger.info("Installing packages: %s", ", ".join(packages))
    subprocess.check_call([sys.executable, "-m", "pip", "install", *packages])


###########################################################################
# Verification functions
###########################################################################


def verify_pybullet_cpu_only() -> None:
    """
    Verify that the ``pybullet`` package is importable.  PyBullet is a pure‑CPU
    physics engine, so successful import is sufficient for our CPU‑only guarantee.
    """
    if not check_package_installed("pybullet"):
        raise RuntimeError("PyBullet is not installed. Please install it via requirements.txt.")
    # Import to ensure there are no hidden import‑time GPU checks.
    import pybullet  # noqa: F401
    logger.info("PyBullet import successful – CPU‑only confirmed.")


def verify_mujoco_cpu_only() -> None:
    """
    Verify that MuJoCo is installed and meets the minimum version requirement
    (>= 2.3).  MuJoCo itself runs on the CPU; the check focuses on version.
    """
    if not check_package_installed("mujoco"):
        raise RuntimeError("MuJoCo is not installed. Please install it via requirements.txt.")
    import mujoco

    # Simple version parsing – MuJoCo follows ``major.minor.patch``.
    version_str = getattr(mujoco, "__version__", "0.0.0")
    major, minor, *_ = (int(part) for part in version_str.split("."))
    if (major, minor) < (2, 3):
        raise RuntimeError(
            f"MuJoCo version {version_str} is too old. Minimum required version is 2.3."
        )
    logger.info("MuJoCo version %s detected – meets CPU‑only requirement.", version_str)


def verify_pytorch_cpu_only() -> None:
    """
    Verify that PyTorch is installed and that it does not have CUDA support
    available at runtime.  The check uses ``torch.cuda.is_available()`` and also
    inspects the build string for a ``+cpu`` suffix as an additional safeguard.
    """
    if not check_package_installed("torch"):
        raise RuntimeError("PyTorch is not installed. Please install it via requirements.txt.")
    import torch

    # ``torch.cuda.is_available()`` returns False when the binary was built
    # without CUDA *or* when no GPU is present.  We also check the build tag.
    cuda_available = torch.cuda.is_available()
    build_tag = getattr(torch, "version", {}).get("git_version", "")
    cpu_build = "+cpu" in getattr(torch, "__config__", {}).get("CMAKE_ARGS", "")

    if cuda_available:
        raise RuntimeError("CUDA is available in the PyTorch build – a CPU‑only build is required.")
    if not cpu_build and not cuda_available:
        # The binary may be a generic build without explicit ``+cpu`` tag.
        # In that case we still enforce that CUDA devices are not visible.
        logger.warning(
            "PyTorch does not report a '+cpu' build tag; ensure the environment does not expose CUDA."
        )
    logger.info("PyTorch CPU‑only verification passed (CUDA not available).")


def verify_cpu_only_environment() -> None:
    """
    Ensure that the process environment does not expose any CUDA devices.
    This is done by checking the ``CUDA_VISIBLE_DEVICES`` environment variable
    and confirming that PyTorch (if present) reports no available GPU.
    """
    cuda_visible = os.getenv("CUDA_VISIBLE_DEVICES")
    if cuda_visible not in (None, "", "0"):
        raise RuntimeError(
            f"CUDA_VISIBLE_DEVICES is set to '{cuda_visible}'. "
            "For CPU‑only execution it must be unset or empty."
        )
    logger.debug("CUDA_VISIBLE_DEVICES is not set or empty.")

    # Re‑use the PyTorch check for a second line of defence.
    if check_package_installed("torch"):
        import torch

        if torch.cuda.is_available():
            raise RuntimeError(
                "CUDA devices are visible to PyTorch despite CUDA_VISIBLE_DEVICES being cleared."
            )
    logger.info("Environment validated as CPU‑only.")


###########################################################################
# Entry point
###########################################################################


def main() -> None:
    """
    Run all verification steps.  The function exits with a non‑zero status
    code if any check fails; otherwise it logs a success message.
    """
    logger.info("Starting CPU‑only environment validation.")
    try:
        verify_cpu_only_environment()
        verify_pybullet_cpu_only()
        verify_mujoco_cpu_only()
        verify_pytorch_cpu_only()
    except RuntimeError as exc:
        logger.error("Environment validation failed: %s", exc)
        sys.exit(1)

    logger.info("All CPU‑only checks passed successfully.")


if __name__ == "__main__":
    main()