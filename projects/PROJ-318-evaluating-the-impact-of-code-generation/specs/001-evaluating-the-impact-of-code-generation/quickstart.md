# Quickstart Guide: Evaluating the Impact of Code Generation Models

This guide provides step-by-step instructions to execute the full research pipeline for evaluating code generation models on documentation completeness.

## Prerequisites

- Python 3.9+
- 16GB+ RAM (32GB recommended for model loading)
- CUDA-enabled GPU (optional, for faster generation)
- Git installed and configured

## 1. Environment Setup

### 1.1 Initialize Project Structure

Run the setup script to create all necessary directories:

```bash
bash scripts/setup.sh
```

Verify the structure was created:

```bash
cat logs/setup.log
```

### 1.2 Install Dependencies

```bash
pip install -r code/requirements.txt
```

### 1.3 Verify Configuration

Ensure seeds are pinned and configuration is correct:

```bash
python code/verify_seed.py
python code/verify_seed.py # Run twice to confirm reproducibility
```

## 2. Data Extraction (User Story 1)

This phase extracts method signatures and human-written docstrings from 20 top PyPI repositories.

### 2.1 Fetch Repository List

Generate the frozen list of 20 top repositories:

```bash
python code/utils/repo_fetcher.py
```

**Output**: `data/raw/frozen_repo_list.json` (exactly 20 entries)

### 2.2 Clone Repositories

Clone the selected repositories to the local cache:

```bash
python code/utils/git_clone.py
```

**Output**: Repositories in `data/raw/repos/`

### 2.3 Extract Methods and Docstrings

Run the extraction pipeline to parse ASTs and collect documentation:

```bash
python code/extract.py
```

**Outputs**:
- `data/raw/repos/{repo_slug}.json` for each repository
- `state/projects/PROJ-318-evaluating-the-impact-of-code-generation.yaml` (updated with SHA-256 hashes)

**Verification**: Check that each JSON file contains `method_signature`, `human_docstring`, and `ast_params`.

## 3. Docstring Generation (User Story 2)

This phase uses a quantized LLM to generate docstrings for the extracted methods.

### 3.1 Generate Docstrings

Run the generation pipeline with strict 4-bit quantization:

```bash
python code/generate.py
```

**Outputs**:
- `data/processed/generation_batch_{repo_slug}.json`

**Constraints**:
- Max 1,000 methods per repository
- 4-bit quantization enforced (no fallback)
- Memory monitoring active (aborts if RAM > 7GB)

### 3.2 Post-Processing

Flag empty or whitespace-only generated docstrings:

```bash
python code/post_process.py
```

**Output**: `data/processed/generation_batch_{repo_slug}_cleaned.json`

### 3.3 Aggregate Results

Consolidate all batch files into a single dataset:

```bash
python code/aggregate.py
```

**Output**: `data/processed/results.json`

**Verification**: Ensure total rows <= 20,000 and per-repo rows <= 1,000.

## 4. Statistical Analysis (User Story 3)

This phase calculates coverage scores and performs statistical testing.

### 4.1 Calculate Parameter Coverage

Compute the parameter coverage score for each method:

```bash
python code/analyze.py --step=coverage
```

**Output**: `data/processed/results_with_coverage.json`

**Metrics**: `coverage_score` (float) for each record.

### 4.2 Calculate Semantic Similarity

Compute semantic similarity between human and generated docstrings:

```bash
python code/analyze.py --step=similarity
```

**Output**: `data/processed/results_with_scores.json`

**Metrics**: `semantic_similarity` (float) appended to existing records.

### 4.3 Statistical Significance Testing

Perform Wilcoxon signed-rank test on coverage scores:

```bash
python code/analyze.py --step=stats
```

**Output**: `data/processed/results_with_stats.json`

**Metrics**: `p_value`, `test_statistic`, `is_significant`.

### 4.4 Generate Final Report

Compile the final research report:

```bash
python code/analyze.py --report
```

**Output**: `data/processed/final_report.json`

**Contents**:
- Overall coverage rates
- Statistical test results
- Key findings summary

## 5. Verification and Reproducibility

### 5.1 Verify Artifact Hashes

Ensure all artifacts match the recorded state:

```bash
bash scripts/verify_repro.sh
```

### 5.2 Run Unit Tests

Execute the full test suite:

```bash
pytest tests/ -v
```

## Troubleshooting

- **Memory Limit Exceeded**: The pipeline automatically aborts if RAM usage exceeds 7GB. Reduce batch size or use a machine with more memory.
- **Quantization Failure**: If 4-bit quantization fails, the script will abort immediately. Ensure `bitsandbytes` is correctly installed and CUDA is available.
- **Missing Data Files**: Ensure all previous steps have completed successfully. Each step depends on the output of the previous one.

## Next Steps

- Review `data/processed/final_report.json` for key insights
- Analyze specific repositories in `data/processed/`
- Extend the pipeline with additional models or metrics