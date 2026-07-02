"""
Setup script for llmXive benchmark project.
"""
from setuptools import setup, find_packages
import os
import sys

def get_requirements():
    """Read requirements from requirements.txt."""
    req_file = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if not os.path.exists(req_file):
        return []
    with open(req_file, 'r', encoding='utf-8') as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.startswith('#')
        ]

if __name__ == '__main__':
    setup(
        name='llmxive-benchmark',
        version='0.1.0',
        description='Heterogeneous Scientific Foundation Model Collaboration Benchmark',
        author='llmXive Research Team',
        python_requires='>=3.11',
        packages=find_packages(where='.'),
        install_requires=get_requirements(),
        entry_points={
            'console_scripts': [
                'run-benchmark=src.benchmark.run_benchmark:main',
                'run-task=src.benchmark.run_task:main',
            ],
        },
        classifiers=[
            'Development Status :: 3 - Alpha',
            'Intended Audience :: Science/Research',
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python :: 3.11',
            'Programming Language :: Python :: 3.12',
        ],
    )
