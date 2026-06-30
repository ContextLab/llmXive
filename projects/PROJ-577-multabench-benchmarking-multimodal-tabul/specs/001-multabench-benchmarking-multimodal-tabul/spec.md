# Feature Specification: MulTaBench: Benchmarking Multimodal Tabular Learning with Text and Image

**Feature Branch**: `577-multabench-reproduction`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: MulTaBench: Benchmarking Multimodal Tabular Learning with Text and Image. Code vendored at external/MulTaBench. Task is to run, validate, and reproduce the shipped implementation end-to-end and confirm it executes and produces real artifacts."

## User Scenarios & Testing

### User Story 1 - Validate Environment Setup and Data Availability (Priority: P1)

The researcher MUST verify that the vendored `MulTaBench` codebase is correctly initialized, dependencies are installed, and the required dataset metadata is accessible without triggering full downloads, ensuring the execution environment is ready for the reproduction run.

**Why this priority**: Without a verified environment and accessible data schema, no experimental runs can be executed. This is the foundational step for any reproduction project.

**Independent Test**: Can be fully tested by executing the initialization script (`init.sh` or equivalent setup) and running a "dry-run" or metadata listing command that outputs dataset names and types without downloading large binary files.

**Acceptance Scenarios**:

1. **Given** the submodule is cloned at `external/MulTaBench`, **When** the researcher runs the project initialization script, **Then** all Python dependencies are installed in the virtual environment without errors.
2. **Given** the environment is initialized, **When** the researcher queries the dataset registry (e.g., via `multabench.datasets.all_datasets`), **Then** the system lists all benchmark datasets with their modality types (image-tabular, text-tabular) and task types (classification, regression) without downloading the actual data files.
3. **Given** the registry query, **When** the researcher requests specific dataset IDs (`BIN_TEXT_FAKE_JOB_POSTING`, `MUL_IMAGE_CBIS_DDSM`), **Then** the system confirms their existence in the registry or logs a fatal error and aborts if they are missing, preventing silent fallback to synthetic data.

---

### User Story 2 - Execute Reduced-Scale Reproduction Run (Priority: P2)

The researcher MUST execute the benchmarking pipeline on a specific subset of datasets and models to validate that the code runs end-to-end, produces valid output artifacts (logs, metrics CSVs), and completes within the CI resource constraints (CPU-only, <6h).

**Why this priority**: This confirms the core logic of the paper's methodology works in the current environment. Running the full multi-dataset benchmark on free-tier CI is likely infeasible; a reduced scale proves the pipeline integrity.

**Independent Test**: Can be fully tested by running `benchmark.py` with a configuration limiting the run to 2 datasets (`BIN_TEXT_FAKE_JOB_POSTING`, `MUL_IMAGE_CBIS_DDSM`) and 2 baseline models (`lgbm`, `tabpfnv2`), verifying that output files (e.g., `results_subset.csv`) are generated and contain non-empty numeric metrics.

**Acceptance Scenarios**:

1. **Given** a subset configuration specifying `BIN_TEXT_FAKE_JOB_POSTING` and `MUL_IMAGE_CBIS_DDSM`, **When** the benchmark script is executed, **Then** the process completes successfully without GPU/CUDA errors and within 2 hours.
2. **Given** the script completes, **When** the researcher inspects the output directory, **Then** a results artifact (e.g., `multabench/leaderboard/data/results_subset.csv`) exists and contains at least 8 rows of valid numeric performance metrics (accuracy/AUC/MSE) corresponding to the selected dataset-model pairs in both "frozen" and "tuned" modes.
3. **Given** a dataset download failure during execution, **When** the system encounters the error, **Then** it logs a clear warning, skips the specific dataset, and proceeds with remaining datasets rather than crashing the entire job or substituting synthetic data.

---

### User Story 3 - Compare Reproduction Metrics Against Paper Claims (Priority: P3)

The researcher MUST compare the metrics generated from the reduced-scale run against the qualitative claims or specific numeric values reported in the paper abstract to confirm the reproduction aligns with the original findings (e.g., tuning improves performance).

**Why this priority**: This validates the scientific claim. While a full statistical reproduction requires the full dataset, confirming the direction of effect (tuning > frozen) on a subset is the minimum viable validation of the paper's hypothesis.

**Experimental Condition**: The reduced-scale run MUST execute two distinct passes for every dataset-model pair in the subset: one pass with **frozen embeddings** and one pass with **tuned embeddings**. The resulting results artifact MUST contain separate rows for both "frozen" and "tuned" configurations for each pair to enable a direct directional comparison.

**Independent Test**: Can be fully tested by verifying the results artifact contains paired rows (frozen/tuned) for each dataset-model combination and calculating the delta between them to verify the direction of the delta matches the paper's abstract claim ("tuning the embeddings to the task improves performance").

**Acceptance Scenarios**:

