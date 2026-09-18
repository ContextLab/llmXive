"""
llmXive Research Pipeline: Code Module

This package contains the core implementation logic for the 
'The Influence of Algorithmic Recommendations' study.

Exposed modules:
- config: Project configuration and logging setup
- data_generation: Synthetic data generation utilities
- ingestion: Data loading and schema validation
- metrics: Diversity score calculations (Shannon entropy)
- modeling: Propensity Score Weighting and regression analysis
- robustness: Permutation tests and sensitivity analysis
- reporting: Report generation and associational framing validation
"""

# Explicitly expose submodules for convenient importing
# Note: Actual imports happen via 'from code import module_name'

__version__ = "0.1.0"
__author__ = "llmXive Research Team"
