"""Root pytest configuration for the tests/ directory.

Registers the custom markers used by the unit, integration and contract
test suites so that ``pytest`` does not emit PytestUnknownMarkWarning,
and exposes a small helper that reports the project root so tests can
locate ``data/`` and ``code/`` regardless of the working directory.
"""

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def pytest_configure(config):
    """Register custom pytest markers used across the test suites."""
    config.addinivalue_line(
        "markers", "unit: fast, isolated unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: tests that exercise multiple pipeline stages"
    )
    config.addinivalue_line(
        "markers", "contract: tests validating artifacts against schema contracts"
    )


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the repository root (the parent of ``tests/``)."""
    return PROJECT_ROOT
