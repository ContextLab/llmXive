"""
Training package for DOPD (Dynamic On-Policy Distillation) and baseline
distillation methods.

This package contains the training loops and distillation logic for
Teacher-Student reinforcement learning experiments.
"""

from .uniform_distillation import UniformDistillationTrainer
from .dopd_distillation import DOPDTrainer

__all__ = [
    "UniformDistillationTrainer",
    "DOPDTrainer",
]