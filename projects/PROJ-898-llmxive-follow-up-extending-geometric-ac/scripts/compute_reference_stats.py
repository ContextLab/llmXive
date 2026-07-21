"""
Script to compute statistical reference distribution for latent drift detection.

This script implements Task T010b:
- Loads physics states from data/generated/physics_states.json
- Computes mean and covariance
- Saves reference statistics to data/raw/gam_reference_stats.json
"""
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from statistical_reference import main

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
