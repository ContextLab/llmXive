# Feature Specification: llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil"

**Feature Branch**: `001-llmxive-follow-up-extending-anyflow-any`  
**Created**: 2026-08-22  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil'"

## User Scenarios & Testing

### User Story 1 - Data Curation and Ground-Truth Annotation (Priority: P1)

As a researcher, I need to curate a dataset of short video clips containing a verified 50/50 mix of continuous motion and abrupt scene cuts, and manually annotate each with a temporal continuity score (0.0 to 1.0), so that I have a labeled ground truth to evaluate model stability against.

**Why this priority**: Without a labeled dataset distinguishing "stable" (continuous) from "unstable" (discontinuous) segments, no metric can be validated. This is the foundational ground-truth layer required for all subsequent correlation analysis.

**Independent Test**: A script can be run to ingest raw video URLs, download a representative sample of video clips (a sequence of frames at 30fps), and output a CSV file where every row contains a video ID and a manual score between 0.0 and 1.0. Verification requires randomly sampling 50 clips and confirming ≥ 90% match against a re-annotation rubric (Cohen's Kappa ≥ 0.81) using two independent annotators applying a 5-point Likert scale rubric distinguishing motion continuity from scene cuts.

**Acceptance Scenarios**:
1. **Given** a list of public video repository URLs (e.g., UCF101, Kinetics), **When** the curation script runs, **Then** a set of unique video clips of exactly 16 frames at 30fps is downloaded and stored locally, ensuring a 50/50 mix of continuous motion and scene cuts.
2. **Given** a downloaded video clip, **When** a human annotator reviews it, **Then** a numeric score between 0.0 (perfect continuity) and 1.0 (maximum discontinuity) is recorded in the ground-truth CSV.
3. **Given** the ground-truth CSV, **When** the system validates the data, **Then** every entry has a valid video path, a score within the [0.0, 1.0] range, and the distribution of scores shows a minimum variance of 0.05 (unless the distribution is bimodal with sample size ≥ 50, in which case the system MUST proceed with binary analysis (Logistic Regression or Mann-Whitney U test)).

---

### User Story 2 - CPU-Tractable Latent Divergence Calculation (Priority: P2)

As a researcher, I need to load a frozen AnyFlow model in a CPU-optimized format (ONNX Runtime) and compute a "flow-map divergence" metric for every video clip without using a GPU, so that I can generate a predictive feature vector for the entire dataset within the 6-hour CI budget.

**Why this priority**: This is the core experimental engine. If the metric cannot be computed on CPU within the time limit, the study cannot proceed. It transforms raw video into the quantitative variable needed for correlation.

**Independent Test**: A script processes the 500 video clips on a standard GitHub Actions free-tier runner (ubuntu-22.04, 2-core vCPU, 7GB RAM) and outputs a CSV with divergence scores, completing within ≤ 6 hours and consuming <7GB peak RAM. The output divergence score for a known static clip (a sequence of uniform zero-valued frames) must match a pre-computed golden value within an absolute tolerance consistent with floating-point precision requirements.

**Acceptance Scenarios**:
1. **Given** a video clip and the frozen AnyFlow model, **When** the inference script runs on a CPU-only environment, **Then** the script completes without CUDA/GPU errors and produces a latent trajectory divergence score.
2. **Given** the full dataset of 500 clips, **When** the batch processing job runs, **Then** the total execution time is ≤ 6 hours and peak memory usage remains ≤ 7 GB.
3. **Given** a clip with a known scene cut and a clip with continuous motion, **When** the metric is computed for both, **Then** the system outputs valid numerical scores for both, allowing the subsequent analysis to determine if they are distinct.

---

### User Story 3 - Correlation Analysis and Threshold Sensitivity (Priority: P3)

As a researcher, I need to perform a Pearson and Spearman correlation analysis, a multivariate logistic regression, and a sensitivity analysis on the classification threshold, so that I can quantify the relationship and validate the metric's robustness as a predictive signature.

**Why this priority**: This delivers the final scientific result (the correlation coefficient and regression model) and addresses the methodological requirement for threshold justification, turning raw numbers into a publishable finding.

**Independent Test**: A statistical script reads the two CSVs (ground truth and divergence), outputs a Pearson $r$ and Spearman $\rho$ value with a p-value, a multivariate logistic regression model, and generates a sensitivity report showing how classification rates change across three specific thresholds. The false-positive and false-negative rates must match a manual calculation on a synthetic subset of 50 clips with known labels within an acceptable tolerance (absolute error < 0.01).

**Acceptance Scenarios**:
1. **Given** the ground-truth scores and divergence metrics, **When** the analysis script runs, **Then** it outputs a Pearson correlation coefficient ($r$), a Spearman rank correlation ($\rho$), and a p-value indicating statistical significance.
2. **Given** a proposed divergence threshold (e.g., 0.05), **When** the sensitivity analysis runs, **Then** the system reports the false-positive and false-negative rates for thresholds {0.01, 0.05, 0.1}.
3. **Given** the correlation result, **When** the report is generated, **Then** it contains a statement explicitly framing the relationship as associational and not causal.
4. **Given** the divergence pattern features, **When** the multivariate model runs, **Then** it outputs a prediction accuracy for discontinuity type (cut vs. continuous) that is significantly better than random chance.

### Edge Cases

- What happens when a video clip contains no motion at all (static image)? The system must assign a divergence score and a continuity score (0.0) that reflect a valid baseline condition.
- How does the system handle a video clip where the AnyFlow model fails to extract latent representations (e.g., corrupted file)? The system must log the error, skip the clip, and flag it in the final report without crashing the batch job.
- What if the manual annotation scores are bimodal (only 0.0 or 1.0) rather than continuous? If the distribution is bimodal and the sample size is ≥ 50, the system MUST proceed with binary analysis (Logistic Regression or Mann-Whitney U test) instead of Pearson/Spearman correlation, regardless of the variance value.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and store a representative set of video clips (16 frames at 30fps) from public repositories (UCF101, Kinetics, DAVIS) ensuring a verified 50/50 mix of continuous motion and scene cuts. The system MUST employ a stratified sampling strategy to achieve this 50/50 mix. All metrics must be computed from real video data; the system MUST compute the divergence metric from actual model inference on real video data. The system MUST ensure that every figure, statistic, or interpretation in the paper traces back to exactly one row in this project's data/ and one block in this project's code/ (no hand-typed numbers). (See US-1)
- **FR-002**: System MUST provide a mechanism for manual annotation of each video clip with a temporal continuity score ranging from 0.0 to 1.0. The annotation process MUST rely solely on pixel-space visual inspection using a 5-point Likert scale rubric distinguishing motion continuity from scene cuts; no latent-space features or model-derived metrics (including optical flow from the AnyFlow trajectory) are permitted for generating the ground-truth score. The annotator MUST be blinded to the dataset's stratification labels (cut vs. continuous) during the annotation process. Disagreements between two annotators MUST be resolved by a third expert adjudicator. Static images MUST be scored as 0.0 (continuous). (See US-1)
- **FR-003**: System MUST load the frozen AnyFlow model in a CPU-optimized format (e.g., ONNX Runtime) and extract latent representations for all frames without requiring GPU acceleration. The system MUST complete this process within ≤ 6 hours and consume <7GB peak RAM. (See US-2)
- **FR-004**: System MUST calculate the "flow-map divergence" for each clip by computing the sum of squared L2 distances (MSE) between the model's predicted intermediate state and a Numerical Baseline (a high-resolution Euler rollout using the Explicit Euler method with N=500 steps, or N=N_max if constrained by FR-009), averaged across the sequence and normalized by the latent vector dimension D to produce a mean squared error. The baseline step count N defaults to a converged baseline (ground truth) for the primary metric, where convergence is defined as 'change in MSE < 1e-4 between N and N+100'. If FR-009 forces a lower N_max, the baseline is N_max. The system MUST also extract temporal pattern features (kurtosis, temporal clustering) from the divergence trajectory. The metric measures numerical integration error (model instability), which is HYPOTHESIZED to correlate with semantic temporal discontinuity. The Euler baseline is ONLY the reference for calculating numerical error; the VALIDATION of this metric relies SOLELY on the independent manual scores (FR-002), not on the baseline itself. The system MUST compare results against a control set of clips known to have continuous motion to distinguish solver error from semantic discontinuity. The system MUST perform a control analysis that compares the distribution of divergence scores on known-smooth vs. known-cut clips. The system MUST test the null hypothesis that numerical error is uncorrelated with semantic discontinuity using Fisher's r-to-z transformation on the correlation coefficient with alpha=0.05. The system MUST also verify that Pearson correlation (r > 0.7) remains stable within ±0.05 tolerance after model quantization changes. (See US-2)
- **FR-005**: System MUST perform a Pearson correlation analysis AND a Spearman rank correlation analysis between the manual continuity scores and the computed divergence metrics to test the hypothesis of a relationship (linear or monotonic). Spearman rank correlation MUST be the primary test for the ordinal nature of the Likert data. The system MUST also perform a multivariate logistic regression model using divergence pattern features to predict discontinuity type (cut vs. continuous), applying inverse-probability weighting (IPW) to correct for the 50/50 stratification bias. If the data is bimodal (0.0/1.0) and sample size ≥ 50, the system MUST use Logistic Regression (with IPW) or Mann-Whitney U test. The system MUST perform a control analysis comparing error rates on continuous vs. discontinuous clips. The system MUST output a prediction accuracy metric for discontinuity type (cut vs. continuous). (See US-3)
- **FR-006**: System MUST execute a sensitivity analysis sweeping the classification threshold over an explicit set of representative values {0.01, 0.05, 0.1} AND sweeping the baseline resolution N over {500, 200, 100} (in descending order) to quantify the impact of the Euler solver's discretization error and test the metric's robustness against coarser approximations. If FR-009 forces a baseline N_max < 500, the sweep is restricted to {N_max, floor(N_max/2), 100} (clamped to available values >= 100 and deduplicated). The system MUST stop and report if a lower N fails to converge. The system MUST report the resulting false-positive and false-negative rates for each combination. (See US-3)
- **FR-007**: System MUST frame all findings regarding the relationship between divergence and continuity as associational, explicitly avoiding causal claims due to the observational nature of the study. (See US-3)
- **FR-008**: System MUST explicitly document in the final report that the "flow-map divergence" metric is a proxy for model instability and that the correlation analysis tests the hypothesis that this instability correlates with semantic discontinuity. (See US-3)
- **FR-009**: System MUST perform a pre-flight complexity check on a representative subset of 10 clips to estimate total runtime with a 95% confidence interval using a t-distribution. The projected total runtime is calculated as (mean runtime of the sample of clips) * target total clips. If the projected total runtime exceeds 5.5 hours on the target runner, the system MUST reduce the Euler steps to N=200 (or the next feasible lower value) and label the resulting metric as "flow-map divergence (N=200)", or halt with an error if N=200 is also infeasible. If N is reduced, the system MUST re-run a pilot on 10 clips to verify the correlation coefficient (r) remains > 0.7 before proceeding with the full dataset. (See US-2)
- **FR-010**: System MUST first verify inter-annotator agreement (Cohen's Kappa ≥ 0.81) on a subset of 50 clips. If Kappa < 0.81, the system MUST halt and report "Insufficient Annotation Agreement". The system MUST verify that the variance of the manual continuity scores is ≥ 0.05 before proceeding to correlation analysis. Bimodality is determined by Hartigan's Dip Test with p < 0.05. EXCEPTION: If the distribution is bimodal (only 0.0 and 1.0) and the sample size is ≥ 50, the system MUST proceed with binary analysis (Logistic Regression or Mann-Whitney U test) regardless of the variance. If variance < 0.05 and the data is not bimodal with sufficient size, the system MUST halt and report an "Insufficient Variance" error. (See US-3)
- **FR-011**: System MUST perform a formal power analysis to justify the sample size of 500, ensuring the study is powered to detect the minimum effect size (r ≈ 0.12) at 80% power (alpha=0.05). (See US-1)
- **FR-012**: System MUST generate a synthetic subset of 50 clips with known labels for validation and verify that the false-positive and false-negative rates match a manual calculation on this subset within an absolute error < 0.01. (See US-3)

### Key Entities

- **VideoClip**: A short video segment with a unique ID, source URL, and file path (16 frames at 30fps).
- **ContinuityScore**: A manual ground-truth label (float 0.0–1.0) assigned to a VideoClip representing temporal stability. This score is derived solely from pixel-space visual inspection using a 5-point Likert scale rubric distinguishing motion continuity from scene cuts.
- **DivergenceMetric**: A computed float value representing the sum of squared L2 distances (normalized by dimension D) between the model's predicted latent state and a Numerical Baseline (high-resolution Euler rollout). This metric quantifies numerical integration error (model instability). The metric is labeled as "flow-map divergence (N=500)" or "flow-map divergence (N=200)" depending on the baseline steps used.
- **SensitivityReport**: A structured output listing threshold values {0.01, 0.05, 0.1} and baseline resolutions {500, 200, 100} (or restricted set) and their corresponding classification error rates.
- **VarianceReport**: A distinct output artifact (variance_report.csv) containing the calculated variance of the ContinuityScore distribution.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The analysis script MUST output a Pearson $r$ value, a Spearman $\rho$ value, and a p-value; the result is recorded regardless of magnitude. (See US-3)
- **SC-002**: The full pipeline (download, annotation, inference, analysis) MUST complete within 6 hours on a CPU-only runner (ubuntu-22.04, 2-core vCPU, 7GB RAM) with peak memory usage ≤ 7 GB. If N=200 is used, the report MUST state this. (See US-2)
- **SC-003**: The sensitivity analysis MUST report distinct classification rates (false-positive rate and false-negative rate) for a range of threshold values AND baseline resolutions, using manual scores > 0.5 as positive labels. (See US-3)
- **SC-004**: The system MUST output a distinct artifact variance_report.csv containing the variance of the ContinuityScore distribution, and this artifact MUST be linked to the final report. (See US-1)
- **SC-005**: The final report MUST explicitly state that the AnyFlow model was run in CPU-only mode without CUDA or quantization methods requiring GPU hardware. (See US-2)
- **SC-006**: The system MUST output the divergence scores in CSV format and link this file to the final report. (See US-2)

## Assumptions

- The public video repositories (UCF101, Kinetics, DAVIS) provide sufficient raw data to curate a representative set of distinct short clips containing both continuous motion and abrupt scene cuts, provided a stratified sampling strategy is used. The UCF101 source is the official Google Drive link or a verified HF dataset card with a stable commit hash. The DAVIS source is verified to contain annotated scene cuts or is replaced by a Kinetics-400 subset known to contain such cuts.
- The frozen AnyFlow model weights are available in a format compatible with ONNX Runtime conversion for CPU inference without requiring retraining or fine-tuning. The source is the official model repository or a stable release tag containing the 'AnyFlow' weights.
- Manual annotation of a representative set of clips by a human (or small team) is feasible within the project timeline, assuming approximately two minutes per clip.
- The "flow-map divergence" metric defined as the sum of squared L2 distances (normalized by dimension D) between predicted and Euler-rolled states is computationally tractable on a limited number of CPU cores for 16-frame sequences with N=500 steps (or N=200 as a fallback).
- The relationship between video content discontinuity and model trajectory stability may be linear or monotonic; therefore, both Pearson and Spearman correlations are used to capture potential non-linear patterns.
- No GPU hardware is available or permitted for this analysis; all methods must strictly adhere to CPU-only execution constraints.
- The "temporal continuity score" is a valid proxy for the ground truth of scene cuts and object appearances, assuming the annotator follows a consistent rubric and does not use model-derived features.
- The hypothesis that "distilled models fail more on cuts than on smooth motion" is tested by comparing the *change* in numerical error (divergence) across conditions. "Fail" in this context refers to the numerical divergence exceeding a threshold relative to the baseline, not necessarily semantic degradation. The correlation analysis tests whether this numerical failure rate is higher for discontinuous scenes.
- N=500 is selected as the baseline because it provides a discretization error < 1e-3 in pilot tests, and the sensitivity analysis will explicitly sweep N=500, N=200, and N=100 to verify robustness against the Euler solver's approximation error.
- The null hypothesis that numerical error is uncorrelated with semantic discontinuity must be tested and rejected (or not) based on the correlation results.
- The 50/50 stratified sampling is used to ensure statistical power, and inverse-probability weighting (IPW) is applied to correct for selection bias.