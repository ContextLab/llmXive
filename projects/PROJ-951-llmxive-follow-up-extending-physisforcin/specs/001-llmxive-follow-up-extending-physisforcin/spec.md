# Feature Specification: llmXive follow-up: extending "PhysisForcing: Physics Reinforced World Simulator for Robotic Manipula"

**Feature Branch**: `001-llmxive-physs-filter`  
**Created**: 2026-07-07  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending PhysisForcing: Does applying a lightweight, post-generation physics-consistency filter to synthetic robotic manipulation videos yield physical consistency in downstream policy learning comparable to that achieved by training-time physics-informed joint optimization?"

## User Scenarios & Testing

### User Story 1 - Generate and Filter Synthetic Video Dataset (Priority: P1)

**Describe this user journey**: The researcher generates a dataset of robotic manipulation videos using the Wan model and immediately processes them through a CPU-based physics filter (PyBullet) to score trajectory continuity and contact conservation. The system automatically discards the bottom [deferred] of videos based on the physics score distribution, producing a curated dataset of high-consistency samples ready for training.

**Why this priority**: This is the foundational data curation step. Without a curated dataset, no downstream training or evaluation can occur. It directly tests the hypothesis that sample exclusion alone can yield high-quality data without expensive training-time optimization.

**Independent Test**: Can be fully tested by running the generation and filtering pipeline on a small subset of videos and verifying that a proportion of videos are discarded based on the [deferred] rule, and that the remaining videos pass the continuity checks.

**Acceptance Scenarios**:

1. **Given** the Wan2.1 model is initialized and prompts are loaded, **When** the system generates [deferred] videos and runs the PyBullet physics filter, **Then** the bottom [deferred] of videos are removed, and the remaining [deferred] are saved to the curated dataset directory with a physics score ≥ the 60th percentile of the batch distribution.
2. **Given** a generated video contains a physically impossible trajectory (e.g., object passing through a wall), **When** the PyBullet filter analyzes the video, **Then** the video is assigned a low consistency score and excluded from the final dataset.
3. **Given** the system runs on a CPU-only environment with 7 GB RAM, **When** the filtering process completes, **Then** the process finishes within 2 hours and consumes less than 6 GB of RAM.

---

### User Story 2 - Train Distilled Diffusion Model on Curated Data (Priority: P2)

**Describe this user journey**: The researcher trains a distilled diffusion model of moderate scale using a curated dataset produced in a prior user story. The training process runs on a CPU-only environment using standard optimization procedures, resulting in a trained policy model capable of generating physically consistent robotic manipulation sequences.

**Why this priority**: This step validates whether the curated data is sufficient to train a model that learns physical priors. It is the core experimental manipulation: training a model *only* on filtered data to see if it matches the performance of a model trained with joint optimization.

**Independent Test**: Can be fully tested by training the model on the curated dataset for a fixed number of epochs (e.g., 10) and verifying that the model converges (loss decreases) and produces output videos that do not crash the physics engine during evaluation.

**Acceptance Scenarios**:

1. **Given** the curated dataset of 600 videos is available, **When** the 50M diffusion model is trained for 10 epochs on a CPU-only runner, **Then** the training loss decreases monotonically and the process completes within 4 hours without exceeding 7 GB RAM.
2. **Given** the trained model, **When** it generates 30 new robotic manipulation videos (ensuring n ≥ 30 for statistical validity), **Then** at least 80% of these videos pass the initial PyBullet continuity check (score ≥ 60th percentile of batch distribution) without physics simulation errors.
3. **Given** the system runs on a GitHub Actions free-tier runner (2 CPU cores, 7 GB RAM), **When** training starts, **Then** no CUDA/GPU specific libraries are loaded, and the process uses only standard CPU-tractable libraries (e.g., `torch` in CPU mode, `scikit-learn`).

---

### User Story 3 - Evaluate and Compare Performance on Benchmarks (Priority: P3)

**Describe this user journey**: The researcher evaluates the trained model from the target user story against the original PhysisForcing baseline and the unfiltered baseline on R-Bench and PAI-Bench. The system computes physical consistency scores and performs statistical significance testing (unpaired t-tests or Mann-Whitney U) to determine if the filtered model's performance is comparable (within 15%) to the baseline.

**Why this priority**: This step provides the scientific answer to the research question. It measures the efficacy of the proposed method against the state-of-the-art and determines if the "sample curation" hypothesis holds.

**Independent Test**: Can be fully tested by running the evaluation suite on the trained model and the baseline models, generating a report with R-Bench/PAI-Bench scores and a p-value from the statistical test, and verifying the performance gap is calculated correctly.

**Acceptance Scenarios**:

