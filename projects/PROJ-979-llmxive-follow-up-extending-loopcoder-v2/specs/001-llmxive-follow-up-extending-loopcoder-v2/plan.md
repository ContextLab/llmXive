# Implementation Plan: llmXive follow-up: extending "LoopCoder-v2"

**Branch**: `001-gene-regulation` | **Date**: 2026-07-11 | **Spec**: `specs/001-llmxive-follow-up-extending-loopcoder-v2/spec.md`
**Input**: Feature specification for extending LoopCoder-v2 to analyze semantic entropy vs. convergence.

## Summary

This feature implements a rigorous statistical analysis to determine if the initial semantic uncertainty (entropy) of a hidden state in an iterative refinement model predicts its convergence trajectory on code generation tasks (HumanEval/MBPP). The plan executes three distinct phases: (1) extracting semantic entropy (AST-only clustering) and convergence trajectories (k=1,2,3) using the CodeLlama-7b-Instruct-hf model, (2) performing survival analysis (Kaplan-Meier) and correlation testing, and (3) simulating a dynamic router via logistic regression with robustness checks (Holm-Bonferroni, sensitivity analysis). The implementation adheres to the project constitution, ensuring reproducibility, data hygiene, and strict separation of uncertainty proxies from ground-truth evaluation.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers`, `datasets`, `scikit-learn`, `pandas`, `numpy`, `statsmodels`, `ast`, `huggingface_hub`, `lifelines`  
**Storage**: Local `data/` directory (parquet/jsonl), `data/processed/` for intermediate results, `code/` for scripts.  
**Testing**: `pytest` (unit tests for entropy clustering, convergence logic; integration tests for full pipeline).  
**Target Platform**: Linux (GitHub Actions runner with GPU offload via Kaggle if CUDA required).  
**Project Type**: Computational Research / Data Analysis  
**Performance Goals**: Complete analysis within 6 hours on CPU (sampled) or 9 hours on GPU (full dataset); memory usage < 16 GB VRAM (GPU) or < 7 GB RAM (CPU sampling).  
**Constraints**: Must run on GitHub Actions free tier (CPU) with auto-offload to Kaggle GPU for transformer inference; no external API calls; strict adherence to verified dataset URLs.  
**Scale/Scope**: HumanEval (a set of programming problems) + MBPP (subset, configurable `max_mbpp_samples`, default a representative sample size); N=10 samples per problem for entropy; k=1,2,3 loops for convergence.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence/Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | `requirements.txt` will pin versions; random seeds pinned in `code/`; datasets fetched from canonical HuggingFace URLs. |
| **II. Verified Accuracy** | **PASS** | All citations (datasets, models, stats methods) will be validated against the `# Verified datasets` block and primary sources. |
| **III. Data Hygiene** | **PASS** | Raw data checksummed; derivations written to new files in `data/processed/`; PII scan passed (code datasets are synthetic). |
| **IV. Single Source of Truth** | **PASS** | All figures/stats trace to `data/processed/*.csv` and `code/*.py`; no hand-typed numbers in paper. |
| **V. Versioning Discipline** | **PASS** | Artifacts carry content hashes; state file updated on change. |
| **VI. Internal State Calibration** | **PASS** | Enforced by `code/src/entropy.py` (AST-only clustering, no test suite) and `code/src/inference.py` (convergence via test suite). Strict separation of data files `entropy_results.csv` and `convergence_results_core.csv`. |
| **VII. Dynamic Compute Budget** | **PASS** | Router simulation reports FLOPs vs. accuracy; non-inferiority test included. |

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Schemas)
└── tasks.md             # [REMOVED]
```

### Source Code (repository root)

```text
projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/
├── code/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── data_loader.py       # Fetches HumanEval/MBPP from verified URLs
│   │   ├── entropy.py           # FR-001: Semantic entropy (AST clustering ONLY)
│   │   ├── inference.py         # FR-002: Iterative refinement (k=1,2,3)
│   │   ├── survival.py          # FR-003: Kaplan-Meier & Correlation
│   │   ├── router.py            # FR-004: Logistic regression simulation
│   │   ├── robustness.py        # FR-005/007: Multiple comparisons & sensitivity
│   │   └── utils.py             # AST normalization, FLOPs estimation, Runtime logging
│   ├── tests/
│   │   ├── test_entropy.py
│   │   ├── test_inference.py
│   │   └── test_router.py
│   └── requirements.txt
├── data/
│   ├── raw/                     # Downloaded parquet/jsonl (checksummed)
│   └── processed/               # Intermediate CSVs, model pickles, results
└── paper/                       # Drafting area (not created by plan)
```

**Structure Decision**: Single project structure selected to minimize overhead for a research pipeline. Data is separated into `raw` (immutable) and `processed` (derivable). Code is modularized by functional requirement (FR) to ensure traceability.

## Complexity Tracking

No violations detected. The plan strictly adheres to the spec and constitution.

## Implementation Phases

### Phase 1: Data Extraction & Trajectory Generation
*Goal: Generate raw data for entropy and convergence.*

1.  **Data Loading**: Load HumanEval (the complete benchmark) and MBPP (subset `max_mbpp_samples`) from verified URLs.
2.  **Entropy Extraction (`code/src/entropy.py`)**:
    *   Generate N=10 samples per problem.
    *   **Clustering**: Normalize samples using AST structure ONLY. Cluster by AST hash. **Do not** use test suite for clustering.
    *   Compute Shannon entropy.
    *   Handle undefined entropy (deterministic) by assigning minimal non-zero value or excluding (log rate).
    *   Output: `data/processed/entropy_results.csv`.
    *   **Contract**: Validate output against `contracts/entropy_schema.schema.yaml`.
3.  **Convergence Tracking (`code/src/inference.py`)**:
    *   Execute iterative refinement for **k=1, k=2, and k=3** (FR-002).
    *   Run samples against hidden test suite to determine correctness.
    *   Record first k where correct, or mark as censored if k=3 and not correct.
    *   Output: `data/processed/convergence_results_core.csv` and `convergence_results_sensitivity.csv` (for k=2,3,4 sensitivity).
    *   **Contract**: Validate output against `contracts/convergence_schema.schema.yaml`.
4.  **Runtime Logging**: Capture RAM/GPU usage and runtime for each step (SC-005).

### Phase 2: Survival Analysis & Correlation (FR-003)
*Goal: Test the primary hypothesis (H1) using survival analysis.*

1.  **Merge Data**: Join entropy and convergence data on `problem_id`.
2.  **Survival Analysis**:
    *   Use Kaplan-Meier estimator to handle censored data (non-convergence at k=3).
    *   Compute Spearman rank correlation between initial entropy and convergence step.
    *   **Censoring Assumption**: Test if censored items have similar entropy distribution to uncensored items. If not, report as lower-bound estimate.
3.  **Power Analysis**: Calculate MDES for combined dataset (HumanEval+MBPP). If underpowered, report confidence intervals.
4.  **Output**: `data/processed/correlation_results.json`.

### Phase 3: Router Simulation & Robustness (FR-004, FR-005, FR-007)
*Goal: Evaluate practical utility and statistical robustness.*

1.  **Router Training (`code/src/router.py`)**:
    *   Train logistic regression to predict optimal k using entropy and difficulty.
    *   **Validation**: 5-fold cross-validation.
    *   **Evaluation**: On held-out folds, predict k and calculate FLOPs savings based on *predicted* k (not actual k) to avoid tautology.
    *   Test non-inferiority (delta=0.05) against static baseline.
    *   Output: `data/processed/router_model.pkl`, `router_metrics.json`.
2.  **Robustness Checks (`code/src/robustness.py`)**:
    *   **Multiple Comparisons**: Apply Holm-Bonferroni correction to correlations across difficulty strata (FR-005).
    *   **Sensitivity**: Sweep convergence threshold k in {2, 3, 4}.
    *   **Small Strata**: Use hierarchical mixed-effects models for strata with < 50 samples (FR-007).
    *   **Edge Cases**: Explicitly handle undefined entropy and censored data logic.
    *   Output: `data/processed/sensitivity_sweep.json`.
3.  **Compute Metrics**: Finalize and report runtime/memory metrics (SC-005).