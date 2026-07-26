# PROJ-877: llmXive Follow-up - Extending Mellum2 Technical Report

## Overview
This project implements an automated research pipeline to investigate the relationship between static code complexity metrics and the prediction loss (perplexity) of Large Language Models (LLMs).
Building on the "Mellum2" technical report, this study aims to:
1. Quantify the correlation between structural complexity (cyclomatic complexity, nesting depth) and LLM inference loss.
2. Identify non-linear thresholds where this relationship shifts.
3. Validate findings using statistical significance testing (permutation tests) and cross-language validation (Python vs. Java).

## Key Objectives
- **Hypothesis**: Code complexity is positively correlated with LLM prediction loss, with potential non-linear thresholds.
- **Methodology**:
 - Data: `codeparrot/github-code` (Python/Java subsets).
 - Static Analysis: Tree-sitter and CodeQL for complexity metrics.
 - Inference: Frozen Mistral-7B (CPU-only) with n-gram normalization.
 - Analysis: Pearson/Spearman correlation, Piecewise Regression, Permutation Tests.

## Project Structure
```
.
├── code/ # Source code
│ ├── analysis/ # Statistical analysis & visualization
│ ├── contracts/ # Data schemas
│ ├── data/ # Data loading, preprocessing, checksumming
│ ├── inference/ # LLM inference engine
│ ├── utils/ # Logging, timeout, env config
│ ├── config.py # Global configuration
│ └── main.py # Pipeline orchestration
├── data/ # Data artifacts
│ ├── raw/ # Raw downloaded datasets
│ ├── processed/ # Preprocessed and annotated data
│ └── results/ # Analysis outputs (JSON, PNG)
├── tests/ # Unit and integration tests
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Prerequisites
- Python 3.9+
- Hugging Face Hub access (token required for dataset/model access)
- CPU-only execution (GPU support explicitly excluded per constraints)

## Setup
1. **Clone & Install**:
 ```bash
 pip install -r requirements.txt
 ```
2. **Configure Environment**:
 Create a `.env` file in the root directory:
 ```
 HF_TOKEN=your_huggingface_token_here
 ```
3. **Run Feasibility Check**:
 Before downloading large datasets, run the feasibility check to determine the maximum sample size within the 6-hour compute limit:
 ```bash
 python code/analysis/feasibility.py
 ```

## Execution
Run the full pipeline (or specific stages) via `code/main.py`:
```bash
python code/main.py --stage full
```
Available stages: `feasibility`, `download`, `preprocess`, `ngram`, `inference`, `correlation`, `threshold`, `stats`, `validation`.

## Output Artifacts
- `data/results/us1_correlation_stats.json`: Correlation coefficients (Pearson/Spearman).
- `data/results/us1_correlation_plot.png`: Scatter plots with regression lines.
- `data/results/us2_threshold_candidates.json`: Detected complexity thresholds.
- `data/results/us3_validation.json`: Benchmark validation results.

## License
Research project for academic purposes.