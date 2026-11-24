"""
Root pytest configuration (T004).

Responsibilities:
1. Make the project's source packages (``code/src``) importable as ``src.*``
    so that tests using ``from src.utils.validation import ...`` collect
    correctly when pytest is invoked from the project root.
2. Register CPU resource limit markers and provide fixtures that enforce
    the edge-environment constraints (CPU-only, <= 2 vCPUs, < 7GB RAM),
    per FR-003 and SC-004 of the specification.
"""

import os
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent
CODE_DIR = PROJECT_ROOT / "code"

# Ensure `import src.<module>` resolves to code/src regardless of the
# directory pytest was invoked from. Insert at the FRONT so the real
# project package is never shadowed by an unrelated `src` module.
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

# Enforce CPU-only execution for the whole test session (FR-003).
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

# Edge-environment limits (AWS c6i.large equivalent, SC-004).
MAX_VCPUS = 2
MAX_RAM_GB = 7.0


def pytest_configure(config):
    """Register custom markers with pytest (defensive; also in pytest.ini)."""
    for name, helptext in [
        ("cpu_limit", "test runs under enforced CPU resource limits (<= 2 vCPUs, CPU-only)."),
        ("memory_limit", "test runs under enforced RAM limits (< 7GB peak)."),
        ("resource_limits", "test enforces both CPU and RAM edge-environment limits."),
        ("integration", "integration test spanning multiple pipeline stages."),
        ("unit", "unit test for a single module."),
        ("contract", "contract test verifying schema/API compliance."),
        ("slow", "test that may take a long time."),
    ]:
        config.addinivalue_line("markers", f"{name}: {helptext}")


@pytest.fixture
def cpu_limit_env(monkeypatch):
    """
    Fixture for tests marked ``cpu_limit``: pin the process to CPU-only
    execution with at most MAX_VCPUS threads.

    Returns a dict describing the enforced limits.
    """
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "")
    monkeypatch.setenv("OMP_NUM_THREADS", str(MAX_VCPUS))
    monkeypatch.setenv("MKL_NUM_THREADS", str(MAX_VCPUS))

    try:
        import torch

        torch.set_num_threads(MAX_VCPUS)
        threads = torch.get_num_threads()
    except Exception:
        # torch may not be installed in minimal environments; the env
        # vars above still carry the constraint.
        threads = MAX_VCPUS

    return {"max_vcpus": MAX_VCPUS, "torch_threads": threads, "device": "cpu"}


@pytest.fixture
def memory_limit_guard():
    """
    Fixture for tests marked ``memory_limit``: assert that available
    system RAM is below the 7GB edge-environment budget, and expose a
    checker the test can call after allocating memory.

    Returns a callable ``check()`` raising AssertionError on violation.
    """
    import psutil

    def check():
        process = psutil.Process(os.getpid())
        rss_gb = process.memory_info().rss / (1024 ** 3)
        assert rss_gb < MAX_RAM_GB, (
            f"RAM limit violated: process RSS {rss_gb:.2f}GB >= {MAX_RAM_GB}GB"
        )
        return rss_gb

    # Baseline check at fixture setup.
    check()
    return check
