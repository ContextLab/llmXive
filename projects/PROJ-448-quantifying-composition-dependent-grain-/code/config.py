"""
Configuration module for the project.
"""
import os

# Project Root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Directories
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
FIGURES_DIR = os.path.join(DATA_DIR, "figures")
CODE_DIR = os.path.join(PROJECT_ROOT, "code")
TESTS_DIR = os.path.join(PROJECT_ROOT, "tests")
RESEARCH_DIR = os.path.join(PROJECT_ROOT, "research")

# Simulation Constants
RANDOM_SEED = 42
TEMPERATURE_RANGE = (300, 900)  # Kelvin
ALLOY_SYSTEMS = ["Fe-Cr", "Fe-Mo", "Fe-V", "Fe-W"]
