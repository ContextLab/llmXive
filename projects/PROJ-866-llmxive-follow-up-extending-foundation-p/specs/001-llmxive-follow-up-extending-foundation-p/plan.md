# Implementation Plan: llmXive follow-up: extending "Foundation Protocol: A Coordination Layer for Agentic Society"

**Branch**: `001-policy-compression-tradeoff` | **Date**: 2026-07-11 | **Spec**: `specs/001-policy-compression-tradeoff/spec.md`
**Input**: Feature specification from `/specs/001-policy-compression-tradeoff/spec.md`

## Summary

This project implements a CPU-only simulation pipeline to quantify the trade-off between context compression (via graph-traversal depth limits) and policy-violation error rates in multi-agent workflows. The system generates a set of synthetic workflows with varying delegation depths and policy complexities., executes them against an independent Oracle Policy Engine (simulated agent logic) under "Full Context" and "Compressed Context" (BFS/DFS limited depth) regimes, and performs Generalized Linear Mixed-Effects Modeling (GLMM) to identify the "safe operating zone" where efficiency gains do not breach a [deferred] error bound. The implementation strictly adheres to the GitHub Actions free-tier constraints (limited CPU, constrained RAM) and ensures reproducibility via pinned seeds and checksummed artifacts.

**Key Updates**: 
- Statistical analysis now uses GLMM with random intercepts for workflow_id to handle hierarchical clustering.
- Oracle logic simulates agent deduction rather than simple set-membership checks.
- Explicit handling of edge cases ('[deferred]' values) and invalid workflows.
- Threshold output rounded to 2 decimal places (FR-006).
- Wall-clock time measurement recorded (SC-005).
- Specific tokenizer `cl100k_base` mandated (FR-009).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `networkx` (graph traversal), `tiktoken` (token counting, **model: cl100k_base**), `scikit-learn` (regression), `pandas` (data handling), `pytest` (testing), `pm4py` (synthetic log generation/verification), `statsmodels` (GLMM), `scipy` (trend tests).  
**Storage**: Local filesystem (`data/raw/`, `data/processed/`, `data/results/`).  
**Testing**: `pytest` with unit tests for graph generation, compression logic, statistical analysis, and **Oracle Independence Verification**.  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` runner).  
**Project Type**: Computational research simulation / CLI tool.  
**Performance Goals**: Complete 500 workflow generations + ~-5000 execution runs (500 workflows × 1 Full + -9 Compressed depths) + analysis within 4 hours on 2 vCPU.  
**Constraints**: CPU-only (no GPU), <7GB RAM peak, deterministic output (fixed seeds), no external API calls for data.  
**Scale/Scope**: A set of synthetic workflows, variable execution runs (approx -5000), 1 regression curve, 1 threshold report.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: **PASS**. The plan mandates pinned seeds in `code/`, deterministic generation logic, and a `requirements.txt` for isolated execution. All data artifacts will be checksummed.
- **Principle II (Verified Accuracy)**: **PASS**. All statistical methods (GLMM, bootstrapping) are cited to standard references. The "Verified datasets" block in `research.md` will strictly use the provided `pm4py` synthetic generation recipe as the data source, avoiding fabricated URLs.
- **Principle III (Data Hygiene)**: **PASS**. The plan includes a `checksums.json` generation step. Raw synthetic data is generated once and stored; derivations (compressed logs) are written to new files. No in-place modification.
- **Principle IV (Single Source of Truth)**: **PASS**. The `data/results/tradeoff_curve.csv` will be the sole source for the paper's figures. The code will read this CSV to generate plots, ensuring no hand-typed numbers. The `analysis_results.json` is the intermediate artifact for code logic, derived from the same logs.
- **Principle V (Versioning Discipline)**: **PASS**. The plan includes a script to update `state/projects/...yaml` with artifact hashes upon completion.
- **Principle VI (Deterministic State-Modeling)**: **PASS**. The architecture explicitly separates the "Oracle Policy Engine" (ground truth) from the "Compressed Context" execution engine. The validation logic compares the compressed result *against* the Oracle, preventing circular validation. **Note**: A specific unit test (`test_oracle_independence`) will verify that the Oracle module is not imported by the Compressed Executor logic.
- **Principle VII (Resource-Constrained Execution Fidelity)**: **PASS**. The plan uses `networkx`, `tiktoken`, and `statsmodels` (CPU-native) and avoids loading large LLMs. The workflow limit ensures memory usage stays well under a practical threshold..

## Project Structure

### Documentation (this feature)

```text
specs/001-policy-compression-tradeoff/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── workflow.schema.yaml
│   ├── execution_log.schema.yaml
│   ├── tradeoff_curve.schema.yaml
│   └── analysis_results.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── models/
│   ├── workflow.py          # Workflow graph definition
│   ├── policy.py            # Oracle Policy Engine logic (INDEPENDENT)
│   └── compression.py       # BFS/DFS traversal logic
├── services/
│   ├── generator.py         # Synthetic workflow generator (500 workflows)
│   ├── executor.py          # Full/Compressed execution engine
│   └── analyzer.py          # GLMM, trend tests, and threshold analysis
├── cli/
│   └── run_simulation.py    # Main entry point
└── lib/
    └── utils.py             # Tokenizer wrapper (cl100k_base), checksum utilities

data/
├── raw/
│   └── workflows.json       # Generated 500 workflows
├── processed/
│   ├── full_context_logs.json
│   └── compressed_context_logs.json
└── results/
    ├── tradeoff_curve.csv   # SSoT for paper
    ├── threshold_report.json
    └── run_metrics.json     # Wall-clock time (SC-005)

tests/
├── contract/
│   └── test_schemas.py      # Validates JSON against YAML schemas
├── integration/
│   └── test_pipeline.py     # End-to-end simulation test
└── unit/
    ├── test_generator.py    # Verifies A set of unique workflows, depth distribution
    ├── test_compression.py  # Verifies token reduction logic
    ├── test_oracle_independence.py # Verifies Oracle is not called by Compressed Executor
    └── test_analyzer.py     # Verifies GLMM and threshold detection
```

**Structure Decision**: The "Single project" structure is selected. The project is a self-contained simulation pipeline requiring no frontend or separate backend services. The separation of `models`, `services`, and `cli` ensures clear boundaries between data definition, logic execution, and orchestration, facilitating unit testing and reproducibility.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | Constitution Check passed. | N/A |

## Specific Implementation Tasks (Addressing Panel Concerns)

- **T-Gen-Adaptive**: Implement adaptive sampling in `generator.py` to densify depth steps near the anticipated 1% error threshold.
- **T-Oracle-Logic**: Implement Oracle as a "Simulated Agent" that attempts deduction, not just set-membership.
- **T-Stat-GLMM**: Implement GLMM with random intercepts in `analyzer.py` using `statsmodels`.
- **T-Stat-Trend**: Implement Cochran-Armitage trend test for monotonicity verification.
- **T-Edge-Case**: Implement logic to output `[deferred]` for `context_reduction_pct` in single-node and depth=0 cases.
- **T-Format-Round**: Ensure threshold output is rounded to 2 decimal places.
- **T-Measure-Time**: Implement wall-clock time measurement and save to `run_metrics.json`.
- **T-Verify-Oracle**: Unit test to ensure `models/policy.py` is not imported by `services/executor.py` for compression logic.
- **T-Tokenizer**: Ensure `tiktoken` uses `cl100k_base` model explicitly.
