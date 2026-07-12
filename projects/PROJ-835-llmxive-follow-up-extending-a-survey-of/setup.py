from setuptools import setup, find_packages

setup(
    name="llmxive-follow-up",
    version="0.1.0",
    packages=find_packages(where="code"),
    package_dir={"": "code"},
    python_requires=">=3.11",
    install_requires=[
        "torch==2.3.0",
        "transformers==4.41.0",
        "scikit-learn==1.5.0",
        "pandas==2.2.2",
        "soundfile==0.12.1",
        "datasets==2.19.1",
    ],
)