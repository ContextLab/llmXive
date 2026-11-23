# Implementation Plan: OPID Critical-First Routing Complexity Analysis

**Branch**: `001-opid-routing-complexity` | **Date**: 2026-08-24 | **Spec**: `specs/001-opid-routing-complexity/spec.md`
**Input**: Feature specification from `specs/001-opid-routing-complexity/spec.md`

## Summary

This project implements a computational study to investigate the non-monotonic relationship between "critical-first" routing density and policy performance in the OPID (On-Policy Skill Distillation) framework. The technical approach involves generating synthetic State-Graph Environments across three complexity tiers (Deterministic, Stochastic, High-Entropy), integrating a tunable routing threshold into the OPID agent, and executing a sensitivity sweep (0.0 to 1.0) to measure success rates and "policy rigidity" (residual action entropy). The analysis will verify if excessive skill injection in low-complexity environments leads to over-constraining (reduced flexibility), identifying an inflection point where distillation becomes counterproductive.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `networkx` (graph generation), `numpy` (numerical operations), `pandas` (data handling), `scipy` (statistical regression), `statsmodels` (GLM for binary outcomes), `pytest` (testing).  
**Storage**: Local filesystem (CSV/JSON artifacts) under `data/`. Raw synthetic graphs are stored in **JSON format** (referencing `data-model.md` schema).  
**Testing**: `pytest` with coverage; unit tests for graph generation and router logic; integration tests for the simulation loop.  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, ~7GB RAM).  
**Project Type**: Computational research / simulation library.  

**Performance Goals & Graceful Degradation**:
- **Goal**: Complete [deferred] episodes per setting (11 thresholds × 3 tiers = 33,000 total episodes) within 6 hours.
- **Source**: This target is derived from **FR-003** (G*Power analysis for one-way ANOVA, f=0.25, α=0.05, power=0.80).
- **Graceful Degradation**: To satisfy **SC-005** (ensuring experiment completion), the system will perform a feasibility check before execution. If the estimated runtime (based on a 100-node, 200-step baseline) exceeds 6 hours, the system will **automatically reduce N** (e.g., to 500 episodes) and log the power limitation. This prevents a binary hard-fail and ensures partial results are generated.

**Constraints**: CPU-only execution; no external GPU; strict reproducibility via pinned seeds; no synthetic data fabrication (must use real graph generation logic).  
**Scale/Scope**: A substantial number of simulated episodes; 3 complexity tiers; 11 threshold points.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: **COMPLIANT**. Plan mandates pinned random seeds in `src/seed.py` and sequential, deterministic graph generation. All artifacts will be checksummed. **Graceful Degradation** logic (N reduction) is explicitly defined to handle compute constraints without violating reproducibility (the reduced N is logged and deterministic).
- **II. Verified Accuracy**: **COMPLIANT**. The OPID framework logic is derived from the project's own internal specification (`spec.md`), which serves as the primary source for the algorithm implementation. No external citations are required for the core logic, satisfying Principle II for internal concepts.
- **III. Data Hygiene**: **COMPLIANT**. Raw synthetic graphs will be generated and stored in `data/raw/` (JSON format) with checksums; processed results in `data/processed/` with derivation logs. No PII involved.
- **IV. Single Source of Truth**: **COMPLIANT**. All metrics (success rate, entropy variance) will be calculated by `src/analysis/aggregation.py`. Specifically, the **policy rigidity** metric (FR-004) is calculated by the `calculate_rigidity` function, which performs the required **quadratic regression** to isolate residuals, ensuring the SSoT mapping is explicit. The paper will reference `data/processed/episode_results.csv` directly.
- **V. Versioning Discipline**: **COMPLIANT**. Content hashes will be recorded in `state/...yaml` upon artifact generation.
- **VI. Complexity-Aware Skill Injection**: **COMPLIANT**. The plan explicitly structures the experiment around the three tiers and the routing threshold sweep.
  - **Inflection Point Detection**: A specific task (**T-Inflection**) is defined to identify the exact threshold where performance declines (derivative of quadratic fit < 0 or cost-benefit < 0), explicitly backing **FR-006** and **US-3**.
  - **Router-Policy Verification**: A specific task (**T-Router-Policy-Verify**) is defined to measure the entropy variance reduction caused by the router, explicitly backing **FR-004** and the core hypothesis of **US-3**.
- **VII. Synthetic State-Graph Validation**: **COMPLIANT**. Graph generation logic includes a validation step to ensure a valid path exists.
  - **Graph-Level Splitting**: To satisfy **SC-002**, the plan mandates a **Graph-Level Splitting** mechanism (A majority split for training and a smaller portion for validation) performed **before** episode generation. The "Distillation Cost-Benefit Ratio" is calculated exclusively on the held-out validation set, ensuring true independence.

## Project Structure

### Documentation (this feature)

