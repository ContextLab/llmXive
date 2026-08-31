# Evaluating the Effectiveness of LLMs for Detecting Code Smells (PROJ-271)

This project evaluates whether Large Language Models (LLMs) can effectively detect code smells compared to traditional static analysis tools (Pylint, Radon).

## Features

- **Automated Data Pipeline**: Ingests code from `codeparrot/github-code` using HuggingFace datasets.
- **Static Analysis**: Computes LOC, Cyclomatic Complexity, and Nesting Depth using `radon`; detects smells using `pylint`.
- **Semantic Analysis**: Generates embeddings using `sentence-transformers` and detects smells using a quantized `CodeLlama-7B` LLM.
- **Statistical Analysis**: Performs McNemar's test, Logistic Regression (with VIF), and sensitivity analysis to compare methods.
- **Resource Monitoring**: Tracks RAM, CPU, and inference time per batch.

## Installation

### Prerequisites

- Python 3.11+
- pip
- 16GB+ RAM (for LLM inference)

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd PROJ-271-evaluating-the-effectiveness-of-llms-for

# Create virtual environment
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Quick Start

For a step-by-step guide, see [`quickstart.md`](quickstart.md).

### Running the Pipeline

1. **Initialize Directories**:
 ```bash
 python code/setup_directories.py
 ```

2. **Run Data Pipeline (User Story 1)**:
 ```bash
 python code/data_pipeline.py
 ```

3. **Run Semantic Analysis (User Story 2)**:
 ```bash
 python code/semantic_analysis.py
 ```

4. **Run Statistical Analysis (User Story 3)**:
 ```bash
 python code/statistical_analysis.py
 ```

5. **Validate Results**:
 ```bash
 python code/run_quickstart_validation.py
 ```

### CLI Arguments

Most scripts accept standard arguments. For example:

```bash
python code/data_pipeline.py --sample-size 1000 --seed 42
```

Use `--help` for detailed usage:

```bash
python code/data_pipeline.py --help
```

## Dependencies

Key dependencies (see `requirements.txt` for full list):

- `datasets`: For loading code from HuggingFace.
- `radon`: For structural metrics (LOC, Cyclomatic Complexity).
- `pylint`: For static smell detection.
- `sentence-transformers`: For semantic embeddings.
- `llama-cpp-python`: For running the quantized LLM.
- `scikit-learn`, `statsmodels`: For statistical analysis.
- `psutil`: For resource monitoring.

## Project Structure

```
PROJ-271/
├── code/ # Source code
│ ├── config.py # Configuration and paths
│ ├── data_pipeline.py # Data ingestion and static analysis
│ ├── semantic_analysis.py # Embeddings and LLM inference
│ ├── statistical_analysis.py # Statistical tests and reporting
│ ├── monitoring.py # Resource tracking
│ └──...
├── data/ # Data directories
│ ├── raw/ # Raw dataset (streamed)
│ └── processed/ # Processed results
├── results/ # Output reports and metrics
├── tests/ # Unit and integration tests
├── contracts/ # Schema and prompt definitions
├── requirements.txt # Dependencies
├── README.md # This file
└── quickstart.md # Step-by-step guide
```

## Validation

To ensure end-to-end reproducibility, run:

```bash
python code/run_quickstart_validation.py
```

This script checks for the existence and validity of all required output artifacts.

## License

[Insert License Here]
