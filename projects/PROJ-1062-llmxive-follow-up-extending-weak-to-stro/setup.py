"""
Setup script for the llmXive follow-up project.
"""
from setuptools import setup, find_packages

setup(
    name="llmxive-follow-up",
    version="0.1.0",
    packages=find_packages(where="code"),
    package_dir={"": "code"},
    python_requires=">=3.11",
    install_requires=[
        # Dependencies will be finalized in T002
        # Placeholder for initial structure
    ],
)