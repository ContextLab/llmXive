# Evaluating the Impact of Code Generation Models on Code Testability

**Project ID**: PROJ-294
**Status**: Research Pipeline Implementation

## Overview

This project implements an automated scientific research pipeline to evaluate how code generation models (specifically varying sizes and architectures like CodeGen-350M vs CodeLlama-7B) impact the **testability** of generated code.

We analyze metrics including:
- **Structural Complexity**: Cyclomatic Complexity, Halstead Volume
- **Functional Success**: Pass Rate on HumanEval test suites
- **Coverage**: Branch Coverage percentages
- **Statistical Significance**: Wilcoxon, McNemar, Fisher, and Permutation tests

## Quick Start

### Prerequisites

- Python 3.9+
- pip
- HuggingFace CLI (for dataset access)

### Installation

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

### Running the Pipeline

The pipeline is executed in stages. Ensure you have a valid HuggingFace token set in your environment (`HF_TOKEN`) if accessing gated models.

1. **Data Acquisition**:
 ```bash
 python code/download_data.py
 ```
 Downloads HumanEval, verifies integrity, and performs stratified sampling.

2. **Code Generation**:
 ```bash
 python code/generate_code.py
 ```
 Generates code using the configured model (default: CodeGen-350M) with retry logic.

3. **Metrics Analysis**:
 ```bash
 python code/analyze_metrics.py
 ```
 Computes complexity metrics and executes test suites to determine pass rates and coverage.

4. **Statistical Testing**:
 ```bash
 python code/statistical_tests.py
 ```
 Runs hypothesis tests (Wilcoxon, McNemar, etc.) and power analysis.

5. **Sensitivity Analysis** (Optional):
 ```bash
 python code/merge_sensitivity_metrics.py
 ```
 Integrates results from larger models (e.g., CodeLlama-7B) if available.

6. **Report Generation**:
 ```bash
 python code/report_generator.py
 ```
 Produces `results_report.md` with visualizations and statistical findings.

### Validation

To verify the pipeline end-to-end:
```bash
python code/validate_quickstart.py
```

## Project Structure

```text
.
├── code/
│ ├── download_data.py # Data acquisition and sampling
│ ├── generate_code.py # LLM inference and code generation
│ ├── analyze_metrics.py # Static analysis and test execution
│ ├── statistical_tests.py # Hypothesis testing and power analysis
│ ├── report_generator.py # Visualization and Markdown report
│ ├── merge_sensitivity_metrics.py # Sensitivity data integration
│ ├── utils.py # Logging, hashing, and utilities
│ ├── validate_citations.py # Reference validation agent
│ └── requirements.txt # Dependencies
├── data/
│ ├── raw/ # Downloaded datasets (HumanEval)
│ ├── generated/ # Generated code samples
│ └── analysis/ # Computed metrics (metrics.json)
├── results/
│ ├── figures/ # Plot outputs (PNG)
│ └──...
├── state/
│ └── artifact_hashes.yaml # Integrity tracking
├── tests/
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
├── docs/
│ └──...
└── README.md
```

## Key Artifacts

- **`data/analysis/metrics.json`**: The central dataset containing all metrics for every generated sample.
- **`results_report.md`**: The final scientific report with figures and statistical conclusions.
- **`state/artifact_hashes.yaml`**: SHA256 checksums for reproducibility and integrity verification.

## Contributing

This project follows the `tasks.md` workflow. New features should be implemented as independent user stories with corresponding tests.

## License

Research Code - See LICENSE for details.
