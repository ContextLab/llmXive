# Feature Specification: Reproduce & Validate ProRL

**Feature Branch**: `640-reproduce-prorl`  
**Created**: 2025-05-24  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: ProRL: Effective Reinforcement Learning for Proactive Recommendation via Rectified Policy Gradient Estimation (arXiv:2605.28293)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Execute ProRL Pre-training and RL Training Pipelines (Priority: P1)

**Description**: The system MUST successfully execute the vendored ProRL codebase end-to-end, running both the pre-training phase (to initialize the recommendation backbone) and the ProRL reinforcement learning phase (to optimize the proactive policy) on a single, representative dataset (e.g., Books) within the free-tier CI limits.

**Why this priority**: This is the core definition of "done" for a reproduction project. If the code cannot run without modification or hardware errors, the project fails immediately. It validates the code integrity and environmental setup.

**Independent Test**: Can be fully tested by running the entry script `Proactive_RL_prorl.py` (or the provided shell wrapper) against a minimal configuration and observing the creation of training artifacts (checkpoints, logs) without GPU dependency errors.

**Acceptance Scenarios**:

1. **Given** the ProRL submodule is checked out and dependencies are installed, **When** the pre-training script runs on the `Books` dataset, **Then** a valid checkpoint file (`.pth`) is generated in the `ckpt` directory within 30 minutes.
2. **Given** a valid pre-trained checkpoint exists, **When** the RL training script runs using `trainer_RL_prorl.py`, **Then** the training loop completes at least 100 epochs and outputs a final policy checkpoint without raising `CUDA` or `OutOfMemory` errors.
3. **Given** the training completes, **When** the evaluation script runs, **Then** a results log containing performance metrics (e.g., HitRate, NDCG) is written to the output directory.

---

### User Story 2 - Validate Output Artifacts and Reproducibility (Priority: P2)

**Description**: The system MUST verify that the generated artifacts (checkpoints, metrics logs) are structurally valid and consistent with the paper's reported methodology, ensuring the reproduction is not a "silent failure" where the code runs but produces garbage or empty results.

**Why this priority**: Running code is necessary but insufficient. We must confirm the output represents a valid execution of the ProRL algorithm (e.g., metrics are non-zero, checkpoints have expected keys) to claim successful reproduction.

**Independent Test**: Can be fully tested by parsing the generated JSON/CSV logs and checkpoint files to assert they contain non-null values and match the schema defined in the paper's expected output.

**Acceptance Scenarios**:

1. **Given** the training logs are generated, **When** the validation script parses the final metrics, **Then** The reported HitRate@k and NDCG@k are positive values for a top-k cutoff..
2. **Given** the final policy checkpoint exists, **When** the model loader attempts to load it, **Then** the loading process succeeds and the model parameters are non-zero (not all NaN).
3. **Given** the execution finishes, **When** the system compares the output directory structure against the paper's `ckpt` and `logs` expectations, **Then** all expected file types (`.pth`, `.log`, `.csv`) are present.

---

### User Story 3 - Generate Reproduction Report (Priority: P3)

**Description**: The system MUST generate a human-readable report summarizing the reproduction results, including the hardware constraints used, the specific dataset processed, and a comparison of the obtained metrics against the paper's baseline claims (if available in the code/config).

**Why this priority**: This provides the final deliverable for the research team, documenting the success or failure of the reproduction attempt and the specific conditions under which it was performed.

**Independent Test**: Can be fully tested by checking for the existence of a `reproduction_report.md` file containing specific sections (Method, Results, Constraints) and populated data.

**Acceptance Scenarios**:

1. **Given** the experiment completes successfully, **When** the report generation script runs, **Then** a `reproduction_report.md` is created in the project root.
2. **Given** the report exists, **When** a human reviewer reads it, **Then** it explicitly states the CPU cores and RAM used (e.g., "2 vCPU, 7GB RAM") and confirms no GPU was utilized.
3. **Given** the report exists, **When** the metrics section is reviewed, **Then** it lists the specific dataset used (e.g., "Books") and the final computed metrics.

---

### Edge Cases

