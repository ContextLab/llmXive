# Implementation Plan: Reproduce & Validate NEO-ov One-Vision Model

**Branch**: `001-reproduce-neo-ov` | **Date**: 2026-05-31 | **Spec**: `specs/001-reproduce-neo-ov/spec.md`
**Input**: Feature specification from `specs/001-reproduce-neo-ov/spec.md`

## Summary

This project implements a CPU-tractable reproduction and validation pipeline for the "NEO-ov" (Native One-Vision) model described in the paper "From Pixels to Words -- Towards Native One-Vision Models at Scale." The primary objective is to verify that the vendored codebase executes successfully on free-tier CI hardware (a limited number of CPU cores, constrained RAM, and no GPU) while generating valid prediction artifacts and aggregate metrics. The plan explicitly addresses the methodological critique regarding the "at Scale" claim by documenting the absence of quantitative scaling law analysis in the final report, distinguishing between architectural scale (parameter count) and data/compute scaling laws.

## Technical Context

**Language/Version**: Python 3.9+ (compatible with `VLMEvalKit` and `transformers` CPU wheels)  
**Primary Dependencies**: `torch` (CPU-only), `transformers`, `vlmevalkit` (vendored or installed via pip), `pandas`, `pyyaml`, `requests`, `scipy` (for Wilson score interval)  
**Storage**: Local file system (temporary artifacts, JSON/CSV outputs)  
**Testing**: `pytest` (unit tests for pipeline logic), manual validation of output JSON against schema  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7 GB RAM)  
**Project Type**: CLI/Scientific Validation Script  
**Performance Goals**: Complete inference on ≤1000 samples within 6 hours; memory usage <7 GB peak  
**Constraints**: No CUDA/GPU usage; no 8-bit/4-bit quantization requiring bitsandbytes; strict sample cap (≤1000) to prevent timeout; no scaling exponent fitting performed.  
**Scale/Scope**: Single feature branch; validation limited to functional reproduction on a fixed-size subset of MMBench (500-1000 samples).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on constitution file*

- **Principle 1: Reproducibility**: The plan mandates the use of the specific `VLMEvalKit` entry point and a fixed sample size to ensure the execution is reproducible on identical hardware constraints.
- **Principle 2: Transparency of Limitations**: The plan explicitly requires a "Methodological Notes" section in the final report (FR-005) to address the "at Scale" critique, ensuring the distinction between architectural size and scaling laws is clear.
- **Principle 3: Resource Feasibility**: The plan enforces a hard sample cap (FR-006) and CPU-only execution (FR-001) to guarantee the job completes within the 6-hour CI window and 7 GB RAM limit.
- **Principle 4: Data Integrity**: The plan requires the generation of structured artifacts (FR-002) with non-empty predictions (SC-002) to validate data flow integrity.

## Project Structure

### Documentation (this feature)

```text
specs/001-reproduce-neo-ov/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 0 input (existing schema)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
├── neo_ov/
│   ├── __init__.py
│   ├── inference.py       # Main inference logic wrapper
│   ├── config.py          # Configuration for sample limits and CPU flags
│   └── utils.py           # Logging and error handling utilities
├── scripts/
│   ├── run_smoke_test.py  # Entry point for 5-sample validation
│   ├── run_validation.py  # Entry point for 500-sample validation
│   └── generate_report.py # Script to compile metrics and limitations
├── data/
│   └── samples/           # Local cache for downloaded dataset subsets
└── outputs/
    ├── predictions/       # JSON/CSV artifacts
    └── reports/           # Final validation markdown reports

tests/
├── contract/
│   ├── test_prediction_schema.py
│   └── test_report_content.py
├── integration/
│   └── test_cpu_inference.py
└── unit/
    └── test_config_limits.py
```

**Structure Decision**: The project adopts a single-project structure (`src/neo_ov`) to minimize overhead and dependency resolution complexity on the CI runner. The separation of `scripts/` for entry points allows for distinct execution paths (smoke test vs. full validation) without modifying core logic. The `contracts/` directory hosts the existing JSON schema for prediction artifacts to ensure automated validation.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The project scope is strictly limited to functional reproduction on a fixed subset. | N/A |

## Phase Breakdown

### Phase 0: Environment & Dataset Verification
- **Step 0.1**: Verify availability of the NEO-ov codebase in the submodule.
- **Step 0.2**: Confirm `VLMEvalKit` installation supports CPU-only execution (no CUDA import errors).
- **Step 0.3**: Download and verify the MMBench dataset subset (500-1000 samples) from the verified HuggingFace URL.
- **Step 0.4**: Validate that the dataset contains the required image-text pairs for the inference pipeline.
- **FR Coverage**: FR-004 (Dependency check), FR-001 (CPU execution).

### Phase 1: Inference Pipeline Execution
- **Step 1.1**: Implement the inference wrapper that enforces the sample limit (≤1000) and CPU-only flags.
- **Step 1.2**: Execute the pipeline on the 5-sample smoke test subset.
- **Step 1.3**: Execute the pipeline on the 500-sample validation subset.
- **Step 1.4**: Capture logs and intermediate outputs for error analysis.
- **FR Coverage**: FR-001 (Execution), FR-006 (Sample limit).

### Phase 2: Artifact Generation & Metric Calculation
- **Step 2.1**: Generate the structured JSON/CSV prediction artifact containing model outputs and ground truths.
- **Step 2.2**: Calculate aggregate metrics (accuracy, exact match) with 3 decimal precision. 
  - **Normalization Logic**: `is_correct` is determined by normalizing both prediction and ground truth: convert to lowercase, remove all punctuation, collapse whitespace to single spaces, and trim. 
  - **Aggregation**: Accuracy is reported as a point estimate with a 95% Wilson score confidence interval to address variance on the 500-sample subset.
- **Step 2.3**: Validate artifacts against the defined schema (non-empty text, finite scores).
- **FR Coverage**: FR-002 (Artifact generation), FR-003 (Metric calculation).

### Phase 3: Reporting & Limitations Documentation
- **Step 3.1**: Compile the final validation report including execution status and metrics.
- **Step 3.2**: Insert the "Methodological Notes" section explicitly stating the absence of scaling law analysis. 
  - **Required Content**: The note must explicitly state that "single-point validation cannot refute or confirm scaling laws, only functional correctness at a fixed scale."
- **Step 3.3**: Review the report against SC-004 (text search for "scaling law analysis").
- **FR Coverage**: FR-005 (Methodological notes), SC-004 (Report content).

### Phase 4: CI Integration & Final Validation
- **Step 4.1**: Configure the GitHub Actions workflow to run the pipeline on the free-tier runner.
- **Step 4.2**: Verify the job completes within 6 hours and does not exceed memory limits.
- **Step 4.3**: Validate that all acceptance criteria (SC-001 to SC-005) are met.
  - **SC-004 Specific Check**: Parse the generated report file for the string "scaling law analysis" in a negative context (e.g., "not performed" or "cannot refute").
- **FR Coverage**: FR-001 (Execution), FR-006 (Time limit), SC-005 (Wall-clock time).