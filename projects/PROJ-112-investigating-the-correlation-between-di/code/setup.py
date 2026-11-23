from setuptools import setup, find_packages

setup(
    name="llmxive-proj-112",
    version="0.1.0",
    packages=find_packages(where="code"),
    package_dir={"": "code"},
    python_requires=">=3.11",
    install_requires=[
        "pandas==2.0.3",
        "scikit-learn==1.3.0",
        "scipy==1.11.1",
        "numpy==1.24.3",
        "requests==2.31.0",
        "pyyaml==6.0.1",
        "joblib==1.3.1",
        "miceforest==5.3.3",
        "rpy2==3.5.11",
    ],
    entry_points={
        "console_scripts": [
            "llmxive-main=src.main:main",
        ],
    },
)
