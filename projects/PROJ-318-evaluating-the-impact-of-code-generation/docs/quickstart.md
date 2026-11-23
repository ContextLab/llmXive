# Quickstart Guide: Evaluating the Impact of Code Generation Models

This guide provides step-by-step instructions to execute the full research pipeline for evaluating the impact of code generation models on code documentation completeness.

## Prerequisites

- Python 3.9+
- Git
- ~14GB Disk Space (for model weights and data)
- ~7GB RAM (for inference with fallback logic)

## 1. Setup and Installation

### Create Project Structure
Run the following command to create the required directory hierarchy:
```bash
mkdir -p code code/utils data/raw/repos data/processed tests/unit tests/integration state logs
```

### Create Git Keep Files
Ensure version control tracks empty directories:
```bash
find code data tests state logs -type d -exec touch {}/.gitkeep \;
```

### Install Dependencies
Install the required Python packages:
```bash
pip install -r requirements.txt
```
*Note: `requirements.txt` includes `transformers`, `torch`, `bitsandbytes`, `sentence-transformers`, `docstring_parser`, `scipy`, `requests`, `pyyaml`, and `pytest`.*

## 2. Configuration and Seed Pinning

The project enforces strict reproducibility. Ensure `code/config.py` is configured with the correct model paths and random seeds.

Verify seed reproducibility before running the full pipeline:
```bash
python code/verify_seed_reproducibility.py
```
This script confirms that `numpy`, `random`, `torch`, and `transformers` seeds are pinned and produce identical outputs on repeated runs.

## 3. Phase 1: Repository Data Extraction (User Story 1)

This phase clones repositories, extracts method signatures, and prepares ground truth data.

### Step 3.1: Fetch Repository List
Generate a frozen, deterministic list of up to 20 top Python repositories:
```bash
python code/utils/repo_fetcher.py
```
**Output**: `data/raw/repo_list.json` (Contains `repo_url`, `github_url`, `star_count`).

### Step 3.2: Clone and Extract Methods
Run the extraction pipeline to clone repos and parse Python files:
```bash
python code/extract.py
```
**Actions**:
- Clones repositories from `data/raw/repo_list.json` into `data/raw/repos/`.
- Parses `.py` files using AST.
- Truncates method lists to a maximum of 1,000 methods per repository.
- Computes SHA-256 checksums for extracted data.
- Records artifact hashes in `state/projects/PROJ-318-evaluating-the-impact-of-code-generation.yaml`.

**Output**: `data/raw/repos/*.json` files containing method signatures and docstrings.

## 4. Phase 2: LLM Docstring Generation (User Story 2)

This phase generates docstrings using `Salesforce/codegen-350M-mono` with strict memory constraints.

### Step 4.1: Run Generation
Execute the generation script:
```bash
python code/generate.py
```
**Actions**:
- Loads the model in 4-bit quantization (with 8-bit/full precision fallback).
- Iterates over `data/raw/repos/*.json`.
- Generates docstrings with a fixed low temperature.
- Monitors RAM usage (aborts if > 7GB).
- Writes intermediate results to `data/processed/generation_batch_{repo_id}.json`.

### Step 4.2: Handle Empty Docstrings
Post-process results to flag empty or whitespace-only docstrings:
```bash
python code/handle_empty_docstrings.py --post-process
```
**Actions**:
- Calculates `coverage_score` as 0.0 for empty matches.
- Sets `needs_review` flag.
- Updates intermediate batch files.

### Step 4.3: Aggregate Results
Merge all batch files into a single dataset:
```bash
python code/aggregate.py
```
**Output**: `data/processed/results.json` (Consolidated data, max 20,000 rows).

## 5. Phase 3: Analysis and Reporting (User Story 3)

This phase calculates coverage scores, semantic similarity, and statistical significance.

### Step 5.1: Run Analysis
Execute the full analysis pipeline:
```bash
python code/analyze.py --report
```
**Actions**:
- Calculates Parameter Coverage Scores using `docstring_parser`.
- Computes Semantic Similarity using `sentence-transformers`.
- Runs Wilcoxon signed-rank test for Human vs. LLM scores.
- Logs warnings if sample size < 30.
- Generates the final report.

**Output**:
- `data/processed/results_with_scores.json` (Data with coverage and similarity scores).
- `data/processed/final_report.json` (Contains p-value, test statistic, coverage rates).

## 6. Verification

### Check Output Integrity
Verify the final report exists and contains expected fields:
```bash
cat data/processed/final_report.json
```

### Run Tests
Execute the unit and integration test suite:
```bash
pytest tests/
```

## Troubleshooting

- **OOM Errors**: The generation script automatically attempts 8-bit or full precision if 4-bit fails. If all fail, it raises `ModelLoadException`.
- **Memory Limit**: If RAM exceeds 7GB, the process logs `RAM_LIMIT_EXCEEDED` and aborts. Reduce batch size or run on a machine with more memory.
- **Missing Data**: Ensure `data/raw/repo_list.json` exists before running extraction.