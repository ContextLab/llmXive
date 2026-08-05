# Implementation Plan: llmXive follow-up: extending "DVAO: Dynamic Variance-adaptive Advantage Optimization for Multi-reward"

**Branch**: `001-llmxive-noise-scaling` | **Date**: 2026-07-12 | **Spec**: `specs/001-llmxive-noise-scaling/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-noise-scaling/spec.md`

## Summary

This project extends the "DVAO" framework by deriving a theoretical lower bound on sample complexity for Multi-Objective Reinforcement Learning (MORL) under independent noise, and empirically validating it using synthetic tabular MDPs. The core contribution is a closed-form equation linking the number of objectives $N$ to variance accumulation, validated against a "Moving-Window Heuristic" for variance estimation. The implementation strictly adheres to CPU-only constraints (A limited number of cores, substantial RAM) using a synthetic data generator, ensuring feasibility on GitHub Actions free-tier runners.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy` (for stats), `sympy` (for symbolic derivation), `pytest` (testing), `pyyaml` (contracts)  
**Storage**: In-memory arrays (NumPy), JSON logs for results, no external database.  
**Testing**: `pytest` with `pytest-randomly` for reproducibility verification.  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Computational Research / Algorithmic Validation.  
**Performance Goals**: Full experiment suite (N=5,10,20,50, Multiple runs each) completes within 6 hours; single run < 15 mins.  
**Constraints**: Max modest RAM, limited CPU cores. No GPU usage. Synthetic data only (no external API calls).  
**Scale/Scope**: Synthetic tabular MDPs with a small number of objectives.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence / Plan Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt`, random seed management in `src/utils/seeding.py`, and synthetic data generation logic that is deterministic given a seed. |
| **II. Verified Accuracy** | **PASS** | No external citations required for the theoretical derivation (self-contained math) or synthetic data (self-contained generator). All "citations" will be internal cross-references to the derivation module. |
| **III. Data Hygiene** | **PASS** | `data/` will contain only generated artifacts (JSON/CSV). Checksums recorded in state file. No PII (synthetic data). |
| **IV. Single Source of Truth** | **PASS** | `src/derivation/sample_complexity.py` is the canonical source for the theoretical bound. `docs/theoretical_derivation.md` is a generated report from this module. The contracts in `contracts/` are derived strictly from `data-model.md` to ensure consistency. |
| **V. Versioning Discipline** | **PASS** | Implementation will use `content-hash` for generated data files. Plan includes logic to invalidate results if code changes. |
| **VI. Theoretical Lower Bound Validation** | **PASS** | The plan explicitly separates `src/derivation` (theory) from `src/analysis` (empirical). The validation logic in `src/analysis/stats.py` will compare empirical regression slopes against the *known* theoretical slope from the derivation module, ensuring independence from the variance estimator's accuracy. |
| **VII. Computational Resource Constraint Adherence** | **PASS** | The plan uses tabular MDPs (no neural networks) and NumPy vectorization. Memory scaling is $O(N \cdot |S| \cdot |A|)$. The plan includes explicit logic (FR-016) to degrade $|S|$ if $N > 50$ to stay within a reasonable storage limit. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-noise-scaling/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset_schema.yaml
│   ├── empirical_results.schema.yaml
│   ├── output_schema.yaml
│   ├── statistical_report.schema.yaml
│   ├── statistical_result.schema.yaml
│   └── variance_estimate.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-842-llmxive-follow-up-extending-dvao-dynamic/code/
├── src/
│   ├── __init__.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── seeding.py              # Random seed management (PRNG state)
│   ├── derivation/
│   │   ├── __init__.py
│   │   └── sample_complexity.py    # FR-001, FR-002: Theoretical derivation & inversion
│   ├── environment/
│   │   ├── __init__.py
│   │   ├── synthetic_mdp.py        # FR-003, FR-016: Tabular MDP generator with degradation
│   │   └── pareto_oracle.py        # FR-017: Approximate Pareto frontier calculation
│   ├── heuristic/
│   │   ├── __init__.py
│   │   └── moving_window.py        # FR-004: Moving-Window Heuristic implementation
│   └── analysis/
│       ├── __init__.py
│       ├── stats.py                # FR-006, FR-009, FR-015: Regression, FDR, coincidence check
│       └── metrics.py              # SC-004: False positive rate calculation
├── data/
│   ├── raw/                        # (Empty, synthetic generation happens in-memory)
│   └── processed/
│       ├── empirical_results.json  # FR-035: Aggregated results
│       └── step_logs.json          # Step-level variance estimates
├── docs/
│   └── theoretical_derivation.md   # Generated report from sample_complexity.py
├── tests/
│   ├── test_derivation.py
│   ├── test_environment.py
│   └── test_stats.py
├── requirements.txt
└── run_experiment.py               # Entry point for the full suite
```

**Structure Decision**: The project is split into `derivation` (pure math), `environment` (data generation), `heuristic` (algorithm), and `analysis` (statistics). This enforces the "Single Source of Truth" principle by isolating the theoretical bound calculation from the empirical validation logic. The `src/derivation/sample_complexity.py` is the primary artifact for the theoretical contribution.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Separation of Derivation and Analysis** | Required by Constitution Principle VI (Theoretical Lower Bound Validation) to ensure the theoretical bound is not "tuned" to the empirical results. | Merging derivation and analysis code risks circular validation and violates the "Validation Independence" requirement. |
| **Synthetic Tabular MDPs** | Required by Constitution Principle VII (Resource Constraints) to run within 7GB RAM on CPU. | Using real LLM environments or deep RL would exceed memory limits and introduce non-deterministic noise sources that obscure the specific noise-scaling law being tested. |
| **Graceful Degradation Logic** | Required by FR-016 to handle $N > 50$ without OOM crashes. | Hard-capping $N$ at 50 would prevent the system from testing the edge cases and validating the scaling law's failure points as requested in US-6. |
| **Approximate Pareto Oracle** | Required by FR-017 to compute distance to frontier for N=50 where exact Pareto is NP-hard. | Exact computation is infeasible; a weighted-sum sweep provides a consistent, reproducible proxy. |
| **Log-Log Regression** | Required to validate the scaling law (slope) rather than just variance accuracy. | T-tests on bias are trivial and do not validate the core scaling claim. |