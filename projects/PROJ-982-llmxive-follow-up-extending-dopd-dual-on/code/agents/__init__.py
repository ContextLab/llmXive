"""
code/agents package initialization.

The original ``__init__`` attempted to import ``TeacherAgent`` and
``StudentAgent`` which do not exist.  The public API of the project
provides ``TeacherOracle`` and ``TabularQStudent`` (plus the baseline
estimator).  We expose the correct symbols here so that imports such as
``from agents.student import TabularQStudent`` work without triggering
ImportError during test collection.
"""
from .teacher import TeacherOracle, create_teacher_agent
from .student import TabularQStudent, create_student_agent
from .baseline_estimator import BaselineEstimator, create_baseline_estimator

__all__ = [
    "TeacherOracle",
    "create_teacher_agent",
    "TabularQStudent",
    "create_student_agent",
    "BaselineEstimator",
    "create_baseline_estimator",
]
__version__ = "0.1.0"
