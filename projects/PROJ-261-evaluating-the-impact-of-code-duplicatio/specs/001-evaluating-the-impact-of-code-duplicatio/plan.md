# Implementation Plan: Evaluating the Impact of Code Duplication on LLM Code Understanding

**Branch**: `001-evaluate-code-duplication-llm-understanding` | **Date**: 2026-05-12 | **Spec**: `specs/001-evaluate-code-duplication-llm-understanding/spec.md`
**Input**: Feature specification from `/specs/001-evaluate-code-duplication-llm-understanding/spec.md`

## Summary

This feature implements a research pipeline to measure the correlation between syntactic code duplication density and LLM code understanding metrics. The technical approach involves: (1) streaming a 500MB subset of codeparrot/github-code via HuggingFace Datasets, (2) computing AST-based clone density using Python's built-in ast module, (3) measuring token-level perplexity using Salesforce/codegen-350M-mono in 8-bit quantization, (4) evaluating bug detection accuracy on human-eval, and (5) calculating Spearman's rank correlation between duplication density and model performance metrics.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: datasets (HuggingFace), transformers, bitsandbytes, scipy, matplotlib, pytest  
**Storage**: CSV files under `data/` with checksums recorded in state manifest (`artifact_hashes`)  
**Testing**: pytest with contract tests against YAML schemas  
**Target Platform**: Linux server (GitHub Actions ubuntu-latest runner)  
**Project Type**: computational research pipeline  
**Performance Goals**: Complete 500MB corpus processing within 24 hours; memory under 7GB  
**Constraints**: 8-bit quantization required; streaming mode for dataset; no external clone detection dependencies  
**Scale/Scope**: 500MB code corpus, 1000+ code segments, 50 human-eval problems  
**Clone-Detection Thresholds**: 0.7, 0.8, 0.9 (used for sensitivity analysis in User Story 3)  
**Linting Tools**: black, flake8, isort configured via pre-commit  
**PII Scanning**: Enabled per Constitution Principle III (Data Hygiene) via tasks T014, T017  
**Parallel Execution**: Supported via [P] markers in tasks.md; team capacity planning documented in quickstart.md

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Reference |
|-----------|--------|--------------------------|
| I. Reproducibility | PASS | Random seeds pinned in `code/`; datasets fetched from canonical HuggingFace sources; `requirements.txt` pins all dependencies |
| II. Verified Accuracy | PASS | All citations verified against spec.md; Reference-Validator will verify at artifact write and Advancement-Evaluation gates |
| III. Data Hygiene | PASS | All files under `data/` checksummed in `artifact_hashes`; raw data preserved; transformations produce new files; PII scan enforced via T014, T017 |
| IV. Single Source of Truth | PASS | All figures/statistics trace to exactly one row in `data/` and one block in `code/`; no hand-typed numbers in paper |
| V. Versioning Discipline | PASS | Every artifact carries content hash; Advancement-Evaluator invalidates stale review records on hash change |
| VI. Statistical Correlation Integrity | PASS | Spearman's rank correlation required; p-values reported; p < 0.05 significance threshold documented |
| VII. Clone Detection Consistency | PASS | AST-based clone detector configuration pinned in `code/`; duplication density derived from pinned detector on codeparrot/github-code subset |

**GATE RESULT**: PASS - All 7 constitution principles have explicit implementation references. No violations requiring complexity justification.

## Project Structure

### Documentation (this feature)

```
specs/001-evaluate-code-duplication-llm-understanding/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```
projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/
├── __init__.py
├── config.py                    # Configuration: seeds, thresholds (0.7, 0.8, 0.9), model params
├── data_loader.py               # HuggingFace dataset streaming
├── ast_cloner.py                # AST-based clone detection (stdlib only)
├── model_metrics.py             # Perplexity computation with codegen-350M-mono
├── bug_detection.py             # HumanEval pass@1 evaluation
├── correlation_analysis.py      # Spearman's rank correlation
├── visualization.py             # Scatter plots with regression lines
├── checksum_manifest.py         # State manifest with artifact_hashes tracking
├── pii_scanner.py               # PII pattern scanning per Constitution Principle III
└── main.py                      # Pipeline orchestration

projects/PROJ-261-evaluating-the-impact-of-code-duplication/data/
├── raw/
│   └── github-code-sample.csv   # Streamed code segments (checksummed)
├── processed/
│   ├── clone_metrics.csv        # Clone density per segment (checksummed)
│   ├── perplexity_scores.csv    # Token-level perplexity per segment (checksummed)
│   └── bug_detection_results.csv # HumanEval pass@1 results (checksummed)
├── analysis/
│   ├── correlation_results.csv  # Spearman coefficients and p-values (checksummed)
│   └── figures/                 # Scatter plots with regression lines (checksummed)
└── parse_failures.csv           # Log of files that failed AST parsing

projects/PROJ-261-evaluating-the-impact-of-code-duplication/tests/
├── contract/
│   ├── test_clone_metrics_schema.py
│   ├── test_model_metrics_schema.py
│   └── test_correlation_schema.py
├── integration/
│   └── test_pipeline_end_to_end.py
└── unit/
    ├── test_ast_cloner.py
    ├── test_model_metrics.py
    ├── test_bug_detection.py
    ├── test_correlation_analysis.py
    ├── test_visualization.py
    ├── test_pii_scanner.py
    └── test_data_loader.py

specs/001-evaluate-code-duplication-llm-understanding/contracts/
├── clone_metrics.schema.yaml
├── model_metrics.schema.yaml
├── correlation_results.schema.yaml
└── pipeline_config.schema.yaml
```

**Structure Decision**: Single computational research pipeline structure selected. All processing logic in `code/` directory with clear separation between data loading, AST processing, model inference, and statistical analysis. Contract tests validate schema compliance for all intermediate and final artifacts.

## Computational Task Ordering

The pipeline MUST execute in the following order to satisfy data dependencies:

1. **Data Download**: Stream codeparrot/github-code subset → `data/raw/github-code-sample.csv` (T018)
2. **PII Scan**: Scan all files under `data/` for PII patterns → log findings (T017)
3. **Clone Detection**: Parse AST → compute clone density → `data/processed/clone_metrics.csv` (T019)
4. **Model Inference**: Load codegen-350M-mono (8-bit) → compute perplexity → `data/processed/perplexity_scores.csv` (T020)
5. **Pipeline Orchestration**: Join clone-density and perplexity metrics (T021 main.py)
6. **Bug Detection**: Load human-eval → evaluate pass@1 → `data/processed/bug_detection_results.csv` (T031)
7. **Correlation Analysis**: Join metrics → compute Spearman correlation → `data/analysis/correlation_results.csv` (T032)
8. **Visualization**: Generate scatter plots with regression lines → `data/analysis/figures/` (T041)

**Ordering Rationale**: Data must be downloaded before any task consumes it (Principle I). PII scanning requires data to exist. Clone detection runs before model inference to establish baseline metrics. Correlation analysis requires all intermediate metrics to be complete. Visualization is last to document final findings. Pipeline orchestration (main.py) joins intermediate results.

**Phase Alignment Note**: Computational pipeline stages (Data Download → PII Scan → Clone Detection → Model Inference → Pipeline Orchestration → Bug Detection → Correlation Analysis → Visualization) correspond to development phases in tasks.md (Setup → Foundational → US1 → US2 → US3 → Polish) and serve both technical correctness and project management clarity. Computational stages describe data flow dependencies, while development phases describe implementation ordering and team workflow. Both ordering systems are maintained separately and now aligned for consistency.