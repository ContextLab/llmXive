"""
llmXive Automated Science Pipeline - Core Implementation Package.

This package contains the core logic for the weak-to-strong generalization
experiments via Direct On-Policy Distillation.
"""

from .core import (
    evaluator,
    hard_floor_enforcer,
    memory_monitor,
    reward_computation,
    statistical_tests,
    trainer,
)
from .data import download_aime, preprocess
from .models import teacher_loader, moe_student, ssm_student
from .scripts import hash_artifacts, run_format, run_lint
from .tests import test_environment

__version__ = "0.1.0"
