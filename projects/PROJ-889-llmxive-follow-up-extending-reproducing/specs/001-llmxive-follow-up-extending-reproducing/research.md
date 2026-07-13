# Research: llmXive follow-up: extending "Reproducing, Analyzing, and Detecting Reward Hacking in Rubric-Based R"

## Problem Statement

The project investigates whether the statistical divergence between biased ($J_{\text{biased}}$) and unbiased ($J_{\text{unbiased}}$) LLM-as-a-Judge scores can serve as a reliable, generalizable indicator of reward hacking. The core hypothesis is that a significant spike in the divergence gap $G(t) = |J_{\text{biased}}(t) - J_{\text{unbiased}}(t)|$ precedes or coincides with a collapse in the independent gold-score ($J_{\text{gold}}$), which serves as the ground truth for "hacking" (operationally defined as a drop in $J_{\text{gold}}$).

**Important Caveat**: This analysis is inherently observational. The ground truth is defined by the *consequence* of hacking (a drop in $J_{\text{gold}}$), not by an independent causal mechanism. If the policy is optimizing for $J_{\text{biased}}$, a collapse in $J_{\text{gold}}$ is an expected outcome, not a causal proof of hacking. The detector will correlate divergence with gold drops, but this does not prove divergence *causes* or *predicts* hacking in the causal sense. See **Limitations & Circular Validation Risk** section below.

## Dataset Strategy

### Data Source: CHERRL Repository
The analysis relies on training logs from the CHERRL repository (arXiv:2606.04923). The logs must contain time-series data for $J_{\text{biased}}$, $J_{\text{unbiased}}$, and $J_{\text{gold}}$ across multiple random seeds and bias types (Lexical, Format, Tone, Self-praise).

- **Verified datasets**:
  - **CHERRL Logs**: The spec assumes the CHERRL repository provides downloadable pre-trained checkpoints and training logs.
  - *Note*: As per the "Verified datasets" block in the prompt, **NO verified source URL** was provided for the specific CHERRL log files. Therefore, the plan **must** reference the canonical CHERRL repository (arXiv paper) but cannot cite a specific direct download URL unless it is verified.
  - **Action**: The implementation will attempt to fetch data from a user-specified canonical source (e.g., CHERRL GitHub repository, Zenodo archive, or Hugging Face dataset). If the source is not provided or is unreachable, the system will halt with a clear error message per Constitution Principle I (Reproducibility).
  - **Constraint**: The plan **does not** invent a URL. If the CHERRL logs are not publicly available in a verified format at the time of implementation, the project will halt at the ingestion phase with a clear error message.

### Variable Fit Verification
Before analysis, the system must verify that the downloaded logs contain:
1.  `J_biased`: Biased reward scores.
2.  `J_unbiased`: Unbiased reward scores.
3.  `J_gold`: Independent gold reward scores.
4.  `seed_id`: Random seed identifier.
5.  `bias_type`: Rubric type (Lexical, Format, Tone, Self-praise, etc.).

If any of these variables are missing, the system must raise a `DataValidationError` and halt.

## Methodology

### Phase 1: Data Ingestion & Signal Computation (FR-001)
- **Input**: Raw CHERRL log files (CSV/JSON).
- **Process**:
  - Parse logs to extract time-series data.
  - Compute $G(t) = |J_{\text{biased}}(t) - J_{\text{unbiased}}(t)|$.
  - Compute $\Delta G(t) = G(t) - G(t-1)$.
  - Handle missing timesteps: skip or interpolate (method TBD based on data inspection).
  - Handle zero-variance: if $\sigma(G(t)) \approx 0$ over a window, set $z(G(t)) = 0$ or use epsilon floor.
- **Output**: Processed CSV with columns: `timestep`, `seed_id`, `bias_type`, `J_biased`, `J_unbiased`, `J_gold`, `G(t)`, `dG(t)`.
- **Validation**: Output validated against `contracts/trajectory_schema.schema.yaml` using `jsonschema`.

### Phase 2: Ground Truth Derivation & Extended Independence Check (FR-004, FR-006)
- **Extended Independence Check (FR-006)**:
  - Calculate Pearson correlation $r_1 = \text{corr}(J_{\text{unbiased}}, J_{\text{gold}})$ across the entire trajectory.
  - Calculate Pearson correlation $r_2 = \text{corr}(J_{\text{biased}}, J_{\text{gold}})$ across the entire trajectory.
  - **Gate**: If $r_1 > 0.8$ **OR** $r_2 > 0.8$, the dataset is invalid for this study (circular validation risk). The system halts and emits an error with the correlation values.
  - **Interpretation**: If $r_2$ is high, it suggests the biased model is partially aligned with the gold model, and divergence may be confounded with natural reward saturation rather than hacking. This is flagged as a limitation.
