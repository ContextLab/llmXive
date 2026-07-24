# llmXive: Extending FastContext

This project implements an automated scientific pipeline to evaluate the performance of a lightweight context explorer (`FastContext-Lite`) against the original `FastContext` (4B) baseline on repositories with varying structural regularity.

## Overview

The research investigates whether code repositories with "regular" structures (standard directory layouts, consistent import patterns) yield better context retrieval and exploration performance for coding agents compared to "irregular" repositories.

### Key Features
- **Static Analysis**: Scores repositories based on directory structure, test presence, and import patterns.
- **Stratification**: Splits datasets into "Regular" and "Irregular" sets based on structural scores.
- **FastContext-Lite**: A CPU-efficient, deterministic TF-IDF based context explorer.
- **Baseline Execution**: Runs the original FastContext (4B) model (CPU-only) for comparison.
- **Statistical Analysis**: Performs paired t-tests/Wilcoxon tests and regression analysis to quantify performance boundaries.

## Prerequisites

- Python 3.11+
- pip package manager
- 7GB+ RAM (for baseline execution)
- CPU-only environment (No CUDA required)

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd projects/PROJ-905-llmxive-follow-up-extending-fastcontext
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

4. **Initialize project structure** (if not already done):
 ```bash
 python code/setup_project.py
 ```

## Usage

### 1. Download Data
Fetch the `SWE-bench_Lite` dataset and extract ground truth annotations.
```bash
python code/data_loader.py
python code/annotation_extractor.py
```
*Outputs*: `data/raw/ground_truth_annotations.csv`

### 2. Static Analysis & Stratification
Calculate regularity scores and split the dataset.
```bash
python code/static_analysis.py
python code/stratification.py
```
*Outputs*: `data/processed/regularity_scores.csv`, `data/processed/regular_set.csv`, `data/processed/irregular_set.csv`

### 3. Run Experiments
Execute both the Lite pipeline and the Baseline on the stratified sets.
```bash
python code/main.py
```
*Outputs*: `data/results/exploration_logs.jsonl`

### 4. Statistical Analysis
Analyze the results to find performance boundaries and degradation.
```bash
python code/analysis.py
```
*Outputs*: `data/results/statistical_summary.json`

## Project Structure

```
.
├── code/
│ ├── analysis.py # Statistical analysis and regression
│ ├── annotation_extractor.py # Extracts ground truth from SWE-bench
│ ├── baseline_runner.py # Runs original FastContext (4B) model
│ ├── config.py # Configuration management
│ ├── data_loader.py # Downloads SWE-bench Lite
│ ├── fastcontext_lite.py # Lightweight TF-IDF explorer
│ ├── main.py # Experiment orchestration
│ ├── metrics_logger.py # Logs performance metrics
│ ├── static_analysis.py # Calculates regularity scores
│ ├── stratification.py # Splits datasets by score
│ ├── versioning.py # Artifact hashing
│ └── requirements.txt # Python dependencies
├── data/
│ ├── raw/ # Raw downloaded data & annotations
│ ├── processed/ # Scores and stratified splits
│ └── results/ # Experiment logs and stats
├── specs/
│ └── contracts/ # Feature specifications
├── state/ # Project state tracking
├── tests/ # Unit and integration tests
└── README.md
```

## API Reference

### Static Analysis (`code/static_analysis.py`)
- `calculate_regularity_score(repo_path)`: Returns a score between 0.0 and 1.0.
- `analyze_repository(repo_path)`: Full analysis of a single repo.

### FastContext Lite (`code/fastcontext_lite.py`)
- `run_fastcontext_lite(issue, repo_path)`: Returns retrieved snippets and token count.
- `build_tfidf_index(files)`: Constructs the TF-IDF index for a repository.

### Analysis (`code/analysis.py`)
- `run_ttest(sets)`: Performs statistical significance testing.
- `calculate_regression_analysis(scores, metrics)`: Computes slope and R-squared.

## Contribution Guidelines

1. **Fork the project**.
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`).
3. **Commit your changes** (`git commit -m 'Add some amazing feature'`).
4. **Push to the branch** (`git push origin feature/amazing-feature`).
5. **Open a Pull Request**.

### Coding Standards
- Follow PEP 8 style guidelines.
- Use type hints for all function arguments and return values.
- Ensure all tests pass before submitting PRs: `pytest tests/`.
- Lint with Ruff: `ruff check code/`.

## License

This project is part of the llmXive research initiative. See the project root for license details.

## Acknowledgments

- Based on "FastContext: Training Efficient Repository Explorer for Coding Agents".
- Dataset: `princeton-nlp/SWE-bench_Lite`.
- Framework: llmXive automated science pipeline.