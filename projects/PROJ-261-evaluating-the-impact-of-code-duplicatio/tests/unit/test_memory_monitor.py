"""
Unit tests for ``memory_monitor.setup_memory_monitoring``.
The function must accept calls with positional, keyword, and extra arguments.
"""

from __future__ import annotations

import threading

import pytest

from memory_monitor import setup_memory_monitoring

def test_setup_memory_monitoring_defaults():
    """Calling with no arguments should return a threading.Event."""
    stop_event = setup_memory_monitoring()
    assert isinstance(stop_event, threading.Event)

def test_setup_memory_monitoring_with_kwargs():
    """Calling with keyword arguments should succeed."""
    stop_event = setup_memory_monitoring(memory_limit_mb=1024, interval=1)
    assert isinstance(stop_event, threading.Event)

def test_setup_memory_monitoring_extra_args():
    """Extra positional arguments must be ignored, not raise."""
    stop_event = setup_memory_monitoring(999, 2, "unused", key="value")
    assert isinstance(stop_event, threading.Event)