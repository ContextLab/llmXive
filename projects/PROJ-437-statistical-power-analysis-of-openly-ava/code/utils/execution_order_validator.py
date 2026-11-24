"""
Execution Order Validator.

The pipeline consists of many stages that must be run in a specific order.
This validator encodes a minimal, configurable ordering graph and raises a
``TaskOrderError`` if the current run violates the expected sequence.
For the scaffold we implement a simple static ordering that matches the
expectations of ``code/main.py``.
"""

import logging
from typing import List

logger = logging.getLogger(__name__)

class TaskOrderError(Exception):
    """Raised when the pipeline execution order is invalid."""

class ExecutionOrderValidator:
    """
    Validate that pipeline stages are invoked in the correct order.

    The validator holds a linear ordering that reflects the high‑level
    actions defined in ``code/main.py``. When ``validate()`` is called it
    simply checks that the ordering list is non‑empty; in a full implementation
    it would inspect previous runs or a persisted state file.
    """

    # The canonical order – must be a superset of the actions used in main.py
    _expected_order: List[str] = [
        "download",
        "preprocess",
        "noise",
        "synthetic",
        "analyze",
        "sensitivity",
        "convergence",
        "report",
    ]

    def __init__(self) -> None:
        self._executed: List[str] = []

    def record(self, action: str) -> None:
        """
        Record that ``action`` has been executed.

        This method is intended for future extensions where the validator
        tracks state across multiple invocations. It is not used by the
        current scaffold but is provided for completeness.
        """
        self._executed.append(action)
        logger.debug(f"Recorded execution of action '{action}'")

    def validate(self) -> None:
        """
        Perform a sanity check that the expected ordering is plausible.

        For the scaffold we simply ensure that the list is not empty and
        that the first expected action is ``download`` – a reasonable
        minimal guard against completely malformed pipelines.
        """
        if not self._expected_order:
            raise TaskOrderError("No expected order defined for the pipeline.")
        if self._expected_order[0] != "download":
            raise TaskOrderError(
                f"The first expected action should be 'download', found "
                f"'{self._expected_order[0]}'"
            )
        logger.info("Execution order validator passed basic sanity checks.")
