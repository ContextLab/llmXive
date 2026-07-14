# Feature Specification: llmXive Follow-up: VLA Contextual Interference Study

**Feature Branch**: `001-vla-contextual-interference`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "Does the attenuation of knowledge signals in the upper layers of Vision-Language-Action (VLA) models make them uniquely susceptible to contextual interference, such that their performance on knowledge-based embodied tasks degrades significantly more than their non-action VLM baselines when visually complex, irrelevant distractors are present?"

## User Scenarios & Testing

### User Story 1 - Synthetic Distractor Generation (Priority: P1)

**Researcher** needs to programmatically generate a "Distractor Variant" of the Act2Answer dataset by overlaying semantically irrelevant, high-contrast geometric shapes onto existing task images without occluding the target objects or instruction text, to create the necessary input conditions for the interference study.

**Why this priority**: Without a reliable, reproducible method to generate noisy images that preserve ground truth validity, the core comparison between "Clean" and "Distractor" conditions cannot be established. This is the foundational data engineering step.

**Independent Test**: Can be fully tested by running the generation script on a small subset (e.g., 10 images) and verifying that the target object bounding boxes remain unoccluded and the visual noise is present, without requiring model inference.

**Acceptance Scenarios**:

1. **Given** a clean image from the Act2Answer dataset and a target object bounding box, **When** the distractor script overlays 3–5 high-contrast geometric shapes, **Then** the generated image contains the distractors and the target object remains ≥95% unoccluded.
2. **Given** a batch of 100 images, **When** the script processes them, **Then** the output directory contains exactly 100 modified images with consistent naming conventions (e.g., `img_001_distractor.png`).
3. **Given** an image with text instructions, **When** the script overlays distractors, **Then** the text region remains readable and unobscured by geometric shapes.

---

### User Story 2 - CPU-Constrained Model Inference Loop (Priority: P2)

**Researcher** needs to execute inference on 7 VLA models and 9 VLM baselines using a lightweight, CPU-only loop that processes both clean and distractor images, extracts predicted coordinates/IDs, and logs results without exceeding 7 GB RAM or 6 hours of runtime.

**Why this priority**: This is the core experimental execution. It must be robust enough to handle multiple model types and conditions while strictly adhering to the compute constraints of the CI environment. Failure here prevents any data collection.

**Independent Test**: Can be tested by running the inference loop on a single model (e.g., one VLA) with a subset of 50 images (clean + distractor) and verifying that the process completes within the memory limit and outputs a valid JSON/CSV log of predictions.

**Acceptance Scenarios**:

1. **Given** a pre-trained VLA model loaded in CPU mode, **When** the inference loop processes a batch of 20 distractor images, **Then** the process completes without OOM errors and logs the predicted action for each image.
2. **Given** the system running on the GitHub Actions runner, **When** the total inference time for a model exceeds 45 minutes (1/8th of the 6-hour timeout), **Then** the system logs a warning but continues processing the remaining batches to ensure data completeness.
3. **Given** a model that fails to load or crashes during inference, **When** the loop encounters the error, **Then** the system logs the error with the model name and image ID, retries the batch up to 3 times (See FR-006), and if all attempts fail, skips the batch and proceeds to the next model without terminating the entire job.
4. **Given** a model that returns a prediction format incompatible with the expected coordinate/object ID schema, **When** the inference wrapper attempts to parse it, **Then** the system retries parsing up to 3 times (See FR-008); if all fail, the sample is marked "Invalid Prediction" and excluded from accuracy calculation.

---

### User Story 3 - Fragility Score Calculation & Statistical Analysis (Priority: P3)

**Researcher** needs to compute the "Knowledge Fragility Score" (normalized performance drop) for each model-category pair and perform a paired statistical test to determine if the mean fragility of VLAs is significantly higher than that of VLMs.

**Why this priority**: This transforms raw inference logs into the final scientific result (the hypothesis test). It validates the research question.

**Independent Test**: Can be tested by providing a static CSV of mock accuracy data (clean vs. distractor) and verifying that the script correctly calculates the normalized fragility score and outputs the p-value and test statistic for a paired test.

