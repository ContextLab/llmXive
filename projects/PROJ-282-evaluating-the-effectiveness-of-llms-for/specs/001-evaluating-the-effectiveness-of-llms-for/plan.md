# Implementation Plan: Evaluating the Effectiveness of LLMs for Identifying Security Vulnerabilities in Open-Source Code

**Branch**: `001-gene-regulation` | **Date**: 2026-06-19 | **Spec**: `specs/001-gene-regulation/spec.md`

## Summary

This project implements a reproducible pipeline to evaluate the zero-shot effectiveness of Large Language Models (LLMs) in detecting security vulnerabilities in C, Python, and JavaScript code. The system ingests labeled datasets (VulDeePecker, NIST Juliet, JSVulnDB), extracts structural/semantic features, runs LLM inference on CPU, compares results against static analyzers (Bandit, cppcheck), and performs statistical analysis (Logistic Regression with interaction terms, McNemar's test) to determine if code features predict LLM detection accuracy.

**Dataset Note**: FR-001 mandates BigVul for JavaScript. As verified sources for BigVul are C/C++/Java, we substitute with **JSVulnDB** (verified JS vulnerability dataset) to satisfy the functional requirement of JS vulnerability detection. This substitution is documented in `research.md`.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets` (HuggingFace), `transformers` (CPU-optimized), `scikit-learn`, `networkx` (AST analysis), `tree-sitter`, `bandit`, `cppcheck`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/logs`); no external DB.  
**Testing**: `pytest` (unit/integration), `jsonschema` (contract validation).  
**Target Platform**: GitHub Actions Free Tier (2 CPU, 7GB RAM, no GPU) with optional Kaggle GPU offload for embedding generation if CPU fails.  
**Project Type**: Data Science / Research Pipeline  
**Performance Goals**: Complete [deferred] samples in ≤6 hours; per-sample inference ≤4.32s.
**Constraints**: CPU-only inference; no internet access for gated data; strict memory limits (≤7GB).  
**Scale/Scope**: [deferred] labeled snippets (stratified); 3 languages; 2 baseline tools.

> Empirical specifics (exact sample counts per language, measured inference times) are deferred to `research.md` and implementation logs.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Reference |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates `random_seed` pinning, `requirements.txt` pinning, and CI-based re-runs. |
| **II. Verified Accuracy** | **PASS** | Plan restricts dataset citations to the "Verified datasets" table in `research.md`. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming steps and immutable raw data storage (`data/raw`). |
| **IV. Single Source of Truth** | **PASS** | All stats flow from `data/processed` CSVs; no hand-typed numbers in `paper/`. |
| **V. Versioning** | **PASS** | Artifact hashes recorded in state file; `updated_at` triggers on change. |
| **VI. Compute Limits** | **PASS** | Plan prioritizes CPU-tractable methods (small models: Phi-mini-4k-instruct, Qwen2.5-0.5B) and defines GPU escape hatch. Feasibility: [deferred] samples @ 4.32s/sample = 6h. |
| **VII. Baseline Comparison** | **PASS** | Plan explicitly includes Bandit/cppcheck execution and McNemar's test (with paired sample protocol). |

## Project Structure

*(Note: This section depicts the TARGET state of the repository after implementation.)*

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Target State)
│   ├── dataset.schema.yaml
│   ├── prediction.schema.yaml
│   └── analysis.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── download.py          # Fetches datasets from verified URLs
│   ├── preprocess.py        # Cleans, chunks, and validates raw data
│   └── feature_extractor.py # AST, semantic, embedding extraction
├── models/
│   ├── llm_inference.py     # Zero-shot LLM runner (CPU)
│   └── static_analyzer.py   # Bandit/cpptcheck wrapper
├── analysis/
│   ├── metrics.py           # Precision, Recall, F1, ROC-AUC
│   ├── regression.py        # Logistic Regression, Correlation
│   └── comparison.py        # McNemar's test
├── utils/
│   ├── logger.py            # Structured JSON logging
│   └── config.py            # Constants, seeds, paths
└── main.py                  # Orchestration script

tests/
├── contract/                # Schema validation tests
├── integration/             # End-to-end pipeline tests
└── unit/                    # Feature extraction, metric calc

data/
├── raw/                     # Immutable downloaded datasets (checksummed)
├── processed/               # Feature vectors, predictions, results
└── logs/                    # JSON execution logs (orchestration, linting)
```

**Structure Decision**: Single Python project structure. Separation of `data`, `models`, and `analysis` ensures modularity and testability. `data/logs` handles the verification artifacts (orchestration logs, linting configs) required by the task constraints.

## Complexity Tracking

*No violations found. The plan adheres to CPU-first constraints and open-data requirements.*