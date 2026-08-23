# Implementation Plan: llmXive follow-up: extending "LoopCoder-v2"

**Branch**: `001-gene-regulation` | **Date**: 2026-07-11 | **Spec**: `specs/001-gene-regulation/spec.md`
**Input**: Feature specification from `specs/001-gene-regulation/spec.md`

## Summary

This project investigates the correlation between initial semantic uncertainty (entropy) of hidden states in iterative refinement models and their convergence trajectories on code generation tasks. The technical approach involves: (1) extracting semantic entropy via AST-based clustering of $N=10$ samples per input; (2) tracking convergence trajectories for $k \in \{1, 2, 3\}$ loops on HumanEval/MBPP; (3) performing survival analysis (Kaplan-Meier) to handle censored data; (4) simulating a dynamic router via ordinal logistic regression; and (5) conducting robustness checks (Holm-Bonferroni, sensitivity sweeps). The implementation runs on a GPU escape hatch (Kaggle) due to the 7B model requirements, adhering to the project's compute constraints.

## Technical Context

**Language/Version**: Python 3.10  
**Primary Dependencies**: `transformers` (v4.40+), `datasets` (v2.18+), `scikit-learn`, `lifelines` (for survival analysis), `ast` (stdlib), `numpy`, `pandas`, `torch` (CUDA enabled), `huggingface-hub`, `statsmodels` (for mixed-effects), `scipy`.  
**Storage**: Local filesystem (`data/`), HuggingFace Hub (datasets).  
**Testing**: `pytest` (unit), `pytest-cov` (coverage), manual statistical validation scripts.  
**Target Platform**: Linux (GitHub Actions CPU runner for orchestration, Kaggle GPU for heavy inference).  
**Project Type**: Research/Computational Experiment.  
**Performance Goals**: Complete full inference and analysis within [deferred] on a single T4/V100 GPU (Kaggle limit).  
**Constraints**: Must handle censored data (non-convergence) without bias; strict separation of entropy calculation (unseen inputs) from convergence ground truth; no synthetic data fabrication.  
**Scale/Scope**: Full HumanEval (complete problem set) + MBPP (subset for feasibility), $N=10$ samples per problem, $k=1,2,3$.

**Statistical Parameters**:
- **Non-Inferiority Margin**: The equivalence margin $\delta$ for the non-inferiority test is explicitly set to **0.05** ([deferred] accuracy drop). This is configured in `code/src/config.py` as `NON_INFERIORITY_DELTA = 0.05`.
- **Alpha Level**: $\alpha = 0.05$ for all hypothesis tests.
- **Entropy Clustering**: Uses `ast.unparse` for normalization and `hashlib.sha256` for deterministic hashing.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on constitution file:*

| Principle | Status | Action Required |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned seeds, `requirements.txt`, and deterministic AST hashing. |
| **II. Verified Accuracy** | **PASS** | All dataset URLs restricted to the "Verified datasets" block; citations validated. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming of raw/processed data; no in-place modification. |
| **IV. Single Source of Truth** | **PASS** | Every figure, statistic, or interpretation in the paper MUST trace back to exactly one row in this project's `data/` and one block in this project's `code/`. Derived numbers MUST NOT be hand-typed into the paper. |
| **V. Versioning Discipline** | **PASS** | Artifact hashes to be recorded in state YAML upon completion. |
| **VI. Internal State Calibration Validity** | **PASS** | Strict separation enforced: Entropy extraction ($k=1$, AST clustering on *unseen* inputs) is implemented in a distinct module from convergence tracking ($k=1,2,3$). |
| **VII. Dynamic Compute Budget Verification** | **PASS** | FLOPs accounting: Router simulation must report FLOPs savings vs. static baselines with non-inferiority testing ($\delta=0.05$). The non-inferiority test is performed against the **Static k=2** baseline, not the Oracle. |

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── src/
│   ├── __init__.py
│   ├── config.py             # Centralized config (seeds, thresholds, NON_INFERIORITY_DELTA=0.05, paths)
│   ├── data_loader.py        # Dataset fetching (HumanEval/MBPP) with checksums
│   ├── entropy.py            # Semantic entropy extraction (AST clustering via ast.unparse)
│   ├── inference.py          # Iterative refinement loop (k=1,2,3), convergence tracking
│   ├── analysis.py           # Correlation, Survival Analysis, Ordinal Logistic Regression
│   ├── robustness.py         # Holm-Bonferroni, Sensitivity Sweeps, Mixed-Effects
│   └── utils.py              # AST hashing, FLOPs estimation, logging
├── tests/
│   ├── unit/
│   │   ├── test_entropy.py
│   │   └── test_inference.py
│   └── contract/
│       └── test_schemas.py
├── requirements.txt
└── run_gpu.sh                # Script to trigger Kaggle offload
```

**Structure Decision**: Single Python package structure (`code/src/`) with clear separation of concerns: `data_loader` for ingestion, `entropy` for uncertainty, `inference` for trajectory, `analysis` for stats. This ensures the "Internal State Calibration" principle is met by physically separating entropy and convergence logic.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **GPU Offload** | 7B model inference ($N=10$ samples $\times$ $k=3$) exceeds CPU memory/time limits. | CPU-only inference of CodeLlama-7b is infeasible for the required sample size; synthetic stand-ins violate "Data Hygiene" and "Verified Accuracy". |
| **Survival Analysis** | Non-convergence at $k_{max}$ creates censored data. | Simple correlation (Spearman) on imputed values introduces bias; Kaplan-Meier is required for unbiased estimation (FR-003). |
| **AST Clustering** | Semantic equivalence requires code structure, not string match. | String-based clustering fails on semantically identical but syntactically different solutions (e.g., variable renaming). |
| **Ordinal Logistic Regression** | Target variable (optimal $k$) is ordinal (1, 2, 3), not binary. | Standard Logistic Regression would ignore the ordinal nature of the target; Ordinal Logistic Regression preserves the ordering information. |