"""
Setup script for the project.
"""
from setuptools import setup, find_packages

setup(
    name="brain-network-dynamics-reward",
    version="0.1.0",
    packages=find_packages(where="code"),
    package_dir={"": "code"},
    install_requires=[
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "scikit-learn>=1.3.0",
        "nibabel>=5.1.0",
        "scipy>=1.11.0",
        "matplotlib>=3.7.0",
        "requests>=2.31.0",
        "tqdm>=4.65.0",
        "bids-validator>=1.14.0",
        "nilearn>=0.10.0",
        "pyyaml>=6.0",
    ],
    python_requires=">=3.11",
)