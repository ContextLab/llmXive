# Implementation Plan: llmXive follow-up: extending "Foundation Protocol: A Coordination Layer for Agentic Society"

**Branch**: `001-policy-compression-tradeoff` | **Date**: 2026-07-11 | **Spec**: `specs/001-policy-compression-tradeoff/spec.md`

## Summary

This project implements a deterministic simulation to quantify the trade-off between context compression (via graph-traversal limits) and policy-violation error rates in multi-agent workflows. The system generates 500 synthetic workflows with varying depths and complexities, executes them under "Full Context" and "Compressed Context" (BFS/DFS truncated) regimes, and performs **logistic regression on individual workflow observations** (using actual token reduction % as the predictor) to identify the "safe operating zone" where efficiency gains do not exceed a 1% error threshold. The entire pipeline runs on CPU-only infrastructure, simulating token usage via `tiktoken` and validating against an independent Oracle Policy Engine.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `networkx` (graph generation/traversal), `tiktoken` (token counting), `numpy`/`scipy`/`statsmodels` (statistical analysis), `pandas` (data handling), `pytest` (testing).  
**Storage**: In-memory data structures; execution logs serialized to JSON/CSV in `data/`.  
**Testing**: `pytest` with deterministic seeding.  
**Target Platform**: GitHub Actions `ubuntu-latest` (CPU-only, 2 cores, ~7GB RAM).  
**Project Type**: Computational research simulation / CLI tool.  
**Performance Goals**: Complete 500 workflow generations + executions + analysis in < 6 hours on free-tier runner.  
**Constraints**: No GPU; no large model inference; memory usage < 7GB; deterministic reproducibility.  
**Scale/Scope**: 500 synthetic workflows; 5 compression levels; 1 Oracle Engine.

> Empirical specifics (exact token counts, error rates) are deferred to `research.md` and implementation.

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Reproducibility** | PASS | All random seeds pinned in `code/`; no external live dependencies; deterministic state machine. |
| **II. Verified Accuracy** | PASS | Citations limited to verified datasets (none required for synthetic data); `tiktoken` and `networkx` are standard libraries. |
| **III. Data Hygiene** | PASS | Raw synthetic data generated on run; checksums recorded in `state/`; no PII (synthetic only). **Tested explicitly in Phase 3.** |
| **IV. Single Source of Truth** | PASS | All statistics derived from `data/` CSVs; no hand-typed numbers in `plan.md` or `paper/`. |
| **V. Versioning Discipline** | PASS | Artifacts (code, data) will carry content hashes; `state/` updated on artifact change via explicit tasks in Phase 2/4. |
| **VI. Deterministic State-Modeling** | PASS | Oracle Policy Engine is logically distinct from compression engines; ground truth is independent. |
| **VII. Resource-Constrained Execution** | PASS | Simulation uses CPU-only graph algorithms and token counting; no heavy models; fits 7GB RAM. |

## Project Structure

### Documentation (this feature)

```text
specs/001-policy-compression-tradeoff/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── workflow.schema.yaml
    ├── execution_log.schema.yaml
    └── analysis_results.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-866-llmxive-follow-up-extending-foundation-p/
├── code/
│   ├── __init__.py
│   ├── generators/
│   │   └── synthetic_workflow.py  # FR-001, FR-008
│   ├── engines/
│   │   ├── oracle_policy.py       # FR-008 (Ground Truth)
│   │   ├── full_context.py        # FR-002
│   │   └── compressed_context.py  # FR-003, FR-004
│   ├── analysis/
│   │   └── tradeoff_model.py      # FR-005, FR-006
│   ├── utils/
│   │   └── token_counter.py       # FR-009
│   └── main.py                    # Orchestrator
├── data/
│   ├── raw/                       # Generated synthetic workflows
│   ├── processed/                 # Execution logs
│   └── results/                   # Regression curves
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── state/                         # Versioning registry
│   └── projects/PROJ-866-llmxive-follow-up-extending-foundation-p.yaml
└── requirements.txt               # Dependency lockfile
```

**Structure Decision**: Single project structure (`code/`, `data/`, `tests/`, `state/`) chosen to minimize overhead for a computational simulation. Modules are separated by responsibility (generation, execution, analysis) to ensure the Oracle Engine remains independent (Constitution Principle VI).

## Phase Plan

### Phase 0: Research & Feasibility
- **Goal**: Validate dataset strategy (synthetic generation logic) and statistical methods.
- **Tasks**:
  - Confirm `networkx` can generate a sufficient number of unique DAGs with depth -20 and 1-10 constraints.
  - Verify `tiktoken` `cl100k_base` tokenization speed and memory footprint on CPU.
  - Select regression model (Logistic Regression on individual observations) for error rate vs. reduction %.
  - Define multiple-comparison correction method (Bonferroni) for secondary robustness checks.
