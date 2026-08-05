"""
llmXive Research Pipeline: Code Module

This package contains the core implementation for the
'Exploring the Relationship Between Brain Network Dynamics and Musical Creativity' project.

Modules:
  - models: Data classes for Subject and BehavioralScore
  - utils: Resource monitoring and logging utilities
  - config: Dataset configuration and sample limits
  - download: OpenNeuro data fetching and validation
  - preprocess: fMRI preprocessing pipeline (FSL/AFNI)
  - graph_metrics: Functional connectivity and graph theory metrics
  - stats: Correlation analysis and statistical testing
  - dependency_check: System dependency verification
  - setup_directories: Project directory initialization
"""

# Explicitly expose public API to prevent circular imports and ensure clean namespace
from .models import Subject, BehavioralScore
from .utils import ResourceUsage, ResourceMonitor
from .config import get_dataset_ids, get_sample_limit, get_config_summary

__all__ = [
    'Subject',
    'BehavioralScore',
    'ResourceUsage',
    'ResourceMonitor',
    'get_dataset_ids',
    'get_sample_limit',
    'get_config_summary'
]

__version__ = "0.1.0"
