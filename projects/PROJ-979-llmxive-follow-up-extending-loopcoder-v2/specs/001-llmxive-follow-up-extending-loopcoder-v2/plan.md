# Implementation Plan: llmXive follow-up: extending "LoopCoder-v2: Only Loop Once for Efficient Test-Time Computation Scali"

**Branch**: `001-gene-regulation` | **Date**: 2026-07-11 | **Spec**: `specs/001-llmxive-follow-up-extending-loopcoder-v2/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-follow-up-extending-loopcoder-v2/spec.md`

## Summary

This project investigates the **associational** link between initial semantic uncertainty (entropy) in iterative refinement models and their convergence trajectories on code generation tasks. The primary scientific goal is to determine if higher initial entropy correlates with a need for more refinement loops ($k$) to reach a correct solution. The technical approach involves extracting semantic entropy via sampling ($N=10$) using a verified open-weight model (CodeLlama-1.3b for CPU validation, CodeLlama-3b/7b for full analysis), tracking convergence across loop counts $k$ on HumanEval and MBPP datasets, computing Spearman correlations (via permutation tests), and simulating a lightweight dynamic router using logistic regression to evaluate potential FLOPs savings in an ex-post analysis.

> **Note on Causality**: This study is observational. Findings regarding the relationship between entropy and convergence will be framed as **associational**, not causal. The router simulation is a feasibility study of FLOPs savings based on observed correlations, not a causal prediction model for deployment without ground truth.

## Technical Context

**Language/Version**: Python +  
**Primary Dependencies**: `transformers`, `torch`, `scikit-learn`, `pandas`, `datasets`, `pytest`, `docker` (for sandboxed execution)  
**Storage**: Local file system (`data/`, `code/`), HuggingFace Hub (datasets/models)  
**Testing**: `pytest` (unit/integration), `pytest-cov` for coverage  
**Target Platform**:
- **Validation Mode**: Linux (GitHub Actions runner: multiple vCPUs, sufficient RAM). Uses `CodeLlama-1.3b-Instruct` (FP32). Sample size restricted to N=50 to verify pipeline within 6 hours.
- **Full Analysis Mode**: Linux (GitHub Actions GPU runner or self-hosted GPU). Uses `CodeLlama-3b-Instruct` or `7b-Instruct` in FP32. Runs full dataset (HumanEval + MBPP) to satisfy SC-005.

**Constraints**:
- **No GPU/Quantization for Validation**: The CPU validation run uses default precision on a model small enough to fit in limited RAM (CodeLlama-small).
- **Model Pivot**: The "LoopCoder-v2" checkpoint is not verified. The implementation pivots to smaller and larger variants of CodeLlama-Instruct for CPU and GPU environments respectively, with manual loop logic to satisfy the iterative refinement requirement.
- **Data Subset**: CPU validation uses a stratified sample (N=50). Full analysis uses the full dataset on GPU.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Action |
|-----------|--------|---------------------|
| **I. Reproducibility** | PASS | Plan mandates `requirements.txt` with pinned versions; random seeds to be pinned in `code/`; datasets fetched via canonical HuggingFace loaders. |
| **II. Verified Accuracy** | PASS | Plan requires citations in `research.md` to match verified dataset URLs; model pivot to CodeLlama ensures verified source. |
| **III. Data Hygiene** | PASS | Plan includes checksumming of raw data; derivations written to new files; no in-place modification. |
| **IV. Single Source of Truth** | PASS | Plan structures output so all stats trace to `data/` rows; no hand-typed numbers in paper. |
| **V. Versioning Discipline** | PASS | Artifacts will carry content hashes; state file updated on change. |
| **VI. Internal State Calibration Validity** | PASS | **Architecture Note**: `code/src/entropy.py` (k=1) and `code/src/inference.py` (k>1) are strictly separated. Entropy extraction must complete and be saved to `data/processed/entropy_results.csv` before `inference.py` reads it to ensure no data leakage. |
| **VII. Dynamic Compute Budget Verification** | PASS | Plan includes FLOPs reporting and non-inferiority testing against static $k=2$ baseline. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-loopcoder-v2/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/
├── data/
│   ├── raw/             # Downloaded datasets (HumanEval, MBPP)
│   ├── processed/       # Derived datasets (entropy, trajectories)
│   └── checksums.txt    # SHA256 checksums
├── code/
│   ├── requirements.txt
│   ├── src/
│   │   ├── data_loader.py      # Dataset ingestion & filtering
│   │   ├── entropy.py          # Semantic entropy calculation (FR-001)
│   │   ├── inference.py        # Iterative refinement execution (FR-002)
│   │   ├── analysis.py         # Correlation & router simulation (FR-003, FR-004)
│   │   └── robustness.py       # Sensitivity & multiple comparison tests (FR-005)
│   ├── notebooks/
│   │   └── exploration.ipynb   # Interactive analysis (optional)
│   └── tests/
│       ├── test_entropy.py
│       ├── test_analysis.py
│       └── test_contracts.py
├── paper/
│   └── draft.md         # Final report (generated from data)
└── state/
    └── projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2.yaml
```

**Structure Decision**: Single project structure (`code/`, `data/`, `paper/`) is selected to align with the computational research workflow. All analysis scripts are modular to facilitate unit testing and reproducibility.

**Architecture Note (Principle VI)**:
- `entropy.py` implements **FR-001**: Extracts entropy at $k=1$ only. It writes results to `data/processed/entropy_results.csv` and **must not** run convergence loops.
- `inference.py` implements **FR-002**: Reads `data/processed/entropy_results.csv` (optional) and runs iterative loops $k \in \{1, 2, 3\}$. It writes `convergence_results.csv`.
- This strict separation ensures that the entropy metric (predictor) is not contaminated by the convergence outcome (target) during the extraction phase.

## Complexity Tracking

No violations detected. The project scope is contained within the computational limits of a CPU-only runner for validation (N=50, CodeLlama-1.3b) and a GPU runner for full analysis. The pivot to CodeLlama ensures model availability and memory feasibility.