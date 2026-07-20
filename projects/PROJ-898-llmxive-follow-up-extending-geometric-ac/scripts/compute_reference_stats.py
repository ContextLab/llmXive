#!/usr/bin/env python3
"""
Script to compute statistical reference distribution for T010b.

This script computes mean and covariance statistics from the generated
physics states and saves them to data/raw/gam_reference_stats.json
for use in latent drift detection.

Usage:
    python scripts/compute_reference_stats.py
"""

import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from code.statistical_reference import main

if __name__ == "__main__":
    main()