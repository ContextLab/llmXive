# Feature Specification: llmXive follow-up: extending "Kwai Keye-VL-2.0 Technical Report"

**Feature Branch**: `001-extreme-aspect-ratio-robustness`  
**Created**: 2026-08-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending Kwai Keye-VL-2.0 Technical Report"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Synthetic Benchmark Generation (Priority: P1)

As a researcher, I need to programmatically generate a synthetic video benchmark dataset by applying extreme aspect ratio distortions (1:10, 10:1, 1:20, 20:1) to the ActivityNet Captions dataset, while preserving the original temporal ground-truth annotations, so that I can isolate the impact of geometric distortion on model performance without introducing temporal noise.

**Why this priority**: This is the foundational data layer. Without a valid, controlled dataset where the only variable is aspect ratio, no subsequent inference or analysis can yield valid conclusions. It directly enables the core hypothesis test.

**Independent Test**: Can be fully tested by running the data generation script and verifying that the output directory `output/distorted/` contains a collection of video files matching the naming pattern `{activitynet_id}_{ratio}.mp4`, with multiple files generated per ratio to ensure adequate coverage across the distortion spectrum., that the aspect ratios match the specified targets within a tight tolerance, and that the metadata file correctly maps each distorted video to its original ActivityNet ground-truth timestamps. Additionally, verify that square-cropped control clips are generated in `output/control/`.

**Acceptance Scenarios**:

1. **Given** the ActivityNet Captions source dataset is available, **When** the generation script runs with parameters for 1:10, 10:1, 1:20, and 20:1 ratios, **Then** the output directory contains a substantial set of videos for each ratio with valid video codecs and a metadata CSV linking them to original timestamps.
2. **Given** the generation script is executed, **When** the output is inspected, **Then** the spatial dimensions of the generated frames strictly adhere to the target aspect ratios (e.g., width/height = 0.1 for 1:10) without unintended cropping of the original content's bounding boxes.
3. **Given** the original ground-truth annotations exist, **When** the new metadata is generated, **Then** the start and end timestamps remain identical to the source, ensuring the temporal variable is held constant.
4. **Given** the generation script is executed, **When** the square-cropped control set is generated, **Then** the output directory `output/control/` contains exactly 500 clips with a uniform aspect ratio and valid metadata linking to the same source IDs.

---

### User Story 2 - CPU-Constrained Inference Execution (Priority: P2)

As a researcher, I need to execute the Kwai Keye-VL model (quantized to INT4) on the generated extreme-aspect and square-cropped datasets using a CPU-only environment, so that I can collect temporal grounding predictions (start/end timestamps) for every video clip within the 6-hour CI time limit and 7GB RAM constraint.

**Why this priority**: This delivers the raw empirical data (predictions). It is the core "experiment" phase. If this fails due to resource constraints or incorrect model loading, the project cannot proceed to analysis.

**Independent Test**: Can be fully tested by running the inference script on a subset of 10 videos and verifying that the script completes without OOM errors, that the model loads successfully using `llama.cpp` or `Optimum-Intel` on CPU, and that a JSON output file is generated containing valid timestamp predictions for all 10 inputs. Peak memory usage must be measured via `/proc/[pid]/status VmRSS` and remain within acceptable resource limits.

**Acceptance Scenarios**:

1. **Given** the model checkpoint is loaded in INT4 quantization, **When** the inference script processes a video clip, **Then** the peak VmRSS remains below a moderate threshold and the process completes within 15 minutes per clip (aggregated < 6 hours for full set).
2. **Given** the input video has an extreme aspect ratio (e.g., 1:20), **When** the model processes it, **Then** the output JSON contains a start and end timestamp pair without raising a shape mismatch or dimension error.
3. **Given** the square-cropped control set is processed, **When** the inference completes, **Then** the output file contains predictions for all control clips with the same format as the extreme-aspect set.

---

### User Story 3 - Statistical Analysis & Reporting (Priority: P3)

As a researcher, I need to calculate the mean Intersection-over-Union (mIoU) for both the extreme-aspect and square-cropped conditions and perform a paired statistical test (t-test or Wilcoxon) to determine if the performance drop is significant, so that I can validate or refute the hypothesis regarding spatial token dispersion.

**Why this priority**: This transforms raw data into scientific insight. It is the final step that answers the research question and determines the project's success.

**Independent Test**: Can be fully tested by providing a pre-generated JSON of predictions and ground truths to the analysis script and verifying that it outputs a report containing the mIoU for both groups, the p-value, and the test statistic, confirming the statistical significance threshold (p < 0.05).

**Acceptance Scenarios**:

