# Implementation Plan: llmXive follow-up: extending "S-Agent: Spatial Tool-Use Elicits Reasoning for Spatial Intelligence"

**Branch**: `001-symbolic-spatial-reasoning` | **Date**: 2026-07-03 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-symbolic-spatial-reasoning/spec.md`

## Summary

This feature implements a deterministic Constraint Satisfaction Problem (CSP) solver to evaluate spatial reasoning on the S-Agent-300K dataset, replacing neural VLM planning with symbolic logic. The primary goal is to determine if 3D geometric evidence alone (coordinates, object relations) suffices for accurate spatial counting and positioning, or if neural "semantic disambiguation" is required. The implementation involves extracting geometric constraints from a stratified sample of n=1,000 static scenes, solving them via `python-constraint` or `ortools` on CPU, and benchmarking accuracy/latency against the original VLM baseline and ground truth.

**Critical Constraint**: The plan includes a mandatory **Distributional Validity Gate** (see Research.md) to ensure that any proxy dataset used shares the same statistical distribution of spatial complexity as the target S-Agent-300K dataset. If this gate fails, the primary analysis is aborted or re-labeled as a "Pilot/Proxy" study.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `python-constraint` (or `google-or-tools`), `pandas`, `scipy`, `pytest`, `huggingface_hub`, `scikit-learn` (for distributional checks)  
**Storage**: Local file system (CSV/JSON/Parquet) under `data/` and `data/derived/`  
**Testing**: `pytest` (unit tests for constraint logic, integration tests for pipeline, distributional validity tests)  
**Target Platform**: Linux (GitHub Actions Free Tier: **2 CPU, 7 GB RAM, 14 GB Disk**)  
**Project Type**: Computational Research / Data Analysis Pipeline  
**Performance Goals**: Process [deferred] scenes in **< 6 hours** (hard cap derived from 2-core CPU constraint); < 7 GB RAM peak; < 60s per scene.
**Constraints**: CPU-only execution for symbolic solver; no GPU for symbolic path; strict exclusion of VLM traces from solver input.  
**Scale/Scope**: n=1,000 scenes (sampled from S-Agent-300K or verified proxy); A set of output artifacts (predictions, benchmark report, failure analysis).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
|-----------|-------------------|-----------------------|
| **I. Reproducibility** | PASS | All random seeds pinned in `code/`; `huggingface_hub` used for deterministic dataset fetching; `requirements.txt` pins versions. |
| **II. Verified Accuracy** | PASS | **Verified Accuracy Gate**: Pipeline invokes `validate_citations` to check citations against the "Verified Datasets" block. Exits if mismatch. Citations in `research.md` restricted to verified dataset URLs; ground truth used as immutable baseline. |
| **III. Data Hygiene** | PASS | Raw data checksummed; derived data (constraints) written to new files; no in-place modification. |
| **IV. Single Source of Truth** | PASS | All metrics (F1, Latency) trace to `data/derived/benchmark_results.csv`; no hand-typed numbers in paper. |
| **V. Versioning Discipline** | PASS | **Mechanism**: `code/hygiene.py` computes SHA-256 hashes for `data/raw/*`, `data/derived/constraints.jsonl`, `data/derived/predictions.jsonl`, and `data/derived/benchmark_results.csv`. These hashes are recorded in `state/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat.yaml` `artifact_hashes` map. State timestamp is updated upon any artifact change. |
| **VI. Deterministic Planning** | PASS | CSP solver logic is purely symbolic; identical inputs yield identical outputs; no neural stochasticity in solver. |
| **VII. Neuro-Symbolic Baseline Integrity** | PASS | Solver input strictly limited to extracted geometric constraints; VLM traces excluded from solver input to isolate "geometric" vs "semantic" capability. |
| **VIII. Distributional Validity** | PASS | **New Gate**: Before main execution, `code/data/validate_distribution.py` runs KS-tests on object density, spatial variance, and relation types between proxy and target. If p < 0.05, the run is flagged as "Pilot/Proxy" or aborted. This is a hard blocking condition for the primary analysis. |

## Project Structure

### Documentation (this feature)

```text
specs/001-symbolic-spatial-reasoning/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Design Artifacts (Pre-Implementation)
│   ├── dataset.schema.yaml
│   ├── solver_output.schema.yaml
│   └── benchmark_result.schema.yaml
└── tasks.md             # Phase 2 output
```

**Note on Contracts**: The `contracts/` directory contains **Design Artifacts (Pre-Implementation)**. These schema files are defined *in this plan phase* to serve as the strict interface specifications for the implementation phase. They are not generated outputs of the plan; they are the *inputs* that the implementation must satisfy.

### Source Code (repository root)

```text
projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── config.py                 # Paths, seeds, sample size config
│   ├── hygiene.py                # Computes SHA-256 hashes and updates state YAML
│   ├── data/
│   │   ├── download.py           # Fetches S-Agent-300K subset (or Pilot proxy)
│   │   ├── extract_geometry.py   # Extracts constraints to JSON/CSV
│   │   └── validate_distribution.py # NEW: Runs KS-tests for distributional validity (GATE)
│   ├── solver/
│   │   ├── __init__.py
│   │   ├── csp_engine.py         # Core CSP logic (python-constraint)
│   │   └── run_solver.py         # Batch execution script
│   ├── benchmark/
│   │   ├── __init__.py
│   │   ├── metrics.py            # F1, Exact Match, Latency
│   │   └── analyze_failures.py   # Categorizes "Geometric" vs "Semantic" using GT projection
│   └── main.py                   # Pipeline orchestrator
├── data/
│   ├── raw/                      # Downloaded S-Agent-300K subset
│   ├── derived/                  # Extracted constraints, predictions
│   └── results/                  # Benchmark reports, failure logs
├── specs/001-symbolic-spatial-reasoning/
│   └── ... (docs)
└── tests/
    ├── unit/
    │   ├── test_csp_logic.py
    │   ├── test_metrics.py
    │   └── test_distribution_validity.py
    └── integration/
        └── test_pipeline.py
```

**Structure Decision**: Selected a modular `code/` layout with separation of concerns: `data/` for ingestion/processing, `solver/` for the core symbolic logic, and `benchmark/` for evaluation. This aligns with the Constitution's "Single Source of Truth" by ensuring data flow is explicit and traceable from raw download to final metric.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Separate Solver Module** | The CSP logic must be isolated from data loading to ensure it is purely symbolic and deterministic. | Embedding solver logic in the data loader would risk accidental coupling with VLM traces or non-deterministic data fetching. |
| **Explicit Failure Analysis (GT Projection)** | Required by FR-006 and US-3 to distinguish "Geometric Ambiguity" from "Semantic Gap". | A simple accuracy score cannot answer the research question of *why* the symbolic approach fails. The GT projection mechanism is necessary for construct validity. |
| **Distributional Validity Gate** | Required by methodology panel to ensure proxy datasets are statistically equivalent to S-Agent-300K. | Skipping this risks external validity failure; the study would measure a different population than intended. This gate is now a hard blocking condition. |

## Feasibility Note

The **6-hour wall-clock time** goal is explicitly mapped to the **2-CPU, 7 GB RAM** GitHub Actions Free Tier constraints. The CSP solver's complexity is O(1) per scene for the given n=1,000 (backtracking on small graphs). This ensures the 2-core CPU can meet the deadline without requiring GPU acceleration or complex parallelization. The added distributional validity check (KS-tests) is computationally negligible (<1 minute) for n=1,000.