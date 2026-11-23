"""
CPU Pinning Utility Module

This module provides functionality to pin the current process to a specific CPU core
using OS-level affinity settings. It is designed to be imported and called by the
full run wrapper (T072) at the very start of execution, before any heavy computation,
to ensure deterministic performance and resource isolation.
"""

import os
import sys
import logging
from typing import Set

logger = logging.getLogger(__name__)


def get_available_cores() -> Set[int]:
    """
    Returns the set of available CPU core IDs on the current system.

    Returns:
        Set[int]: A set of integers representing available core IDs.
    """
    try:
        # sched_getaffinity returns the set of cores the current process can use
        # If not available (e.g., Windows), fallback to os.cpu_count()
        if hasattr(os, 'sched_getaffinity'):
            return set(os.sched_getaffinity(0))
        else:
            # Fallback for systems without sched_getaffinity (e.g., Windows)
            count = os.cpu_count() or 1
            return set(range(count))
    except Exception as e:
        logger.warning(f"Could not determine available cores: {e}. Defaulting to range(1).")
        return {0}


def pin_to_core(core_id: int = 0) -> None:
    """
    Pins the current process to the specified CPU core ID.

    This function sets the process affinity to restrict execution to a single core.
    It validates that the requested core is available on the system.

    Args:
        core_id (int): The ID of the CPU core to pin to. Defaults to 0.

    Raises:
        ValueError: If the specified core_id is not available on the system.
        OSError: If the OS call to set affinity fails for other reasons.
    """
    if not isinstance(core_id, int):
        raise TypeError(f"core_id must be an integer, got {type(core_id)}")

    if core_id < 0:
        raise ValueError(f"core_id must be non-negative, got {core_id}")

    available_cores = get_available_cores()

    if core_id not in available_cores:
        available_list = sorted(list(available_cores))
        raise ValueError(
            f"Requested core_id {core_id} is not available. "
            f"Available cores: {available_list}"
        )

    try:
        if hasattr(os, 'sched_setaffinity'):
            os.sched_setaffinity(0, {core_id})
            logger.info(f"Successfully pinned process to CPU core {core_id}.")
        else:
            # Windows or other OS without sched_setaffinity
            # Python's os.sched_setaffinity is Unix/Linux specific.
            # On Windows, we cannot easily pin to a single core via standard os module
            # without using ctypes and SetProcessAffinityMask.
            # For this utility, we raise an error if the method is missing to avoid
            # silent failure, as the task requires handling unavailability.
            raise OSError(
                "CPU pinning via sched_setaffinity is not supported on this OS. "
                "This utility requires Linux/Unix."
            )
    except OSError as e:
        logger.error(f"Failed to set CPU affinity: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during CPU pinning: {e}")
        raise


def verify_pinning(core_id: int) -> bool:
    """
    Verifies that the current process is pinned to the specified core.

    Args:
        core_id (int): The expected core ID.

    Returns:
        bool: True if pinned to the specified core, False otherwise.
    """
    if hasattr(os, 'sched_getaffinity'):
        current_affinity = os.sched_getaffinity(0)
        return current_affinity == {core_id}
    return False
