# Implementation Plan: llmXive follow-up: extending "AdaPlanBench: Evaluating Adaptive Planning in Large Language Model Age"

**Branch**: `001-gene-regulation` | **Date**: 2026-07-14 | **Spec**: `specs/001-llmxive-follow-up-extending-adaplanbench/spec.md`
**Input**: Feature specification from `specs/001-llmxive-follow-up-extending-adaplanbench/spec.md`

## Summary

This project extends the AdaPlanBench evaluation by isolating tasks with progressive constraint accumulation (≥5 constraints) to test a "dual-track" architecture. The dual-track approach pairs a Small Language Model (SLM) generator with a deterministic, rule-based constraint store. The primary goal is to determine if explicit constraint tracking significantly mitigates violation rates compared to a monolithic SLM baseline as constraint complexity increases, using a Generalized Linear Mixed Model (GLMM) for statistical validation.

**Critical Implementation Note**: To satisfy the CI resource constraints (limited vCPU, GB RAM, no external API), the "Monolithic Baseline" is implemented as a local Phi-3-mini instance running *without* the resolver. The comparison tests the architectural intervention (resolver) on the *same* generative model, controlling for model capability. Evaluation of external models (GPT-4, Llama-3-70b) is out of scope for this CI run.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `datasets` (HuggingFace), `statsmodels`, `scikit-learn`, `transformers` (CPU-only, 4-bit quantized), `pyyaml`, `pytest`  
**Storage**: Local file system (`data/`), JSON/CSV logs  
**Testing**: `pytest` (unit, integration, contract validation)  
**Target Platform**: Linux (GitHub Actions free-tier: vCPU, 7GB RAM)  
**Project Type**: Research/Computational Experiment  
**Performance Goals**: Execute on CPU within 6 hours; memory < 7GB; no GPU dependency for core logic.  
**Constraints**: No external API calls; strict adherence to data hygiene (checksums); explicit handling of "implicit" constraints as unverified; synthetic proxy generation if real dataset is unavailable.  
**Scale/Scope**: Subset of AdaPlanBench (tasks with ≥5 constraints) or synthetic proxy; A set of human-annotated samples for validation.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action / Reference |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | `requirements.txt` pins versions; random seeds fixed in `code/`; dataset fetch script uses canonical HuggingFace ID or synthetic proxy. |
| **II. Verified Accuracy** | PASS | All citations in `research.md` verified against primary sources; no fabricated URLs. |
| **III. Data Hygiene** | PASS | `data/` files checksummed; raw data preserved; derivations written to new files. Synthetic proxy generation is deterministic and logged. |
| **IV. Single Source of Truth** | PASS | All statistics in `paper/` will trace to `data/processed/*.csv` and `code/analysis/`. |
| **V. Versioning Discipline** | PASS | Content hashes tracked in `state/`; artifact updates trigger timestamp refreshes. |
| **VI. Dual-Track Integrity** | PASS | Code paths for `generator` (`code/agent/generator.py`) and `resolver` (`code/agent/resolver.py`) are strictly separated. |
| **VII. Resource Constraints** | PASS | `code/main.py` includes `ResourceMonitor` logging CPU/RAM; fails fast if limits exceeded. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-adaplanbench/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── execution_log.schema.yaml
│   └── resource_log.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── main.py              # Entry point, resource monitoring, orchestration
├── dataset/
│   ├── loader.py        # Fetch and filter AdaPlanBench (or generate proxy)
│   └── annotator.py     # Sampling for human annotation
├── agent/
│   ├── generator.py     # SLM (Phi-3-mini) interface
│   ├── resolver.py      # Deterministic constraint store & conflict logic
│   └── runner.py        # Execution loop for dual-track and monolithic
├── analysis/
│   ├── power.py         # Power analysis script
│   └── glmm.py          # GLMM fitting and interaction effect testing
├── utils/
│   └── logging.py       # Resource monitoring and structured logging
└── tests/
    ├── unit/
    ├── integration/
    └── contract/

data/
├── raw/
├── processed/
└── annotations/