- **Ground Truth Labeling (FR-004)**:
  - Identify "hacking" events as drops in $J_{\text{gold}}$ of $\ge 0.1$ relative to the running mean of the preceding 50 timesteps.
  - The drop must be sustained for a minimum of several consecutive timesteps.
  - Labels are binary: `1` (hacked), `0` (not hacked).
  - **Limitation**: This definition assumes hacking always manifests as a sharp drop. Other hacking manifestations (plateaus, slow decay, or spikes in $J_{\text{biased}}$ while $J_{\text{gold}}$ is stable) are not captured. Results should be interpreted as "detection of sharp gold drops," not "detection of all hacking."
- **Output**: Processed CSV with columns: `timestep`, `seed_id`, `bias_type`, `gt_hacked`.

### Phase 3: Divergence-Based Detection with Sensitivity Analysis (FR-002, FR-003)

#### Base Detection Logic
- **Sliding Window Z-Score**:
  - Window size $W$ (default determined via sensitivity analysis).
  - A minimum sample size sufficient to estimate standard deviation will be determined based on power analysis and methodological requirements.
  - Handle zero variance: If $\sigma(G(t)) \approx 0$, set $z(G(t)) = 0$.
  - Normality check: Perform Kolmogorov-Smirnov test on $G(t)$ per rubric type. If non-normal (p < 0.05), use non-parametric alternative.
- **Thresholding**:
  - Flag "hacked" if $z(G(t)) > \tau$ (default 3.0, tuned via sensitivity analysis).
  - **OR** if $\Delta G(t) > 2.5 \times \sigma_{\text{baseline}}$ (where $\sigma_{\text{baseline}}$ is the SD of $\Delta G$ in the first 100 timesteps).

#### Sensitivity Analysis & Threshold Tuning
- **Grid Search**: Evaluate combinations of:
  - Window sizes: $W \in \{10, 20, 30\}$
  - Z-score thresholds: $\tau \in \{2.0, 2.5, 3.0, 3.5\}$
  - $\Delta G$ multiplier: $k \in \{2.0, 2.5, 3.0\}$
- **Procedure**:
  1. Hold out a subset of seeds for validation; use the remaining seeds for grid search.
  2. For each hyperparameter combination, compute F1-score on the 3 training seeds.
  3. Select the combination with the highest mean F1-score.
  4. Validate on the 2 held-out seeds.
  5. Report F1-scores and the selected hyperparameters.
- **Non-Parametric Fallback**: If KS test indicates non-normal $G(t)$ (p < 0.05), use Interquartile Range (IQR) based outlier detection instead: flag timesteps where $G(t) > Q3 + 1.5 \times IQR$ or $G(t) < Q1 - 1.5 \times IQR$.
- **Output**: Processed CSV with columns: `timestep`, `seed_id`, `bias_type`, `G(t)`, `dG(t)`, `z_score`, `hacked_label`, plus metadata columns recording the selected hyperparameters and normality test results.
- **Validation**: Output validated against `contracts/trajectory_schema.schema.yaml`.

### Phase 4: Evaluation & Generalization (FR-005, SC-001, SC-002, SC-003)

#### Metrics Computation
- **Per-Rubric Metrics**: Precision, Recall, F1-score for each bias type (Lexical, Format, Tone, Self-praise).
- **Aggregation**: Macro-average F1-score (equal weighting per seed, then per rubric type).

#### Baseline Comparison
- **Baseline 1: Random Guess**
  - Flag each timestep with probability equal to the empirical hacking rate (proportion of ground-truth hacked timesteps).
  - Neutral control; no time bias.
- **Baseline 2: Mean-Divergence Threshold**
  - Flag timesteps where $G(t) > \text{mean}(G) + 1 \times \sigma(G)$.
  - Simple statistical baseline; no learnable parameters.
- **Proposed Detector**: Divergence-based detector with tuned hyperparameters (from Phase 3 sensitivity analysis).

#### Statistical Testing
- **Primary Test**: Wilcoxon Signed-Rank Test (non-parametric)
  - Paired comparison of F1-scores: Proposed Detector vs. Random Guess baseline.
  - Paired comparison of F1-scores: Proposed Detector vs. Mean-Divergence baseline.
  - Justification: N=5 seeds; Wilcoxon is robust to non-normality and small sample sizes.
  - Report: p-value, rank-biserial correlation (effect size).
