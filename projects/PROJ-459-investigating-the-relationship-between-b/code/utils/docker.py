"""
Utility helpers for interacting with the Docker daemon and the fMRIPrep image.

The integration tests in ``tests/integration/test_fmriprep_wrapper.py`` rely on
two public functions:

* ``validate_docker_daemon()`` – returns ``True`` if the Docker daemon can be
  contacted, otherwise ``False``.
* ``check_fmriprep_image()`` – returns ``True`` if a local Docker image named
  ``fmriprep/fmriprep:latest`` is present, otherwise ``False``.

A convenience ``validate_environment()`` combines the two checks and raises
a ``RuntimeError`` when the environment is not ready.  The implementation
purposefully avoids any heavyweight operations (e.g. pulling images) so that
the test suite runs quickly and deterministically.
"""

import subprocess
import logging
from pathlib import Path

log = logging.getLogger(__name__)


def validate_docker_daemon() -> bool:
    """
    Verify that the Docker daemon is reachable.

    Returns
    -------
    bool
        ``True`` if ``docker info`` exits with a zero return code,
        otherwise ``False``.
    """
    try:
        subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except Exception as exc:  # pragma: no cover – exercised in CI when Docker absent
        log.debug("Docker daemon validation failed: %s", exc)
        return False


def check_fmriprep_image() -> bool:
    """
    Check whether the ``fmriprep/fmriprep:latest`` image is available locally.

    Returns
    -------
    bool
        ``True`` if the image ID is non‑empty, otherwise ``False``.
    """
    try:
        result = subprocess.run(
            ["docker", "images", "-q", "fmriprep/fmriprep:latest"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=True,
        )
        return bool(result.stdout.strip())
    except Exception as exc:  # pragma: no cover – exercised when Docker absent
        log.debug("Docker image check failed: %s", exc)
        return False


def validate_environment() -> None:
    """
    Ensure that Docker is running and the fMRIPrep image is present.

    Raises
    ------
    RuntimeError
        If either the Docker daemon is unavailable or the fMRIPrep image
        cannot be found locally.
    """
    if not validate_docker_daemon():
        raise RuntimeError("Docker daemon is not available.")
    if not check_fmriprep_image():
        raise RuntimeError("fMRIPrep Docker image not found locally.")
