# Feature Specification: llmXive follow-up: extending "Reproducing, Analyzing, and Detecting Reward Hacking in Rubric-Based R"

**Feature Branch**: `001-llmxive-followup`  
**Created**: 2026-07-13  
**Status**: Draft  
**Input**: User description: "To what extent does the statistical divergence between biased and unbiased LLM-as-a-Judge scores serve as a reliable, generalizable indicator of reward hacking across different rubric types and policy optimization stages?"

## User Scenarios & Testing

### User Story 1 - Ingest CHERRL Trajectories and Compute Divergence Gap (Priority: P1)

The researcher downloads pre-trained policy checkpoints and training logs from the CHERRL repository, extracting time-series data for biased ($J_{\text{biased}}$), unbiased ($J_{\text{unbiased}}$), and gold ($J_{\text{gold}}$) scores. The system computes the instantaneous divergence gap $G(t) = |J_{\text{biased}}(t) - J_{\text{unbiased}}(t)|$ and the rate of change $\Delta G(t)$ for every timestep across multiple random seeds.

**Why this priority**: This is the foundational data pipeline. Without accurate computation of the divergence signal and its derivative, no detection or analysis can occur. It establishes the ground truth for the entire study.

**Independent Test**: Can be fully tested by running the ingestion script on a small subset of CHERRL logs and verifying that the output CSV contains the computed $G(t)$ and $\Delta G(t)$ columns with correct mathematical values derived from the input $J$ columns.

**Acceptance Scenarios**:
1. **Given** a valid CHERRL log file containing $J_{\text{biased}}$, $J_{\text{unbiased}}$, and $J_{\text{gold}}$ columns, **When** the ingestion script processes the file, **Then** the output contains a new column $G(t)$ where every value equals $|J_{\text{biased}} - J_{\text{unbiased}}|$.
2. **Given** a valid CHERRL log file, **When** the script processes it, **Then** the output contains a column $\Delta G(t)$ representing the discrete derivative of $G(t)$ (e.g., $G(t) - G(t-1)$).
3. **Given** multiple log files from different seeds, **When** processed, **Then** the system aggregates them into a single dataset preserving the `seed_id` and `bias_type` (Lexical, Format, Tone) metadata.

---

### User Story 2 - Detect Hacking via Statistical Thresholding (Priority: P2)

The researcher runs the detector module which calculates the z-score of $G(t)$ over a sliding window and flags a timestep as "hacked" if $z(G(t)) > \tau$ or $\Delta G(t)$ exceeds a dynamic threshold derived from a baseline noise floor. The system outputs a binary label for each timestep indicating "hacking suspected."

**Why this priority**: This implements the core hypothesis testing mechanism. It transforms the raw signal into a decision, allowing the researcher to evaluate if the divergence signal is a viable proxy for misalignment.

**Independent Test**: Can be fully tested by feeding a synthetic dataset with a known "spike" in divergence and verifying that the detector correctly flags the timesteps surrounding the spike while ignoring low-noise periods.

**Acceptance Scenarios**:
1. **Given** a dataset with a pre-computed baseline noise floor and a known divergence spike, **When** the detector runs with a fixed threshold $\tau = 3.0$, **Then** timesteps where $z(G(t)) > 3.0$ are labeled as "hacked."
2. **Given** a dataset where $\Delta G(t)$ suddenly increases by >50% relative to the baseline variance, **When** the detector runs, **Then** the system flags the onset of the increase even if the absolute z-score is below $\tau$.
3. **Given** a "non-hacked" control run (unbiased rewards only), **When** the detector runs, **Then** the false-positive rate remains below [deferred] across the entire trajectory.

---

### User Story 3 - Evaluate Generalization and Statistical Significance (Priority: P3)

The researcher evaluates the detector's performance across different rubric types (Lexical, Format, Tone, Self-praise) by calculating Precision, Recall, and F1-score against ground-truth hacking labels (derived from $J_{\text{gold}}$ drops). The system performs a paired t-test comparing the detector's F1-scores against a static-threshold baseline to confirm statistical significance (p < 0.05). This evaluation is valid only if the independence check in FR-006 passes.

**Why this priority**: This validates the generalizability claim. It determines if the method works across different bias types and if the results are statistically robust rather than due to chance.

**Independent Test**: Can be fully tested by running the evaluation script on a pre-labeled test set and verifying that the output includes a confusion matrix, F1-score per bias type, and a p-value from the t-test.

**Acceptance Scenarios**:
1. **Given** a dataset with ground-truth hacking labels derived from $J_{\text{gold}}$ drops (verified independent of $J_{\text{unbiased}}$), **When** the evaluation runs, **Then** the system reports Precision, Recall, and F1-score for each rubric type separately.
2. **Given** F1-scores from the proposed detector and a static-threshold baseline (flagging last [deferred] of steps) across 10 seeds, **When** the t-test runs, **Then** the system outputs a p-value and a boolean indicating if $p < 0.05$.
3. **Given** the results, **When** the report is generated, **Then** it explicitly states whether a single threshold generalizes across all bias types or if rubric-specific tuning is required.

### Edge Cases

