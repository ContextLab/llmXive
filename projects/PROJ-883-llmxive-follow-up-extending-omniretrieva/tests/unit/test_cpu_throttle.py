"""Unit tests for the CPU throttling utilities.

The tests verify that the module behaves correctly in environments
where cgroup manipulation is not permitted (the typical CI runner).
In such cases ``check_throttling_validity`` must return ``False`` and
attempting to apply the limits must raise ``ThrottleError``.
"""

import pytest

from utils.cpu_throttle import (
    CgroupController,
    ThrottleError,
    check_throttling_validity,
)


def test_check_throttling_validity_returns_false_when_unavailable():
    """On CI runners we expect cgroup v2 to be unavailable or unwritable."""
    # The function should never raise; it should simply return False.
    assert check_throttling_validity() is False


def test_cgroup_controller_apply_raises_when_unavailable():
    """Applying the controller in an environment without cgroup permission
    must raise ``ThrottleError``."""
    controller = CgroupController()
    with pytest.raises(ThrottleError):
        controller.apply()