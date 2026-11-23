"""
Configuration module for the Predicting Molecular Properties project.

This file defines project-wide constants used across the pipeline.
It is deliberately lightweight to avoid heavy imports at module load time.
"""

from pathlib import Path

# Zenodo accession ID for the experimental barrier dataset (FR-001)
ZENODO_ID = "1048765"

# Project root directory – useful for scripts that need an absolute base path.
# The value is the directory that contains the top‑level ``code`` package.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Additional configuration values (e.g., random seeds) can be added here as the
# project evolves. Keeping them in a single module ensures consistency.
