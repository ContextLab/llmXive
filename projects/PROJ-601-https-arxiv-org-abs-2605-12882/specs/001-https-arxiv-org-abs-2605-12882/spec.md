# Feature Specification: CiteVQA Reproduction & Validation

**Feature Branch**: `601-reproduce-citevqa`  
**Created**: 2026-05-21  
**Status**: Draft  
**Input**: User description: "Reproduce and validate the CiteVQA benchmark implementation (vendored at `external/CiteVQA`) to confirm end-to-end execution and artifact generation on free-tier CPU CI."

## User Scenarios & Testing

### User Story 1 - Execute End-to-End Inference Pipeline (Priority: P1)

The researcher MUST be able to trigger the vendored `infer/run.py` script against a subset of the CiteVQA dataset and obtain raw prediction artifacts (JSONL with answers and bounding boxes) without manual intervention or GPU hardware.

**Why this priority**: This is the foundational step. Without a successful run of the inference engine on the free-tier runner, no validation or benchmarking can occur. It validates the "reproduction" aspect of the project.

**Independent Test**: The CI job runs `infer/run.py` with a configured sample size (e.g., a representative set of documents). The test passes if the script exits with code 0 and generates a non-empty `outputs/infer_results.jsonl` file containing valid JSON objects.

**Acceptance Scenarios**:

1. **Given** the `external/CiteVQA` submodule is cloned and dependencies are installed, **When** the CI runner executes `infer/run.py` with `--sample-size 10`, **Then** the process completes within 60 minutes and outputs `outputs/infer_results.jsonl` containing exactly 10 prediction records.
2. **Given** the runner has no GPU (CUDA unavailable), **When** the script attempts to load the MLLM model, **Then** the system successfully loads the model in CPU-only mode (using `device_map="cpu"` or default CPU inference) and does not raise a `RuntimeError` regarding missing CUDA devices.

---

### User Story 2 - Execute Evaluation & Scoring Pipeline (Priority: P2)

The researcher MUST be able to feed the inference artifacts into `eval/run.py` to compute the Strict Attributed Accuracy (SAA) and other benchmark metrics, generating a summary report.

**Why this priority**: This validates the "benchmarking" aspect. It confirms the evaluation logic (SAA calculation) works correctly against the ground truth provided in the dataset.

**Independent Test**: The CI job runs `eval/run.py` pointing to the `outputs/infer_results.jsonl` from Story 1. The test passes if a `outputs/evaluation_report.json` is generated containing the SAA metric.

**Acceptance Scenarios**:

1. **Given** valid inference results exist in `outputs/infer_results.jsonl`, **When** `eval/run.py` is executed, **Then** The system computes the SAA metric and writes it to `outputs/evaluation_report.json` with a numeric value.
2. **Given** the evaluation logic checks for bounding box overlap, **When** the script runs, **Then** it correctly identifies "Attribution Hallucination" cases (correct answer, wrong region) and logs them in the report, distinguishing them from simple answer errors.

---

### User Story 3 - Validate Dataset Integrity & Variable Fit (Priority: P3)

The researcher MUST verify that the vendored dataset contains all required variables (questions, ground-truth answers, ground-truth bounding boxes, document images) to support the SAA calculation, and that the data fits within the runner's memory constraints.

**Why this priority**: Ensures the input data is valid and the experimental design is feasible on the target hardware. If data is missing or too large, the project fails immediately.

**Independent Test**: A script `data/validate_dataset.py` (or equivalent logic in `eval/run.py`) is run to check the dataset structure and size. The test passes if all required columns exist and the total dataset size is < 7 GB.

**Acceptance Scenarios**:

1. **Given** the dataset path is configured, **When** the validation script runs, **Then** it confirms the presence of `question`, `answer`, `ground_truth_bbox`, and `image_path` fields in the data records.
2. **Given** the dataset contains [deferred] questions, **When** the system attempts to load the full dataset into RAM, **Then** it either succeeds within 7 GB RAM or successfully streams/processes the data in batches without OOM (Out of Memory) errors.

---

### Edge Cases

