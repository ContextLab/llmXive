# Implementation Plan: Evaluating the Effectiveness of LLMs for Identifying Security Vulnerabilities in Open-Source Code

**Branch**: `001-gene-regulation` | **Date**: 2026-06-25 | **Spec**: `specs/001-evaluating-the-effectiveness-of-llms-for/spec.md`

## Summary

This plan implements a zero-shot vulnerability detection pipeline that ingests code snippets from the VulDeePecker (Python), BigVul (C/C++ and JavaScript), and a curated JS dataset. It executes CPU-constrained LLM inference, extracts structural and semantic features, and performs statistical analysis (Point-Biserial correlation, Logistic Regression with dataset controls, McNemar's test) to evaluate LLM effectiveness against static analyzer baselines (Bandit, cppcheck). The implementation strictly adheres to the runtime and memory constraints of the GitHub Actions runner. **Note**: The study explicitly frames results as predictive associations, not causal mechanisms, and acknowledges the substitution of BigVul for NIST Juliet due to data availability constraints.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers` (CPU-only), `tree-sitter`, `scikit-learn`, `pandas`, `numpy`, `bandit`, `cppcheck`, `datasets`, `pydantic` (for schema validation)  
**Storage**: Local filesystem (`data/raw`, `data/processed`) with checksums; CSV/Parquet for portability. **SQLite is explicitly excluded.**  
**Testing**: `pytest` with fixtures for synthetic snippets.  
**Target Platform**: GitHub Actions Linux runner (Multiple CPU, 7GB RAM).  
**Project Type**: Research pipeline / CLI tool.  
**Performance Goals**: Total runtime ≤ 6 hours; per-sample inference ≤ 4.32s; memory ≤ 7GB.  
**Constraints**: No GPU access for primary inference; CPU-only execution; strict stratified sampling; no PII in data.  
**Scale/Scope**: Max a sufficient number of samples (stratified); Several languages (C, Python, JS).

> *Note: Empirical values (exact dataset sizes, specific model IDs) are deferred to `research.md` and `data-model.md` based on verified sources.*

## Constitution Check

| Principle | Status | Reference |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `src/utils/config.py`; datasets fetched from canonical HF URLs; `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **PASS** | All dataset URLs cited from the "# Verified datasets" block in research.md; no fabricated sources. |
| **III. Data Hygiene** | **PASS** | `src/data/download.py` computes checksums; raw data immutable; derivations in `data/processed/`. |
| **IV. Single Source of Truth** | **PASS** | All metrics derived from `data/processed/predictions.csv` and `data/processed/features.csv`; no hand-typed stats. |
| **V. Versioning Discipline** | **PASS** | `src/utils/hash_artifacts.py` integrated into `main.py` to compute content hashes and update `state.yaml` after each stage. |
| **VI. Computational Limits** | **PASS** | Pipeline designed for CPU-only; batch size ≤ 50; quantized/small models selected for 7GB RAM fit. Circuit breaker prevents timeout. |
| **VII. Baseline Comparison** | **PASS** | Bandit (Python) and cppcheck (C) integrated; McNemar's test planned with strict binary mapping. |

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── feature.schema.yaml
    ├── prediction.schema.yaml
    └── analysis_metric.schema.yaml
```

### Source Code (repository root)

```text
src/
├── __init__.py
├── config.py            # Global config, seeds, paths
├── models/              # Dataclasses generated from contracts/*.yaml
│   ├── __init__.py
│   ├── code_snippet.py  # Validated against dataset.schema.yaml
│   ├── feature_vector.py# Validated against feature.schema.yaml
│   └── prediction_result.py # Validated against prediction.schema.yaml
├── data/
│   ├── __init__.py
│   ├── download.py      # HF dataset loading, checksumming
│   └── preprocess.py    # Sampling, cleaning, batching
├── services/
│   ├── __init__.py
│   ├── llm_inference.py # Zero-shot inference, truncation handling
│   ├── static_analyzer.py # Bandit/cppcheck wrappers
│   └── feature_extractor.py # AST, taint, embeddings
├── analysis/
│   ├── __init__.py
│   ├── metrics.py       # Precision, Recall, F1, ROC-AUC
│   ├── regression.py    # Logistic Regression, Correlation
│   └── comparison.py    # McNemar's test
├── utils/
│   ├── __init__.py
│   ├── logger.py        # Structured logging
│   └── hash_artifacts.py# Checksum utilities
└── main.py              # Orchestration entry point

tests/
├── __init__.py
├── contract/            # Schema validation tests
├── integration/         # Pipeline flow tests
└── unit/                # Feature extraction, parsing tests

data/
├── raw/                 # Downloaded datasets (immutable)
├── processed/           # Predictions, features, metrics
└── logs/                # Runtime logs
```

**Structure Decision**: Single-project structure selected for tight coupling of data processing and analysis. `src/` contains all logic; `data/` is strictly for artifacts. This aligns with Constitution Principle I (Reproducibility) by keeping the entire pipeline in one repository. **Schema-Code Synchronization**: Dataclasses in `src/models/` are generated from and validated against `contracts/*.yaml` (specifically `feature.schema.yaml` and `prediction.schema.yaml` as the canonical sources) using `pydantic` to ensure Single Source of Truth.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **CPU-First** | Meets Constitution Principle VI (6h limit, 7GB RAM). GPU is an escape hatch, not the default. | A full GPU pipeline would exceed the 6-hour CI limit for the LLM part and complicate the "CPU-first" mandate. |
| **Multiple Languages** | The spec requires C, Python, and JS. | A single-language study would miss the cross-language generalizability required by the research question. |
| **Static Analyzer Baseline** | Required by Constitution Principle VII. | Skipping the baseline would invalidate the "effectiveness" claim relative to existing tools. |
| **Circuit Breaker** | LLM inference on CPU is variable. | A linear runtime assumption risks total job failure if outliers occur. |
| **Dataset Substitution** | NIST Juliet raw code is unavailable. | Using BigVul is the only verified path to C-code analysis. |

## Runtime Safety Mechanisms

To address the risk of timeout due to variable LLM inference times (Methodology Concern):
1.  **Monitoring**: `main.py` tracks cumulative runtime.
2.  **Circuit Breaker**: If runtime > 90% of 6 hours, the pipeline:
    *   Reduces batch size to 1.
    *   Switches to "fast-fail" mode (skips complex features for remaining samples).
    *   Logs `timeout_risk: true` in the final report.
3.  **Data Loss Handling**: Samples processed after the circuit breaker trigger are flagged as "partial" and excluded from the primary regression but included in descriptive stats.