from setuptools import setup, find_packages

setup(
    name="amorphous-silicon-heat-transport",
    version="0.1.0",
    packages=find_packages(where="code"),
    package_dir={"": "code"},
    install_requires=[
        "ase>=3.22.0",
        "networkx>=3.1",
        "scikit-learn>=1.3.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "matplotlib>=3.7.0",
        "requests>=2.31.0",
        "tqdm>=4.65.0",
        "pyyaml>=6.0.1",
        "python-dotenv>=1.0.0",
    ],
    python_requires=">=3.11",
)