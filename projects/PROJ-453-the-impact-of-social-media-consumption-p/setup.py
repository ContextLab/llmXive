"""
Setup script for the Social Media Cognitive Flexibility project.
Enables installation as a package and running entry points.
"""
from setuptools import setup, find_packages
from pathlib import Path

def read_requirements():
    """Read dependencies from code/requirements.txt."""
    req_file = Path(__file__).parent / "code" / "requirements.txt"
    if not req_file.exists():
        return []
    with req_file.open("r", encoding="utf-8") as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]

def read_long_description():
    """Read project description from docs/README.md if available."""
    readme_file = Path(__file__).parent / "docs" / "README.md"
    if readme_file.exists():
        with readme_file.open("r", encoding="utf-8") as f:
            return f.read()
    return "Automated analysis of social media consumption patterns on cognitive flexibility."

setup(
    name="social-media-cognitive-flexibility",
    version="0.1.0",
    description="Analysis of social media consumption patterns on cognitive flexibility",
    long_description=read_long_description(),
    long_description_content_type="text/markdown",
    author="llmXive Research Team",
    packages=find_packages(where="code"),
    package_dir={"": "code"},
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": ["pytest", "ruff", "black"],
    },
    entry_points={
        "console_scripts": [
            "feasibility-check=00_feasibility_check:main",
            "setup-dirs=setup_directories:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)