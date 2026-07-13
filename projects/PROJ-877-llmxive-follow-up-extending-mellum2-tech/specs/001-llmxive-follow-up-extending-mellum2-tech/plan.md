# Implementation Plan: llmXive follow-up: extending "Mellum2 Technical Report"

**Branch**: `001-llmxive-complexity-loss` | **Date**: 2026-07-13 | **Spec**: `specs/001-llmxive-complexity-loss/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-complexity-loss/spec.md`

## Summary

This feature implements a computational research pipeline to investigate the correlation between static code complexity (cyclomatic complexity, nesting depth) and LLM prediction loss (perplexity). The system will download a subset of code from the `codeparrot/github-code` dataset, apply static analysis tools (CodeQL, tree-sitter) to label chunks, process them through a frozen CPU-optimized LLM (TinyLlama-1.1B), and perform statistical analysis including correlation on Repository-Level Aggregates, piecewise regression for threshold detection, and permutation testing. The implementation strictly adheres to GitHub Actions free-tier constraints (limited CPU resources, constrained RAM, no GPU).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets`, `transformers` (CPU-only), `tree-sitter`, `codeql` (CLI), `scikit-learn`, `statsmodels`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `kenlm` (for n-gram baseline)  
**Storage**: Local filesystem (`data/`, `code/`) with checksums; no external DB.  
**Testing**: `pytest` (unit tests for data parsing, integration tests for pipeline stages).  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Computational Research Pipeline (CLI).  
**Performance Goals**: Complete analysis within 6 hours; <14 GB disk usage; <7 GB RAM peak.  
**Constraints**: No GPU/CUDA; no 8-bit quantization; no large-model fine-tuning; strict data hygiene (checksums); static analysis must be independent of LLM inference.  
**Scale/Scope**: Sampled subset of public repositories (Python/Java); [deferred] chunk count.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Compliance Strategy |
|-----------|--------|---------------------|
| **I. Reproducibility** | PASS | `random.seed()` pinned in all scripts; `requirements.txt` with exact versions; dataset fetched from canonical HF source; CI runs on fresh runner. |
| **II. Verified Accuracy** | PASS | All citations in `research.md` will be validated by the **Reference-Validator Agent** against the `# Verified datasets` block before proceeding to implementation. |
| **III. Data Hygiene** | PASS | `data/` files checksummed; raw data immutable; derived data in new files; PII scan in CI. |
| **IV. Single Source of Truth** | PASS | All figures/stats in paper trace to `data/` rows via script output logs. |
| **V. Versioning Discipline** | PASS | A CI job computes **SHA-256** hashes of all files in `data/` and updates `state/projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech.yaml` with these hashes. |
| **VI. Static Analysis Inference Independence** | PASS | Pipeline stages strictly ordered: 1. Download, 2. Static Analysis (CodeQL/tree-sitter), 3. LLM Inference (frozen). No feedback loop. |
| **VII. Non-Linear Threshold Detection Rigor** | PASS | Plan includes piecewise regression/change-point detection (not just linear) and sensitivity analysis as required. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-mellum2-tech/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Schema definitions)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech/
├── code/
│   ├── __init__.py
│   ├── config.py           # Paths, seeds, hyperparameters
│   ├── data/
│   │   ├── download.py     # HF dataset fetcher
│   │   ├── preprocess.py   # Chunking & static analysis runner
│   │   └── inference.py    # LLM loss calculator
│   ├── analysis/
│   │   ├── correlation.py  # Pearson/Spearman & visualization (on aggregates)
│   │   ├── threshold.py    # Piecewise regression & change-point
│   │   └── stats.py        # Permutation test & FDR correction
│   └── main.py             # Pipeline orchestrator
├── data/
│   ├── raw/                # Downloaded parquet chunks
│   ├── processed/          # Annotated chunks with complexity labels
│   └── results/            # Correlation stats, plots, threshold reports
├── tests/
│   ├── unit/
│   │   ├── test_preprocess.py
│   │   └── test_inference.py
│   └── integration/
│       └── test_pipeline.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure chosen. The pipeline is linear (Download -> Annotate -> Infer -> Analyze), making a monolithic `code/` directory with sub-packages (`data`, `analysis`) the most maintainable approach for a research script. No separate frontend/backend is needed.

## Complexity Tracking

*No violations detected. The complexity of static analysis + CPU inference is necessary to meet the research question (FR-002, FR-003) and cannot be simplified without invalidating the study.*