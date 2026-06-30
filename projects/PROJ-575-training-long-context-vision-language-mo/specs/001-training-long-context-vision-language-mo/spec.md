# Feature Specification: Reproduce & Validate Long-Context VLM Training with MMLongBench

**Feature Branch**: `575-reproduce-long-context-vlm`  
**Created**: 2026-05-20  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: Training Long-Context Vision-Language Models Effectively with Generalization Beyond 128K Context. The code that implements this paper has been vendored as a git submodule. The task is to run, validate, and reproduce the shipped implementation end-to-end."

## User Scenarios & Testing

### User Story 1 - Execute MMLongBench Evaluation Pipeline on CPU (Priority: P1)

The researcher MUST be able to trigger the vendored `MMLongBench` evaluation scripts on a standard GitHub Actions free-tier runner (2 CPU, 7 GB RAM, no GPU) to generate at least one valid artifact (e.g., a JSON result file or a summary table) without crashing due to memory or hardware errors.

**Why this priority**: This is the foundational "smoke test." If the code cannot run in the target environment, the project cannot proceed to validation or reproduction. The paper's claims are irrelevant if the code is non-functional in the CI environment.

**Independent Test**: Run the `scripts/run_eval.sh` script (or the direct Python entry point `eval.py`) with a minimal, pre-sampled configuration against a single, small benchmark subset. Verify exit code is 0 and output files exist.

**Acceptance Scenarios**:

1. **Given** a GitHub Actions runner with 2 CPU cores and 7 GB RAM, **When** the user executes the evaluation script with a `--sample-size` argument set to 10 items, **Then** the process completes within 60 minutes and generates a `results_sample.json` file containing at least 10 rows of evaluation data.
2. **Given** the same runner environment, **When** the user attempts to load a default 7B model for inference without specifying GPU device flags, **Then** the system successfully loads the model in float32 or float16 precision on the CPU and begins processing the first sample without throwing a `CUDA_ERROR` or `OutOfMemoryError`.

---

### User Story 2 - Validate Reproduction of Paper's Key Findings (Priority: P2)

The researcher MUST be able to compare the generated evaluation metrics against the specific numerical claims in the paper (e.g., "[deferred] improvement in long-document VQA") to confirm the implementation reproduces the reported results within a defined tolerance.

**Why this priority**: The project is a "Reproduction" project. The value lies in confirming that the code actually produces the results claimed by the authors, not just running the code. This validates the scientific integrity of the vendored artifact.

**Independent Test**: Run the evaluation on the specific benchmark categories mentioned in the abstract (e.g., long-document VQA) and compute the delta between the baseline (Qwen2.5-VL-7B) and the proposed method (MMProLong or equivalent configuration) using the generated artifacts.

**Acceptance Scenarios**:

1. **Given** the evaluation results for the "long-document VQA" task, **When** the researcher calculates the score difference between the baseline and the long-context trained model, **Then** the difference is reported as a percentage change, and the report explicitly states whether this change is within ±1.0% of the paper's claimed "[deferred] improvement."
2. **Given** the generated results for generalization tests (256K and 512K contexts), **When** the researcher inspects the performance drop-off, **Then** the system produces a table showing that performance at 256K/512K is at least 80% of the performance at the 128K training window, confirming the "generalization beyond 128K" claim.

---

### User Story 3 - Analyze Scaling and Multiplicity of Results (Priority: P3)

The researcher MUST be able to generate a summary report that addresses the reviewer's concern regarding scaling laws and statistical validity, specifically by aggregating results across multiple context lengths and applying multiple-comparison corrections where appropriate.

**Why this priority**: The reviewer (Geoffrey West) explicitly challenged the lack of scaling law analysis. To satisfy the methodology panel, the reproduction must not just run the code but also analyze the *distribution* of results across context lengths to determine if the relationship is linear, sublinear, or otherwise.

**Independent Test**: Execute a batch evaluation across a set of context lengths (e.g., 32K, 64K, 128K, 256K) and generate a plot or table showing the performance curve.

**Acceptance Scenarios**:

1. **Given** results from 5 distinct context lengths (32K to 512K), **When** the researcher fits a simple regression model to the performance vs. log(context_length) data, **Then** the output includes the slope coefficient and an explicit statement classifying the trend as "linear," "sublinear," or "superlinear" based on the sign and magnitude of the exponent.
2. **Given** multiple hypothesis tests performed across different task categories (e.g., VQA, RAG, Summ), **When** the final report is generated, **Then** it includes a section stating whether a multiple-comparison correction (e.g., Bonferroni or Benjamini-Hochberg) was applied to the significance testing, or explicitly acknowledges the lack thereof as a limitation.

---

### Edge Cases

