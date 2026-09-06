# Implementation Plan: OPID Critical-First Routing Complexity Analysis

**Branch**: `001-opid-routing-complexity` | **Date**: 2026-08-24 | **Spec**: `specs/001-opid-routing-complexity/spec.md`
**Input**: Feature specification from `specs/001-opid-routing-complexity/spec.md`

## Summary

This feature implements a controlled empirical study to investigate the non-monotonic relationship between "critical-first" routing density and policy performance in the OPID (On-Policy Skill Distillation) framework. The system generates synthetic State-Graph Environments across three complexity tiers (Deterministic, Stochastic, High-Entropy) and sweeps a tunable routing threshold (0.0 to 1.0). It executes multiple episodes per setting to measure success rates and policy rigidity (action entropy variance), identifying the inflection point where skill injection becomes counterproductive. The implementation prioritizes CPU feasibility on GitHub Actions runners, utilizing NetworkX for graph generation and a lightweight rule-based policy head to ensure reproducibility within resource constraints.

## Technical Context

**Language/Version**: Python  
**Primary Dependencies**: `networkx` (graph generation), `numpy` (numerical ops), `pandas` (data logging), `scipy` (statistical analysis), `pytest` (testing).  
**Storage**: Local CSV/Parquet files under `data/` for episode results; no external database.  
**Testing**: `pytest` with contract tests validating graph properties and statistical output schemas.  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Computational Research / Simulation Engine.  
**Performance Goals**: Complete [deferred] total episodes (3 tiers × 11 thresholds × multiple episodes) within 6 hours; memory footprint < 7 GB via sequential processing.
**Constraints**: CPU-only execution; no GPU/CUDA; synthetic data only (no external datasets); strict adherence to [deferred] episodes per setting for statistical power.
**Scale/Scope**: Multiple complexity tiers, threshold settings, ~k simulated episodes.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: **COMPLIANT**. The plan mandates pinned `requirements.txt`, random seed initialization in `code/`, and synthetic graph generation logic that is deterministic given a seed. No external data dependencies exist to break reproducibility.
- **Principle II (Verified Accuracy)**: **COMPLIANT**. The plan relies on the OPID paper (verified as having no external URL source in the input block, so cited by title only) and internal synthetic logic. No external URLs are fabricated.
- **Principle III (Data Hygiene)**: **COMPLIANT**. All generated episode data will be written to `data/` with checksums recorded. Raw synthetic graphs will be regenerated on-the-fly or cached with versioning; no in-place modification.
- **Principle IV (Single Source of Truth)**: **COMPLIANT**. All success rates and entropy variances will be computed by `code/` scripts and written to `data/` CSVs. The paper will reference these files directly.
- **Principle V (Versioning Discipline)**: **COMPLIANT**. The plan includes a structure for content hashing of generated data files and updating the project state YAML.
- **Principle VI (Complexity-Aware Skill Injection)**: **COMPLIANT**. The plan explicitly structures the experiment around the three defined tiers and the routing threshold sweep to measure the non-monotonic relationship and "policy rigidity."
- **Principle VII (Synthetic State-Graph Validation)**: **COMPLIANT**. The environment generation uses NetworkX to create ground-truth paths independent of the policy. The "distillation cost-benefit ratio" is planned as a calculated metric comparing log-probability shifts to success rates.

## Project Structure

### Documentation (this feature)

```text
specs/001-opid-routing-complexity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-970-llmxive-follow-up-extending-opid-on-poli/code/
├── __init__.py
├── config.py            # Hyperparameters, seeds, tier definitions
├── env/
│   ├── __init__.py
│   ├── graph_generator.py  # NetworkX logic for Tiers 1-3
│   └── state_graph.py      # StateGraph entity definition
├── agent/
│   ├── __init__.py
│   ├── policy.py           # Lightweight baseline policy
│   └── opid_router.py      # Critical-first routing logic
├── experiments/
│   ├── __init__.py
│   ├── runner.py           # Episode execution loop
│   └── analyzer.py         # Statistical analysis (ANOVA, regression)
├── utils/
│   ├── __init__.py
│   └── metrics.py          # Entropy variance, success rate calculators
├── main.py                 # Entry point for sweep
└── tests/
    ├── test_graph_gen.py
    └── test_metrics.py

projects/PROJ-970-llmxive-follow-up-extending-opid-on-poli/data/
├── raw/
│   └── synthetic_graphs/   # Cached graph seeds (optional)
└── processed/
    ├── episode_results.csv
    └── summary_stats.csv
```

**Structure Decision**: Single project structure selected. The complexity of the research (graph gen, agent, analysis) fits within a modular `code/` directory. No web or mobile components are required. The separation of `env`, `agent`, and `experiments` ensures clear boundaries for the "Synthetic State-Graph Validation" and "Complexity-Aware Skill Injection" principles.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | The plan adheres to the minimal viable structure for a computational research project. | N/A |
