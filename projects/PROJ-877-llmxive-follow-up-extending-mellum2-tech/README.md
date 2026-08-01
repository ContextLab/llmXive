# llmXive: Extending Mellum2 Technical Report

## Project Overview

This project implements an automated research pipeline to investigate the relationship between code complexity and prediction loss in Large Language Models (LLMs), extending the findings of the "Mellum2 Technical Report."

The pipeline performs the following steps:
1. **Feasibility Analysis**: Estimates required sample sizes and validates computational constraints.
2. **Data Acquisition**: Streams code chunks from the `codeparrot/github-code` dataset (Python and Java subsets).
3. **Preprocessing**: Annotates code with static analysis metrics (cyclomatic complexity, nesting depth) using CodeQL and Tree-sitter.
4. **Inference**: Runs frozen LLMs (Mistral-7B, with TinyLlama fallback) to compute token-level prediction loss, normalized by n-gram baselines (KenLM).
5. **Correlation & Threshold Detection**: Computes statistical correlations (Pearson/Spearman) and identifies non-linear structural thresholds using piecewise regression.
6. **Statistical Validation**: Performs permutation tests and power analysis to ensure result robustness.

## Setup Instructions

### Prerequisites
- Python 3.9+
- `kenlm` library (system-level installation required for n-gram modeling)
- `codeql` CLI (for static analysis)
- `tree-sitter` (system libraries)

### Installation
1. Clone the repository and navigate to the project root.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install Python dependencies:
 ```bash
 pip install -r requirements.txt
 ```
4. Configure environment variables by copying `.env.template` to `.env` and filling in your values:
 ```bash
 cp.env.template.env
 # Edit.env to add HF_TOKEN, etc.
 ```

## Usage

The pipeline is executed via the `code/main.py` CLI.

### Running the Full Pipeline
To execute the entire workflow from feasibility to final report:
```bash
python code/main.py --phase full
```

### Running Specific Phases
You can run specific stages independently:
```bash
# Feasibility and Power Analysis
python code/main.py --phase feasibility

# Download and Preprocess
python code/main.py --phase download
python code/main.py --phase preprocess

# Inference
python code/main.py --phase inference

# Analysis and Visualization
python code/main.py --phase analysis
```

### Configuration
All configuration is handled via `code/config.py` and the `.env` file. Key settings include the HuggingFace dataset name, model paths, and timeout constraints.

## Results Directory

All generated artifacts are stored under the `data/` directory within the project root:

- `data/raw/`: Raw downloads from external sources (if applicable).
- `data/processed/`: Intermediate artifacts including annotated JSONL files, KenLM models, and inference logs.
- `data/results/`: Final analysis outputs:
 - `feasibility_report.json`: Sample size calculations and constraints.
 - `us1_correlation_stats.json`: Correlation coefficients and p-values.
 - `us1_correlation_plot.png`: Visualization of complexity vs. loss.
 - `us2_threshold_candidates.json`: Detected breakpoints and sensitivity analysis.
 - `us3_permutation_pvalue.json`: Statistical significance results.

## License

This project is licensed under the MIT License. See the LICENSE file for details.