"""Setup configuration for llmXive Automation System"""

from setuptools import setup, find_packages
import os

# Read README for long description
readme_path = os.path.join(os.path.dirname(__file__), "..", "README.md")
with open(readme_path, "r", encoding="utf-8") as f:
    long_description = f.read()

# Core requirements
install_requires = [
    "transformers>=4.36.0",
    "torch>=2.0.0",
    "accelerate>=0.25.0",
    "huggingface-hub>=0.19.0",
    "PyGithub>=2.1.0",
    "click>=8.1.0",
    "bitsandbytes>=0.41.0",
    "einops>=0.7.0",
]

# Development requirements
dev_requires = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
    "mypy>=1.7.0",
    "sphinx>=7.0.0",
    "sphinx-rtd-theme>=1.3.0",
]

# Optional requirements for specific model types
extras_require = {
    "dev": dev_requires,
    "gguf": ["llama-cpp-python>=0.2.0"],
    "gptq": ["auto-gptq>=0.5.0"],
    "all": dev_requires + ["llama-cpp-python>=0.2.0", "auto-gptq>=0.5.0"],
}

setup(
    name="llmxive-automation",
    version="0.1.0",
    author="llmXive Contributors",
    author_email="noreply@github.com",
    description="Automated scientific discovery pipeline for llmXive",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ContextLab/llmXive",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=install_requires,
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "llmxive-auto=llmxive_automation.__main__:main",
        ],
    },
    include_package_data=True,
    package_data={
        "llmxive_automation": ["templates/*.txt", "prompts/*.json"],
    },
)