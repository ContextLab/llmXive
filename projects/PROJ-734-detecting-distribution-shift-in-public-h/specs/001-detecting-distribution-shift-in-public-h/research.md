# Research: Detecting Distribution Shift in Public Health Surveillance Data via Kernel Two‑Sample Tests

## Overview

This document details the dataset strategy, methodological choices, and feasibility analysis for the distribution shift detection pipeline. It explicitly addresses the distinction between statistical distribution shifts and clinical outbreak events, and defines the fallback protocols for data availability.

## Dataset Strategy

### Primary Dataset: CDC FluView ILI Rates
- **Description**: Weekly Influenza-like Illness (ILI) rates from the CDC FluView surveillance system.
- **Variables**: `week_id` (ISO week string), `ili_rate` (percentage of outpatient visits).
- **Usage**: Primary time series for MMD, Pettitt, and BOCPD analysis.
- **Source Status**: **Verified Source Available (with caveats)**.
 - *Access Method*: The pipeline will attempt to download the CSV from the CDC FluView Interactive Web Reports API or a direct archived CSV URL (e.g., ` -> download link). If the official URL changes, the pipeline will fail with `E-NO-DATA` and require manual URL update.
 - *Action*: The implementation will use a robust downloader that verifies the file integrity (checksum) and halts if the source is unreachable. No mock data is used for the final run.
 - *Note*: The spec mentions "CDC FluView weekly ILI CSV (≈ 20 years, < 10 MB)". The implementation will handle missing weeks and outliers as per FR-002.

### Ground Truth Dataset: Virological/Hospitalization Data
- **Description**: Independent outbreak labels (start/end weeks) derived from virological surveillance (e.g., % positive for Flu A/B) or hospitalization data (CDC FluSurv-NET, NREVSS).
- **Variables**: `event_name`, `start_week`, `end_week`.
- **Usage**: Calculation of precision, recall, and detection delay (FR-006).
- **Source Status**: **Verified Source Available (with caveats)**.
 - *Access Method*: The pipeline will attempt to download from CDC FluSurv-NET or NREVSS public CSV/API endpoints. If unavailable, the pipeline halts with `E-NO-GROUND-TRUTH`.
 - *Action*: The pipeline will look for a `ground_truth_events.csv` in `data/raw/`. If absent, the evaluation step (FR-006) will **halt** and report "Ground Truth Unavailable" to avoid hallucinated metrics. The spec mandates real data; synthetic data is **not** used for final metrics.
 - *Note*: The spec assumes this data is available; the implementation must handle the missing case robustly by halting.

### Verified Datasets (Available for Testing)
The following datasets are verified and available for **unit testing** (CSV parsing, schema validation) only:
- ` (Generic CSV)
- ` (CDC FAQ, not ILI)
- ` (Heart data)
- ` (CD Conv data)

*Decision*: The primary pipeline will **not** use these verified datasets for the core analysis. They are used **only** to test the CSV parsing and schema validation logic in `tests/unit/`. The main analysis requires real CDC data.

## Methodological Approach

### 1. Preprocessing (FR-002)
- **Missing Values**: Rows with missing `ili_rate` are dropped. Imputation is rejected per spec to avoid introducing bias.
- **Zero Handling**: If `ili_rate` is 0, it is replaced with a small positive constant (e.g., 0.01) before log-transform to avoid `-inf`. This is a standard practice for rate data with zero counts.
- **Transformation**: Log-transform applied to `ili_rate` (after zero handling) to normalize the distribution (common for rate data).
- **Standardization**: **Rolling (Window-Local) Z-score standardization** applied to the log-transformed series. For each window pair, the mean and std are computed *within* the two windows being compared. This preserves local mean shifts (the primary signal of an outbreak) while removing global scale effects. **Global standardization is rejected** as it would mask local shifts.
- **Seasonal Baseline Adjustment**: To distinguish between expected seasonal shifts and actual outbreaks, a seasonal baseline (e.g., 52-week moving average) is subtracted from the log-transformed series before local standardization. This isolates non-seasonal distributional changes.

### 2. MMD Two-Sample Test (FR-003, FR-004)
- **Kernel**: Gaussian RBF kernel.
- **Bandwidth**: Median heuristic (default) and cross-validation (sensitivity). The bandwidth is computed from the *original* pooled sample of the two windows and **fixed** for the permutation test to ensure the null distribution is valid. Re-computing bandwidth per permutation is computationally prohibitive; the fixed-bandwidth approach is a standard approximation.
- **Null Distribution**: Permutation test with $B=1000$ permutations.
- **Significance**: Bonferroni correction $\alpha_{adj} = 0.01 / N$, where $N$ is the number of window pairs.
- **Feasibility**: With ~1000 weeks, $N \approx 988$. $1000 \times 988$ permutations is computationally heavy.
 - *Optimization*: If runtime exceeds 25 minutes, the system reduces $B$ to 500 (FR-008).

### 3. Baseline Methods (FR-005)
- **Pettitt Test (Sliding-Window Adaptation)**: The Pettitt test is run on each 12-week sliding window to detect a change point *within* that window. This matches the MMD's local sensitivity and is required by FR-005. The null hypothesis is "no change point within this window".
- **BOCPD**: Bayesian Online Change-Point Detection with a Gaussian observation model. This provides a continuous run-length estimate.
- **Thresholding Strategy**: To compare MMD (continuous p-values) with Pettitt/BOCPD (discrete change points), MMD detections are converted to "events" by identifying **contiguous runs** of flagged weeks (p < alpha). The start of the run is the detection point. This enables direct comparison of "detection delay".
- **Comparison**: Detected change points (from Pettitt/BOCPD) and MMD event starts are aligned to the MMD window indices for comparison.

### 4. Sensitivity Analysis (FR-007, FR-010)
- **Grid**:
 - Bandwidth: Median heuristic, Cross-validated.
 - Window Length:, 12, 16 weeks.
 - **Tolerance**: ±1, ±2, ±3 weeks for ground truth matching (FR-010).
- **Output**: `sensitivity.csv` recording metrics for each configuration.

### 5. Performance Metrics (FR-006, SC-001 to SC-003)
- **Precision**: True Positives / (True Positives + False Positives).
- **Recall**: True Positives / (True Positives + False Negatives).
- **Detection Delay**: Mean lag between true event start and first detected flag (MMD event start or baseline change point).
 - *Note*: Due to biological lags between ILI and Virological/Hospitalization data, this metric is interpreted as "lead time" rather than "simultaneous detection".
- **False Positive Rate**: (Number of flagged weeks outside any ground‑truth interval) / (Total number of non‑outbreak weeks). The denominator is explicitly tracked.
- **Statistical Comparison (SC-004)**: Detection delays of Pettitt and BOCPD are compared to MMD's using a two-sample t-test; the p-value is reported.

## Computational Feasibility

- **Hardware**: GitHub Actions Free Tier (2 CPU, 7 GB RAM).
- **Memory**: The dataset is <10 MB. The largest memory footprint will be the permutation matrix for MMD ($N \times B$). With $N \approx 1000, B=1000$, this is ~8 MB (float64), well within limits.
- **Time**:
 - MMD calculation: $O(N \cdot B \cdot W)$ where $W$ is window size. $1000 \times 1000 \times 12 \approx 1.2 \times 10^7$ ops. Feasible in <5 mins.
 - Sensitivity Grid: 2 bandwidths $\times$ 3 windows $\times$ 3 tolerances = 18 runs. Total time $\approx 30$ mins.
 - **Fallback**: FR-008 mandates reducing $B$ if time exceeds threshold.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **No verified source for ILI/Ground Truth** | Pipeline fails to download data. | Pipeline halts with clear error (E-NO-DATA). No mock data for final run. Unit tests use synthetic data. |
| **Permutation test too slow** | Timeout on CI. | Auto-reduce $B$ to 500; log the reduction. |
| **Collinearity in predictors** | N/A (MMD is non-parametric, no predictors). | Not applicable. |
| **Multiple Comparisons** | High false positive rate. | Bonferroni correction (FR-004) strictly enforced. |
| **Ground Truth Misalignment** | Metrics skewed. | ±2 week tolerance window (FR-006) applied; sensitivity analysis includes ±1, ±2, ±3 weeks. |
| **Variance Shifts affecting MMD** | Bandwidth adaptation masks shift. | Bandwidth fixed from original pooled sample; caveat noted in report. |

## Decision Rationale

- **Why Permutation Test?** Analytic approximations for MMD p-values are less accurate for small sample sizes (windows of 12 weeks). Permutation tests provide robust, distribution-free p-values.
- **Why Bonferroni?** Public health surveillance requires high specificity to avoid alarm fatigue. Bonferroni is conservative but guarantees family-wise error rate control.
- **Why CPU-only?** The dataset size and algorithmic complexity ($O(N \cdot B)$) are tractable on CPU. GPU overhead (data transfer, kernel launch) would outweigh benefits for this scale.
- **Why Local Standardization?** Global standardization would mask local mean shifts (outbreaks). Local standardization preserves the signal while removing scale effects.
- **Why Sliding-Window Pettitt?** Required by FR-005 to match MMD's local sensitivity. Global Pettitt would not detect local changes.
- **Why Halt on Missing Data?** The spec (FR-006) mandates real ground truth for metrics. Using synthetic data for final results would violate the "Verified Accuracy" principle.
