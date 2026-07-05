"""
llmXive Project: Assessing the Validity of Statistical Power in Publicly Available Pre-Registered Studies

This module defines global constants and configuration shared across the pipeline.
"""

# Statistical Constants
ALPHA = 0.05  # Significance level for hypothesis testing (FR-003)

# Regression Diagnostics
VIF_THRESHOLD = 5.0  # Variance Inflation Factor threshold for multicollinearity (FR-006)

# Data Quality & Safety Constraints
MIN_SAMPLE_SIZE = 30  # Minimum number of studies required for valid regression analysis (SC-004)