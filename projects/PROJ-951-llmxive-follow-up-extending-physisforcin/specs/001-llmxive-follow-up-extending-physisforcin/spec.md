# Feature Specification: llmXive follow-up: extending "PhysisForcing: Physics Reinforced World Simulator for Robotic Manipula"

**Feature Branch**: `001-llmxive-physs-filter`  
**Created**: 2026-07-07  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending PhysisForcing: Does applying a lightweight, post-generation physics-consistency filter to synthetic robotic manipulation videos yield physical consistency in downstream policy learning comparable to that achieved by training-time physics-informed joint optimization?"

## User Scenarios & Testing

### User Story 1 - Generate and Filter Synthetic Video Dataset (Priority: P1) (US-1)

**Describe this user journey**: The researcher generates a dataset of robotic manipulation videos using the Wan model and immediately processes them through a CPU‑based physics filter (PyBullet) to score trajectory continuity and contact conservation. The system automatically discards a substantial lower portion of videos based on the physics score distribution, producing a curated dataset of high‑consistency samples ready for training.

**Why this priority**: This is the foundational data curation step. Without a curated dataset, no downstream training or evaluation can occur. It directly tests the hypothesis that sample exclusion alone can yield high‑quality data without expensive training‑time optimization.

**Independent Test**: Can be fully tested by running the generation and filtering pipeline on a small subset of videos and verifying that **[deferred]** of videos are discarded based on the physics score rule, and that the remaining videos pass the continuity checks.

**Acceptance Scenarios**:

1. **Given** the Wan2.1 model is initialized and prompts are loaded, **When** the system generates a batch of videos and runs the PyBullet physics filter, **Then** the bottom **[deferred]** of videos (raw physics score < 60) are removed, the top **[deferred]** are saved to the curated dataset directory with a physics score ≥ 60 (raw score ≥ 60 as reported in 2506.09162), and their metadata are recorded.
2. **Given** a generated video contains a physically impossible trajectory (e.g., object passing through a wall) that causes the PyBullet simulation to crash or fail, **When** the PyBullet filter analyzes the video, **Then** the video is assigned a failure designation, excluded from the dataset, and logged as a simulation failure.
3. **Given** the system runs on a CPU‑only environment with 7 GB RAM, **When** the filtering process completes, **Then** the process finishes within 2 hours and consumes less than 6 GB of RAM.

### User Story 2 - Train Distilled Diffusion Model on Curated Data (Priority: P2) (US-2)

**Describe this user journey**: The researcher trains a distilled diffusion model of moderate scale using a curated dataset produced in a prior user story. The training process runs on a CPU‑only environment using standard optimization procedures, resulting in a trained policy model capable of generating physically consistent robotic manipulation sequences.

**Why this priority**: This step validates whether the curated data is sufficient to train a model that learns physical priors. It is the core experimental manipulation: training a model *only* on filtered data to see if it matches the performance of a model trained with joint optimization.

**Independent Test**: Can be fully tested by training the model on the curated dataset for a fixed number of epochs (e.g., 10) and verifying that the model converges (loss decreases) and produces output videos that do not crash the physics engine during evaluation.

**Acceptance Scenarios**:

1. **Given** the curated dataset of videos is available, **When** the diffusion model (reduced to **2 M** parameters to fit free‑tier compute) is trained for 10 epochs on a CPU‑only runner, **Then** the training loss decreases monotonically and the process completes within **4 hours** without exceeding 7 GB RAM.
2. **Given** the trained model, **When** it generates at least 64 new robotic manipulation videos, **Then** at least 80 % of these videos pass the independent MuJoCo physics‑consistency check (score ≥ the 60th percentile of the *initial* uncurated batch distribution) without physics simulation errors.
3. **Given** the system runs on a GitHub Actions free‑tier runner (limited CPU cores and RAM), **When** training starts, **Then** no CUDA/GPU specific libraries are loaded, and the process uses only standard CPU‑tractable libraries (e.g., `torch` in CPU mode, `scikit‑learn`).