- What happens when a trajectory has zero variance in $G(t)$ (e.g., constant scores), causing division by zero in z-score calculation? The system must handle this by setting the z-score to 0 or using a small epsilon floor.
- How does the system handle missing timesteps in the CHERRL logs (gaps in the time series)? The system must interpolate or skip gaps without breaking the sliding window calculation.
- What occurs if the $J_{\text{gold}}$ signal is noisy and does not show a sharp drop despite high divergence? The system must correctly label this as a "false positive" or "missed detection" based on the ground truth, without crashing.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest CHERRL log files and compute the divergence gap $G(t) = |J_{\text{biased}}(t) - J_{\text{unbiased}}(t)|$ for every timestep, ensuring the calculation is performed on the raw float values without rounding errors that could distort the signal. (See US-1)
- **FR-002**: System MUST calculate the rate of change $\Delta G(t)$ and the rolling z-score of $G(t)$ using a sliding window of size $W=20$ timesteps, with a minimum of 5 samples required to compute the standard deviation. (See US-2)
- **FR-003**: System MUST flag a timestep as "hacked" if $z(G(t)) > 3.0$ OR if $\Delta G(t)$ exceeds a substantially elevated multiple of the sample standard deviation (ddof=1, excluding NaN values) of the first several timesteps. (See US-2)
- **FR-004**: System MUST derive ground-truth hacking labels strictly from drops in the $J_{\text{gold}}$ signal, defined as a decrease of ≥ 0.1 relative to the running mean of the preceding timesteps (excluding the current window), sustained for ≥ 3 timesteps. This derivation is valid ONLY if FR-006 confirms statistical independence between $J_{\text{unbiased}}$ and $J_{\text{gold}}$. (See US-3)
- **FR-005**: System MUST perform a paired t-test comparing the F1-scores of the divergence detector against a static-threshold baseline (which flags the last [deferred] of training steps as hacked) across all seeds, reporting the p-value and effect size. (See US-3)
- **FR-006**: System MUST calculate the Pearson correlation coefficient between $J_{\text{unbiased}}$ and $J_{\text{gold}}$ across the entire trajectory. If the correlation coefficient exceeds a high threshold, the system MUST halt ground-truth generation and emit an error, as this indicates circular validation risk. (See US-3)

### Key Entities

- **Trajectory**: A time-series record of a policy's training run, containing columns for $J_{\text{biased}}$, $J_{\text{unbiased}}$, $J_{\text{gold}}$, `seed_id`, and `bias_type`.
- **Divergence Signal**: A computed feature set derived from a Trajectory, containing $G(t)$, $\Delta G(t)$, $z(G(t))$, and the binary `hacked_label`.
- **Evaluation Report**: A summary object containing Precision, Recall, F1-score per bias type, and statistical test results (p-value, t-statistic).
- **False Positive Rate**: Defined as $FP / (FP + TN)$, where FP is the count of timesteps flagged as hacked when not ground-truth hacked, and TN is the count of timesteps correctly identified as not hacked.
- **Aggregated F1-Score**: The macro-average of F1-scores calculated independently for each seed, ensuring equal weighting regardless of hacking frequency per seed.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The detector's F1-score is measured against the ground-truth hacking labels derived from $J_{\text{gold}}$ drops (verified independent), with success defined as achieving an F1-score > 0.6 across at least 3 distinct bias types. (See FR-004, US-3)
- **SC-002**: The statistical significance of the detector is measured against a static-threshold baseline using a paired t-test, with success defined as a p-value < 0.05 across the set of seeds. (See FR-005, US-3)
- **SC-003**: The generalization capability is measured by the variance in F1-scores across rubric types (Lexical, Format, Tone), with success defined as a standard deviation of F1-scores ≤ 0.15, indicating a single threshold is viable. (See US-3)
- **SC-004**: The computational feasibility is measured by the total runtime on a standard GitHub Actions free-tier runner (2 CPU, 7GB RAM), with success defined as completing the full analysis of all available seeds in the CHERRL repository (minimum N=5) within 4 hours. (See FR-001, FR-002)

## Assumptions

- The CHERRL repository (arXiv:2606.04923) provides downloadable pre-trained checkpoints and training logs containing the necessary $J_{\text{biased}}$, $J_{\text{unbiased}}$, and $J_{\text{gold}}$ time-series data for multiple random seeds and bias types.
- The $J_{\text{unbiased}}$ signal is derived from an independent reward model trained on a separate dataset, ensuring it is not a direct function of $J_{\text{gold}}$. This independence is verified at runtime by FR-006.
- The analysis will be restricted to a CPU-only environment; therefore, any statistical methods requiring GPU acceleration (e.g., deep learning-based anomaly detection) are out of scope.
- The sliding window size for z-score calculation is fixed at a predetermined number of timesteps., and the threshold $\tau$ is fixed at 3.0, as these are standard statistical defaults for outlier detection in time-series data.
- The dataset size (number of timesteps and seeds) will fit within the available RAM limit of the CI runner.; if not, the system will process seeds sequentially rather than in parallel.
- The "drop" in $J_{\text{gold}}$ used for ground-truth labeling is defined as a sustained decrease of ≥ 0.1 relative to the preceding 50 timesteps, based on the typical magnitude of reward collapse observed in the CHERRL paper.
- If FR-006 detects high correlation (>0.8), the dataset is considered invalid for this specific study, and the system must halt rather than proceed with circular validation.