"""
Verify that the required project directories exist.
"""

import os

REQUIRED_DIRS = [
    "code",
    "code/utils",
    "data/raw",
    "data/interim",
    "data/processed",
    "results",
    "paper",
    "tests",
]

def test_directories_exist():
    for d in REQUIRED_DIRS:
        assert os.path.isdir(d), f"Required directory missing: {d}"