- **Sensitivity Check**: Paired t-test (parametric)
  - Run Shapiro-Wilk test on F1-score differences to assess normality.
  - If p > 0.05 (normal), report t-test as secondary confirmation.
  - If p < 0.05 (non-normal), note that Wilcoxon is the primary inference.
- **Effect Size**: Report Cohen's d (standardized mean difference) alongside p-values.

#### Generalization Assessment
- **Variance Across Rubric Types**: Calculate the standard deviation of F-scores across the multiple rubric types (Lexical, Format, Tone, Self-praise).
- **Success Criterion (SC-003)**: If $\sigma(F1) \le 0.15$, a universal threshold is viable.
- **Failure & Rubric-Specific Tuning**: If $\sigma(F1) > 0.15$, the system triggers Phase 4b (rubric-specific tuning):
  - For each rubric type, perform a separate grid search (same hyperparameter ranges as Phase 3) on a dedicated subset of seeds.
  - Validate rubric-specific thresholds on held-out seeds.
  - Report F1-scores per rubric with rubric-specific thresholds.
  - Explicitly state in the final report: "Universal threshold was not viable; rubric-specific tuning was applied."

#### Multiple Comparisons Correction
- When testing across 4 rubric types, apply Benjamini-Hochberg correction to control the False Discovery Rate (FDR) at α = 0.05.
- Report both raw and corrected p-values.

#### Output
- Processed CSV with columns: `bias_type`, `precision`, `recall`, `f1_score`, `t_statistic`, `p_value`, `effect_size`, `method` (e.g., "Wilcoxon", "t-test").
- Validation: Output validated against `contracts/metrics_schema.schema.yaml`.

## Limitations & Circular Validation Risk

### Operational vs. Causal Definition of Hacking
The ground truth is **operationally defined** as a drop in $J_{\text{gold}}$. However, this is not a causal proof of hacking:
- If the policy is optimizing for $J_{\text{biased}}$, a collapse in $J_{\text{gold}}$ is an *expected outcome*, not a causal consequence of divergence.
- The detector will correlate divergence with gold drops, but this does not prove divergence *predicts* hacking in an independent sense.
- This analysis is purely **correlational**: "divergence correlates with gold drops" ≠ "divergence predicts hacking."

### Mitigation & Recommendations
- **Interpretation**: Results should be framed as "the divergence signal correlates with sharp drops in the gold score" rather than "the divergence signal detects hacking."
- **Independent Ground Truth**: If available, collect independent ground truth via:
  - Human review of trajectories to identify hacking events (beyond sharp drops).
  - A separate policy trained without the bias, compared to the biased policy.
  - Synthetic hacking (intentionally inject bias and measure divergence).
- **Sensitivity to Ground Truth Definition**: Evaluate the detector's robustness to alternative definitions of hacking (e.g., plateau detection, slow decay, or a broader threshold).

## Decision Rationale & Constraints

- **CPU-Only Feasibility**: All operations (pandas, numpy, scipy) are CPU-tractable. No GPU or deep learning models are used, ensuring execution on GitHub Actions free-tier (multiple CPU cores, substantial RAM).
- **Dataset Limitations**: If the CHERRL repository does not provide the required $J_{\text{gold}}$ column or the logs are incomplete, the project cannot proceed. This is a hard dependency flagged for user clarification.
- **Hyperparameter Selection**: Initial defaults ($\tau=3.0$, $W=20$) are standard for outlier detection, but sensitivity analysis ensures data-driven tuning.
- **Statistical Power**: With N=5 seeds, power is limited for small effect sizes. Wilcoxon test and effect size reporting mitigate this. Results are framed as preliminary.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Missing $J_{\text{gold}}$ data | Fatal: Cannot derive ground truth. | Halt with clear error; request data clarification. |
| High correlation ($r > 0.8$) between $J_{\text{unbiased}}$ or $J_{\text{biased}}$ and $J_{\text{gold}}$ | Fatal: Circular validation. | Extended check on both; halt and report invalid dataset. |
| Zero variance in $G(t)$ | Runtime error in z-score. | Implement epsilon floor or set $z=0$. |
| Non-normal $G(t)$ distribution | Z-score thresholding may be invalid. | KS test per rubric; fallback to IQR-based detection. |
| Small sample size ($N=5$ seeds) | Low statistical power. | Use Wilcoxon (non-parametric); report effect sizes; frame as preliminary. |
| Runtime > 4 hours | CI failure. | Process seeds sequentially; optimize data loading. |
| Universal threshold fails (SC-003 fails) | Generalization claim invalid. | Trigger rubric-specific tuning; explicitly report method in final output. |