- **Memory Overflow**: What happens if the model loading consumes >7 GB RAM before inference starts? The system MUST catch this and fail gracefully with a clear "OOM on CPU" error message, rather than hanging or corrupting data.
- **Data Missing**: What happens if the required dataset files (e.g., `MMLongBench` data) are not present in the expected directory? The system MUST exit with code 1 and print a "Data not found" error listing the missing files, rather than proceeding with empty inputs.
- **Hardware Mismatch**: What happens if the code attempts to call a CUDA-specific kernel? The system MUST detect the absence of a GPU and either switch to CPU fallback (if implemented) or fail with a "No CUDA device found" error immediately.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST execute the `eval.py` entry point from the `MMLongBench` submodule using only CPU resources, ensuring no GPU-specific flags (e.g., `--device cuda`) are passed by default. (See US-1)
- **FR-002**: The system MUST support a `--sample-size` parameter that limits the number of evaluation samples to a concrete integer (e.g., 10) to ensure the job completes within the 6-hour CI limit. (See US-1)
- **FR-003**: The system MUST generate a structured output file (JSON or CSV) containing the raw scores for each sample, including columns for `context_length`, `task_type`, `model_baseline_score`, and `model_target_score`. (See US-2)
- **FR-004**: The system MUST calculate and report the percentage improvement of the target model over the baseline for the "long-document VQA" category, explicitly comparing this value to the paper's claimed [deferred]. (See US-2)
- **FR-005**: The system MUST generate a summary table or plot data file that maps performance metrics against a set of at least 5 distinct context lengths (e.g., 32K, 64K, 128K, 256K, 512K) to enable scaling analysis. (See US-3)
- **FR-006**: The system MUST include a logic check that verifies the presence of required dataset files before starting execution, failing fast with an error code if any are missing. (See US-1)
- **FR-007**: The system MUST explicitly state in the final report whether a multiple-comparison correction was applied to the statistical analysis of results across task categories. (See US-3)
- **FR-008**: The system MUST limit memory usage to <7 GB by using a CPU-optimized model loading strategy (e.g., `torch_dtype=torch.float16` or `torch.float32` without quantization libraries requiring CUDA). (See US-1)

### Key Entities

- **EvaluationRun**: Represents a single execution of the evaluation pipeline, containing metadata (run_id, timestamp, sample_size, context_lengths) and the resulting metrics.
- **BenchmarkResult**: Represents the score of a model on a specific task at a specific context length, containing `task_id`, `context_length`, `score`, and `baseline_score`.
- **ScalingAnalysis**: Represents the aggregated analysis of performance across context lengths, containing `slope_coefficient`, `r_squared`, and `trend_classification`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The execution time of the `eval.py` script with `--sample-size=10` is measured against the 6-hour CI job limit, targeting ≤ 60 minutes. (See FR-002, US-1)
- **SC-002**: The reported percentage improvement in long-document VQA is measured against the paper's claimed value of 7.1%, with a tolerance of ±1.0% to confirm reproduction validity. (See FR-004, US-2)
- **SC-003**: The scaling trend (linear/sublinear/superlinear) is measured against the regression slope of performance vs. log(context_length) across multiple context lengths. (See FR-005, US-3)
- **SC-004**: The memory peak usage during model loading is measured against the available RAM limit, ensuring no OOM errors occur. (See FR-008, US-1)
- **SC-005**: The reproducibility of the "generalization beyond 128K" claim is measured by the performance retention rate at 256K and 512K contexts, targeting ≥ 80% of 128K performance. (See FR-003, US-2)

## Assumptions

- **Assumption about Data/Environment**: The `MMLongBench` submodule contains all necessary code to run on CPU, but the required dataset files (e.g., `MMLongBench` data) must be downloaded separately or are assumed to be present in the `data/` directory; if not, the `scripts/download_*.sh` scripts are assumed to be executable and functional.
- **Assumption about Scope Boundaries**: The reproduction focuses on the *evaluation* and *validation* of the existing code, not on re-training the MMProLong model from scratch, as re-training a 7B model is not feasible on the free-tier CI.
- **Assumption about Target Users**: The primary user is a researcher running CI jobs to validate the paper's claims, not an end-user interacting with a deployed API.
- **Assumption about Model Availability**: The code assumes that the `Qwen2.5-VL-7B` model weights are available via Hugging Face Hub and can be downloaded within the CI time limits; if the download fails, the job is assumed to fail.
- **Assumption about Scaling Law**: The paper's claim of "generalization beyond 128K" implies a non-trivial scaling relationship, but the specific exponent (linear vs. sublinear) is an empirical result to be measured, not a pre-defined constant.
- **Assumption about Multiplicity**: The evaluation involves multiple task categories; while the paper may not explicitly correct for multiplicity, the reproduction plan assumes that a simple descriptive comparison is sufficient for the initial validation, with statistical corrections noted as a limitation if not explicitly implemented in the code.
- **Assumption about Threshold Justification**: The paper's "[deferred] improvement" is a specific claim; the reproduction assumes this is a valid target for validation, and any deviation beyond ±1.0% will be flagged as a potential discrepancy requiring further investigation.
