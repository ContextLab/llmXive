"""
Setup script for the llmXive benchmark project.
Ensures Python 3.11+ is used and installs dependencies.
"""
import sys
import os
from setuptools import setup, find_packages

# Check Python version
if sys.version_info < (3, 11):
    print("Error: This project requires Python 3.11 or higher.")
    print(f"Current version: {sys.version}")
    sys.exit(1)

# Read requirements
def get_requirements():
    req_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if not os.path.exists(req_path):
        return []
    with open(req_path, "r", encoding="utf-8") as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]

setup(
    name="llmxive-benchmark",
    version="0.1.0",
    description="Heterogeneous Scientific Foundation Model Collaboration Benchmark",
    author="llmXive Research Team",
    packages=find_packages(where="."),
    python_requires=">=3.11",
    install_requires=get_requirements(),
    entry_points={
        "console_scripts": [
            "run-benchmark=src.benchmark.run_benchmark:main",
            "run-task=src.benchmark.run_task:main",
        ],
    },
)
