# Research: llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil"

## Executive Summary

This research investigates whether the numerical instability of the AnyFlow video diffusion model—quantified as "flow-map divergence"—correlates with semantic temporal discontinuities (scene cuts). The hypothesis is that distilled models, which approximate flow maps, exhibit higher integration error at discontinuities compared to continuous motion. The study relies on a CPU-tractable pipeline using ONNX Runtime, manual ground-truth annotation, and rigorous statistical testing (Spearman correlation primary, Pearson exploratory, logistic regression, sensitivity analysis).

**Critical Feasibility Note**: The project specification requires data from UCF101, Kinetics, or DAVIS. The provided "Verified datasets" block **does not contain a verified URL** for any video dataset (UCF101, DAVIS, or Kinetics). It lists text datasets and a manifest for AnyFlow status.
- **Constraint**: Per the plan rules, we **cannot** invent a URL or assume a dataset exists if not verified.
- **Action**: The implementation script `download_curation.py` will attempt to load a verified video dataset via `datasets.load_dataset("kinetics-400")` (if available in the HF Hub with verified URL). **If no verified source is found during execution, the pipeline will halt with a "Data Availability Failure" error.**
- **Fallback**: If the primary verified dataset is unavailable, the system will attempt to load a hardcoded, small, verified subset of synthetic/known-cut clips (bundled in the repo under `data/raw/verified_small_set/`) **ONLY TO VALIDATE PIPELINE MECHANICS**. Statistical results from this fallback are labeled 'Pilot/Validation Only' and **CANNOT** be used for the primary hypothesis test.

## Dataset Strategy

**Primary Dataset (Target)**: Kinetics-400 (or verified subset)
- **Source**: Hugging Face Datasets (Requires verified URL).
- **Content**: Short video clips (approx. 2-3 mins) containing diverse actions.
- **Selection Strategy**:
 1. Download a large pool of clips.
 2. Run `PySceneDetect` (threshold=25.0) to identify candidate cuts **ONLY FOR EFFICIENT CANDIDATE DISCOVERY**.
 3. Stratified Sampling: Select a balanced set of clips with detected cuts and a balanced set of clips without (continuous).
 4. **Manual Verification**: A human expert verifies the stratification (FR-013) to ensure the "Cut" group actually contains cuts and the "Continuous" group does not. **The manual annotation is the EXCLUSIVE source of truth for the 'Cut' vs 'Continuous' label used in the final correlation.** PySceneDetect is not used to define the labels for the statistical test. The algorithmic labels are discarded for the final analysis to prevent confounding.

**Control Dataset**:
- A subset of 50 clips manually verified to be "known-smooth" and 50 "known-cut" (via physical frame swapping for synthetic cuts).

**Data Streaming**:
- To stay within 7GB RAM, the pipeline will stream clips using `datasets.load_dataset(..., streaming=True)` and process them in batches.

**IPW Prevalence Estimation**:
- The plan requires an estimate of $P(Cut)$ (natural prevalence) for Inverse-Probability Weighting (IPW).
- If external prevalence data is not present in the verified dataset metadata, the plan mandates a 'Prevalence Estimation Step': a random sample of 1000 clips from the *verified* dataset source (if available) will be processed to estimate $P(Cut)$ empirically before the stratified sampling begins.
- If the dataset cannot be sampled (e.g., streaming only), the plan will default to reporting 'Stratified Sample Statistics' only, explicitly noting that IPW cannot be applied and that results are conditional on the sample distribution.

## Methodology

### 1. Data Curation & Annotation (FR-001, FR-002, FR-010)
- **Download**: Retrieve clips from the verified source.
- **Pre-screening**: Use PySceneDetect to filter candidates (for efficiency only).
- **Annotation**:
 - **Rubric**: 5-point Likert scale (1=Continuous, 5=Cut).
 - **Blinding**: Annotators are blinded to the stratification label.
 - **Agreement**: Two independent annotators. If disagreement > 1 point, a third expert (ID from `experts.json`) adjudicates.
 - **Threshold**: Cohen's Kappa ≥ 0.81. If < 0.81, halt.
 - **Output**: `manual_continuity_scores.csv` (0.0 to 1.0, mapped from Likert).

### 2. CPU-Optimized Inference (FR-003, FR-004, FR-009)
- **Model**: AnyFlow (frozen weights).
- **Format**: ONNX Runtime (CPU).
- **Metric**: Flow-map divergence.
 - **Definition**: $D = \frac{1}{D_{lat}} \sum || \text{Model}(z_t) - \text{Euler}_{N}(z_t) ||^2$.
 - **Clarification**: The 'High-Resolution Euler Baseline' is a **numerical reference** for integration stability, NOT a semantic ground truth. The hypothesis is that numerical instability (divergence from Euler) spikes at frames identified as semantically discontinuous by human annotators.
 - **Baseline**: High-Resolution Euler (N=500) **FIXED FOR ALL PRIMARY ANALYSIS**. The baseline step count N is constant (500) for all clips in the primary hypothesis test. If runtime > 5.5h for N=500, the pilot phase halts the study rather than changing the baseline definition.
 - **Sensitivity Analysis**: A separate sweep (N=200, N=100) is performed to test robustness, but these results are reported separately and do not alter the primary metric definition.
