"""
CorrectnessLabel entity definition.

Defines the data structure for storing the correctness assessment of a generated patch.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class CorrectnessLabel:
    """
    Represents the correctness label for a specific bug fix attempt.

    Attributes:
        bug_id (str): Unique identifier for the bug (e.g., 'Lang-1').
        pass_fail (bool): True if the patch passes the test suite, False otherwise.
        unsafe_flag (Optional[bool]): Flag indicating if the patch introduced
            unsafe behavior or triggered a timeout/crash during execution.
            None if the status is unknown or not applicable.
    """
    bug_id: str
    pass_fail: bool
    unsafe_flag: Optional[bool] = None