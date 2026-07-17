"""
Setup script for llmXive EvalVerse pipeline.
"""
from setuptools import setup, find_packages

setup(
    name="llmxive-evalverse",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        "opencv-python>=4.8.0",
        "librosa>=0.10.0",
        "scikit-learn>=1.3.0",
        "xgboost>=2.0.0",
        "psutil>=5.9.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "ruff>=0.1.0",
            "black>=23.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "llmxive-run=src.cli.run_pipeline:main",
        ]
    },
)