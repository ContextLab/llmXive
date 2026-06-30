# Implementation Plan: CiteVQA Reproduction & Validation

**Branch**: `601-reproduce-citevqa` | **Date**: 2026-05-21 | **Spec**: `specs/601-reproduce-citevqa/spec.md`
**Input**: Feature specification from `specs/601-reproduce-citevqa/spec.md`

## Summary

This plan implements the reproduction and validation of the CiteVQA benchmark on a free-tier GitHub Actions CPU runner. The approach involves executing the vendored `external/CiteVQA` inference pipeline (`infer/run.py`) against a subset of the dataset, ensuring CPU-only model loading, and subsequently running the evaluation pipeline (`eval/run.py`) to compute Strict Attributed Accuracy (SAA). The implementation strictly adheres to memory constraints (<7 GB RAM) by utilizing batched processing and avoiding GPU dependencies. The evaluation logic will be verified to distinguish between answer-only errors and attribution hallucinations (incorrect bounding boxes), addressing the "WYSIATI" bias concern by rigorously penalizing correct answers derived from incorrect regions.

## Technical Context

**Language/Version**: Python 3.11 (inferred from typical MLLM ecosystem and CiteVQA requirements)  
**Primary Dependencies**: `transformers`, `torch` (CPU-only), `Pillow`, `datasets`, `pytest`  
**Storage**: Local filesystem (`outputs/` for artifacts, `external/CiteVQA/` for code/data)  
**Testing**: `pytest` (contract tests on output schemas, integration tests on pipeline execution)  
**Target Platform**: GitHub Actions free-tier runner (Linux, 2 CPU, ~7 GB RAM, No GPU)  
**Project Type**: CLI / Benchmarking Pipeline  
**Performance Goals**: < 6 hours total runtime per job; < 7 GB peak RAM usage  
**Constraints**: No CUDA/GPU; model must load in default precision or CPU-compatible quantization; dataset must be streamed or sampled to fit memory.  
**Scale/Scope**: Subset of CiteVQA dataset (sample size configurable, default 10 for CI); 1 MLLM model instance.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

*Note: The project `constitution.md` was not provided in the input. The following checks are based on standard project integrity principles inferred from the spec and the "Verified datasets" constraints. Formal verification against constitutional principles (e.g., Principle V on real-call testing) is pending the provision of the constitution file.*

1.  **Data Integrity**: The plan mandates a pre-check (FR-005) to verify the presence of `question`, `answer`, `ground_truth_bbox`, and `image_path` before processing. This prevents "garbage in, garbage out" failures.
2.  **Compute Feasibility**: The plan explicitly forbids GPU usage and mandates CPU-only loading strategies (FR-002), ensuring the job does not fail on the free-tier runner.
3.  **Metric Validity**: The SAA calculation (FR-003) is strictly defined by the CiteVQA paper methodology, preventing the introduction of un-spec'd success metrics.
4.  **Bias Mitigation**: Addressing the reviewer's concern regarding "WYSIATI" (What You See Is All There Is), the evaluation logic explicitly separates answer correctness from region correctness. A correct answer with a wrong bounding box is penalized as an "Attribution Hallucination," ensuring the system is not rewarded for mere coherence without truth.

## Project Structure

### Documentation (this feature)

```text
specs/601-reproduce-citevqa/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── inference_result.schema.yaml
│   └── evaluation_report.schema.yaml
└── tasks.md             # Phase 2 output (not created by /speckit-plan)
```

### Source Code (repository root)

```text
external/
└── CiteVQA/             # Vendored submodule containing infer/, eval/, and data loaders

outputs/
├── validation_log.json  # Intermediate log of skipped records (Phase 0)
├── infer_results.jsonl  # Raw predictions from Phase 1
└── evaluation_report.json # Aggregated metrics from Phase 2

data/
└── validate_dataset.py  # Utility script for FR-005 and FR-006

tests/
├── contract/
│   ├── test_inference_schema.py
│   └── test_evaluation_schema.py
└── integration/
    └── test_pipeline_e2e.py
```

**Structure Decision**: The structure leverages the vendored `external/CiteVQA` for core logic, wrapping it with a local `data/` validation layer and `tests/` for contract verification. This minimizes code duplication and ensures the reproduction remains faithful to the original benchmark while adding necessary CI constraints.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The scope is strictly limited to reproducing an existing benchmark with added CI constraints. | N/A |

