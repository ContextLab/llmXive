# Quickstart Guide: Evaluating the Impact of Code Duplication on LLM Code Understanding

This guide provides step-by-step instructions for setting up, running, and validating the research pipeline.

## Project Overview

This project investigates the relationship between code duplication density and large language model (LLM) code understanding capabilities. The pipeline computes AST-based clone density metrics, measures model perplexity on duplicated vs. non-duplicated code, evaluates bug detection accuracy on HumanEval, and calculates Spearman rank correlations.

## Prerequisites

- Python 3.11+
- pip package manager
- 7GB+ available RAM (for 8-bit quantized model inference)
- Internet access (for HuggingFace dataset streaming)
- 24-hour runtime window for full corpus processing

## Quick Setup

1. **Clone and install dependencies:**
 ```bash
 cd projects/PROJ-261-evaluating-the-impact-of-code-duplication
 pip install -r requirements.txt
 ```

2. **Configure pre-commit hooks:**
 ```bash
 pre-commit install
 ```

3. **Verify directory structure:**
 ```bash
 python code/quickstart_validation.py validate_directory_structure
 ```

## Running the Pipeline

### Full Pipeline Execution

```bash
python code/main.py
```

This will:
- Stream 500MB of code from `codeparrot/github-code`
- Scan for PII patterns
- Compute AST clone density
- Calculate perplexity scores (8-bit quantized model)
- Evaluate bug detection on HumanEval
- Generate correlation results and visualizations

### Individual Stage Execution

For debugging or partial runs:
```bash
python code/data_loader.py # Stage 1: Download data
python code/pii_scanner.py # Stage 1: PII scan
python code/ast_cloner.py # Stage 2: Clone detection
python code/model_metrics.py # Stage 3: Perplexity computation
python code/bug_detection.py # Stage 4: Bug detection
python code/correlation_analysis.py # Stage 5: Correlation analysis
python code/visualization.py # Stage 6: Visualizations
```

## Parallel Execution Opportunities

The pipeline supports parallel execution at multiple levels to reduce wall-clock time:

### Task-Level Parallelism

| Phase | Parallel Tasks | Description |
|-------|----------------|-------------|
| Setup | T001-T005 | Project initialization, requirements, linting, documentation |
| Foundational | T006-T011 | Config, data dirs, logging, checksums, contracts, tests |
| US1 Tests | T012-T016c | All unit/integration tests can run in parallel |
| US2 Tests | T027-T030 | All unit/integration tests can run in parallel |
| US3 Tests | T037-T039 | All unit/integration tests can run in parallel |
| Validation | T024, T026, T035 | Performance and segment count validation |

### Stage-Level Parallelism

Once data is downloaded (T018), the following stages can run in parallel:

```
Data Download (T018)
 ↓
┌─────────────┬─────────────┐
│ Clone Detection │ Model Inference │
│ (T019) │ (T020) │
└─────────────┴─────────────┘
 ↓ ↓
└─────────── Join (T021) ───────────┘
```

**Implementation Note:** T019 (ast_cloner.py) uses stdlib only and has no external dependencies, making it ideal for parallel execution alongside T020 (model_metrics.py) which requires GPU memory.

### Sensitivity Analysis Parallelism

T040 performs sensitivity analysis across thresholds (0.7, 0.8, 0.9). Each threshold computation is independent and can be parallelized:

```bash
# Run threshold analyses in parallel
python code/correlation_analysis.py --threshold 0.7 &
python code/correlation_analysis.py --threshold 0.8 &
python code/correlation_analysis.py --threshold 0.9 &
wait
```

## Team Capacity Planning

### Recommended Team Size: 3-5 Developers

| Team Role | Tasks | Estimated Duration |
|-----------|-------|-------------------|
| Data Engineer | T018, T017, T022, T025 | 2-3 days |
| ML Engineer | T020, T023, T031, T032 | 3-4 days |
| QA Engineer | T012-T016c, T027-T030, T037-T039 | 2-3 days |
| Research Lead | T034, T040, T041, T043 | 2-3 days |
| DevOps | T001-T005, T006-T011, T045-T049 | 1-2 days |

### Parallel Workstreams

**Workstream A (Foundation):** DevOps team handles T001-T011 (1-2 days, fully parallelizable)

**Workstream B (US1):** Data Engineer + ML Engineer handle T018-T026 (3-4 days, T019 and T020 parallel)

**Workstream C (US2):** ML Engineer + QA Engineer handle T031-T036 (2-3 days)

**Workstream D (US3):** Research Lead + QA Engineer handle T040-T044 (2-3 days)

**Workstream E (Polish):** DevOps + Research Lead handle T045-T052 (1-2 days)

### Critical Path Analysis

The critical path (sequential dependencies) is:

```
T018 (download) → T019/T020 (parallel) → T021 (join) → T031 → T032 → T034 → T040 → T041 → T042
```

**Minimum wall-clock time:** ~10-12 days with 5 developers
**With 3 developers:** ~14-16 days
**With 1 developer:** ~25-30 days

### Resource Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| RAM | 7GB | 16GB+ |
| GPU | None (8-bit quantization) | 1× T4/V100 (faster inference) |
| Disk | 2GB | 10GB+ (for datasets and outputs) |
| Network | 500MB download | High-bandwidth for streaming |

## Output Artifacts

After successful execution, verify these files exist:

| Path | Description |
|------|-------------|
| `data/raw/github-code-sample.csv` | Raw dataset |
| `data/processed/clone_metrics.csv` | Clone density per file |
| `data/processed/perplexity_scores.csv` | Perplexity per file |
| `data/analysis/correlation_results.csv` | Spearman correlation with p-values |
| `data/analysis/figures/*.png` | Scatter plots (PNG) |
| `data/analysis/figures/*.pdf` | Scatter plots (PDF) |
| `data/parse_failures.csv` | Parse error log |
| `data/checksum_manifest.json` | Artifact checksums |

## Validation

Run the validation script to ensure reproducibility:

```bash
python code/quickstart_validation.py
```

This validates:
- Configuration documentation completeness
- Directory structure integrity
- Checksum manifest consistency
- Output file existence
- Quickstart step correctness

## Performance Constraints

- **SC-001:** Full pipeline must complete within 24 hours (T024 validates)
- **SC-002:** Memory usage must stay under 7GB (T023 validates)
- **SC-003:** At least 1000 valid code segments (T026 validates)
- **SC-004:** Statistical significance p < 0.05 (T035 validates)
- **SC-005:** Reproducible with documented seeds/thresholds (T043 validates)
- **SC-006:** All artifacts checksummed (T025, T036, T044 validate)
- **SC-007:** No PII in outputs (T017, T052 validate)

## Troubleshooting

### HuggingFace Rate Limiting

If you encounter rate limits during data download (T015a), implement exponential backoff:

```python
from datasets import load_dataset
dataset = load_dataset("codeparrot/github-code", split="train", streaming=True)
```

### Model Loading Failures

For 8-bit quantization failures (T016c), ensure `bitsandbytes` is installed and GPU is accessible:

```bash
pip install bitsandbytes
```

### Parse Failures

Check `data/parse_failures.csv` for Python files that failed AST parsing. These are logged per T022.

## License and Attribution

This research pipeline is developed under the Constitution Check principles for reproducible AI research. All artifacts are checksummed and versioned per SC-006.