contracts/
├── dataset.schema.yaml
├── execution_log.schema.yaml
└── resource_log.schema.yaml
```

**Structure Decision**: Single-project structure selected to minimize overhead. The separation of `agent/` into `generator` and `resolver` enforces the Dual-Track Integrity principle (Constitution VI). `analysis/` is isolated to ensure statistical rigor (Constitution I).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Dual-Track Architecture** | Required by Spec FR-002/FR-003 to test explicit memory vs. stochastic generation. | A monolithic baseline alone cannot isolate the "memory" effect from "reasoning" capability. |
| **Explicit Constraint Store** | Required to detect violations deterministically (FR-007) and handle implicit cases (FR-009). | Keyword-only matching in the generator leads to false negatives on complex constraints. |
| **GLMM Analysis** | Required by Spec FR-005 to handle repeated measures (multiple constraints per task) and binary outcomes. The model tests the interaction effect (Architecture * Constraint_Count) with a binomial link function. | Simple t-tests ignore task-level variance and constraint count as a covariate. |

## Phases and Tasks

### Phase 0: Data Acquisition and Validation
- **T001**: Fetch and Validate Dataset.
  - **Input**: None.
  - **Action**: Attempt to fetch AdaPlanBench from HuggingFace. If fetch fails or `progressive_constraints` field is missing, generate a deterministic synthetic proxy dataset with the required structure.
  - **Output**: `data/raw/adaplanbench.jsonl` (or `data/raw/synthetic_proxy.jsonl`), `data/processed/validation_report.json`.
  - **Verification**: Checksum verification; `validation_report.json` confirms dataset structure.

### Phase 1: Data Preparation
- **T013**: Filter and Prepare Tasks.
  - **Input**: `data/raw/adaplanbench.jsonl` (or proxy).
  - **Action**: Filter for tasks with `len(progressive_constraints) >= 5`.
  - **Output**: `data/processed/filtered_tasks.csv`.
  - **Verification**: `pytest tests/unit/test_filter.py::test_constraint_count_calculation`; verify row count matches expected N.

### Phase 2: Agent Implementation
- **T022**: Implement Resolver.
  - **Action**: Implement `code/agent/resolver.py` with logic for explicit constraint checking and `implicit_unverified` logging.
  - **Output**: `code/agent/resolver.py`.
- **T024**: Implement Implicit Constraint Logging.
  - **Action**: Ensure `resolver.py` logs `implicit_unverified` events and flags them for exclusion from primary violation rate.
  - **Output**: Updated `code/agent/resolver.py`.
- **T026a**: Implement Monolithic Runner.
  - **Action**: Implement `code/agent/monolithic_runner.py` to run Phi-3-mini *without* the resolver.
  - **Output**: `data/processed/monolithic_logs.json`.
  - **Verification**: `pytest tests/integration/test_monolithic_execution.py`.
- **T026b**: Implement Dual-Track Runner.
  - **Action**: Implement `code/agent/dual_track_runner.py` to run Phi-3-mini *with* the resolver.
  - **Output**: `data/processed/dual_track_logs.json`.
  - **Verification**: `pytest tests/integration/test_dual_track_execution.py`.

### Phase 3: Execution and Logging
- **T026f**: Merge and Validate Logs.
  - **Action**: Combine `monolithic_logs.json` and `dual_track_logs.json` into `data/processed/execution_traces.csv`.
  - **Output**: `data/processed/execution_traces.csv`.
  - **Verification**: `pytest tests/contract/test_execution_trace_schema.py`.
- **T030**: Power Analysis.
  - **Action**: Run power analysis on `filtered_tasks.csv`.
  - **Output**: `data/processed/power_report.json`.
  - **Verification**: Verify `power_report.json` contains power >= 0.80 for effect size >= 0.15.

### Phase 4: Human Annotation and Validation
- **T033**: Annotate Sample.
  - **Action**: Stratified random sampling of a representative set of tasks from `filtered_tasks.csv`.
  - **Output**: `data/annotations/annotation_sample.csv`.
  - **Verification**: `pytest tests/unit/test_stratified_sampling.py`.
- **T034b**: Validate Exclusion Logic.
  - **Action**: Compare `implicit_unverified` labels from `dual_track_logs.json` against human annotations in `annotation_sample.csv`.
  - **Output**: `data/processed/exclusion_validation_report.json`.
  - **Verification**: Verify agreement rate >= 90% for exclusion decisions.

### Phase 5: Statistical Analysis
- **T034**: Compare Architectures.
  - **Action**: Run GLMM on `execution_traces.csv` to test interaction effect.
  - **Output**: `data/processed/statistical_results.json`.
  - **Verification**: `pytest tests/contract/test_statistical_results_schema.py`.
- **T035**: Calculate Adherence Rate.
  - **Action**: Calculate adherence rate for Dual-Track and compare to threshold.
  - **Output**: `data/processed/adherence_verification.json`.
  - **Verification**: Verify `adherence_verification.json` contains threshold_passed boolean.
