# Implementation Plan: Reproduction of MM-OCEAN Benchmark

**Branch**: `620-reproduce-mm-ocean-benchmark` | **Date**: 2024-05-22 | **Spec**: `specs/620-reproduce-mm-ocean-benchmark/spec.md`
**Input**: Feature specification from `specs/620-reproduce-mm-ocean-benchmark/spec.md`

## Summary

This feature implements a CPU-tractable reproduction pipeline for the "Perception or Prejudice" MM-OCEAN benchmark. The plan focuses on executing the vendored `MM-OCEAN` evaluation script against the `data/test` subset, computing four specific failure-mode metrics (Prejudice, Confabulation, Integration-failure, Holistic-grounding), and generating diagnostic reports. The implementation strictly adheres to CPU-only constraints (2 cores, 7 GB RAM) by disabling CUDA, implementing per-sample timeouts, and streaming video frames to avoid disk exhaustion.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: `torch` (CPU wheel), `transformers`, `accelerate`, `pandas`, `matplotlib`, `pyyaml`, `jsonschema`, `statsmodels`  
**Storage**: Local filesystem (`data/test`, `results/`, `reports/`)  
**Testing**: `pytest` (Unit tests for metric calculation against schemas; Integration tests for real-call inference)  
**Target Platform**: Linux (GitHub Actions free-tier runner: CPU, 7 GB RAM)  
**Project Type**: Research/Reproduction Pipeline  
**Performance Goals**: Process ≥ 90% of test videos within 6 hours; single video inference < 600s  
**Constraints**: No GPU/CUDA; no 8-bit/4-bit quantization; streaming frame extraction; graceful skip on model load failure  
**Scale/Scope**: Full `data/test` set (or stratified random sample if full set exceeds CI time limit)  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Reference |
| :--- | :--- | :--- |
| **Project Constitution** | **Checked** | Explicitly referenced `projects/PROJ-620-perception-or-prejudice-can-mllms-go-bey/.specify/memory/constitution.md`. *Result*: No specific principles found in the provided constitution file; defaulting to general scientific reproducibility and data integrity standards as per project governance. |
| **Reproducibility** | **Pass** | Plan explicitly mandates execution of the vendored `evaluate.py` and verification of metrics against paper baselines (FR-001, FR-002). |
| **Transparency** | **Pass** | All failure modes (PR, CR, IR, HR) are explicitly defined and computed; diagnostic reports will list top failure modes (FR-006). |
| **Feasibility** | **Pass** | Plan strictly enforces CPU-only execution, timeout mechanisms, and streaming data handling to fit the 2-core/7GB RAM CI box (FR-003, FR-005, Edge Cases). |
| **Data Integrity** | **Pass** | Metrics are derived directly from the evaluation results JSON; no external data fabrication (FR-004). |
| **Ethical AI** | **Pass** | The study itself investigates "Prejudice"; the plan ensures the reproduction does not amplify bias by strictly following the paper's methodology without modification. |

## Project Structure

### Documentation (this feature)

```text
specs/620-reproduce-mm-ocean-benchmark/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
external/
└── MM-OCEAN/            # Vendored submodule containing evaluate.py and core logic

data/
└── test/                # Test dataset (videos + JSON annotations)

results/
└── test_subset_results.json  # Primary output artifact

reports/
├── summary_report.md    # Human-readable diagnostic report
└── failure_mode_distribution.png # Visualization of error rates

src/
├── runners/
│   └── evaluate_runner.py # Wrapper for evaluate.py with timeout/CPU constraints
├── metrics/
│   └── failure_mode_calculator.py # Logic for PR, CR, IR, HR (Validates against contracts/aggregated_metrics.schema.yaml)
└── viz/
    └── report_generator.py # Markdown/PDF/Chart generation

tests/
├── unit/
│   └── test_failure_mode_calculator.py # Validates output against contracts/aggregated_metrics.schema.yaml
│   └── test_evaluation_result_schema.py # Validates output against contracts/evaluation_result.schema.yaml
└── integration/
    └── test_pipeline_execution.py # Real-call inference on data/test subset
```

**Structure Decision**: The plan adopts a modular wrapper approach. The core `MM-OCEAN` logic remains in `external/MM-OCEAN/` to preserve the original codebase integrity. New logic for `evaluate_runner.py` (timeout, CPU enforcement) and `metrics/` (aggregation) is separated to ensure testability and maintainability without modifying the vendored submodule directly. All metric calculations must produce output conforming to `contracts/aggregated_metrics.schema.yaml`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Timeout Wrapper** | CI jobs fail if a single video hangs (h limit). | Direct execution of `evaluate.py` risks total job failure on one slow sample. |
| **Streaming Frames** | Full video caching exceeds disk capacity constraints.. | Loading all frames into memory/disk at once would crash the runner. |
| **Graceful Skip** | Model load failures on CPU should not halt the whole run. | A hard crash on one model would prevent evaluation of others, violating SC-001. |
| **Schema Validation** | Ensures data integrity across pipeline stages. | Ad-hoc JSON parsing risks silent data corruption or format drift. |
| **Heuristic Sanity Check** | Addresses circular validation of "Prejudice" labels. | Relying solely on vendored code logic risks confirming a tautology. |

## Success Criteria & Methodology

- **SC-001**: The reproduction pipeline MUST successfully process ≥ 90% of the [deferred] test videos without runtime crashes. **Logic**: If dropout is < 5%, the study proceeds. If dropout is 5-10%, a sensitivity analysis is triggered to check for bias. If dropout > 10%, the pipeline fails (SC-001 not met).
- **SC-002**: The computed Prejudice Rate (PR) for the baseline model MUST fall within ±5% of the value reported in the original paper (as per spec). **Methodology**: This is the primary pass/fail check. Additionally, an Equivalence Test (TOST) will be performed *if* the sample size is sufficient to achieve a 90% CI width < 0.10. If the sample is too small for TOST, the point-estimate check stands alone, and a limitation is noted. The spec's ±5% is the hard pass/fail; TOST provides confidence reporting.
- **SC-003**: The Holistic-Grounding Rate (HR) distribution across models MUST show a range consistent with the paper's finding. **Methodology**: Confidence Intervals of the reproduced rates must overlap with the paper's reported intervals.
- **SC-004**: The total wall-clock time for the full evaluation run MUST remain within a feasible operational timeframe.
- **SC-005**: The generated diagnostic report MUST contain at least 3 distinct failure mode categories with non-zero counts.

## Testing Strategy

- **Unit Tests**: Validate `failure_mode_calculator.py` output against `contracts/aggregated_metrics.schema.yaml` and `contracts/evaluation_result.schema.yaml` using `jsonschema`.
- **Integration Tests**: Perform **Real-Call** inference on a subset of `data/test` videos using `evaluate_runner.py`. This ensures the pipeline handles actual model loading, video streaming, and timeout logic correctly, not just mocked data.
- **Validation Tests**: Verify that the `validation_source` field in `evaluation_result` correctly reflects the derivation method (e.g., "vendored_code", "heuristic").

## Statistical Rigor & Dropout Analysis

- **Dropout Bias**: If the dropout rate (samples skipped due to timeout/error) exceeds a predefined threshold, a statistical comparison (Mann-Whitney U test) of video duration/complexity between dropped and processed samples will be performed. If a significant difference (p < 0.05) is found, the metrics will be reported as "potentially biased" with a sensitivity analysis, and the study may be marked as "inconclusive".
- **Power & TOST**: TOST requires a sample size sufficient to detect equivalence within the ±5% margin with 80% power. If the available test set is too small, TOST is skipped, and the study relies on the point-estimate check with a limitation note.