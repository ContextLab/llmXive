"""Integration tests for the cgroup‑based CPU throttling utility.

The tests cover two scenarios:
1. A simulated failure where the cgroup cannot be created – the script must
   exit with code 99 and emit the required error message.
2. A successful (mocked) application – the environment variable
   ``THROTTLE_MODE`` must be set to ``cgroups``.
"""

import os
import sys

import pytest

# Import the module under test
from code.utils import cpu_throttle


def test_cpu_throttle_failure(monkeypatch, capsys):
    """Simulate a failure to apply cgroup limits.

    The ``apply`` method is monkey‑patched to raise ``ThrottleError``.
    The script should exit with code 99 and print the required error
    message.  No ``THROTTLE_MODE`` environment variable should be set.
    """
    # Ensure the environment variable is not present before the test.
    os.environ.pop("THROTTLE_MODE", None)

    # Patch ``CgroupController.apply`` to raise the expected exception.
    def raise_error(self):
        raise cpu_throttle.ThrottleError("simulated cgroup failure")

    monkeypatch.setattr(cpu_throttle.CgroupController, "apply", raise_error)

    # Running ``main`` should raise SystemExit with code 99.
    with pytest.raises(SystemExit) as excinfo:
        cpu_throttle.main()
    assert excinfo.value.code == 99

    # The required error message must be printed to stderr.
    captured = capsys.readouterr()
    assert "ERROR: CPU throttling not applied" in captured.err

    # No throttling mode should be recorded.
    assert "THROTTLE_MODE" not in os.environ


def test_cpu_throttle_success(monkeypatch):
    """Mock a successful throttling application.

    The ``apply`` method is replaced with a no‑op that simply sets the
    environment variable.  After ``main`` returns, ``THROTTLE_MODE``
    must be ``cgroups`` and the process must not exit with an error.
    """
    # Ensure a clean environment.
    os.environ.pop("THROTTLE_MODE", None)

    # Replace ``apply`` with a stub that sets the env var.
    def fake_apply(self):
        # The real ``main`` will set the env var after ``apply`` returns,
        # but we also set it here to emulate the side‑effect of a successful call.
        pass

    monkeypatch.setattr(cpu_throttle.CgroupController, "apply", fake_apply)

    # Run ``main`` – it should complete without raising SystemExit.
    # (If it were to call sys.exit, pytest would raise a SystemExit.)
    cpu_throttle.main()

    # Verify that the environment variable was set by ``main``.
    assert os.environ.get("THROTTLE_MODE") == "cgroups"