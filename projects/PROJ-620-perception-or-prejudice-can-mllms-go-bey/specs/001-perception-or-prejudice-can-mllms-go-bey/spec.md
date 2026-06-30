# Feature Specification: Reproduction of MM-OCEAN Benchmark

**Feature Branch**: `620-reproduce-mm-ocean-benchmark`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: Perception or Prejudice: Can MLLMs Go Beyond First Impressions of Personality?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Execute End-to-End Evaluation Pipeline (Priority: P1)

As a researcher, I want to run the vendored `MM-OCEAN` evaluation script against the provided test dataset so that I can verify the codebase executes without runtime errors and produces the primary output artifacts (JSON results and summary logs).

**Why this priority**: This is the foundational step. Without a successful execution of the pipeline, no validation of the paper's claims can occur. It confirms the environment is correctly set up and the code is functional.

**Independent Test**: Can be fully tested by executing the entry point script (`evaluate.py`) with the test subset and verifying the existence of non-empty output files in the designated results directory.

**Acceptance Scenarios**:

1. **Given** the `external/MM-OCEAN` submodule is initialized and dependencies are installed, **When** the user runs `python evaluate.py --subset test --limit 10`, **Then** the script completes with exit code 0 and generates `results/test_subset_results.json`.
2. **Given** the environment has no GPU (CPU-only runner), **When** the script attempts to load the model, **Then** it successfully loads the model in default precision on the CPU without CUDA-related errors.

---

### User Story 2 - Validate Quantitative Metrics and Reproduce Key Findings (Priority: P2)

As a reviewer, I want the system to compute the four sample-level failure-mode metrics (Prejudice Rate, Confabulation Rate, Integration-failure Rate, Holistic-grounding Rate) on the test set so that I can compare the results against the paper's reported "Prejudice Gap" and "Holistic-Grounding Rate" statistics.

**Why this priority**: The core scientific contribution of the paper is the identification of the "Prejudice Gap." Validating these specific metrics confirms whether the reproduction aligns with the original findings.

**Independent Test**: Can be fully tested by parsing the generated JSON results, calculating the four metrics, and confirming they fall within a reasonable variance (e.g., ±5%) of the paper's reported baselines for the tested models.

**Acceptance Scenarios**:

1. **Given** the evaluation results file contains rating, reasoning, and grounding data, **When** the validation script aggregates the metrics, **Then** it outputs a summary table showing Prejudice Rate (PR) and Holistic-grounding Rate (HR) for each evaluated model.
2. **Given** the computed Prejudice Rate for a baseline model, **When** compared to the paper's reported value, **Then** the difference is ≤ 0.05 (5 percentage points), confirming the logic implementation matches the paper.

---

### User Story 3 - Generate Diagnostic Reports and Visualizations (Priority: P3)

As an analyst, I want the system to generate human-readable diagnostic reports and summary visualizations (e.g., bar charts of failure rates) so that I can qualitatively assess the types of errors (Prejudice vs. Confabulation) without manually parsing JSON logs.

**Why this priority**: While P1 and P2 confirm correctness, P3 provides the interpretability needed to understand *why* models fail, supporting the "roadmap for grounded social cognition" mentioned in the abstract.

**Independent Test**: Can be fully tested by checking for the existence of generated report files (e.g., `reports/summary_report.md`, `reports/failure_mode_distribution.png`) and verifying they contain non-placeholder content derived from the test run.

**Acceptance Scenarios**:

1. **Given** the evaluation has completed, **When** the post-processing script runs, **Then** it generates a markdown report listing the top 3 failure modes by frequency.
2. **Given** the aggregated metrics, **When** the visualization script runs, **Then** it produces a PNG image comparing the Prejudice Rate across different model families.

### Edge Cases

