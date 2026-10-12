"""
Exception hierarchy for the plant disease resistance prediction pipeline.

This module defines a set of custom exception classes that carry both a
human‑readable error message and an associated exit code.  The exit code
values are chosen to match the identifiers used in the specification
(e.g. ``EX_DATA_INTEGRITY (02)``).  All pipeline‑wide exceptions inherit
from :class:`PipelineError` so that callers can catch a single base type
if they do not need to distinguish the concrete reason.

The classes are deliberately lightweight – they store the message and
exit code as attributes and implement ``__str__``/``__repr__`` to return
the message.  This makes it straightforward for unit tests to raise the
exception and assert both the string representation and the ``exit_code``
attribute.
"""

from __future__ import annotations

__all__ = [
    "PipelineError",
    "EX_DATA_INTEGRITY",
    "EX_POWER_INSUFFICIENT",
    "EX_RESOURCE_LIMIT",
]


class PipelineError(Exception):
    """
    Base class for all pipeline‑specific errors.

    Sub‑classes should define a ``default_message`` class attribute and an
    ``exit_code`` integer.  The constructor allows an optional custom
    message; if omitted, the class‑level ``default_message`` is used.
    """

    default_message: str = "An unspecified pipeline error occurred."
    exit_code: int = 1

    def __init__(self, message: str | None = None) -> None:
        self.message = message if message is not None else self.default_message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, exit_code={self.exit_code})"


class EX_DATA_INTEGRITY(PipelineError):
    """
    Raised when the pipeline cannot continue because the required data
    modalities are missing or too few paired samples remain after exclusion.

    Corresponds to error code **02** in the specification.
    """

    default_message = "Insufficient data modalities: Remaining samples < 100"
    exit_code = 2


class EX_POWER_INSUFFICIENT(PipelineError):
    """
    Raised when a power analysis determines that the dataset is too small
    to achieve the desired statistical power.

    Corresponds to error code **03** in the specification.
    """

    default_message = (
        "Power deficiency: n < 100 required for multivariate omics analysis with BH correction"
    )
    exit_code = 3


class EX_RESOURCE_LIMIT(PipelineError):
    """
    Raised when the resource monitor detects that the process exceeds the
    user‑provided limits for memory usage or runtime.

    Corresponds to error code **04** in the specification.
    """

    default_message = (
        "Resource limit exceeded: memory or runtime constraints violated"
    )
    exit_code = 4