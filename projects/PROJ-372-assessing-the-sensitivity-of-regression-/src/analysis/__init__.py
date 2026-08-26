"""
Analysis module for the llmXive automated science pipeline.

This module implements User Story 3: Interaction Analysis and Sensitivity Visualization.
It provides tools for multiple regression with interaction terms, sensitivity sweeps,
and visualization of stability curves.

Exports:
    - run_meta_analysis: Main pipeline entry point for meta-analysis.
    - hlm_analysis: Module containing multiple regression and interaction logic.
    - visualization: Module for generating sensitivity plots.
    - report_generator: Module for generating final analysis reports.
"""

from .hlm_analysis import run_meta_analysis
from . import visualization
from . import report_generator

__all__ = [
    "run_meta_analysis",
    "visualization",
    "report_generator",
]