## Phase Breakdown

### Phase 0: Research & Dataset Verification
- **Objective**: Confirm dataset availability, variable fit, and public source accessibility.
- **Actions**:
  - Verify the `external/CiteVQA` submodule contains the dataset or download logic.
  - Validate that the dataset contains `question`, `answer`, `ground_truth_bbox`, and `image_path`.
  - **Data Source Verification**: Confirm the public source (Hugging Face `lmsys/citevqa` or GitHub repo) is accessible. If the local submodule is empty, the plan will attempt to fetch a minimal subset from the public source to validate the pipeline.
  - Confirm the dataset size can be subsetted to fit <7 GB RAM.
  - **FR-005** & **FR-006** addressed here.
  - **SC-005** measured by logging skipped records to `outputs/validation_log.json`, which feeds into the final report.
  - **Functional vs. Metric Validation**: Explicitly distinguish that the CI run (n=10) is for *functional validation* (does the code run?). *Metric validation* (assessing SAA sensitivity to WYSIATI bias) requires a larger, statistically powered sample size which is deferred to a separate run.

### Phase 1: Inference Pipeline Execution
- **Objective**: Run `infer/run.py` in CPU mode with spatial output enabled.
- **Actions**:
  - Configure `device_map="cpu"` and ensure no CUDA calls.
  - **Spatial Output Mechanism**: Ensure the model is prompted (via the CiteVQA prompt template) to output bounding boxes in a structured format (e.g., JSON or specific token sequence) alongside the answer.
  - Execute on a small sample to verify end-to-end flow.
  - Generate `outputs/infer_results.jsonl`.
  - **FR-001** & **FR-002** addressed here.
  - **SC-001** measured by exit code and file generation.

### Phase 2: Evaluation & Scoring
- **Objective**: Compute SAA and generate report.
- **Actions**:
  - Run `eval/run.py` against `infer_results.jsonl`.
  - **Normalization Strategy**: Normalize both `predicted_bbox` and `ground_truth_bbox` to the [0, 1] range relative to image width/height before calculating IoU to ensure mathematical validity.
  - **IoU Threshold**: Apply a strict IoU threshold aligned with community standards (CiteVQA paper) for bounding box overlap.
  - Distinguish "Answer Correct/Region Wrong" from "Answer Wrong".
  - Aggregate `skipped_count` from `outputs/validation_log.json` into the final report.
  - Generate `outputs/evaluation_report.json`.
  - **FR-003** & **FR-004** addressed here.
  - **SC-002** & **SC-004** measured by report content.
  - **Statistical Limitation**: Acknowledge that with n=10, the `answer_only_correct` count has high variance; this run is a *sanity check* for the metric's existence, not a statistical validation of bias mitigation.

### Phase 3: Validation & Contract Testing
- **Objective**: Ensure artifacts meet schema requirements.
- **Actions**:
  - Validate JSONL/JSON against `contracts/` schemas.
  - Run integration tests.
  - **SC-003** (Memory) verified via CI logs.

## Dependencies & Data Flow

1.  **Data Ingestion**: `external/CiteVQA` (or public fetch) -> `data/validate_dataset.py` -> `outputs/validation_log.json` (skipped records).
2.  **Inference**: `outputs/validation_log.json` (filtered IDs) -> `infer/run.py` -> `outputs/infer_results.jsonl`.
3.  **Evaluation**: `outputs/infer_results.jsonl` + `external/CiteVQA` -> `eval/run.py` -> `outputs/evaluation_report.json`.
4.  **Testing**: `outputs/evaluation_report.json` -> `tests/` -> Pass/Fail.

## Risk Mitigation

- **OOM**: If model exceeds 7 GB RAM, the script logs "Model too large for CPU runner" and exits with code 1.
- **Missing BBox**: Records with missing `ground_truth_bbox` are skipped, logged in `validation_log.json`, and counted in `skipped_count`.
- **Missing Image**: If PDF download fails, the record is skipped and logged.
- **Public Source Unavailable**: If the public dataset is unreachable, the pipeline fails with a clear error message citing the missing source.