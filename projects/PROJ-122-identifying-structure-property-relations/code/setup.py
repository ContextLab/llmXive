import os
from setuptools import setup, find_packages
from setup_directories import create_directories
from setup_state import create_state_structure

# Ensure directory structure exists before installation
def run_setup():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    create_directories(base_dir)
    create_state_structure(base_dir)

if __name__ == "__main__":
    run_setup()
    setup(
        name="llmxive-polymer-blends",
        version="0.1.0",
        packages=find_packages(where="."),
        python_requires=">=3.11",
    )