- **Dataset Variable Fit**: The test set contains a substantial collection of videos. The full run might exceed the disk limit if all intermediate video frames are cached. The system must handle streaming or on-the-fly frame extraction to avoid disk exhaustion.
- **Model Loading Failures**: If a specific MLLM model fails to load due to architecture mismatch on the CPU-only runner, the system must skip that model gracefully, log the error, and continue with the remaining models rather than crashing the entire pipeline.
- **Timeout Handling**: If the inference for a single video exceeds a reasonable time threshold (due to slow CPU performance), the system must terminate that specific inference., log a timeout error, and proceed to the next sample to ensure the full dataset is processed within the 6-hour CI limit.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST execute the `evaluate.py` entry point to process the `data/test` directory using the vendored `MM-OCEAN` codebase (See US-1).
- **FR-002**: The system MUST compute the four sample-level metrics: Prejudice Rate (PR), Confabulation Rate (CR), Integration-failure Rate (IR), and Holistic-grounding Rate (HR) for every evaluated model (See US-2).
- **FR-003**: The system MUST detect and handle CPU-only execution constraints by disabling any CUDA-specific flags or GPU-dependent libraries during model initialization (See US-1).
- **FR-004**: The system MUST generate a summary JSON artifact containing the calculated metrics and model configurations for every successful inference run (See US-2).
- **FR-005**: The system MUST implement a timeout mechanism (≤ 600 seconds per video) to prevent single-sample hangs from blocking the 6-hour CI job (See US-1).
- **FR-006**: The system MUST produce a human-readable report (Markdown or PDF) summarizing the distribution of failure modes across the dataset (See US-3).

### Key Entities

- **Video Sample**: A single video file from the `data/test` directory paired with its corresponding JSON annotation containing Big Five scores and behavioral cues.
- **Evaluation Result**: A structured record containing the model's rating, reasoning trace, grounding evidence, and the computed failure mode flags for a specific video sample.
- **Failure Mode Metric**: An aggregated statistic (PR, CR, IR, HR) derived from the set of Evaluation Results for a specific model.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The reproduction pipeline MUST successfully process ≥ 90% of the [deferred] test videos without runtime crashes, measured against the total video count in `data/test` (See FR-001, US-1).
- **SC-002**: The computed Prejudice Rate (PR) for the baseline model MUST fall within ±5% of the value reported in the original paper ([deferred]), measured against the paper's abstract results (See FR-002, US-2).
- **SC-003**: The Holistic-Grounding Rate (HR) distribution across models MUST show a range consistent with the paper's finding of low to moderate percentages., measured against the paper's results section (See FR-002, US-2).
- **SC-004**: The total wall-clock time for the full evaluation run MUST not exceed a reasonable duration on the default GitHub Actions free-tier runner. (2 CPU, 7 GB RAM), measured against the CI job timeout limit (See FR-005, US-1).
- **SC-005**: The generated diagnostic report MUST contain at least 3 distinct failure mode categories with non-zero counts, measured against the paper's defined categories (PR, CR, IR, HR) (See FR-006, US-3).

## Assumptions

- The `external/MM-OCEAN` submodule contains a fully functional `evaluate.py` script that does not require manual code modification to run on a CPU-only environment, provided standard dependencies are met.
- The test dataset (`data/test`) is self-contained within the repository and does not require external video downloads during the CI run, assuming the video files are either present or accessible via a lightweight internal reference.
- The "Prejudice Gap" and other metrics defined in the paper are implemented correctly in the vendored code, and the reproduction task is to verify execution and output consistency, not to re-derive the metric formulas.
- The [deferred] video samples in the test set can be processed within the 6-hour CI limit by sampling or parallelizing across the 2 available CPU cores, or the full set is small enough for sequential CPU inference.
- The paper's reported metrics (e.g., [deferred] PR) are based on the exact same test split and model configurations available in the vendored code.
- No GPU-specific quantization (e.g., 8-bit/4-bit) is required for the models used in the reproduction; standard float32 or float16 CPU inference is sufficient.
