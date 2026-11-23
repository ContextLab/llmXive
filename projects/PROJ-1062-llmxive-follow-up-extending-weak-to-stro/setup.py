"""
Setup script for llmXive follow-up project.
Note: PyTorch must be installed separately via:
pip install torch --index-url https://download.pytorch.org/whl/cpu
"""
from setuptools import setup, find_packages

setup(
    name="llmxive-follow-up-extending-weak-to-stro",
    version="0.1.0",
    packages=find_packages(where="code"),
    package_dir={"": "code"},
    python_requires=">=3.11",
    install_requires=[
        "numpy>=1.26.0,<2.0.0",
        "pandas>=2.1.0,<3.0.0",
        "scipy>=1.11.0,<2.0.0",
        "scikit-learn>=1.3.0,<2.0.0",
        "transformers>=4.36.0,<5.0.0",
        "accelerate>=0.25.0,<1.0.0",
        "peft>=0.7.0,<1.0.0",
        "datasets>=2.14.0,<3.0.0",
        "huggingface-hub>=0.19.0,<1.0.0",
        "bitsandbytes>=0.41.0,<1.0.0",
        "pyyaml>=6.0.0,<7.0.0",
        "pytest>=7.4.0,<8.0.0",
        "black>=23.0.0,<24.0.0",
        "ruff>=0.1.0,<1.0.0",
        "pytest-cov>=4.1.0,<5.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0,<8.0.0",
            "pytest-cov>=4.1.0,<5.0.0",
            "black>=23.0.0,<24.0.0",
            "ruff>=0.1.0,<1.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "run-lint=scripts.run_lint:main",
            "run-format=scripts.run_format:main",
        ]
    },
)
