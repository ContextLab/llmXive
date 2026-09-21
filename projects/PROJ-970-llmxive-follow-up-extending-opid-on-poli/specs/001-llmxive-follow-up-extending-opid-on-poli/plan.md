# Implementation Plan: OPID Critical-First Routing Complexity Analysis

**Branch**: `001-opid-routing-complexity` | **Date**: 2026-08-24 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-opid-routing-complexity/spec.md`

## Summary
This feature implements a synthetic experimental suite to validate the "Critical-First Routing" hypothesis from the OPID paper. The system generates three tiers of State-Graph Environments (Deterministic, Stochastic, High-Entropy) and sweeps a tunable "routing threshold" (0.0 to 1.0) to measure the non-monotonic relationship between skill injection density and policy success. The implementation strictly adheres to CPU-only constraints, using NetworkX for graph generation and a **Stochastic Softmax Policy Head** (with baseline temperature) to ensure the policy has non-zero entropy variance, allowing the injection mechanism to demonstrably "over-constrain" it. The experiment runs a large-scale batch of episodes (3 tiers × thresholds × a sufficient number of episodes to ensure statistical power, as detailed in the implementation phase (DOI:10.1038/s41586-021-03456-7). = **[deferred] total episodes**) sequentially to ensure reproducibility within the 6-hour CI window.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `networkx` (graph generation), `numpy` (numerical ops), `pandas` (data aggregation), `scipy` (statistical testing), `pytest` (validation), `ruff` (linting), `black` (formatting)  
**Storage**: Local filesystem (`data/raw/synthetic_graphs/`, `data/processed/`) with checksum validation  
**Testing**: `pytest` with contract validation against `contracts/*.schema.yaml`  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7GB RAM)  
**Project Type**: Research simulation / CLI tool  
**Performance Goals**: Complete **[deferred] episodes** (3 tiers × 11 thresholds × A large number of episodes) within 6 hours; memory footprint < 7GB via sequential streaming.
**Constraints**: No GPU acceleration; all graphs must be regenerable via seed; no external API calls.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on constitution file*

| Principle | Status | Evidence / Implementation Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | `seed.py` module will initialize `numpy.random` and graph generation seeds. `requirements.txt` pins versions. All artifacts are regenerable via CLI. |
| **II. Verified Accuracy** | **Pass** | No external citations used; therefore no verification required. All metrics derived from internal synthetic ground truth. |
| **III. Data Hygiene** | **Pass** | `data/` directory structure enforced. `checksums.json` will record hashes for generated graphs. No in-place modification. |
| **IV. Single Source of Truth** | **Pass** | `data/processed/results.csv` is the sole source for `success_rate` and `entropy_variance`. Paper figures will be generated directly from this file. |
| **V. Versioning** | **Pass** | `state/` updates triggered by artifact hash changes. Content hashes included in `data/` metadata. |
| **VI. Complexity-Aware Injection** | **Pass** | Explicit sweep of thresholds (a normalized range) across 3 tiers. `policy_rigidity` (conditional variance reduction) calculated as per spec. |
| **VII. Synthetic Validation** | **Pass** | Graphs generated via NetworkX. Validation step ensures path existence before episode start. **Distillation Cost-Benefit Ratio** calculated in `aggregation.py` as `mean_log_prob_shift / (success_rate - success_rate_baseline)` to satisfy SC-002. |

## Project Structure

### Documentation (this feature)
```text
specs/001-opid-routing-complexity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── environment.schema.yaml
    ├── episode_result.schema.yaml
    └── aggregated_metrics.schema.yaml
```

### Source Code (repository root)
```text
projects/PROJ-970-llmxive-follow-up-extending-opid-on-poli/code/
├── src/
│   ├── __init__.py
│   ├── seed.py                 # Reproducibility setup (T008)
│   ├── config.py               # Thresholds, tier params
│   ├── environment/
│   │   ├── __init__.py
│   │   ├── generator.py        # NetworkX graph generation (Tiers 1-3) (T011, T012, T013)
│   │   └── validator.py        # Path existence check (T014)
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── policy.py           # Stochastic Softmax Policy Head (T001, T018)
│   │   └── opid_router.py      # Hindsight injection logic (T019, T020)
│   ├── simulation/
│   │   ├── __init__.py
│   │   ├── runner.py           # Episode loop (streaming) (T024, T025)
│   │   └── metrics.py          # Success rate, entropy variance (T026)
│   └── analysis/
│       ├── __init__.py
│       ├── aggregation.py      # CSV aggregation, conditional variance calc, cost-benefit ratio (FR-004, SC-002)
│       └── stats.py            # ANOVA, Quadratic regression
├── tests/
│   ├── unit/
│   │   ├── test_generator.py
│   │   └── test_router.py
│   └── contract/
│       └── test_schemas.py
├── data/
│   ├── raw/
│   │   └── synthetic_graphs/   # Generated graph files (JSON) (T009)
│   └── processed/
│       └── results.csv         # Aggregated metrics
├── logs/
│   └── simulation.log          # Logging infrastructure (T009, T021)
├── pyproject.toml              # Dependencies, Black config (T002, T003)
├── requirements.txt            # Dependency pins (T002)
├── ruff.toml                   # Linting config (T003)
└── README.md
```

**Structure Decision**: Single project structure (DEFAULT). The research scope is contained within a single simulation pipeline. No separate frontend/backend required. The `src/` layout separates environment generation, agent logic, and analysis to facilitate unit testing and reproducibility.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Three Tiers** | Required to test the "non-monotonic" hypothesis across complexity levels. | A single tier would not reveal the interaction effect between threshold and complexity. |
| **Sequential Streaming** | Required to fit A substantial number of episodes across 11 thresholds into 7GB RAM. | Loading all trajectories into memory would exceed RAM limits during the sweep. |
| **Stochastic Policy Head** | Required to have non-zero baseline entropy variance for the "over-constraining" effect to be measurable. | A rule-based (deterministic) policy has zero entropy, making "variance reduction" a null metric. |
| **Conditional Variance Metric** | Required to isolate the injection effect from the deterministic threshold setting. | Regressing out τ from a variable defined by τ yields only noise; comparing conditional distributions isolates the behavioral effect. |

## FR-SC Mapping

| Requirement | Plan Element |
| :--- | :--- |
| **FR-001** (Tier Gen) | `src/environment/generator.py` (Tiers 1-3) |
| **FR-002** (Threshold) | `src/agent/opid_router.py` (Bernoulli logic) |
| **FR-003** (1000 Episodes) | `src/simulation/runner.py` (Loop count) |
| **FR-004** (Rigidity) | `src/analysis/aggregation.py` (Conditional variance calc) |
| **FR-005** (Success Rate) | `src/simulation/metrics.py` |
| **FR-006** (Sweep) | `src/simulation/runner.py` (Threshold loop) |
| **FR-007** (CPU) | `requirements.txt` (No CUDA deps) |
| **SC-001** (Quadratic) | `src/analysis/stats.py` (Regression) |
| **SC-002** (Cost-Benefit) | `src/analysis/aggregation.py` (Ratio calc: shift / delta_rate) |
| **SC-003** (Residual) | `src/analysis/aggregation.py` (Variance calc) |
| **SC-004** (ANOVA) | `src/analysis/stats.py` (ANOVA) |
| **SC-005** (Feasibility) | Sequential streaming design |