"""
Analysis and reporting module.
"""

from failure_classifier import classify_failure, FailureClassification
from merge_results import merge_results

__all__ = ["classify_failure", "FailureClassification", "merge_results"]
