"""pytest conftest — gate real-call tests behind LLMXIVE_REAL_TESTS=1."""

from __future__ import annotations

import os

import pytest


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if os.environ.get("LLMXIVE_REAL_TESTS") == "1":
        return
    skip = pytest.mark.skip(reason="set LLMXIVE_REAL_TESTS=1 to run real-call tests")
    for item in items:
        if "real_call" in item.nodeid.split("/"):
            item.add_marker(skip)