- **Constraints**: Max 7GB RAM, ≤ 6 hours total.

### 3. Statistical Analysis (FR-005, FR-006, FR-011)
- **Correlation**:
 - **Primary**: **Spearman's Rho ($\rho$)** is the mandatory primary metric for the 5-point Likert data, as it is ordinal.
 - **Exploratory**: Pearson ($r$) is calculated only if the data is treated as continuous (justified by the 5-point scale being treated as interval for this specific analysis), with a strict note on the ordinal nature of the primary metric.
- **Bimodality Check**: Hartigan's Dip Test. If bimodal (0.0/1.0) and $N \ge 50$, use Logistic Regression.
- **Regression**: Multivariate Logistic Regression with IPW ($w = P(Cut) / P(Cut|Sample)$).
- **Sensitivity**: Sweep thresholds {0.01, 0.05, 0.1} and solver steps {500, 200, 100}.
- **Control**: Fisher's r-to-z transformation to compare correlation in "Cut" vs "Continuous" groups.
- **Power Analysis**: Justify $N=500$ for effect size $r=0.12$, power=80%.

### 4. Validation (FR-012)
- **Synthetic Subset**: Physically modify frames to create hard cuts.
- **Validation Logic**: The synthetic subset tests the model's *sensitivity* to discontinuities, not its *detection* accuracy. We expect high divergence for synthetic cuts if the model is numerically unstable at discontinuities. If the model is robust (low divergence), the metric correctly identifies stability, not failure to detect.
- **Verification**: Compare false-positive/negative rates against manual calculation ($< 0.01$ error).

### 5. Cut Window Aggregation (Scientific Soundness)
- **Cut Window Definition**: The 'Cut Window' is defined as a small window of frames centered on the manually annotated cut frame (or the single frame if the annotation is frame-precise). If the annotation is a range, the window is that range.
- **Aggregation Logic**: Compute divergence per frame; for the final clip score, take the MAXIMUM divergence value within the defined Cut Window. If no cut is annotated, take the MAXIMUM over the entire clip. This ensures the metric captures localized instability.

## Decision/Rationale

| Decision | Rationale |
|----------|-----------|
| **ONNX Runtime (CPU)** | Required by CI constraints (no GPU). ONNX is the only faithful CPU implementation for transformer-based diffusion. |
| **Stratified Sampling + IPW** | Natural video data has few cuts. Stratification ensures power; IPW corrects for the artificial balance to estimate true population metrics. |
| **Manual Annotation** | Automated metrics cannot distinguish "semantic discontinuity" from "motion". Human judgment is the only valid ground truth for this hypothesis. |
| **Sensitivity Sweep (N)** | Numerical error is confounded with model error. Sweeping N isolates the component of divergence due to solver discretization. |
| **Bimodal Handling** | Likert data often collapses to extremes. Hartigan's Dip Test ensures the correct statistical test (Logistic vs Correlation) is used. |
| **Spearman's Rho (Primary)** | The data is ordinal (5-point Likert). Spearman is the statistically correct metric for ordinal data. Pearson is exploratory only. |
| **Fixed Baseline (N=500)** | Changing the baseline definition mid-stream invalidates the metric. N=500 is fixed for the primary hypothesis; sensitivity sweeps are separate. |

## Risks & Mitigations

- **Risk**: No verified video dataset URL.
 - **Mitigation**: Pipeline halts with "Data Availability Failure" if no source is found. Research team must identify a verified source (e.g., Kinetics-400 on HF) and update the verified block. Fallback to pre-verified small subset for pipeline validation only.
- **Risk**: Runtime exceeds 6 hours.
 - **Mitigation**: Pilot phase (FR-009) checks N=500. If infeasible, the study halts (does not reduce N for the primary metric).
- **Risk**: Low inter-annotator agreement.
 - **Mitigation**: System halts if Kappa < 0.81. Re-training of annotators required.
- **Risk**: Memory overflow (>7GB).
 - **Mitigation**: Streaming dataset loading; batch processing of frames; clearing latent vectors after each clip.
- **Risk**: Missing Model Weights.
 - **Mitigation**: Pipeline halts with "Model Unavailable Failure" if the frozen AnyFlow weights or ONNX conversion source are not verified.

## References
- **AnyFlow**: ` (Manifest only; weights must be sourced from official repo).
- **Statistical Methods**: Standard texts on IPW, Fisher's r-to-z, and Hartigan's Dip Test.
- **Video Datasets**: *Note: No verified URL found for UCF101/DAVIS/Kinetics in input. Execution depends on external verification.*