1. **Given** the trained model, the PhysisForcing baseline, and the unfiltered baseline, **When** the evaluation suite runs on R-Bench and PAI-Bench, **Then** the system outputs a JSON report containing the physical consistency score for each model and the p-value from the statistical test.
2. **Given** the performance scores, **When** the system calculates the percentage difference between the filtered model and the PhysisForcing baseline, **Then** the difference is reported as a concrete percentage (e.g., [deferred]), and the conclusion (comparable/not comparable) is derived based on the ≤ 15% threshold.
3. **Given** the statistical test results, **When** the p-value is < 0.05, **Then** the system flags the difference as statistically significant; otherwise, it flags the performance as comparable.

---

### Edge Cases

- **What happens when** the PyBullet simulation fails to load a specific video frame due to format corruption?
  - *Handling*: The system logs the error, assigns a default low consistency score to that video, and excludes it from the dataset.
- **How does the system handle** a scenario where the 50M model training diverges or produces NaN loss on the CPU?
  - *Handling*: The training script includes a check for NaN loss; if detected, the run is aborted, and a specific error code is returned to trigger a retry with adjusted learning rates (up to 3 attempts).
- **What happens when** the dataset size is too small to achieve statistical significance in the test (e.g., < 30 samples)?
  - *Handling*: The system triggers the data augmentation procedure defined in FR-009 to reach a minimum sample size of 30 before proceeding with statistical testing.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate [deferred] robotic manipulation videos using the Wan2.1 model with standard prompts and save them in a standardized video format (MP4). (See US-1)
- **FR-002**: System MUST implement a CPU-based physics filter using PyBullet in headless mode to score each video on trajectory continuity and contact conservation metrics. (See US-1)
- **FR-003**: System MUST discard the bottom [deferred] of videos based on the physics consistency score to create a curated dataset. (See US-1)
- **FR-004**: System MUST train a distilled parameter-efficient diffusion model on the curated dataset using standard CPU-tractable optimization procedures. (See US-2)
- **FR-005**: System MUST evaluate the trained model against the PhysisForcing baseline and the unfiltered baseline on R-Bench and PAI-Bench metrics. (See US-3)
- **FR-006**: System MUST perform statistical significance testing using an unpaired t-test or Mann-Whitney U test on the evaluation metrics, ensuring a minimum sample size of 30 for the evaluation set. (See US-3)
- **FR-007**: System MUST ensure all training and inference steps run without GPU/CUDA dependencies, adhering to the CPU-only constraint. (See US-2)
- **FR-008**: System MUST validate the final physical consistency scores using an independent physics engine (MuJoCo) or real-world data to ensure the evaluation is not circular. (See US-3)
- **FR-009**: System MUST apply data augmentation techniques to the curated dataset if the evaluation set size is insufficient (n < 30) to meet the statistical power requirements. (See US-2)

### Key Entities

- **VideoSample**: A generated robotic manipulation video with associated metadata (prompt, physics score, pass/fail status).
- **CuratedDataset**: A subset of VideoSamples that passed the physics filter (top [deferred]).
- **TrainedModel**: The 50M parameter diffusion model trained on the CuratedDataset.
- **BenchmarkResult**: The output metrics (R-Bench score, PAI-Bench score, p-value) for a specific model.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The percentage of videos retained after filtering is measured against the target of [deferred] discard rate. (See US-1)
- **SC-002**: The physical consistency score of the trained model is measured against the PhysisForcing baseline score on R-Bench and PAI-Bench. (See US-3)
- **SC-003**: The performance gap between the filtered model and the PhysisForcing baseline is measured against the 15% threshold (gap ≤ 15%) to determine comparability. (See US-3)
- **SC-004**: The statistical significance of the performance difference is measured against a conventional p-value threshold. (See US-3)
- **SC-005**: The total training time for the large-scale parameter model is measured against a predefined time limit on a CPU-only runner. (See US-2)
- **SC-006**: The independent validation score (MuJoCo/Real-world) is measured against the PyBullet filter score to verify no circularity (correlation coefficient < 0.95 or distinct metric distribution). (See US-3)

## Assumptions

- The open-source Wan2.1 model weights and architecture are available and can be downloaded without requiring GPU resources for the generation step.
- The PyBullet physics engine is sufficient for filtering low-quality videos but is insufficient for final validation; therefore, an independent engine (MuJoCo) or real-world data is required for the final evaluation to ensure scientific validity.
- The R-Bench and PAI-Bench evaluation metrics are accessible and can be computed without GPU acceleration.
- The bottom [deferred] discard rate is the defined experimental parameter as per the research idea.
- The compact diffusion model is small enough to fit within the 7 GB RAM limit of the GitHub Actions free-tier runner during training.
- A sufficiently large dataset of videos is sufficient to produce a statistically meaningful result for the paired t-test (assuming a moderate effect size).; if the resulting sample size is too small, the power limitation will be explicitly reported and data augmentation (FR-009) will be applied.
- The physics consistency score threshold for "passing" is derived from the distribution of scores in the generated batch, specifically the 60th percentile.