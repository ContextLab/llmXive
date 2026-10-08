# Evaluating the Impact of Code Generation Models on Code Documentation Completeness

This project evaluates how code generation models (specifically `Salesforce/codegen-350M-mono` in 4-bit quantization) impact the completeness of code documentation by comparing human-written docstrings against LLM-generated ones.

## Prerequisites

- Python 3.9+
- Git
- 16GB+ RAM (for model loading and generation)
- CUDA-compatible GPU recommended (optional, but speeds up generation)

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd <project-root>
 ```

2. **Set up the project structure**:
 ```bash
 bash scripts/setup.sh
 ```

3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

4. **Verify seed reproducibility** (optional but recommended):
 ```bash
 python code/verify_seed.py
 ```

## Configuration

Edit `code/config.py` to adjust:
- `SEED`: Random seed for reproducibility (default: 42)
- `MAX_METHODS`: Maximum number of methods per repository (default: 1000)
- `MODEL_NAME`: Model to use for generation (default: `Salesforce/codegen-350M-mono`)
- `TEMPERATURE`: Generation temperature (default: 0.7)

## Usage

### Step 1: Repository Data Extraction (User Story 1)

Extract public method signatures and docstrings from top PyPI repositories.

```bash
python code/extract.py
```

**Output**: `data/raw/repos/{repo_slug}.json` for each repository in `data/raw/frozen_repo_list.json`.

### Step 2: LLM Docstring Generation (User Story 2)

Generate docstrings for extracted methods using the quantized model.

```bash
python code/generate.py --input-dir data/raw/repos --output-dir data/processed
```

**Output**: `data/processed/generation_batch_{repo_slug}.json` and `data/processed/generation_batch_{repo_slug}_cleaned.json`.

### Step 3: Analysis (User Story 3)

Run the full analysis pipeline to calculate coverage scores, semantic similarity, and statistical significance.

```bash
# Calculate coverage scores
python code/analyze.py --step=coverage

# Calculate semantic similarity
python code/analyze.py --step=similarity

# Run Wilcoxon statistical test
python code/analyze.py --step=stats

# Generate final report
python code/analyze.py --report
```

**Output**: `data/processed/results_with_coverage.json`, `data/processed/results_with_scores.json`, `data/processed/results_with_stats.json`, and `data/processed/final_report.json`.

## Project Structure

```
.
├── code/
│ ├── analyze.py # Analysis pipeline (coverage, similarity, stats, report)
│ ├── aggregate.py # Aggregates generation batches
│ ├── config.py # Configuration and seed pinning
│ ├── extract.py # Repository data extraction
│ ├── generate.py # LLM docstring generation
│ ├── post_process.py # Post-processing (empty docstring handling)
│ ├── utils/
│ │ ├── ast_parser.py # AST parsing utilities
│ │ ├── config.py # Configuration loading
│ │ ├── coverage.py # Coverage calculation
│ │ ├── exceptions.py # Custom exceptions
│ │ ├── file_walker.py # File walking utilities
│ │ ├── git_clone.py # Git repository cloning
│ │ ├── model_loader.py # Model loading with 4-bit quantization
│ │ ├── models.py # Data models
│ │ ├── monitor.py # Memory monitoring
│ │ ├── repo_fetcher.py # Repository list fetching
│ │ ├── repo_loader.py # Repository list loading
│ │ ├── similarity.py # Semantic similarity calculation
│ │ └── stats.py # Statistical testing
│ └── requirements.txt # Dependencies
├── data/
│ ├── raw/
│ │ ├── frozen_repo_list.json # Frozen list of 20 top PyPI repos
│ │ ├── repo_list.json # Copy of frozen list
│ │ └── repos/ # Extracted method data per repo
│ └── processed/ # Generated docstrings and analysis results
├── logs/ # Execution logs
├── scripts/
│ └── setup.sh # Project setup script
├── specs/
│ └── 001-evaluating-the-impact-of-code-generation/
│ ├── data-model.md # Data schema definitions
│ └──...
├── state/
│ └── projects/
│ └── PROJ-318-evaluating-the-impact-of-code-generation.yaml # Artifact hashes
├── tests/
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
├── README.md # This file
└── quickstart.md # Step-by-step execution guide
```

## Testing

Run all tests:
```bash
pytest tests/
```

Run specific test suites:
```bash
pytest tests/unit/
pytest tests/integration/
```

## Reproducibility

All random seeds are pinned in `code/config.py`. To verify reproducibility:
```bash
python code/verify_seed.py
python code/verify_seed.py # Run again; output should be identical
```

## License

[Insert License Here]