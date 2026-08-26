"""
code/agents package initialization.

This package contains agent implementations for the DOPD (Dynamic On-Policy
Distillation) research pipeline. It includes the Teacher (Oracle) and Student
agents, as well as baseline estimators.

Available agents:
- Teacher: Oracle policy with full state access (O, H)
- Student: Tabular Q-table agent with partial state access (O)
- BaselineEstimator: Computes V_baseline(s) for advantage calculation
"""

from .teacher import TeacherAgent
from .student import StudentAgent
from .baseline_estimator import BaselineEstimator

__all__ = ["TeacherAgent", "StudentAgent", "BaselineEstimator"]
__version__ = "0.1.0"