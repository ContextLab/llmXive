# llmXive follow-up: extending "ResearchClawBench: A Benchmark for End-to-End Autonomous Scientific Re"

**Project ID**: PROJ-957-llmxive-follow-up-extending-researchclaw

## Overview
This project implements an automated science pipeline to evaluate autonomous agents on the ResearchClawBench dataset. It focuses on scaffolded protocol injection, dual-condition execution, and statistical decoupling analysis.

## Project Structure
```
.
├── assets/ # Templates and static assets
│ └── templates/
├── code/ # Source code
│ ├── src/
│ │ ├── agents/ # Agent implementations
│ │ ├── analysis/ # Statistical analysis
│ │ ├── cli/ # Command line interface
│ │ ├── data/ # Data loading and filtering
│ │ ├── scaffolding/ # Template injection and validation
│ │ ├── scoring/ # Rubric engine and scoring
│ │ └── utils/ # Utilities (checksum, logging, config)
│ └── tests/ # Test suite
├── data/ # Data artifacts
│ ├── raw/ # Raw dataset downloads
│ └── processed/ # Processed data subsets
├── docs/ # Documentation
├── results/ # Experiment outputs and logs
├── specs/ # Design documents
├── assets/ # Static assets
├── requirements.txt # Python dependencies
└── pyproject.toml # Project configuration
```

## Prerequisites
- Python 3.11+
- pip

## Installation
1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage
Run the main experiment:
```bash
python -m code.src.cli.run_experiment
```

## License
[Insert License]
