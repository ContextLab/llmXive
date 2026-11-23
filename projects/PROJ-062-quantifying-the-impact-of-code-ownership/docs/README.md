# PROJ-062: Quantifying the Impact of Code Ownership on Software Quality

## Overview

This project implements an automated pipeline to analyze the relationship between code ownership (measured via Gini coefficients) and software quality metrics (bugs, complexity, churn) across multiple open-source repositories.

## Research Question

Does high code ownership (low Gini coefficient) correlate with better software quality?

## Project Structure

```
PROJ-062-quantifying-the-impact-of-code-ownership/
├── code/ # Source code
│ ├── config.py # Configuration and environment variables
│ ├── data_collection.py # Git cloning, commit parsing, issue fetching
│ ├── metrics_calc.py # Gini, churn, complexity, bug density calculations
│ ├── statistical_analysis.py # Correlation, VIF, non-linearity tests
│ ├── visualizations.py # Scatter plots and regression lines
│ ├── main.py # Pipeline orchestration
│ ├── utils/ # Utility modules
│ │ ├── backoff.py # Exponential backoff for API retries
│ │ ├── path_normalizer.py # Path normalization per FR-009
│ │ ├── logging_utils.py # Logging configuration
│ │ ├── memory_utils.py # Memory management utilities
│ │ └── api_utils.py # API request utilities
│ └── scripts/ # Helper scripts
├── data/
│ ├── raw/ # Cloned repositories (gitignore'd)
│ ├── intermediate/ # Processing artifacts (ownership CSVs versioned)
│ └── results/ # Final analysis outputs
├── docs/ # Documentation
│ └── README.md # This file
├── specs/
│ └── 001-code-ownership-analysis/
│ ├── plan.md # Implementation plan
│ ├── spec.md # Feature specification
│ ├── research.md # Research methodology
│ └── data-model.md # Data model definitions
├── tests/ # Test suite
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
├── requirements.txt # Python dependencies
├──.gitignore # Git ignore rules
└── README.md # Project root readme
```

## Quick Start

### Prerequisites

- Python 3.11+
- Git (for repository cloning)
- GitHub API token (optional, for rate limit bypass)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd PROJ-062-quantifying-the-impact-of-code-ownership

# Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Set environment variables in `.env` or export them:

```bash
export GITHUB_TOKEN=your_token_here
export CUTOFF_DATE=2024-01-01
export DEPTH_LIMIT=1000
export REPO_LIST=repo1,repo2,repo3
export RANDOM_SEED=42
```

### Running the Pipeline

```bash
# Run the full pipeline
python code/main.py

# Or run individual stages:
python code/data_collection.py
python code/metrics_calc.py
python code/statistical_analysis.py
python code/visualizations.py
```

### Output Files

The pipeline generates:

- `data/intermediate/ownership.csv` - Ownership attribution per module
- `data/results/metrics.csv` - Calculated metrics per module
- `data/results/correlation_results.csv` - Spearman correlation results
- `data/results/sensitivity_pvalue.csv` - P-value sensitivity analysis
- `data/results/sensitivity_rho.csv` - Correlation magnitude sensitivity
- `data/results/final_report.json` - Comprehensive analysis report
- `figures/*.png` - Visualization plots (300+ DPI)

## Methodology

### Data Collection (User Story 1)

1. Clone repositories with shallow history (depth=1000 or full history if <1000)
2. Parse commit logs to extract author, timestamp, and file paths
3. Fetch GitHub issues for bug tracking (time window T+1)
4. Link issues to modules using path-based proximity (FR-009)

### Metric Calculation (User Story 2)

1. **Gini Coefficient**: Measure ownership concentration per module
2. **Code Churn**: Lines added/deleted per module
3. **Cyclomatic Complexity**: Using Radon (exclude non-Python files)
4. **Bug Density**: Normalized bugs per KLOC
5. **Module Size & Age**: KLOC and months since creation

### Statistical Analysis (User Story 3)

1. **Spearman Correlation**: Gini vs. bug density
2. **VIF Diagnostics**: Check for multicollinearity (exclude Gini² due to mathematical collinearity)
3. **Non-linearity Test**: Likelihood Ratio Test comparing linear vs. quadratic models
4. **Sensitivity Analysis**: Sweep p-value cutoffs {0.01, 0.05, 0.1} and correlation magnitudes {0.2, 0.3, 0.4}
5. **Multiple Comparison Correction**: Bonferroni or Benjamini-Hochberg

## Key Findings

*See `data/results/final_report.json` for complete results.*

### Associational Framing

All findings are explicitly framed as **associational rather than causal** (FR-010). This project identifies correlations between code ownership patterns and software quality metrics but does not claim causal relationships.

## Reproducibility

- **Random Seed**: Fixed at 42 (configurable via `RANDOM_SEED` environment variable)
- **Version Control**: Ownership attribution CSVs are version-controlled per Constitution Principle VI
- **State Management**: Content hashes recorded in `state/` directory

## Testing

```bash
# Run unit tests
python -m pytest tests/unit/ -v

# Run integration tests
python -m pytest tests/integration/ -v

# Run full test suite
python -m pytest tests/ -v
```

## Dependencies

See `requirements.txt` for the complete list:
- GitPython
- scikit-learn
- scipy
- pandas
- numpy
- radon
- matplotlib
- pyyaml
- requests

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

MIT License - See LICENSE file for details.

## Acknowledgments

This research was conducted as part of the llmXive automated science pipeline.
