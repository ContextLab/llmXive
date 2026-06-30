# Implementation Plan: Claw-SWE-Bench Reproduction & Validation

**Branch**: `001-reproduce-claw-swe-bench` | **Date**: 2024-05-21 | **Spec**: `specs/001-reproduce-claw-swe-bench/spec.md`

## Summary

This plan implements the reproduction and validation of the "Claw-SWE-Bench" benchmark. The technical approach involves initializing a vendored `external/claw-swe-bench` submodule, configuring the evaluation harness to support both `minimal_adapter` and `full_adapter` modes, and orchestrating evaluations against the SWE-bench Multilingual dataset (verified size: approximately one hundred to one hundred fifty instances) and the SWE-bench Verified subset (a representative sample of instances). The implementation prioritizes robust error handling (retries, skip-on-fail), a pre-execution harness validation step using ground-truth patches, and strict resource management to ensure the full pipeline runs within the GitHub Actions free-tier constraints. The primary deliverable is a set of execution logs and summary metrics (Pass@k, cost, runtime) that allow direct comparison with the paper's claims, including a statistical significance test (McNemar's) for the adapter comparison.

## Technical Context

**Language/Version**: Python 3.9+ (Minimum supported version per spec assumptions)  
**Primary Dependencies**: `swebench`, `datasets`, `huggingface_hub`, `pandas`, `pyyaml`, `requests`, `tenacity` (for retries), `scipy` (for McNemar's test).  
**Storage**: Local ephemeral filesystem (GitHub Actions runner) for `results/`, `patches/`, and `logs/`.  
**Testing**: `pytest` for unit tests of adapter logic; CI integration tests for full pipeline execution.  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest`).  
**Project Type**: Research Benchmark / CLI Tool.  
**Performance Goals**: Complete Lite subset (80 instances) within 2 hours; Multilingual subset (~100-150 instances) within 6 hours (with dynamic stopping rule).  
**Constraints**: CPU-only execution; no GPU; strict memory limit (~ GB); hard timeout per job.  
**Scale/Scope**: 8 languages, 43 repositories (verified), ~100-150 instances (Multilingual), 80 instances (Lite/Verified).

## Constitution Check

*This section explicitly references the project's `constitution.md` file (FR-030) to ensure alignment with project-specific principles.*

**Constitution File**: `projects/PROJ-695-claw-swe-bench-a-benchmark-for-evaluatin/.specify/memory/constitution.md`

**Status**: No constitution file was supplied in the project input.
**Action**: In the absence of a specific `constitution.md`, this plan proceeds by explicitly listing **Fallback Research Integrity Principles** as a temporary governance model. These principles include:
1.  **Reproducibility**: Use of specific dataset versions and exact submodule commits.
2.  **Transparency**: Explicit logging of all cost and runtime metrics.
3.  **Robustness**: Implementation of error handling for API rate limits and patch application failures.
4.  **Resource Feasibility**: Restriction to CPU-only inference and enforcement of a 6-hour timeout.
5.  **Scientific Integrity**: Inclusion of a harness validation step and statistical significance testing.
*Note: These principles are provisional until a specific `constitution.md` is provided to the project.*

## Project Structure

### Documentation (this feature)

```text
specs/001-reproduce-claw-swe-bench/
├── plan.md              # This file
├── research.md          # Pre-existing design artifact (Phase 0 output)
├── data-model.md        # Pre-existing design artifact (Phase 1 output)
├── quickstart.md        # Pre-existing design artifact (Phase 1 output)
└── contracts/           # Pre-existing design artifact (Phase 1 output)
```
*Note: `research.md`, `data-model.md`, `quickstart.md`, and `contracts/` are treated as pre-existing design artifacts that inform this plan, not future deliverables generated after this step.*

### Source Code (repository root)

```text
# Option 1: Single project (DEFAULT)
src/
├── evaluators/
│   ├── run_eval.py          # Main entry point
│   ├── orchestrator.py      # Job scheduling & timeout handling
│   └── adapters/
│       ├── base.py
│       ├── minimal_adapter.py
│       └── full_adapter.py
├── loaders/
│   └── dataset_loader.py    # Handles SWE-bench Parquet ingestion
├── utils/
│   ├── cost_calculator.py   # Token counting & cost estimation
│   ├── retry_utils.py       # Exponential backoff logic
│   └── stats_utils.py       # McNemar's test implementation
└── config/
    ├── multilingual.yaml    # Full dataset config
    └── verified.yaml        # Lite subset config

tests/
├── contract/
│   └── test_schema_validation.py
├── integration/
│   └── test_eval_pipeline.py
└── unit/
    └── test_adapters.py

results/                     # Output directory (generated at runtime)
├── full_eval_summary.json
├── lite_full_adapter.json
├── lite_minimal_adapter.json
├── cost_summary.csv
└── patches/
```

**Structure Decision**: A single-project structure is selected to minimize overhead. The `src/evaluators` directory houses the core benchmark logic, while `src/loaders` abstracts dataset ingestion. The `results/` directory is generated dynamically during CI runs.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Dual Adapter Modes | Required to validate the paper's central hypothesis regarding adapter design (US-2). | A single adapter would fail to reproduce the comparative analysis (FR-002). |
| Robust Retry Logic | API rate limits (HTTP 429) are common in LLM evaluation; skipping instances immediately would bias results. | A simple "fail-fast" approach would result in incomplete datasets and invalid Pass@1 metrics (US-1). |
| Timeout Enforcement | The 6-hour CI limit is hard; without explicit enforcement, the job would be killed by the runner, losing partial results. | Relying on the runner's kill signal provides no structured partial output or cost accounting (US-3). |
| McNemar's Test | Required to statistically validate the paired difference between adapters on the same instances. | A simple delta check ignores the variance reduction from the paired design and may yield false positives. |
| Harness Validation | Ensures the `evaluate.py` logic is correct before the main experiment. | Skipping this risks validating a buggy harness, rendering all results invalid. |

## Implementation Phases

### Phase 0: Pre-Execution Verification & Validation
1.  **Phase 0.1: Dataset Metadata Verification**:
    -   **Action**: Run a script to load the `SWE-bench Multilingual` dataset and verify:
        -   Total instance count is in the range of one hundred to one hundred fifty (not 350).
        -   Language distribution includes multiple distinct languages.
        -   Required fields (`instance_id`, `repo`, `problem_statement`) are present.
    -   **Fail Condition**: If the dataset does not match these criteria, the build fails immediately with a clear error message.
2.  **Phase 0.5: Harness Validation (Ground Truth)**:
    -   **Action**: Select 5 instances with known ground-truth patches from the `verified` split.
    -   **Execution**: Run the `evaluate.py` logic against these instances using the ground-truth patches.
    -   **Success Condition**: The harness must correctly identify these as `passed`. If it fails to identify any, the build stops immediately with `validation_failed`.

### Phase 1: Core Evaluation Execution
1.  **Phase 1.1: Multilingual Run (FR-001)**:
    -   Execute `run_eval.py` with `minimal_adapter` on the verified Multilingual dataset.
    -   Enforce 6-hour timeout with partial result saving.
    -   **Dynamic Stopping Rule**: If time remaining < 30 mins, stop new instance starts and finalize current batch.
2.  **Phase 1.2: Lite Subset Comparison (FR-002)**:
    -   Execute `run_eval.py` with `minimal_adapter` on the Verified subset (80 instances).
    -   Execute `run_eval.py` with `full_adapter` on the Verified subset (80 instances).
    -   Ensure both runs use the same instances for paired comparison.

### Phase 2: Analysis & Reporting
1.  **Phase 2.1: Statistical Analysis**:
    -   Compute Pass@1 for both adapters on the Lite subset.
    -   Perform **McNemar's Test** on the paired binary outcomes (Pass/Fail) to determine statistical significance ($\alpha=0.05$).
    -   If Multilingual run was partial, report power based on actual N.
2.  **Phase 2.2: Cost & Efficiency Report**:
    -   Aggregate `cost_summary.csv` data.
    -   Compare total costs against the paper's qualitative claims.
3.  **Phase 2.3: Final Summary**:
    -   Generate `full_eval_summary.json` and comparative reports.
    -   Include a section explicitly distinguishing between "search efficiency" (Verified set) and "general capability" (Multilingual set).

## Success Criteria

-   **SC-001**: The Pass@1 metric for the minimal adapter on the full dataset is measured against the paper's reported value of a significant percentage. (See FR-001, US-1)
-   **SC-002**: The Pass@1 metric for the full adapter on the Lite subset is measured against the paper's reported value of a high percentage. **Crucially, this metric is interpreted as a measure of 'search efficiency on solvable tasks' only, not general capability.** (See FR-002, US-2)
-   **SC-003**: The total API cost and runtime are measured against the paper's qualitative claim that "systems with similar accuracy can differ substantially in total API cost." (See FR-003, US-3)
-   **SC-004**: The error recovery rate is measured by the percentage of instances successfully processed after an initial transient failure (target: $>95\%$ recovery of recoverable errors). (See FR-004, US-1)
-   **SC-005**: The completeness of the output dataset is measured by the count of successfully processed instances vs. the total **~100-150** (Multilingual) or **80** (Lite) instances (target: $\ge$ a sufficient number of instances processed, excluding known data gaps). (See FR-007, US-1)