from setuptools import setup, find_packages

setup(
    name="llmxive-follow-up",
    version="0.1.0",
    packages=find_packages(where="."),
    python_requires=">=3.11",
    install_requires=[
        "networkx>=3.2.1",
        "pandas>=2.1.0",
        "llama-cpp-python>=0.2.90",
        "statsmodels>=0.14.1",
        "sentence-transformers>=2.2.2",
        "pyyaml>=6.0.1",
        "huggingface_hub>=0.20.3",
    ],
)