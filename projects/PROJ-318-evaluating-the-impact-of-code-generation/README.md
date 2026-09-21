# Evaluating the Impact of Code Generation Models on Code Documentation Completeness

This project implements an automated pipeline to evaluate how code generation models (specifically `Salesforce/codegen-350M-mono`) affect the completeness of code documentation. It extracts public method signatures and human-written docstrings from top PyPI repositories, generates docstrings using a quantized LLM, and performs statistical analysis on parameter coverage.

## Prerequisites

- Python 3.9+
- PyTorch 2.1.0+
- CUDA-capable GPU (recommended for 4-bit quantization) or sufficient RAM for CPU inference

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. **Set up the project structure**:
 ```bash
 bash scripts/setup.sh
 ```

3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

4. **Verify reproducibility**:
 ```bash
 python code/verify_seed.py
 ```

## Usage

The pipeline is divided into three main user stories (phases). Execute them in order.

### Phase 1: Repository Data Extraction (US1)

Extract public methods and docstrings from 20 top PyPI repositories. [UNRESOLVED-CLAIM: c_bf79dfc4 — status=not_enough_info]

```bash
# 1. Fetch the list of top repositories
python code/utils/repo_fetcher.py

# 2. Clone repositories and extract methods
python code/extract.py --input data/raw/frozen_repo_list.json --output data/raw/repos
```

**Outputs**:
- `data/raw/repos/{repo_slug}.json`: Extracted method signatures and human docstrings.

### Phase 2: LLM Docstring Generation (US2)

Generate docstrings using the quantized CodeGen model.

```bash
# 1. Generate docstrings for all extracted methods
python code/generate.py --input-dir data/raw/repos --output-dir data/processed

# 2. Post-process to flag empty/whitespace docstrings
python code/post_process.py --input-dir data/processed --output-dir data/processed

# 3. Aggregate results
python code/aggregate.py --input-dir data/processed --output data/processed/results.json
```

**Outputs**:
- `data/processed/generation_batch_{repo_slug}_cleaned.json`: Cleaned generation results.
- `data/processed/results.json`: Aggregated dataset.

### Phase 3: Parameter Coverage Analysis (US3)

Calculate coverage scores and perform statistical analysis.

```bash
# 1. Calculate Parameter Coverage Scores
python code/analyze.py --step=coverage --input data/processed/results.json --output data/processed/results_with_coverage.json

# 2. Calculate Semantic Similarity
python code/analyze.py --step=similarity --input data/processed/results_with_coverage.json --output data/processed/results_with_scores.json

# 3. Run Wilcoxon Signed-Rank Test
python code/analyze.py --step=stats --input data/processed/results_with_scores.json --output data/processed/results_with_stats.json

# 4. Generate Final Report
python code/analyze.py --report --input data/processed/results_with_stats.json --output data/processed/final_report.json
```

**Outputs**:
- `data/processed/results_with_coverage.json`: Results with coverage scores.
- `data/processed/results_with_scores.json`: Results with semantic similarity.
- `data/processed/results_with_stats.json`: Statistical test results.
- `data/processed/final_report.json`: Final summary report.

## Configuration

- **Random Seed**: Defined in `code/config.py` (default: 42).
- **Max Methods per Repo**: Defined in `code/config.py` (default: 1000).
- **Quantization**: 4-bit quantization is enforced by default. No fallback is allowed.

## Testing

Run unit and integration tests:

```bash
pytest tests/unit/
pytest tests/integration/
```

## Project Structure

```
.
├── code/
│ ├── analyze.py
│ ├── aggregate.py
│ ├── config.py
│ ├── extract.py
│ ├── generate.py
│ ├── post_process.py
│ ├── utils/
│ │ ├── ast_parser.py
│ │ ├── model_loader.py
│ │ ├── monitor.py
│ │ ├── repo_fetcher.py
│ │ └──...
│ └── requirements.txt
├── data/
│ ├── raw/
│ │ ├── frozen_repo_list.json
│ │ └── repos/
│ └── processed/
├── logs/
├── state/
├── tests/
├── scripts/
│ └── setup.sh
└── README.md
```

## License

[Insert License Here]