**Acceptance Scenarios**:

1. **Given** a CSV containing accuracy metrics for 7 VLAs and 9 VLMs across clean and distractor conditions, **When** the analysis script runs, **Then** it outputs a "Knowledge Fragility Score" for every model-category pair.
2. **Given** the calculated fragility scores, **When** the statistical test is performed, **Then** the output includes the test type (paired t-test or Wilcoxon signed-rank), the p-value, and a boolean indicating if $Mean_{VLA} > Mean_{VLM}$ at $\alpha = 0.05$.
3. **Given** a scenario where the data distribution is non-normal (Shapiro-Wilk p < 0.05), **When** the script detects this, **Then** it automatically switches to the Wilcoxon signed-rank test and logs the switch.
4. **Given** the p-values from the group comparison, **When** the multiple-comparison correction is applied, **Then** the system applies Bonferroni or Holm-Bonferroni correction to control the family-wise error rate at $\alpha = 0.05$.

---

### User Story 4 - Pilot Feasibility Check (Priority: P2)

**Researcher** needs to execute a small-scale pilot run (50 images) to estimate the total runtime for the full experiment and abort the process if the projection exceeds the 6-hour CI limit, preventing wasted compute resources.

**Why this priority**: The CI environment has a hard 6-hour timeout. A pilot check ensures the full experiment is feasible before committing to the full run, saving time and resources if the configuration is too slow.

**Independent Test**: Can be tested by running the pilot script on a subset of 50 images and verifying that the system correctly calculates the projected time and either proceeds or aborts based on the 6-hour threshold.

**Acceptance Scenarios**:

1. **Given** a pilot sample of 50 images, **When** the system runs inference on a single model, **Then** it calculates the average time per image and projects the total time for the full dataset (N_images × 2 conditions × 16 models).
2. **Given** a projected total time > 6 hours, **When** the pilot check completes, **Then** the system aborts the run and logs "Insufficient Compute: Projected time exceeds 6 hours".
3. **Given** a projected total time ≤ 6 hours, **When** the pilot check completes, **Then** the system proceeds to the full inference run.

---

### User Story 5 - Scientific Reporting & Causal Framing (Priority: P3)

**Researcher** needs to generate a final report that explicitly frames all statistical findings as associational (not causal) and includes a standard disclaimer, ensuring the study adheres to scientific integrity given the observational nature of the data.

**Why this priority**: The study design is observational (no random assignment of models to environments). Misinterpreting association as causation would invalidate the scientific contribution. This requirement ensures the output is scientifically rigorous.

**Independent Test**: Can be tested by generating a mock report and verifying that it contains the mandatory "Correlation does not imply causation" disclaimer and avoids causal language (e.g., "causes", "leads to") when describing model differences.

**Acceptance Scenarios**:

1. **Given** the final statistical results, **When** the report is generated, **Then** the report explicitly states that findings are associational and includes the disclaimer: "Correlation does not imply causation".
2. **Given** a draft report containing causal language (e.g., "VLA models cause higher fragility"), **When** the validation step runs, **Then** the system flags the language as non-compliant and requires revision.

---

### Edge Cases

- **What happens when** a distractor shape accidentally occludes a critical part of the target object (e.g., a hand holding an object)? -> The script must include a validation step that calculates IoU between distractor polygons and target bounding boxes; if IoU > 0.05, the image is flagged and regenerated with a different random seed (See FR-001).
- **How does system handle** a model that returns a prediction format incompatible with the expected coordinate/object ID schema? -> The inference wrapper must implement a strict parsing regex; if parsing fails 3 times for a specific sample, the sample is marked as "Invalid Prediction" and excluded from accuracy calculation (See FR-008), with a log entry.
- **What happens when** the GitHub Actions runner hits the 6-hour timeout before all models are processed? -> The system must implement a "checkpoint" mechanism (saving intermediate results every 10 images) so that a restart can resume from the last successful batch rather than restarting from zero (See FR-007).

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate synthetic distractor images by overlaying 3–5 high-contrast geometric shapes onto Act2Answer images while ensuring target object occlusion is ≤5% (IoU ≤ 0.05). The system MUST calculate Intersection-over-Union (IoU) between distractor polygons and target bounding boxes and reject/regenerate if IoU > 0.05 (See US-1).
- **FR-002**: System MUST load and run inference on specified VLA and VLM models using CPU-only flags (no CUDA/GPU) and default precision to fit within 7 GB RAM (See US-2).
- **FR-003**: System MUST extract predicted coordinates or object IDs from model outputs and compare them against ground truth labels to calculate accuracy for both clean and distractor conditions (See US-2).
- **FR-004**: System MUST compute the "Knowledge Fragility Score" as follows:
  1. If Clean Accuracy > 0: Score = (Clean Accuracy - Distractor Accuracy) / Clean Accuracy.
  2. If Clean Accuracy = 0: Score = (0 - Distractor Accuracy) (i.e., the absolute negative drop).
  This definition prevents models that fail on clean data from artificially appearing robust (See US-3).