```text
specs/001-opid-routing-complexity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── episode_result.schema.yaml
    ├── graph_config.schema.yaml
    ├── environment.schema.yaml
    ├── graph_schema.schema.yaml
    ├── summary_stats.schema.yaml
    └── aggregated_metrics.schema.yaml
```

### Source Code (repository root)

```text
src/
├── config.py            # Configuration and hyperparameters
├── seed.py              # Global seed management
├── environment/
│   ├── state_graph.py   # Graph data structure
│   ├── graph_generator.py # Tier-specific generation logic
│   └── validator.py     # Path validation logic
├── agent/
│   ├── policy_head.py   # Stochastic softmax policy
│   └── opid_router.py   # Routing threshold logic
├── simulation/
│   ├── runner.py        # Episode execution loop
│   └── metrics.py       # Real-time metric calculation
├── analysis/
│   ├── aggregation.py   # Post-run statistical analysis (includes quadratic rigidity calc)
│   └── regression.py    # GLM and Polynomial Regression models
└── utils/
    └── helpers.py       # File I/O and logging

tests/
├── unit/
│   ├── test_graph_gen.py
│   ├── test_router.py
│   └── test_metrics.py
└── integration/
    └── test_full_loop.py

data/
├── raw/
│   └── synthetic_graphs/ # Generated graph files (JSON)
└── processed/
    └── episode_results.csv
```

**Structure Decision**: Single-project structure selected to minimize overhead and ensure tight coupling between simulation and analysis. The `src/` hierarchy separates concerns (Environment, Agent, Simulation, Analysis) to facilitate independent testing of the router logic and graph generation.

## Implementation Phases

### Phase 0: Environment Setup & Configuration
- **T001**: Initialize project structure and `requirements.txt`.
- **T002**: Implement `src/seed.py` for global random seed management.
- **T003**: Implement `src/config.py` with hyperparameters (N, thresholds, tiers).

### Phase 1: Synthetic Environment Generation
- **T010**: Implement `src/environment/graph_generator.py` for Tier 1, 2, 3 generation.
- **T011**: Implement validation logic in `src/environment/validator.py` to ensure path existence.
- **T012**: Implement Graph-Level Splitting (Train/Validation) logic.
- **T013**: Generate initial graph suite and store in `data/raw/synthetic_graphs/`.

### Phase 2: Agent & Router Implementation
- **T020**: **Implement Routing Logic**: Implement `src/agent/opid_router.py` with `should_inject` logic.
  - **Requirement**: Must explicitly suppress skill signals when `threshold` logic dictates (FR-002, US-2).
  - **Artifact**: `src/agent/opid_router.py` containing `inject_skill` and `should_inject` functions.
- **T021**: **Implement Runner**: Implement `src/simulation/runner.py`.
  - **Requirement**: Must integrate the router with the policy head and execute episodes.
  - **Artifact**: `src/simulation/runner.py` containing the main simulation loop.

### Phase 3: Simulation Execution & Data Collection
- **T024b**: **Feasibility & N-Adaptation Check**:
  - **Action**: Estimate runtime for N=1,000 episodes per setting.
  - **Logic**: If estimated time > 6 hours, **reduce N** (e.g., to 500) and log the change.
  - **Constraint**: This task MUST complete **before** T024 starts.
- **T024**: **Episode Execution Loop**:
  - **Action**: Run simulations for all (Tier, Threshold) combinations.
  - **Logic**: Use the N determined by T024b. Stream results to `data/processed/episode_results.csv`.
  - **Dependency**: Depends on T024b completion.

### Phase 4: Statistical Analysis
- **T030**: **Calculate Distillation Cost-Benefit Ratio**:
  - **Logic**: Compute ratio using **Validation Set** data only (SC-002).
  - **Artifact**: `src/analysis/aggregation.py` function `calculate_cost_benefit`.
- **T031**: **Calculate Policy Rigidity (Quadratic)**:
  - **Logic**: Fit **Quadratic Regression** to action entropy vs. threshold.
  - **Output**: Extract residuals and compute variance (FR-004).
  - **Artifact**: `src/analysis/aggregation.py` function `calculate_rigidity`.
- **T032**: **GLM Fitting**: Fit GLM for non-monotonicity (SC-001).

### Phase 5: Refinement & Testing
- **T033**: **Code Cleanup and Refactoring**:
  - **Specifics**: Replace manual loops with `pandas.groupby` in `src/analysis/aggregation.py`. Vectorize residual calculations.
  - **Artifact**: Refactored `src/analysis/aggregation.py`.
- **T035**: **Add Unit Tests**:
  - **Specifics**: Implement `tests/unit/test_router.py` with `test_inject_logic` (verifies suppression) and `test_entropy_variance`.
  - **Specifics**: Implement `tests/unit/test_metrics.py` with `test_quadratic_residuals` (verifies non-linear fit logic).
  - **Artifact**: `tests/unit/test_router.py`, `tests/unit/test_metrics.py`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | Constitution Check passed all gates. | N/A |