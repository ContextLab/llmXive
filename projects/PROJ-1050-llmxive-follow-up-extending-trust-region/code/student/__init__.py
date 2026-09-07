"""
Student Policy Package.

Implements the capacity-constrained student policy and the TOP-D loss
calculation for policy distillation.
"""

from .policy import StudentPolicy
from .topd_loss import TOPDLoss

__all__ = [
    "StudentPolicy",
    "TOPDLoss",
]
