# Implementation Plan: Quantifying Hallucination in LLM-Generated API Documentation

**Branch**: `001-quantify-hallucination` | **Date**: 2026-06-22 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-quantify-hallucination/spec.md`

## Summary

This feature implements a reproducible pipeline to quantify hallucination in LLM-generated API documentation. The system ingests the Python subset of the CodeSearchNet dataset, generates one-sentence descriptions using two CPU-tractable models (`codegen` and `starcoderbase`), and computes a composite hallucination index based on entity-overlap F1 scores against source code ASTs. The pipeline performs correlation analysis, regression modeling, and robustness checks (sensitivity analysis, manual validation) to determine if intrinsic code characteristics drive hallucinations, while strictly adhering to GitHub Actions free-tier constraints (CPU-only, streaming data, memory limits).

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `transformers`, `torch` (CPU), `spacy`, `radon`, `pandas`, `scikit-learn`, `datasets`, `pyyaml`, `statsmodels`
**Storage**: Local `data/` directory (streamed from Hugging Face), `results/` directory for CSV/JSON outputs
**Testing**: `pytest` (contract tests against YAML schemas, unit tests for metric calculation)
**Target Platform**: Linux (GitHub Actions free-tier runner), CPU-only execution.
**Project Type**: Research pipeline / CLI tool
**Performance Goals**: Process 1000 functions in < 4 hours; Memory usage < 7 GB RAM; Disk usage < 14 GB.
**Constraints**: Must run on a limited number of CPU cores., ~7 GB RAM. Must handle streaming datasets to avoid OOM. Must enforce one-sentence output generation deterministically.
**Scale/Scope**: Initial sample: a substantial set of functions (adjusted for regression power). Full run: up to 10k functions if memory permits via streaming.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on constitution file:*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`. Data fetched from canonical Hugging Face URLs. `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **PASS** | Citations in `research.md` restricted to the "Verified datasets" block. No fabricated URLs. |
| **III. Data Hygiene** | **PASS** | Data downloaded to `data/` with checksums recorded. Raw data preserved; derivations written to new files. |
| **IV. Single Source of Truth** | **PASS** | All statistics in `results/` trace back to `data/` and `code/`. No hand-typed numbers in reports. |
| **V. Versioning Discipline** | **PASS** | **Mechanism**: A `hash_utils.py` module will compute SHA-256 hashes for every intermediate file (`features.csv`, `metrics.csv`) immediately upon write. These hashes are stored in `data/hashes.json` and the project state file. This ensures every artifact carries a content hash as required. |
| **VI. Metric Alignment** | **PASS** | **Mechanism**: `validate.py` will randomly sample [deferred] of the dataset. Human annotators will score these based on *semantic intent* (runtime behavior) vs. description. `analysis.py` will compute the correlation between the automated entity-F1 and the manual score. If $r < 0.7$, the metric is flagged. This directly satisfies the principle. |
| **VII. Code-Metric Isolation** | **PASS** | Regression models will control for model-specific variance by running both `codegen-350M` and `starcoderbase-1b` and comparing coefficients. |

## Project Structure

### Documentation (this feature)

```text
specs/001-quantify-hallucination/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Defined in Phase 1, Implemented/Validated in Phase 2)
│   ├── dataset.schema.yaml
│   ├── metrics.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-762-quantifying-hallucination-in-llm-generat/code/
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── download.py          # Data ingestion (streaming)
│   ├── preprocess.py        # AST parsing, entity extraction
│   ├── generate.py          # LLM inference (CPU)
│   ├── metrics.py           # F1 calculation, Hallucination Index
│   ├── analysis.py          # Correlation, Regression, Sensitivity, VIF, Encoding
│   ├── validate.py          # Manual validation logic
│   └── hash_utils.py        # SHA-256 hashing for data hygiene
├── tests/
│   ├── unit/
│   │   ├── test_metrics.py
│   │   └── test_preprocess.py
│   ├── contract/
│   │   └── test_schemas.py
│   └── integration/
│       └── test_pipeline.py
└── data/                    # Gitignored (or small samples)
    └── raw/
    └── processed/
```

**Structure Decision**: Single project structure (`projects/.../code/`) with a modular `src/` layout. This minimizes overhead and aligns with the "Research pipeline" type, allowing direct script execution for the data flow.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Dual Model Execution | Required by FR-010 and Constitution Principle VII to isolate model-specific variance. | Running a single model would fail to distinguish between code-characteristic effects and model artifacts. |
| Streaming Data | Required by SC-001/SC-002 to fit 7GB RAM limit with large datasets. | Loading the full dataset into memory would cause OOM on the free-tier runner. |
| AST-Based Ground Truth | Required by FR-003 to ensure factual accuracy against code, not just reference docstrings. | Using reference docstrings as ground truth would propagate existing hallucinations/errors from the dataset. |
| Manual Validation (Semantic) | Required to avoid circular validation (AST vs AST). | Using AST for both automated and manual scoring would artificially inflate correlation. |

## Versioning & Hashing Strategy

To satisfy Constitution Principle V and III:
1.  **Intermediate Files**: Every file written to `data/processed/` (e.g., `features.csv`, `metrics.csv`) triggers `hash_utils.py` to compute a SHA-256 hash.
2.  **Manifest**: A `data/hashes.json` manifest is updated atomically after each write, recording the file path and its hash.
3.  **State Sync**: The project state file (`state/projects/...yaml`) is updated with the latest hash values upon pipeline completion.
4.  **Verification**: The `validate.py` script checks `data/hashes.json` against current file hashes before running analysis to ensure data integrity.