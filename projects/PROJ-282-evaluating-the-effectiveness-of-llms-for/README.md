# llmXive: Evaluating the Effectiveness of LLMs for Identifying Security Vulnerabilities in Open-Source Code

**Project ID**: PROJ-282
**Status**: Pipeline Implementation Complete

## Overview

This project implements an automated scientific pipeline to evaluate the effectiveness of Large Language Models (LLMs) in identifying security vulnerabilities in open-source code. The pipeline ingests real-world vulnerability datasets (VulDeePecker, JSVulnDB, NIST Juliet), extracts structural and semantic features, runs zero-shot LLM inference, compares results against static analysis baselines, and performs rigorous statistical analysis.

## Key Features

- **Real Data Ingestion**: Strict loaders for VulDeePecker, JSVulnDB, and NIST Juliet datasets. No synthetic data fallbacks.
- **CPU-Optimized Inference**: Dynamic batch sizing and memory monitoring for CPU-only environments.
- **Multi-Modal Feature Extraction**: AST-based structural features, cyclomatic complexity, and semantic embeddings.
- **Statistical Rigor**: Logistic regression, McNemar's test, and correlation analysis with multiple-comparison correction.
- **Reproducibility**: Deterministic seeds, artifact hashing, and comprehensive logging.

## Project Structure

```
.
├── code/
│ ├── src/
│ │ ├── data/ # Ingestion, preprocessing, feature extraction
│ │ ├── models/ # LLM inference, static analyzers, data models
│ │ ├── analysis/ # Statistical analysis, metrics, reporting
│ │ ├── utils/ # Configuration, logging, memory monitoring
│ │ └── orchestration/ # Pipeline DAG management
│ ├── scripts/ # Executable entry points for tasks
│ └── tests/ # Unit and integration tests
├── data/
│ ├── raw/ # Downloaded source datasets
│ ├── processed/ # Cleaned, parsed, and feature-engineered data
│ ├── results/ # Model predictions, metrics, visualizations
│ └── logs/ # Execution logs, checksums, verification reports
├── state/ # Pipeline state tracking
├── contracts/ # Data schemas (Pydantic)
├── research.md # Final research report
└── requirements.txt # Python dependencies
```

## Prerequisites

- Python 3.9+
- System packages: `build-essential`, `git`
- CPU-only environment (GPU detection aborts execution)

## Installation

1. **Clone and Setup**
 ```bash
 git clone <repository-url>
 cd <project-root>
 ```

2. **Install Dependencies**
 ```bash
 pip install -r requirements.txt
 ```

 *Note: This project requires `transformers`, `torch` (CPU version recommended), `tree-sitter`, `radon`, `statsmodels`, and `pandas`.*

3. **Configure Environment**
 - Ensure sufficient RAM (minimum 8GB recommended for batch processing).
 - The pipeline automatically detects CPU-only mode and adjusts batch sizes accordingly.

## Usage

### Full Pipeline Execution

To run the complete research pipeline from data ingestion to final report:

```bash
python code/src/main.py
```

This executes the DAG defined in `src/orchestration/orchestrator.py`, covering:
1. Data Ingestion (VulDeePecker, JSVulnDB, Juliet)
2. Preprocessing & Stratified Sampling
3. Feature Extraction (Structural, Semantic, Embeddings)
4. Zero-Shot LLM Inference
5. Static Analyzer Baseline (Bandit, Cppcheck)
6. Statistical Analysis & Reporting

### Individual Task Execution

Specific pipeline stages can be executed independently via scripts in `code/scripts/`:

- **Data Ingestion**: `python code/scripts/run_download_vuldeepecker.py`, `run_download_jsvulndb.py`, `run_download_juliet.py`
- **Feature Extraction**: `python code/scripts/run_feature_extraction.py`
- **Inference**: `python code/scripts/run_llm_inference.py`
- **Analysis**: `python code/scripts/run_analysis.py`

### Verification & Testing

- **Unit Tests**: `pytest code/tests/unit/`
- **Linting**: `python code/scripts/verify_linting_config.py`
- **Artifact Hashing**: `python code/scripts/run_hash_artifacts.py`

## Reproducibility

This pipeline enforces strict reproducibility standards:

- **Deterministic Seeds**: All random operations use seeds defined in `src/utils/config.py`.
- **Artifact Hashing**: All output files are checksummed via `src/utils/hash_artifacts.py`.
- **Strict Data Loading**: No synthetic data fallbacks. If real data cannot be fetched, the pipeline fails loudly.
- **State Tracking**: Pipeline state is persisted in `state/projects/PROJ-282-*.yaml`.

## Data Sources

- **VulDeePecker**: Python vulnerability dataset (via Hugging Face Datasets)
- **JSVulnDB**: JavaScript vulnerability dataset
- **NIST Juliet**: C/C++ test cases for secure coding
- **NVD**: National Vulnerability Database for reference patterns

## Statistical Methods

- **Performance Metrics**: Precision, Recall, F1, ROC-AUC
- **Regression**: Logistic Regression (McFadden's & Nagelkerke R²)
- **Comparison**: McNemar's Test for LLM vs. Static Analyzer
- **Correction**: Bonferroni adjustment for multiple comparisons

## License

[Project License]

## Contributing

See `docs/CONTRIBUTING.md` for guidelines on adding new datasets, models, or analysis modules.