1. **Given** the prediction JSON and ground-truth metadata are loaded, **When** the mIoU calculation runs, **Then** the script outputs a mean mIoU value for the extreme-aspect group and the square-cropped group.
2. **Given** the two mIoU distributions are calculated, **When** the statistical test runs, **Then** the script correctly identifies the normality of the data using the Shapiro-Wilk test (alpha=0.05) and selects either a paired t-test or Wilcoxon signed-rank test accordingly.
3. **Given** the statistical test is complete, **When** the report is generated, **Then** it explicitly states whether the difference is statistically significant (p < 0.05) and includes the effect size.

---

### Edge Cases

- What happens if the video frame rate is too low to generate enough frames for the model's native resolution requirement? (System must skip or upsample with a warning).
- How does the system handle a video clip where the extreme aspect ratio causes the content to be reduced to a 1-pixel line? (System must flag as "unresolvable" and exclude from the final count, recording the exclusion).
- What happens if the INT4 quantization causes the model to crash on a specific video length? (System must implement a retry mechanism with a fallback to FP16 for that specific clip, logging the event as JSON with {clip_id, error, fallback_mode} after consecutive OOM errors).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST programmatically generate 500 synthetic video clips from ActivityNet Captions with aspect ratios of:10, 10:1, 1:20, and 20:1 (125 clips per ratio), preserving original temporal ground-truth annotations. The system MUST exclude and regenerate any clip where the distortion reduces the primary subject's bounding box area by >95% to ensure semantic integrity is preserved (See US-001).
- **FR-002**: The system MUST load the Kwai Keye-VL checkpoint in INT4 quantization. and execute inference on a CPU-only environment without requiring CUDA or GPU accelerators. If INT4 load fails due to memory constraints, the system MUST fallback to FP for the vision encoder (keeping LLM in INT4) and log the deviation (See US-002).
- **FR-003**: The system MUST output prediction timestamps (start/end) for every processed video clip in a structured JSON format compatible with the mIoU calculation (See US-002).
- **FR-004**: The system MUST calculate the mean Intersection-over-Union (mIoU) for the predicted timestamps against the preserved ground-truth annotations for both the extreme-aspect and square-cropped conditions (See US-003).
- **FR-005**: The system MUST perform a paired statistical test (t-test or Wilcoxon signed-rank) to compare the mIoU distributions and report the p-value and effect size (See US-003).
- **FR-006**: The system MUST enforce a hard memory limit (measured via VmRSS) and a total batch execution time limit within a reasonable operational window. The system MUST use `cgroups` (or `ulimit` fallback) to kill processes exceeding the memory limit and a wrapper script to abort the batch if the total time limit is exceeded (See US-002).

### Key Entities

- **SyntheticVideoClip**: A video file with specific aspect ratio distortion, linked to an original ActivityNet ID and ground-truth timestamps.
- **Prediction**: A record containing the video ID, predicted start timestamp, and predicted end timestamp.
- **EvaluationMetric**: A record containing the calculated mIoU score for a specific video, the condition (extreme vs. square), and the ground-truth interval.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The mIoU score for the extreme-aspect condition is measured against the mIoU score of the square-cropped control condition to determine the performance delta (See FR-004, FR-005).
- **SC-002**: The statistical significance of the performance difference is measured against the standard alpha threshold of p < 0.05 using a paired test (See FR-005).
- **SC-003**: The inference execution time per video is measured against the 6-hour total job limit to ensure feasibility on free-tier CI (See FR-002).
- **SC-004**: The memory footprint of the inference process is measured against the 7GB RAM limit to ensure no OOM failures occur (See FR-002).
- **SC-005**: The dataset completeness is measured against the target of a representative set of distorted video clips (distributed across ratios) and a corresponding set of square-cropped control clips to ensure statistical power (See FR-001).

## Assumptions

- **Assumption about data**: The ActivityNet Captions dataset is accessible and contains sufficient video content that can be distorted to extreme aspect ratios (1:20) without losing all semantic visual information (e.g., the video is not already a single vertical strip).
- **Assumption about model availability**: The Kwai Keye-VL-2.0 checkpoint is available in a format compatible with `llama.cpp` or `Optimum-Intel` for CPU inference, or a compatible INT4 quantized version can be derived without violating the 7GB RAM constraint.
- **Assumption about computational limits**: The 500 video clips, when processed sequentially on a 2-core CPU, will complete within the 6-hour limit; if the average inference time exceeds a predefined threshold, the dataset size will be dynamically reduced to a manageable subset to maintain feasibility.
- **Assumption about ground truth**: The original ActivityNet ground-truth timestamps are accurate and do not require adjustment when the video aspect ratio is changed, as the temporal event boundaries remain constant regardless of spatial distortion, provided the visual signal is not destroyed (clips failing the semantic integrity check in FR-001 are excluded).
- **Assumption about quantization**: The INT4 quantization of the model does not degrade the temporal grounding accuracy so severely that it masks the effect of aspect ratio distortion (i.e., the signal-to-noise ratio remains sufficient to detect a >15% drop).