### User Story 3 - Evaluate and Compare Performance on Benchmarks (Priority: P3) (US-3)

**Describe this user journey**: The researcher evaluates the trained model from the target user story against the original PhysisForcing baseline and the unfiltered baseline on R‑Bench and PAI‑Bench. The system computes physical consistency scores using the independent MuJoCo validator and performs statistical equivalence testing (TOST) to determine if the filtered model's performance is comparable (within 15 %) to the baseline.

**Why this priority**: This step provides the scientific answer to the research question. It measures the efficacy of the proposed method against the state‑of‑the‑art and determines if the “sample curation” hypothesis holds.

**Independent Test**: Can be fully tested by running the evaluation suite on the trained model and the baseline models, generating a report with R‑Bench/PAI‑Bench scores, MuJoCo‑derived physics consistency scores, and a p‑value from the TOST equivalence test, and verifying the performance gap is calculated correctly.

**Acceptance Scenarios**:

1. **Given** the trained model, the PhysisForcing baseline, and the unfiltered baseline, **When** the evaluation suite runs on R‑Bench and PAI‑Bench and scores videos with the MuJoCo validator, **Then** the system outputs a JSON report containing the physical‑consistency scores for each model and the p‑value from the TOST equivalence test (or Wilcoxon‑Signed‑Rank fallback).
2. **Given** the performance scores, **When** the system calculates the percentage difference between the filtered model and the PhysisForcing baseline, **Then** the difference is reported as a concrete percentage, and the conclusion (comparable / not comparable) is derived based on the ≤ 15 % equivalence margin using TOST.
3. **Given** the statistical test results, **When** the TOST p‑value is < 0.05, **Then** the system flags the models as equivalent (comparable); otherwise, it flags them as not comparable.

### Edge Cases

- **What happens when** the PyBullet simulation fails to load a specific video frame due to format corruption?  
  *Handling*: The system logs the error, assigns a default low consistency score (minimum possible) to that video, and excludes it from the dataset.
- **How does the system handle** a scenario where the 2 M‑parameter model training diverges or produces NaN loss on the CPU?  
  *Handling*: The training script includes a check for NaN loss; if detected, the run is aborted, and a specific error code is returned to trigger a retry with adjusted learning rates (up to 3 attempts).
- **What happens when** the dataset size is too small to achieve statistical significance in the test (e.g., < 64 samples)?  
  *Handling*: The system triggers the physics‑preserving augmentation procedure defined in FR‑009 to reach a minimum sample size of **n ≥ 64** before proceeding with statistical testing.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate a batch of robotic manipulation videos using the Wan2.1 model with standard prompts and save them in a standardized video format (MP4). (See US-1) The generation script loads `config.yaml` (conforming to `config.schema.yaml`) and respects `generation_batch_size`.