- **Output**: `research.md`.

### Phase 1: Data Model & Contracts
- **Goal**: Define schemas for workflows, logs, and results.
- **Tasks**:
  - Design `Workflow` schema (nodes, edges, policy constraints).
  - Design `ExecutionLog` schema (compression depth, token count, violations, **actual reduction %**).
  - Design `AnalysisResult` schema (regression coefficients, threshold).
  - Create YAML schemas in `contracts/`.
- **Output**: `data-model.md`, `contracts/*.schema.yaml`.

### Phase 2: Implementation
- **Goal**: Build the simulation pipeline.
- **Tasks**:
  - **Initialize State Registry**: Create `state/` directory and initial `state/projects/...yaml` file.
  - **Generate Dependencies**: Create `requirements.txt` with pinned versions.
  - Implement `synthetic_workflow.py` with deterministic seeding (FR-001).
  - Implement `oracle_policy.py` as a distinct rule-based validator (FR-008).
  - Implement `full_context.py` (simulator) and `compressed_context.py` (FR-002, FR-003).
  - Integrate `tiktoken` for exact token counting (FR-009).
  - Implement `tradeoff_model.py` with **Logistic Regression** (individual observations) and covariates (FR-005, FR-006).
  - Write `main.py` to orchestrate: Generate -> Execute (Full) -> Execute (Compressed) -> Analyze.
  - **Update State**: Script to update `state/projects/...yaml` with artifact hashes after generation.
- **Output**: `code/` directory, `requirements.txt`, `state/` registry.

### Phase 3: Testing & Validation
- **Goal**: Ensure correctness and reproducibility.
- **Tasks**:
  - Unit tests for graph generation (variance checks).
  - Integration test: Run multiple workflows to verify Oracle detects violations correctly.
  - Contract tests: Validate JSON output against `contracts/` schemas.
  - **State Integrity Test**: Verify that checksums in `state/` match actual file hashes.
  - Performance test: Run full 500-workflow suite on CPU, verify < 6h runtime.
- **Output**: `tests/`, `data/` samples.

### Phase 4: Analysis & Reporting
- **Goal**: Generate final results.
- **Tasks**:
  - Run full pipeline.
  - Generate `TradeOffCurve` and identify safe zone threshold (SC-004) via logistic regression.
  - **Update State**: Final update of `state/projects/...yaml` with final artifact hashes and `updated_at`.
  - Write `paper/` draft with results derived strictly from `data/`.
- **Output**: `data/results/`, `paper/`.

## Compliance with Methodological Rigor

- **FR/SC Coverage**: Every FR (001-009) and SC (001-005) is mapped to a specific phase/task above.
  - FR-001/008: Phase 2, `generators/` and `engines/oracle_policy.py`.
  - FR-002/003/004: Phase 2, `engines/` and `utils/`.
  - FR-005/006: Phase 2, `analysis/` (Logistic Regression).
  - SC-001/002/003/004/005: Phase 4, derived from logs.
- **Dataset Fit**: No external dataset used; synthetic data generation logic is validated in Phase 0 to ensure it contains all required variables (depth, complexity, constraints).
- **Statistical Rigor**:
  - **Multiple Comparisons**: Bonferroni correction applied as a secondary robustness check for pairwise depth comparisons.
  - **Power**: 500 individual observations used for regression (not 5 aggregated points) to ensure sufficient power.
  - **Causal/Associational**: Clarified that 'compression depth' is randomized, but 'token reduction %' is observational (confounded by graph topology). The model includes 'graph depth' and 'complexity' as covariates to control for confounding.
  - **Collinearity**: Depth and complexity generated independently; included as covariates.
- **Oracle Independence**: The Oracle is a distinct rule-based validator. The 'Full Context' engine is a simulator that approximates the Oracle. Errors are measured as deviations from the Oracle, ensuring the baseline is non-trivial and not tautological.

## Compute Feasibility

- **No GPU**: Simulation uses pure Python graph algorithms and token counting.
- **Memory**: 500 small graphs + logs fit well within 7GB RAM.
- **Time**: Graph traversal and token counting are O(N); 500 runs estimated < 1 hour on 2-core CPU.
- **Libraries**: `networkx`, `tiktoken`, `numpy`, `pandas`, `scipy`, `statsmodels` all have CPU wheels and low memory footprints.