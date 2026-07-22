# Evaluating the Effectiveness of LLMs for Detecting Code Smells

This project implements an automated pipeline to evaluate how well Large Language Models (LLMs) detect code smells compared to static analysis tools (Pylint, Radon).

## Project Structure

- `code/`: Python modules for data pipeline, semantic analysis, and statistical evaluation.
- `data/raw/`: Raw data downloaded from HuggingFace (`codeparrot/github-code`).
- `data/processed/`: Intermediate and final processed datasets.
- `results/`: Statistical analysis outputs, reports, and metrics.
- `tests/`: Unit and contract tests.

## Prerequisites

- Python 3.11+
- pip

## Installation

1. Clone the repository and navigate to the project root.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage Instructions

The pipeline consists of three main stages corresponding to the User Stories.

### Stage 1: Data Pipeline & Static Baseline (User Story 1)

Generates a sample of functions, computes structural metrics (LOC, Cyclomatic Complexity), and runs Pylint to establish a static baseline.

```bash
python code/data_pipeline.py
```

**Output**: `data/static_baseline.csv` containing code snippets, metrics, and normalized static smell labels.

### Stage 2: Semantic Analysis & LLM Inference (User Story 2)

Computes semantic embeddings and runs a quantized LLM (CodeLlama-7B-GGUF) to detect smells via natural language reasoning.

```bash
python code/semantic_analysis.py
```

**Output**: `data/processed/semantic_results.json` containing embeddings and LLM-generated smell labels.
**Metrics**: `results/resource_metrics.json` containing RAM/CPU usage per batch.

### Stage 3: Statistical Analysis (User Story 3)

Performs comparative analysis (McNemar's test, Logistic Regression with VIF, Sensitivity Analysis) to evaluate LLM effectiveness.

```bash
python code/statistical_analysis.py
```

**Outputs**:
- `results/statistical_significance.json`: McNemar's test p-values.
- `results/logistic_regression.json`: Regression coefficients and VIF scores.
- `results/sensitivity_report.md`: Detailed sensitivity analysis report.

## Validation

Run the verification script to ensure all outputs meet completeness requirements:

```bash
python code/verify_results.py
```

## Linting and Formatting

To ensure code quality, run the linting checks defined in `code/linting_config.py`:

```bash
python code/linting_config.py
```

## License

MIT License