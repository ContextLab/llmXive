# Feature Specification: llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil"

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil'"

## User Scenarios & Testing

### User Story 1 - Data Curation and Ground-Truth Annotation (Priority: P1)

As a researcher, I need to curate a dataset of short video clips containing a verified mix of continuous motion and abrupt scene cuts, and manually annotate each with a temporal continuity score (0.0 to 1.0), so that I have a labeled ground truth to evaluate model stability against.

**Why this priority**: Without a labeled dataset distinguishing "stable" (continuous) from "unstable" (discontinuous) segments, no metric can be validated. This is the foundational ground-truth layer required for all subsequent correlation analysis.

**Independent Test**: A script can be run to ingest raw video URLs, download a representative sample of video clips (16 frames at 30fps), and output a CSV file where every row contains a video ID and a manual score between 0.0 and 1.0. Verification requires randomly sampling [deferred] of rows (minimum 50 clips) and confirming ≥ 90% match against a re-annotation rubric (Cohen's Kappa ≥ 0.81).

**Acceptance Scenarios**:
1. **Given** a list of public video repository URLs (e.g., UCF101, Kinetics), **When** the curation script runs, **Then** a set of unique video clips of exactly 16 frames at 30fps is downloaded and stored locally.
2. **Given** a downloaded video clip, **When** a human annotator reviews it, **Then** a numeric score between 0.0 (perfect continuity) and 1.0 (maximum discontinuity) is recorded in the ground-truth CSV.
3. **Given** the ground-truth CSV, **When** the system validates the data, **Then** every entry has a valid video path, a score within the [0.0, 1.0] range, and the distribution of scores shows a minimum variance of 0.05 (unless the distribution is bimodal with sample size ≥ 50, in which case binary analysis is permitted).

---

### User Story 2 - CPU-Tractable Latent Divergence Calculation (Priority: P2)

As a researcher, I need to load a frozen AnyFlow model in a CPU-optimized format (ONNX Runtime) and compute a "flow-map divergence" metric for every video clip without using a GPU, so that I can generate a predictive feature vector for the entire dataset within the 6-hour CI budget.

**Why this priority**: This is the core experimental engine. If the metric cannot be computed on CPU within the time limit, the study cannot proceed. It transforms raw video into the quantitative variable needed for correlation.

**Independent Test**: A script processes the 500 video clips on a standard GitHub Actions free-tier runner (ubuntu-latest, 2-core vCPU, 7GB RAM) and outputs a CSV with divergence scores, completing within ≤ 6 hours and consuming <7GB peak RAM. The output divergence score for a known static clip (e.g., a single-color frame repeated 16 times) must match a pre-computed golden value within a tolerance of 1e-4.

**Acceptance Scenarios**:
1. **Given** a video clip and the frozen AnyFlow model, **When** the inference script runs on a CPU-only environment, **Then** the script completes without CUDA/GPU errors and produces a latent trajectory divergence score.
2. **Given** the full dataset of 500 clips, **When** the batch processing job runs, **Then** the total execution time is ≤ 6 hours and peak memory usage remains ≤ 7 GB.
3. **Given** a clip with a known scene cut and a clip with continuous motion, **When** the metric is computed for both, **Then** the system outputs valid numerical scores for both, allowing the subsequent analysis to determine if they are distinct.

---

### User Story 3 - Correlation Analysis and Threshold Sensitivity (Priority: P3)

As a researcher, I need to perform a Pearson and Spearman correlation analysis between the manual continuity scores and the computed divergence metrics, and run a sensitivity analysis on the classification threshold, so that I can quantify the relationship and validate the metric's robustness.

**Why this priority**: This delivers the final scientific result (the correlation coefficient) and addresses the methodological requirement for threshold justification, turning raw numbers into a publishable finding.

**Independent Test**: A statistical script reads the two CSVs (ground truth and divergence), outputs a Pearson $r$ and Spearman $\rho$ value with a p-value, and generates a sensitivity report showing how classification rates change across three specific thresholds. The false-positive and false-negative rates must match a manual calculation on a synthetic subset of known labels within a tolerance of 0.01.

**Acceptance Scenarios**:
1. **Given** the ground-truth scores and divergence metrics, **When** the analysis script runs, **Then** it outputs a Pearson correlation coefficient ($r$), a Spearman rank correlation ($\rho$), and a p-value indicating statistical significance.
2. **Given** a proposed divergence threshold (e.g., 0.05), **When** the sensitivity analysis runs, **Then** the system reports the false-positive and false-negative rates for thresholds {0.01, 0.05, 0.1}.
3. **Given** the correlation result, **When** the report is generated, **Then** it contains a statement explicitly framing the relationship as associational and not causal.

### Edge Cases

- What happens when a video clip contains no motion at all (static image)? The system must assign a divergence score and a continuity score that reflect a valid baseline condition.
- How does the system handle a video clip where the AnyFlow model fails to extract latent representations (e.g., corrupted file)? The system must log the error, skip the clip, and flag it in the final report without crashing the batch job.
- What if the manual annotation scores are bimodal (only 0.0 or 1.0) rather than continuous? If the distribution is bimodal and the sample size is ≥ 50, the system MUST proceed with a binary classification analysis (Fisher's Exact Test) instead of Pearson/Spearman correlation, regardless of the variance value.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and store a representative set of video clips (16 frames at 30fps) from public repositories (UCF101, Kinetics, DAVIS) ensuring a mix of continuous motion and scene cuts. The system MUST employ a stratified sampling strategy to guarantee that at least 20% of the curated clips contain abrupt scene cuts. NO synthetic data, placeholder metrics, or simulated scores are generated or used. All metrics must be computed from real video data. (See US-1)
- **FR-002**: System MUST provide a mechanism for manual annotation of each video clip with a temporal continuity score ranging from 0.0 to 1.0. The annotation process MUST rely solely on pixel-space visual inspection; no latent-space features or model-derived metrics (including optical flow from the AnyFlow trajectory) are permitted for generating the ground-truth score. (See US-1)
- **FR-003**: System MUST load the frozen AnyFlow model in a CPU-optimized format (e.g., ONNX Runtime) and extract latent representations for all frames without requiring GPU acceleration. (See US-2)
- **FR-004**: System MUST calculate the "flow-map divergence" for each clip by computing the L2 distance between the model's predicted intermediate state and a Numerical Baseline (a high-resolution Euler rollout using the Explicit Euler method with N steps), averaged across the sequence. The distance is normalized by the latent vector dimension D to produce a mean squared error (MSE). The baseline step count N defaults to 500 but is permitted to be reduced to 200 if runtime constraints (FR-009) are met. The metric measures numerical integration error (model instability), which is HYPOTHESIZED to correlate with semantic temporal discontinuity. The system MUST test the null hypothesis that numerical error is uncorrelated with semantic discontinuity. (See US-2)
- **FR-005**: System MUST perform a Pearson correlation analysis AND a Spearman rank correlation analysis between the manual continuity scores and the computed divergence metrics to test the hypothesis of a relationship (linear or monotonic). If the data is bimodal (0.0/1.0) and sample size ≥ 50, the system MUST use Fisher's Exact Test. (See US-3)
- **FR-006**: System MUST execute a sensitivity analysis sweeping the classification threshold over an explicit set of representative values {0.01, 0.05, 0.1} AND sweeping the baseline resolution N over {500, 200, 100} to quantify the impact of the Euler solver's discretization error. The system MUST report the resulting false-positive and false-negative rates for each combination. (See US-3)
- **FR-007**: System MUST frame all findings regarding the relationship between divergence and continuity as associational, explicitly avoiding causal claims due to the observational nature of the study. (See US-3)
- **FR-008**: System MUST explicitly document in the final report that the "flow-map divergence" metric is a proxy for model instability and that the correlation analysis tests the hypothesis that this instability correlates with semantic discontinuity. (See US-3)
- **FR-009**: System MUST perform a pre-flight complexity check on the first 5 clips to estimate total runtime. The projected total runtime is calculated as (mean runtime of a sample of clips / sample size) * target total clips. If the projected total runtime exceeds 5.5 hours on the target runner, the system MUST reduce the Euler steps to N=200 and label the resulting metric as "flow-map divergence (N=200)", or halt with an error if N=200 is also infeasible. (See US-2)
- **FR-010**: System MUST verify that the variance of the manual continuity scores is ≥ 0.05 before proceeding to correlation analysis. EXCEPTION: If the distribution is bimodal (only 0.0 and 1.0) and the sample size is ≥ 50, the system MUST proceed with binary analysis (Fisher's Exact Test) regardless of the variance. If variance < 0.05 and the data is not bimodal with sufficient size, the system MUST halt and report an "Insufficient Variance" error. (See US-3)

### Key Entities

- **VideoClip**: A short video segment with a unique ID, source URL, and file path (16 frames at 30fps).
- **ContinuityScore**: A manual ground-truth label (float 0.0–1.0) assigned to a VideoClip representing temporal stability. This score is derived solely from pixel-space visual inspection.
- **DivergenceMetric**: A computed float value representing the L2 distance (normalized by dimension D) between the model's predicted latent state and a Numerical Baseline (high-resolution Euler rollout). This metric quantifies numerical integration error (model instability). The metric is labeled as "flow-map divergence (N=500)" or "flow-map divergence (N=200)" depending on the baseline steps used.
- **SensitivityReport**: A structured output listing threshold values {0.01, 0.05, 0.1} and baseline resolutions {500, 200, 100} and their corresponding classification error rates.
- **VarianceReport**: A distinct output artifact (variance_report.csv) containing the calculated variance of the ContinuityScore distribution.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The analysis script MUST output a Pearson $r$ value, a Spearman $\rho$ value, and a p-value; the result is recorded regardless of magnitude. (See US-3)
- **SC-002**: The full pipeline (download, annotation, inference, analysis) MUST complete within 6 hours on a CPU-only runner (ubuntu-latest, 2-core vCPU, 7GB RAM) with peak memory usage ≤ 7 GB. If N=200 is used, the report MUST state this. (See US-2)
- **SC-003**: The sensitivity analysis MUST report distinct classification rates (false-positive/negative) for a range of threshold values AND baseline resolutions. (See US-3)
- **SC-004**: The system MUST output a distinct artifact variance_report.csv containing the variance of the ContinuityScore distribution, and this artifact MUST be linked to the final report. (See US-1)
- **SC-005**: The final report MUST explicitly state that the AnyFlow model was run in CPU-only mode without CUDA or quantization methods requiring GPU hardware. (See US-2)

## Assumptions

- The public video repositories (UCF, Kinetics, DAVIS) provide sufficient raw data to curate a representative set of distinct short clips containing both continuous motion and abrupt scene cuts, provided a stratified sampling strategy is used.
- The frozen AnyFlow model weights are available in a format compatible with ONNX Runtime conversion for CPU inference without requiring retraining or fine-tuning.
- Manual annotation of a representative set of clips by a human (or small team) is feasible within the project timeline, assuming approximately two minutes per clip.
- The "flow-map divergence" metric defined as the L2 distance (normalized by dimension D) between predicted and Euler-rolled states is computationally tractable on a limited number of CPU cores for 16-frame sequences with N=500 steps (or N=200 as a fallback).
- The relationship between video content discontinuity and model trajectory stability may be linear or monotonic; therefore, both Pearson and Spearman correlations are used to capture potential non-linear patterns.
- No GPU hardware is available or permitted for this analysis; all methods must strictly adhere to CPU-only execution constraints.
- The "temporal continuity score" is a valid proxy for the ground truth of scene cuts and object appearances, assuming the annotator follows a consistent rubric and does not use model-derived features.
- The hypothesis that "distilled models fail more on cuts than on smooth motion" is tested by comparing the *change* in numerical error (divergence) across conditions. "Fail" in this context refers to the numerical divergence exceeding a threshold relative to the baseline, not necessarily semantic degradation. The correlation analysis tests whether this numerical failure rate is higher for discontinuous scenes.
- N=500 is selected as the baseline because it provides a discretization error < 1e-3 in pilot tests, and the sensitivity analysis will explicitly sweep N=500, N=200, and N=100 to verify robustness against the Euler solver's approximation error.
- The null hypothesis that numerical error is uncorrelated with semantic discontinuity must be tested and rejected (or not) based on the correlation results.