- **What happens when the dataset is too large for 7GB RAM?** The system MUST fail gracefully with a clear error message suggesting a smaller dataset or sampling, rather than hanging or crashing the CI runner.
- **How does the system handle missing pre-trained checkpoints?** If the pre-training step fails or is skipped, the RL step MUST detect the missing backbone and either abort with a clear error or trigger the pre-training script automatically before proceeding.
- **What if the paper's claimed performance is not achieved?** The system MUST still report the actual metrics obtained and flag the discrepancy in the report, rather than masking the result as a "success" solely based on code execution.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST execute the ProRL pre-training phase on the `Books` dataset using only CPU resources, producing a valid backbone checkpoint within 3 hours. (See US-1)
- **FR-002**: System MUST execute the ProRL RL training phase using the pre-trained backbone, completing at least 100 epochs without GPU acceleration. (See US-1)
- **FR-003**: System MUST validate that all generated checkpoints (`.pth`) contain non-null parameters and are loadable by the `model.py` loader. (See US-2)
- **FR-004**: System MUST extract and log final performance metrics (HitRate@10, NDCG@10) to a structured file (JSON/CSV) upon completion. (See US-2)
- **FR-005**: System MUST generate a `reproduction_report.md` containing the execution environment details, dataset used, and final metrics, explicitly stating that no GPU was used. (See US-3)
- **FR-006**: System MUST detect and abort if the dataset size exceeds the available RAM limit of the free-tier runner, providing a specific error message. (See US-1, Edge Cases)
- **FR-007**: System MUST ensure the training loop does not attempt to load `bitsandbytes` or any CUDA-specific libraries, failing early if such dependencies are invoked. (See US-1)

### Key Entities

- **Checkpoint**: A serialized model state (`.pth` file) representing the backbone or policy at a specific training step.
- **Metrics Log**: A structured record (JSON/CSV) containing evaluation scores (HitRate, NDCG) and training statistics.
- **Reproduction Report**: A Markdown document summarizing the run, environment, and results.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Execution success is measured against the requirement that the full pipeline (Pretrain + RL) completes without error on the `Books` dataset within the 6-hour CI time limit. (See US-1)
- **SC-002**: Artifact validity is measured against the criterion that the final checkpoint file size is > 0 bytes and contains at least one non-zero parameter tensor. (See US-2)
- **SC-003**: Reproducibility is measured against the presence of a `reproduction_report.md` that explicitly documents the CPU-only constraint and lists the final numeric metrics. (See US-3)
- **SC-004**: Resource compliance is measured against the constraint that peak RAM usage remains within acceptable hardware limits during the pre-training and RL phases. (See US-1)
- **SC-005**: Methodological integrity is measured against the absence of any CUDA/GPU-specific library calls in the execution logs. (See US-1)

## Assumptions

- **Assumption about hardware**: The free-tier GitHub Actions runner provides sufficient CPU (2 vCPU) and RAM (~7 GB) to process the `Books` dataset (subset if necessary) and run the ProRL algorithm in default float32 precision without quantization.
- **Assumption about data integrity**: The vendored `datasets/Books` directory contains valid `.inter`, `.datamaps`, and `.sem_ids` files compatible with the `dataset.py` parser as defined in the ProRL repository.
- **Assumption about dependencies**: The `requirements.txt` or `setup.py` in the ProRL repository lists only CPU-compatible versions of `torch` and `transformers` (or the project will pin them to CPU-compatible versions in the workflow).
- **Assumption about time limits**: The pre-training and RL training for the `Books` dataset can complete within the 6-hour CI job limit; if not, the workflow will sample a smaller subset of the dataset (e.g., a representative fraction of items) to ensure feasibility.
- **Assumption about baseline comparison**: The paper's exact numerical claims are not strictly required to be matched for the project to be considered "reproduced," provided the code runs and produces valid metrics; the report will note any significant deviations.
- **Assumption about dataset-variable fit**: The `Books` dataset provided in the submodule contains the necessary user-item interaction sequences and item embeddings (`qwen3-embedding-8b-pca.sem_ids`) required by the ProRL model architecture.
