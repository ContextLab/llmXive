from setuptools import setup, find_packages

setup(
    name="mito_aging_correlation",
    version="0.1.0",
    packages=find_packages(where="."),
    python_requires=">=3.11",
    install_requires=[
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "scipy>=1.10.0",
        "scikit-learn>=1.2.0",
        "vcfpy>=0.13.0",
        "haplogrep2>=3.0.0",
        "requests>=2.28.0",
        "tqdm>=4.65.0",
        "pyyaml>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ]
    },
    description="Investigating the Correlation Between Mitochondrial DNA Variation and Aging Rates",
)