- **FR-005**: System MUST perform a paired statistical hypothesis test (paired t-test or Wilcoxon signed-rank test) to compare the mean fragility scores of the VLA group versus the VLM group, accounting for the shared image stimuli. The system MUST output the p-value (See US-3).
- **FR-006**: System MUST implement a retry mechanism for Model Batch Load/Crash failures with a maximum of 3 attempts per batch. If all 3 attempts fail, the batch is logged as "Skipped" and the job proceeds to the next batch/model. This retry logic applies ONLY to model load/crash events, not to individual sample parsing errors (See US-2).
- **FR-007**: System MUST save intermediate inference results to disk periodically at regular intervals. Additionally, the system MUST calculate the estimated remaining time based on linear extrapolation from the average time of a recent set of processed images and log a warning if the projected total time exceeds 5.4 hours ([deferred] of the 6-hour limit) (See US-2).
- **FR-008**: System MUST implement a retry mechanism for Sample Parsing failures with a maximum of 3 attempts per sample. If all 3 attempts fail, the sample is marked as "Invalid Prediction" and MUST be excluded from accuracy calculations (See US-2).
- **FR-009**: System MUST perform a sensitivity analysis on the distractor density (varying numbers of shapes) to ensure the fragility score is not an artifact of a specific density configuration. The system MUST report the variation in Knowledge Fragility Scores across these density levels (See US-3).
- **FR-010**: System MUST execute a Pilot Feasibility Check on a sample of images before the full run. If the projected total time for the full run (based on the pilot) exceeds a reasonable operational threshold, the system MUST abort. and report "Insufficient Compute" (See US-4).
- **FR-011**: System MUST frame all statistical findings regarding VLA vs. VLM performance differences as ASSOCIATIONAL, explicitly avoiding causal language unless the dataset contains randomized assignment (which it does not). The report MUST include a disclaimer stating "Correlation does not imply causation" (See US-5).
- **FR-012**: System MUST apply a multiple-comparison correction (e.g., Bonferroni or Holm-Bonferroni) to the p-values generated across the 7 VLA and 9 VLM models to control the family-wise error rate at α = 0.05 (See US-3).
- **FR-013**: System MUST validate that CPU-only inference (with default precision) preserves the signal-to-noise ratio required for the study. This validation MUST be performed on a "Golden Set" of 10 images where ground truth is known; if the model accuracy on the Golden Set drops below [deferred] compared to a GPU baseline (or known reference), the system MUST abort and flag "Quantization/Compute Degradation" (See Assumptions).

### Key Entities

