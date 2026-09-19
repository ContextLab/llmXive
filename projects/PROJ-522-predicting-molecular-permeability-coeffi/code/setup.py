"""
Setup script for the molecular permeability prediction project.
Handles installation and basic configuration.
"""
from setuptools import setup, find_packages

setup(
    name="llmxive-molecular-permeability",
    version="0.1.0",
    description="Predicting Molecular Permeability Coefficients via Graph Neural Networks",
    author="llmXive Research Team",
    author_email="research@llmxive.example.com",
    packages=find_packages(where="."),
    package_dir={"": "."},
    python_requires=">=3.9",
    install_requires=[
        "rdkit",
        "torch",
        "torch-geometric",
        "scikit-learn",
        "pandas",
        "numpy",
        "pyyaml",
        "datasets",
        "pyarrow",
        "scipy",
        "matplotlib",
        "seaborn",
        "ruff",
        "black",
        "pytest",
    ],
    extras_require={
        "dev": [
            "ruff",
            "black",
            "pytest",
            "pytest-cov",
            "memory-profiler",
        ]
    },
    entry_points={
        "console_scripts": [
            "setup-project=setup_directories:main",
            "setup-linting=setup_linting:main",
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="molecular permeability graph neural networks rdkit pytorch",
)
