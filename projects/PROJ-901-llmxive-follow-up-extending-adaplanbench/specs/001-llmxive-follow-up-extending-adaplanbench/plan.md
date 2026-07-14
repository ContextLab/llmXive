# Implementation Plan: llmXive follow-up: extending "AdaPlanBench: Evaluating Adaptive Planning in Large Language Model Age"

**Branch**: `001-gene-regulation` | **Date**: 2026-07-14 | **Spec**: `specs/001-gene-regulation/spec.md`
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary

This feature extends the AdaPlanBench evaluation by implementing a **Dual-Track Agent Architecture** to test the hypothesis that explicit, deterministic constraint tracking mitigates performance degradation in Large Language Models (LLMs) under high constraint loads. The plan covers the implementation of a rule-based conflict resolution module, a filtered dataset subset (≥5 constraints), and a Generalized Linear Mixed Model (GLMM) analysis to quantify the interaction between constraint count and architecture type on *initial* violation rates. All execution is constrained to a CPU-only, GB RAM environment.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers` (CPU-optimized), `datasets`, `pandas`, `statsmodels`, `scikit-learn`, `pytest`  
**Storage**: Local file system (CSV/Parquet) for intermediate logs and final artifacts; no external database.  
**Testing**: `pytest` (unit tests for constraint logic, integration tests for agent execution, statistical sanity checks).  
**Target Platform**: Linux (GitHub Actions free-tier runner: limited vCPU, moderate RAM, no GPU).  
**Project Type**: Computational Research / Data Analysis Pipeline  
**Performance Goals**: Complete full execution (filtering, dual-track/monolithic inference, logging, GLMM) within 6 hours; memory usage < 6.5GB to allow headroom for OS overhead.  
**Constraints**: No GPU acceleration; no 8-bit/4-bit quantization requiring CUDA; no external API calls for inference (local SLM only); strict adherence to dataset filtering rules (≥5 constraints).  
**Scale/Scope**: Subset of AdaPlanBench household tasks; a sample size of tasks for human annotation validation.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/`. Dataset fetch logic uses canonical sources. `requirements.txt` pins all versions. |
| **II. Verified Accuracy** | **PASS (Conditional)** | All dataset citations in `research.md` strictly adhere to the "Verified datasets" block. The project is **BLOCKED** if the AdaPlanBench dataset (ID: `adaplanbench/adaplanbench`) is unreachable or lacks the `progressive_constraints` field. |
| **III. Data Hygiene** | **PASS** | Raw data preserved in `data/raw/`. Filtered data written to `data/processed/` with checksums recorded in state file. |
| **IV. Single Source of Truth** | **PASS** | All statistics in the final paper will be derived from `data/processed/` and `code/` outputs, not hand-typed. |
| **V. Versioning Discipline** | **PASS** | A `hash_artifacts.py` script (mandated in `code/`) computes SHA-256 hashes for all files in `data/` and updates the project state YAML upon any change. This script is executed as part of the CI pipeline. |
| **VI. Dual-Track Architecture Integrity** | **PASS** | Code structure enforces separation: `services/generator.py` (SLM) and `services/constraint_store.py` (Deterministic). Logs distinguish between "model error" and "rule-based correction". |
| **VII. Resource-Constrained Execution** | **PASS** | `code/` includes a resource monitor wrapper that logs CPU/RAM usage per task. Execution will fail fast if limits are exceeded. |

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── execution-log.schema.yaml
│   ├── filtered-task.schema.yaml
│   └── human-annotation.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-901-llmxive-follow-up-extending-adaplanbench/
├── data/
│   ├── raw/                  # Original AdaPlanBench dump (if accessible)
│   └── processed/            # Filtered subset (≥5 constraints), logs, and analysis results
├── code/
│   ├── __init__.py
│   ├── config.py             # Paths, seeds, resource limits
│   ├── dataset/
│   │   ├── loader.py         # AdaPlanBench fetcher & filter logic
│   │   └── annotator.py      # Human annotation interface (CLI)
│   ├── agent/
│   │   ├── base.py           # Abstract agent interface
│   │   ├── monolithic.py     # Baseline: Direct SLM prompt
│   │   ├── dual_track.py     # Generator + Constraint Store + Resolver
│   │   └── resolver.py       # Rule-based conflict detection (FR-007, FR-008, FR-009)
│   ├── analysis/
│   │   ├── power.py          # Power analysis script (FR-011)
│   │   └── glmm.py           # GLMM fitting and diagnostics (FR-005)
│   ├── hash_artifacts.py     # Versioning script for Constitution Principle V
│   └── main.py               # Orchestration script
├── tests/
│   ├── unit/
│   │   ├── test_resolver.py
│   │   └── test_filter.py
│   └── integration/
│       └── test_agent_flow.py
├── requirements.txt
└── README.md
```

**Structure Decision**: The single-project structure is chosen to minimize overhead and ensure all components (data loading, agent execution, analysis) are tightly coupled for reproducibility. The separation of `agent/` into `monolithic` and `dual_track` ensures the "Dual-Track Architecture Integrity" principle is enforced at the code level.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Dual-Track vs. Monolithic** | Required to isolate the effect of explicit memory. | A single "smart" prompt cannot distinguish between model failure and memory failure. |
| **Rule-based Resolver** | Required for deterministic constraint checking (FR-007). | Using an LLM to check constraints introduces the same failure mode we are trying to measure. |
| **GLMM Analysis** | Required for binary repeated measures (FR-005). | Simple t-tests or ANOVA ignore the nested structure of tasks and varying constraint counts. |
| **Human Annotation Sample** | Required to validate the rule-based logic (FR-010). | Automated metrics alone cannot verify "implicit" constraint handling or false negatives. |