- **What happens when the MLLM model fails to load due to memory constraints?** The system MUST catch the OOM error, log a specific message indicating the model is too large for the CPU runner, and exit gracefully with a non-zero code, rather than hanging or crashing the runner.
- **How does the system handle missing ground-truth bounding boxes?** If a record in the ground truth lacks a bounding box (violating the CiteVQA definition), the evaluation script MUST skip that record and log a warning, ensuring the SAA calculation is not skewed by malformed data.
- **What happens if the PDF download fails for a specific document?** The system MUST skip the missing document, log the failure, and proceed with the remaining valid documents, ensuring the pipeline does not abort entirely.

## Requirements

### Functional Requirements

- **FR-001**: System MUST execute the `infer/run.py` entry point using the vendored CiteVQA codebase to generate predictions for a subset of documents (See US-1).
- **FR-002**: System MUST load the specified MLLM model in CPU-only mode, ensuring no CUDA/GPU dependencies are invoked (See US-1).
- **FR-003**: System MUST compute the Strict Attributed Accuracy (SAA) metric by comparing predicted answers and bounding boxes against ground truth (See US-2).
- **FR-004**: System MUST generate a machine-readable evaluation report (JSON) containing the SAA score and breakdown of attribution errors (See US-2).
- **FR-005**: System MUST validate that the input dataset contains all required fields (question, answer, bbox, image) before processing (See US-3).
- **FR-006**: System MUST handle dataset loading in a memory-efficient manner (e.g., streaming or batching) to stay within 7 GB RAM limits (See US-3).

### Key Entities

- **InferenceResult**: A record containing the input question, the model's predicted answer, and the predicted bounding box coordinates.
- **GroundTruth**: A record from the dataset containing the correct answer and the verified ground-truth bounding box.
- **EvaluationReport**: A summary artifact containing the SAA score, total samples processed, and counts of specific error types (answer-only vs. attribution errors).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Inference execution success rate is measured against the requirement that the script exits with code 0 and produces valid JSONL output (See FR-001, US-1).
- **SC-002**: SAA metric validity is measured against the definition in the CiteVQA paper: a prediction is credited only if both answer and region are correct (See FR-003, US-2).
- **SC-003**: Memory usage is measured against the RAM limit of the GitHub Actions free-tier runner during dataset loading and model inference. (See FR-006, US-3).
- **SC-004**: Evaluation report completeness is measured by the presence of the SAA score and error breakdown fields in the generated JSON (See FR-004, US-2).
- **SC-005**: Dataset integrity is measured by the count of records skipped due to missing fields; this count must be logged and reported (See FR-005, US-3).

## Assumptions

- **Assumption about compute environment**: The GitHub Actions free-tier runner (multiple CPU cores, sufficient RAM) is sufficient to run the specified MLLM model in CPU mode. if the model is quantized or if the batch size is limited to 1. If the model requires >7 GB RAM even with quantization, the project scope will be limited to a smaller subset of the model or a distilled version, as recorded in the implementation logs.
- **Assumption about data availability**: The vendored `external/CiteVQA` submodule contains the full dataset or a mechanism to download it automatically. The download process is assumed to be stable and fit within the available disk capacity.
- **Assumption about model compatibility**: The MLLM model weights referenced in the code are available on Hugging Face and can be loaded using the `transformers` library without requiring proprietary API keys or external services.
- **Assumption about methodological framing**: Since this is a benchmarking reproduction of an existing paper, the "inference" is observational. The SAA score is an associational metric describing the model's performance on this specific dataset, not a causal claim about the model's general ability.
- **Assumption about threshold justification**: The definition of "Strict Attributed Accuracy" (exact match for answer + IoU threshold for boxes) is taken directly from the CiteVQA paper. The IoU threshold (e.g., 0.5) is a community-standard value defined in the paper's methodology; no new threshold is introduced by this reproduction project.
- **Assumption about dataset-variable fit**: The CiteVQA dataset is assumed to contain all necessary variables (questions, answers, bounding boxes) as per the paper's abstract. If the dataset is found to lack specific variables (e.g., missing image paths for some records), a `[NEEDS CLARIFICATION]` marker will be generated during the validation phase (FR-005).
