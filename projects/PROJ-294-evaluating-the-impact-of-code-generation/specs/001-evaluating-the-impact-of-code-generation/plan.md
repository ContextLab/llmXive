# Implementation Plan: Evaluating the Impact of Code Generation Models on Code Testability

**Branch**: `294-evaluating-impact-code-gen-testability` | **Date**: 2026-06-25 | **Spec**: `specs/294-evaluating-impact-code-generation/spec.md`
**Input**: Feature specification from `/specs/294-evaluating-impact-code-generation/spec.md`

## Summary

This project evaluates how code generation models (specifically Salesforce/codegen-mono and CodeLlama variants) impact the **testability** of generated code compared to human reference solutions. The technical approach involves downloading the HumanEval benchmark, generating code samples via API (with retry logic), running static analysis (Radon for complexity), **mutation testing (using `mutmut` for testability)**, and executing test suites (for correctness). The output is a paired JSON dataset, a Markdown report with visualizations, and a sensitivity analysis across model variants.

**Key Methodological Correction**: The study explicitly **replaces** `branch_coverage_pct` with **Mutation Score** as the primary metric for "testability". Branch coverage on the HumanEval test suite is a measure of *correctness* (does it pass the specific tests?), not *testability* (is the code resistant to perturbation?). Mutation score provides a scientifically valid proxy for testability.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets`, `huggingface_hub`, `radon`, `mutmut`, `coverage`, `scipy`, `statsmodels`, `pandas`, `matplotlib`, `seaborn`, `pyyaml`, `requests`  
**Storage**: Local file system (`data/raw`, `data/analysis`, `data/metadata.yaml`)  
**Testing**: `pytest` (unit tests for metric calculators, integration tests for pipeline)  
**Target Platform**: Linux (GitHub Actions runner: CPU, 7GB RAM)  
**Project Type**: Research CLI / Data Pipeline  
**Performance Goals**: Process 164 HumanEval tasks within 6 hours; generate reports in <10 minutes.  
**Constraints**: No local GPU (CPU-first for stats); must run on free-tier CI; strict checksum validation (SHA256); no PII in data.  
**Scale/Scope**: The HumanEval full set; -4 model variants for sensitivity analysis (with fallback).

> **Methodological Note**: The plan explicitly **excludes** "stratified sampling based on human pass-rate quartiles" as identified in the unresolved panel concerns. The study will use the full HumanEval set or a random subset if compute constraints require it, but **never** a pass-rate stratified subset, as the spec does not authorize this scope change.

### Worst-Case Budget Calculation (Addressing Feasibility)
- **Task Count**: 164 tasks.
- **Estimated Cost per Task**:
  - Generation (CPU-tractable model): acceptable latency within a single session (with retry).
  - Static Analysis (Radon): ~s.
  - Mutation Testing (`mutmut`): CPU intensive, with expected execution times varying based on codebase size and mutation complexity..
  - Execution (Coverage/Pass): ~several seconds.
 - **Total per Task**: [deferred].
- **Total Runtime**: 164 * 60s = 9840s ≈ **hours**.
- **Overhead**: [deferred] (setup, I/O, retries).
- **Hard Cap**: **4.0 hours**.
- **Fallback**: If runtime exceeds 4.0 hours, the pipeline triggers a `TIMEOUT` signal, aborts the current batch, and re-runs on a **random -task sample** to ensure a valid result is produced within the -hour CI limit.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ Met | Random seeds pinned in `code/config.py`. All external datasets fetched from `openai/openai_humaneval` via `datasets` library. |
| **II. Verified Accuracy** | 🟡 Planned (Phase 3) | `code/validate_citations.py` is **planned** for Phase 3. **Current State**: Script is not yet fully implemented (missing CLI args, subprocess calls). The plan asserts it will be implemented before report generation. |
| **III. Data Hygiene** | 🟡 Planned (Phase 2) | `data/raw/humaneval.parquet` checksummed on download. Metrics written to `data/analysis/metrics.json` with SHA256 hash in `state/artifact_hashes.yaml`. **Current State**: `metrics.json` is a target artifact for Phase 2. |
| **IV. Single Source of Truth** | 🟡 Planned (Phase 2) | All figures/stats in reports generated programmatically from `data/analysis/metrics.json`. No hand-typed numbers. **Current State**: `metrics.json` does not exist yet. |
| **V. Versioning Discipline** | 🟡 Planned (Phase 3) | `state/projects/PROJ-294...yaml` updated on every artifact write. Content hashes tracked for `code/` and `data/`. **Current State**: `state/validation_results.yaml` is a target artifact for Phase 3 and does not exist yet. |
| **VI. Testability Evaluation** | ✅ Met (Methodology) | `radon` (complexity) and `mutmut` (mutation score) used on **both** human and LLM code. Results stored in `data/analysis/` with accompanying provenance metadata. |
| **VII. Benchmark Integrity** | ✅ Met | HumanEval downloaded directly from HuggingFace (`openai/openai_humaneval`) without modification. Version recorded in `data/metadata.yaml`. |

## Project Structure

### Documentation (this feature)

```text
specs/294-evaluating-impact-code-generation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (Updated to remove T010b/T010c)
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Seeds, API keys, paths
├── download_data.py     # FR-001: HumanEval download + checksum
├── generate_code.py     # FR-002: LLM generation + retry logic + GPU Escape Hatch
├── analyze_metrics.py   # FR-003, FR-005: Radon, Mutmut, Coverage
├── statistical_tests.py # FR-004, FR-008: Wilcoxon, McNemar, Power Analysis
├── report_generator.py  # FR-006, FR-010: Markdown + Figures + Power Analysis
├── validate_citations.py# FR-010: Citation validation logic (Phase 3)
├── utils.py             # FR-007, FR-011: Logging, Hashing
└── main.py              # Orchestration script
```

**Structure Decision**: Single project structure (`code/`, `data/`, `tests/`) selected to maintain a tight coupling between data processing and analysis scripts, ensuring reproducibility and ease of CI execution.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **None** | The project scope is strictly bounded by the HumanEval dataset and CPU-first statistical methods. No architectural complexity is required beyond standard data pipeline patterns. | N/A |

## Phase Breakdown

### Phase 0: Data Acquisition & Validation
- **Goal**: Download HumanEval, verify checksums, and setup environment.
- **FRs**: FR-001, FR-007.
- **Output**: `data/raw/humaneval.parquet`, `state/artifact_hashes.yaml`.

### Phase 1: Code Generation & Sensitivity (FR-002, FR-009)
- **Goal**: Generate code for all tasks.
- **Logic**:
  1. Attempt generation with `CodeLlama-7b` if `GENERATE_WITH_GPU` is set (triggers remote Kaggle execution).
  2. If GPU execution fails or flag is unset, **mandatory fallback** to `Salesforce/codegen-mono-350M` (CPU).
  3. Implement exponential backoff (max limited retries).
- **Output**: `data/analysis/model_outputs/`.

### Phase 2: Metric Calculation (FR-003, FR-005)
- **Goal**: Compute Complexity, Mutation Score, and Pass Rate.
- **Logic**:
  1. Run `radon` for Cyclomatic Complexity.
  2. Run `mutmut` for Mutation Score (Testability Proxy).
  3. Run `coverage.py` for Pass Rate (Correctness Proxy).
  4. Write results to `data/analysis/metrics.json`.
- **Output**: `data/analysis/metrics.json`.

### Phase 3: Statistical Analysis & Validation (FR-004, FR-008, FR-010)
- **Goal**: Perform hypothesis tests and validate citations.
- **Logic**:
  1. Run `statistical_tests.py`: Wilcoxon (Complexity, Mutation Score), McNemar (Pass Rate), Power Analysis.
  2. Write `state/validation_results.yaml` and `state/power_analysis.yaml`.
  3. **Validation Gate**: Run `validate_citations.py`. If exit code != 0, **halt pipeline** (do not generate report).
- **Output**: `state/validation_results.yaml`, `state/power_analysis.yaml`.

### Phase 4: Reporting (FR-006)
- **Goal**: Generate Markdown report.
- **Logic**: `report_generator.py` reads `data/analysis/metrics.json`, `state/validation_results.yaml`, and `state/power_analysis.yaml` to produce the final report.
- **Output**: `report.md`.
