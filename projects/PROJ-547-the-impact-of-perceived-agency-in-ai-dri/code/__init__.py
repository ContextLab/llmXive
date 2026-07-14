"""
llmXive Agency CBT Project Package.

This package contains the modules for analyzing the impact of perceived agency
in AI-driven Cognitive Behavioral Therapy on treatment adherence.
"""

__version__ = "0.1.0"
__author__ = "llmXive Research Team"

# Expose main package modules for convenient importing
from . import (
    adherence_extraction,
    agency_scoring,
    analysis,
    config,
    data_acquisition,
    logging,
    utils,
    validation,
)

__all__ = [
    "adherence_extraction",
    "agency_scoring",
    "analysis",
    "config",
    "data_acquisition",
    "logging",
    "utils",
    "validation",
]
