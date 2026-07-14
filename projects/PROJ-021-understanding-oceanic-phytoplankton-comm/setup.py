from setuptools import setup, find_packages

setup(
    name="phytoplankton-analysis",
    version="0.1.0",
    packages=find_packages(where="code"),
    package_dir={"": "code"},
    install_requires=[
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "scikit-learn>=1.3.0",
        "torch>=2.0.0",
        "transformers>=4.30.0",
        "xarray>=2023.1.0",
        "netCDF4>=1.6.0",
        "matplotlib>=3.7.0",
        "seaborn>=0.12.0",
        "datasets>=2.14.0",
    ],
    python_requires=">=3.11",
)