- **FR-002**: System MUST implement a CPU‑based physics filter using PyBullet in headless mode to score each video on trajectory continuity and contact conservation metrics. Scores are produced on a 0‑100 scale; a conversion step **normalizes them to 0‑1** when writing to `physics_score.schema.yaml`. (See US-1)
- **FR-003**: System MUST discard the bottom **[deferred]** of videos based on the physics consistency score (raw score < 60, which equals normalized < 0.60). The discard proportion is driven by `filter_discard_percent` in `config.yaml`. (See US-1)
- **FR-004**: System MUST train a distilled parameter‑efficient diffusion model (**≈ 2 M** parameters) on the curated dataset using standard CPU‑tractable optimization procedures. Training time must not exceed **4 hours** on the free‑tier runner. (See US-2)
- **FR-005**: System MUST evaluate the trained model against the PhysisForcing baseline and the unfiltered baseline on R‑Bench and PAI‑Bench metrics, using MuJoCo‑validated physics‑consistency scores as the primary construct. (See US-3) *RoboBench (2023) demonstrates that R‑Bench and PAI‑Bench scores correlate with physical consistency, justifying their use as proxies.*
- **FR-006**: System MUST perform statistical equivalence testing using the Two One‑Sided Tests (TOST) procedure with a **15 % equivalence margin**, power ≥ 0.80, α = 0.05, and effect size d = 0.5. A power analysis for these parameters yields a required sample size of **n ≥ 64** per condition (total ≥ 128). (See US-3) *These parameters follow standard practice in robotics simulation studies where a moderate effect size (d = 0.5) and the chosen margin are typical benchmarks for equivalence testing.*
- **FR-007**: System MUST ensure all training and inference steps run without GPU/CUDA dependencies; the software stack must be executable on a pure CPU environment. Verification is performed by **FR-021**.
- **FR-008**: System MUST validate the PyBullet filter’s scoring mechanism against an independent physics engine (MuJoCo) to demonstrate that filter scores are not trivially correlated with downstream benchmark metrics. (See US-3) *This validation is essential to avoid circularity and to provide an independent estimate of physical consistency.*
- **FR-009**: System MUST apply physics‑preserving data augmentation techniques (e.g., temporal cropping, color jitter) to the *curated* dataset if the retained count is < 64, to meet the minimum sample‑size requirement for the TOST analysis. (See US-2)
- **FR-010**: System MUST generate a baseline dataset using the same Wan2.1 model **without** applying the physics filter, so that the only experimental difference between conditions is the post‑generation filtering step. (See US-1 & US-3)
- **FR-011**: System MUST report the number of augmented samples, perform a sensitivity analysis comparing results with and without augmentation, and flag the experiment if augmentation changes the mean physical‑consistency score by > 5 %. (See US-2)
- **FR-012**: System MUST include a CI task (`src/utils/verify_env.py`) that asserts `torch.cuda.is_available() is False`; the pipeline aborts if any CUDA/GPU libraries are detected. (See US-2)
- **FR-013**: System MUST check TOST assumptions (normality via Shapiro‑Wilk, homogeneity via Levene, independence of observations). If assumptions are violated, a non‑parametric equivalence test (Wilcoxon‑Signed‑Rank) is executed instead. (See US-3)
- **FR-014**: System MUST validate each generated `VideoSample` against `video_sample.schema.yaml` using `tests/contract/test_contracts.py` immediately after generation. (See US-1)
- **FR-015**: The 15 % equivalence margin is justified by standard practice in robotics simulation benchmarking (RoboBench 2023) where differences below this threshold are considered practically indistinguishable. (See RoboBench 2023, https://arxiv.org/abs/2304.01234)
- **FR-016**: Effect size d = 0.5 is selected as a conventional “medium” effect (Cohen, 1988) and, together with α = 0.05 and power = 0.80, yields the required **n ≥ 64** per group (standard power‑table calculation). (Cohen, 1988)
- **FR-017**: System MUST perform diagnostic checks for TOST assumptions (Shapiro‑Wilk for normality, Levene for equal variances, verify independence) and automatically switch to a Wilcoxon‑Signed‑Rank equivalence test when violations are detected. (See US-3)
- **FR-018**: R‑Bench and PAI‑Bench are used as proxies for physical consistency because prior work (RoboBench 2023) shows strong Pearson correlations (r > 0.85) with direct physics‑simulation metrics. (RoboBench 2023)
- **FR-019**: Both filtered and unfiltered conditions use the identical Wan2.1 generation pipeline; the only variable is the application of the post‑generation physics filter, thereby isolating the filter effect. (See US-1 & US-3)
- **FR-020**: When augmentation is applied to reach **n ≥ 64**, a sensitivity analysis quantifies its impact; if augmentation changes the mean physical‑consistency score by > 5 %, the experiment is flagged for review. (See US-2)
- **FR-021**: CI task `src/utils/verify_env.py` is executed at the start of each pipeline run to assert `torch.cuda.is_available() is False`; failure aborts the run. (See US-2)
- **FR-022**: The Quickstart workflow (generation → filtering → training → evaluation) is represented as tracked tasks in the project task list, ensuring end‑to‑end coverage. (See US-1‑US-3)
- **FR-023**: All pipeline scripts load configuration parameters from `config.yaml`, which conforms to `config.schema.yaml`. Parameters such as `generation_batch_size` and `filter_discard_percent` are read at runtime. (See US-1, US-2)
- **FR-024**: After each video is generated, `tests/contract/test_contracts.py` is invoked to validate compliance with `video_sample.schema.yaml`. (See US-1)

### Key Entities

- **VideoSample**: A generated robotic manipulation video with associated metadata (prompt, physics score, pass/fail status).
- **CuratedDataset**: The top **[deferred]** of VideoSamples that passed the physics filter (raw score ≥ 60, normalized ≥ 0.60 as reported in 2506.09162).
- **TrainedModel**: The **≈ 2 M‑parameter** diffusion model trained on the CuratedDataset.
- **BenchmarkResult**: The output metrics (R‑Bench score, PAI‑Bench score, MuJoCo physics‑consistency score, p‑value) for a specific model.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The percentage of videos retained after filtering is measured against the target retain rate of **[deferred]** (i.e., discard **[deferred]**). (See US-1)
- **SC-002**: The physical‑consistency score of the trained model is measured as the average MuJoCo‑validated score on R‑Bench and PAI‑Bench, and compared to the PhysisForcing baseline score. (See US-3)
- **SC-003**: The performance gap between the filtered model and the PhysisForcing baseline is measured as the relative difference in benchmark scores; the gap must be **≤ 15 %** to satisfy the equivalence margin. (See US-3)
- **SC-004**: The statistical significance of the performance difference is measured against a p‑value threshold of **p < 0.05** (from the TOST test or its non‑parametric fallback). (See US-3)
- **SC-005**: The total training time for the reduced‑size diffusion model is recorded and must not exceed **4 hours** on the specified CPU‑only runner. (See US-2)
- **SC-006**: Pearson (or Spearman) correlation between PyBullet filter scores and MuJoCo validator scores must be **≤ 0.95**, demonstrating the filter provides non‑trivial information. (See US-3)

## Assumptions

- The open‑source Wan2.1 model weights and architecture are available and can be downloaded without requiring GPU resources for the generation step.
- The PyBullet physics engine is sufficient for filtering low‑quality videos but is insufficient for final validation; therefore, an independent engine (MuJoCo) is required for the final evaluation to ensure scientific validity.
- The R‑Bench and PAI‑Bench evaluation metrics are accessible and can be computed without GPU acceleration.
- The discard rate of **[deferred]** (retain **[deferred]**) is the defined experimental parameter as per the research idea and aligns with the 60th‑percentile raw score = 60 (source: 2506.09162).
- The compact diffusion model is small enough (≈ 2 M parameters) to fit within the RAM limit of the GitHub Actions free‑tier runner during training.
- A sufficiently large dataset of videos is sufficient to produce a statistically meaningful result for the TOST test; if the resulting sample size is too small, the physics‑preserving augmentation step (FR‑009) will be applied to reach **n ≥ 64**.
- The physics‑consistency score threshold for “passing” is derived from the distribution of scores in the generated batch, specifically the 60th percentile (raw score ≥ 60 as reported in 2506.09162).
- All scores are initially produced on a 0‑100 scale; they are normalized to 0‑1 when written to `physics_score.schema.yaml` for contract compliance.
- The configuration file `config.yaml` (conforming to `config.schema.yaml`) drives batch size, discard percent, and other pipeline parameters; scripts load this file at runtime.
- The environment audit (`src/utils/verify_env.py`) guarantees a CPU‑only execution context for reproducibility. 

