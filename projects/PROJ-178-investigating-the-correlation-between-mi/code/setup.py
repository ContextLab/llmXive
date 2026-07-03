from setuptools import setup, find_packages

setup(
    name="mito-aging-correlation",
    version="0.1.0",
    packages=find_packages(where="."),
    python_requires=">=3.11",
    install_requires=[
        "scikit-learn>=1.3.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "scipy>=1.11.0",
        "vcfpy>=0.13.0",
        "haplogrep2>=2.3.0",
        "requests>=2.31.0",
        "tqdm>=4.65.0",
        "pyyaml>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "flake8>=6.1.0",
            "black>=23.0.0",
        ]
    },
)