from setuptools import setup, find_packages

setup(
    name="llmxive-follow-up-extending-qwen-image-v",
    version="0.1.0",
    packages=find_packages(where="."),
    package_dir={"": "."},
    install_requires=[
        "torch",
        "transformers",
        "scikit-learn",
        "pandas",
        "opencv-python",
        "paddleocr",
        "pillow",
        "numpy",
        "pytest",
    ],
    python_requires=">=3.11",
)