- **Model Instance**: Represents a specific pre-trained VLA or VLM model configuration (name, version, architecture) used for inference.
- **Test Condition**: Represents the input state of an image, categorized as either "Clean" or "Distractor" (with specific distractor parameters).
- **Prediction Record**: A data point containing the image ID, model ID, condition, predicted action/coordinate, ground truth, and binary correctness flag.
- **Fragility Metric**: An aggregate value representing the normalized performance drop (or absolute drop if clean accuracy is 0) for a specific model-category pair.
- **N_models**: A constant representing the total number of models (N_models = 16, composed of 7 VLAs and 9 VLMs).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The "Knowledge Fragility Score" (normalized or absolute) is measured for every model-category pair, with the reference being the calculated difference between Clean and Distractor accuracy (See FR-004, US-3).
- **SC-002**: The statistical significance of the difference between VLA and VLM fragility is measured against the standard alpha threshold of 0.05, using a paired test with correction for multiple comparisons (See FR-005, FR-012, US-3).
- **SC-003a**: The System Completion Rate is measured against the total number of scheduled batches, requiring ≥95% of batches to complete (excluding known invalid batches) (See FR-006, US-2).
- **SC-003b**: The Data Validity Rate is measured against the total number of processed samples, requiring ≥95% of samples to be valid (excluding "Invalid Prediction" samples) (See FR-008, US-2).
- **SC-004**: The memory footprint of the inference loop is measured against the 7 GB RAM limit, requiring peak usage to remain ≤6.5 GB to provide a safety margin (See FR-002, US-2).
- **SC-005**: The distractor generation validity is measured by the percentage of generated images where target object occlusion is ≤5%, requiring ≥95% of valid outputs to meet this criteria (See FR-001, US-1).
- **SC-006**: The Pilot Feasibility Check is measured against the 6-hour timeout constraint, requiring the projected time to be ≤6 hours for the full run to proceed (See FR-010).
- **SC-007**: The sensitivity analysis is measured by the stability of the Fragility Score across the tested distractor densities (3, 4, 5 shapes), requiring the variation (max difference) in Fragility Scores to be <10% across the sweep (See FR-009, US-3).
- **SC-008**: The Signal Validation (FR-013) is measured by the accuracy on the Golden Set, requiring ≥90% accuracy relative to the GPU baseline (See FR-013).

## Assumptions

- **Assumption about dataset variables**: The Act2Answer dataset contains the necessary ground truth labels (coordinates/object IDs) for all episodes, and the associated VLM benchmark images are accessible via the source repository.
- **Assumption about model availability**: The VLA models and VLM baselines specified in the original preprint are available on HuggingFace with compatible `transformers` implementations that support CPU-only inference without requiring specific hardware accelerators.
- **Assumption about distractor semantics**: The "semantically irrelevant" geometric shapes (circles, squares, triangles) can be generated programmatically without requiring a separate generative model, ensuring the distractors do not introduce new semantic content that could confuse the models.
- **Assumption about compute constraints**: The total number of inference operations (N_images × 2 conditions × 16 models) is subject to a Pilot Feasibility Check (FR-010) on 50 images. If the pilot indicates the full run will exceed 6 hours, the experiment is aborted. This is a resource constraint necessary to prevent wasted CI time.
- **Assumption about statistical power**: The sample size of N_images episodes is sufficient to detect a meaningful difference in fragility scores between VLA and VLM groups using a paired t-test or Wilcoxon signed-rank test at $\alpha=0.05$ with 80% power; if the effect size is extremely small, the result may be inconclusive (power limitation acknowledged).
- **Assumption about inference precision**: Using default precision (float32) on CPU is sufficient to produce stable predictions for these models; 8-bit or 4-bit quantization is avoided to ensure compatibility with CPU-only runners. However, a validation step (FR-013) ensures signal integrity.
- **Assumption about observational nature**: The study design is purely observational (no random assignment of models to environments); therefore, any observed differences in fragility are interpreted as associations between model architecture and robustness, not causal effects of the architecture on the specific noise condition.
- **Assumption about collinearity**: The predictor variables (VLA vs. VLM architecture) are distinct and not definitionally derived from one another. While the model groups are distinct, the statistical test is **paired** on the image stimuli (Clean vs. Distractor for each model), meaning the analysis does not assume the two groups are independent samples in the calculation of the test statistic, but rather accounts for the within-image correlation.
- **Assumption about sensitivity analysis**: The sensitivity analysis on distractor density (FR-009) is essential to rule out the possibility that the observed fragility is an artifact of a specific noise density (e.g., 4 shapes) rather than a general property of the model architecture.
- **Assumption about timeout variable**: The maximum runtime constraint is defined as **MAX_RUNTIME_HOURS = 6.0**. Warnings are triggered at a high threshold and aborts at 100% (6.0 hours).