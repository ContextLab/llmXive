# llmXive Follow-up: Extending Mellum2 Technical Report

## Project Overview

This project implements an automated science pipeline to investigate the relationship between code complexity and prediction loss in Large Language Models (LLMs). It extends the findings of the "Mellum2 Technical Report" by performing rigorous correlation analysis, non-linear threshold detection, and statistical significance validation on a large corpus of real-world code.

## Core Objectives

1. **Correlation Analysis**: Quantify the relationship between static complexity metrics (cyclomatic complexity, nesting depth) and LLM prediction loss.
2. **Threshold Detection**: Identify structural thresholds where the complexity/loss relationship shifts using piecewise regression and change-point detection.
3. **Statistical Validation**: Perform permutation tests, power analysis, and cross-language validation to ensure robust findings.

## Project Structure

```
.
├── code/ # Source code
│ ├── analysis/ # Analysis logic (feasibility, correlation, stats, threshold)
│ ├── contracts/ # Data schemas and contracts
│ ├── data/ # Data processing (download, preprocess, checksum)
│ ├── inference/ # LLM inference engine
│ ├── utils/ # Utilities (logging, timeout, env)
│ ├── config.py # Configuration management
│ └── setup_directories.py# Directory setup
├── data/ # Data storage
│ ├── raw/ # Raw downloaded datasets
│ ├── processed/ # Processed and annotated data
│ └── results/ # Analysis outputs (stats, plots)
├── tests/ # Unit and integration tests
├──.gitignore # Git ignore rules
├──.env # Environment variables (HF_TOKEN)
├── pyproject.toml # Project dependencies and tool config (ruff, black)
└── README.md # This file
```

## Prerequisites

- Python 3.9+
- Hugging Face account with access to `codeparrot/github-code`
- Sufficient disk space for dataset caching (~50GB+)

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd PROJ-877-llmxive-follow-up-extending-mellum2-tech
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -e.
 ```

4. **Configure environment**:
 Create a `.env` file in the root directory:
 ```
 HF_TOKEN=your_huggingface_token_here
 ```

## Usage

### Run the Pipeline

The main orchestration script handles the full pipeline execution:

```bash
python code/main.py
```

This will execute the following stages in order:
1. Feasibility Check (T011)
2. Data Download (T015)
3. Preprocessing (T016)
4. Variance Check (T011b)
5. N-Gram Model Building (T018)
6. Inference (T017)
7. Correlation Analysis (T019)
8. Threshold Detection (T024-T027)
9. Statistical Validation (T029-T031)

### Run Tests

```bash
pytest tests/ -v
```

### Code Quality

Format code:
```bash
black code/ tests/
```

Lint code:
```bash
ruff check code/ tests/
```

## License

This project is part of the llmXive research initiative. See LICENSE for details.