1. **Given** the results from User Story 2, **When** the researcher inspects the results artifact, **Then** it contains both "frozen" and "tuned" rows for every dataset-model pair in the subset.
2. **Given** the paired rows exist, **When** the researcher calculates the performance difference between the frozen baseline and the tuned baseline for the same dataset, **Then** the tuned baseline shows an improvement (or the result is flagged as inconclusive due to sample size) in the direction claimed by the paper.
3. **Given** the validation logic, **When** the number of successful comparisons is insufficient to draw a statistical conclusion, **Then** the system explicitly flags the result as "inconclusive" rather than forcing a pass/fail verdict.

---

### Edge Cases

- **Dataset Download Failure**: What happens when a specific dataset (e.g., `MUL_IMAGE_CHEXPERT`) fails to download due to rate limiting or broken links? The system MUST skip the specific dataset, log a warning, and proceed with remaining datasets rather than crashing the entire run or substituting synthetic data.
- **GPU Detection on CPU-only Runner**: How does the system handle code paths that default to CUDA? The system MUST detect the absence of a GPU and force the use of CPU-only device maps for all PyTorch/TensorFlow models to prevent `CUDA_ERROR_NO_DEVICE` crashes.
- **Memory Exhaustion**: How does the system handle large image batches on 7GB RAM? The system MUST implement a fallback to smaller batch sizes (e.g., `batch_size=8` or `16`) if a `MemoryError` is detected during the data loading phase.
- **Dataset Unavailability**: What happens if the specific validation datasets (`BIN_TEXT_FAKE_JOB_POSTING` or `MUL_IMAGE_CBIS_DDSM`) are not found in the registry? The system MUST log a fatal error and abort the run immediately, preventing the use of fallback synthetic data for the validation claim.

## Requirements

### Functional Requirements

- **FR-001**: System MUST execute the `benchmark.py` entry point with a user-defined subset of datasets and models to validate the pipeline logic (See US-002).
- **FR-002**: System MUST detect the absence of a GPU and automatically configure all deep learning models to run on CPU using default precision (float32), avoiding any CUDA-specific device assignments (See US-002).
- **FR-003**: System MUST generate a structured results artifact (CSV/JSON) containing dataset ID, model ID, mode (frozen/tuned), and performance metrics (accuracy/AUC/MSE) for every successful run (See US-002).
- **FR-004**: System MUST handle dataset download failures gracefully by logging the error and skipping the specific dataset without terminating the entire benchmarking job (See Edge Cases).
- **FR-005**: System MUST validate that the output metrics are numeric and within a plausible range (e.g., accuracy ∈ [0, 1]) before writing to the final results file (See US-003).
- **FR-006**: System MUST abort the execution immediately if the required validation datasets (`BIN_TEXT_FAKE_JOB_POSTING`, `MUL_IMAGE_CBIS_DDSM`) are not found in the registry, preventing silent substitution with synthetic data (See US-001).

### Key Entities

- **Dataset**: A multimodal tabular instance defined by a unique ID, modality type (text/image), and task type (classification/regression).
- **Baseline Model**: A specific algorithm implementation (e.g., XGBoost, TabPFNv2) configured with either frozen or target-aware tuned embeddings.
- **Benchmark Run**: An execution instance of the pipeline on a specific dataset-model pair, producing a set of metrics.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Reproduction success rate is measured against the requirement that ≥ 80% of the selected subset runs complete without fatal errors (See US-002).
- **SC-002**: Metric validity is measured against the requirement that 100% of generated metrics in the results artifact are numeric and within the theoretical bounds of the metric (e.g., AUC ≤ 1.0) (See US-003).
- **SC-003**: Resource compliance is measured against the constraint that the reduced-scale run completes within 2 hours on a standard free-tier CPU runner (See US-002).
- **SC-004**: Directional validity is measured against the paper's claim that "tuning improves performance" by verifying the tuned baseline outperforms the frozen baseline in ≥ 2 out of 4 subset comparisons (See US-003).
- **SC-005**: Data integrity is measured against the requirement that no synthetic data is used for the validation report unless the real datasets are explicitly unavailable, in which case the report must state "inconclusive due to data unavailability" (See US-001).

## Assumptions

- The vendored code in `external/MulTaBench` is functionally complete and matches the version used in the submitted paper, requiring no code modifications for basic execution, except for the necessary CPU enforcement and error handling logic.
- The specific validation datasets (`BIN_TEXT_FAKE_JOB_POSTING`, `MUL_IMAGE_CBIS_DDSM`) are publicly accessible via the URLs defined in the dataset configuration files, though download times may vary.
- The "free-tier" CI runner provides sufficient RAM (≥7GB) to load small-to-medium image batches and tabular data for a single dataset at a time, provided batch sizes are constrained.
- The paper's claim regarding "target-aware representation tuning" relies on the existence of a specific training loop in `multabench/dino/` or `multabench/e5/` that is correctly invoked by the benchmark runner.
- Network bandwidth is sufficient to download the subset of datasets (estimated <500MB for text-only, <2GB for image-only) within the job time limit.
- The benchmark script `benchmark.py` accepts command-line arguments to specify a subset of datasets and models, or a configuration file can be passed to define this subset.
