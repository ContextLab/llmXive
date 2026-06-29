# Research: Investigating the Relationship Between Brain Network Dynamics and Response to Cognitive Training (Pivoted: Baseline Association)

## 1. Problem Definition & Hypothesis (Pivoted)

**Original Hypothesis**: Individual differences in baseline resting-state functional connectivity (RSFC) predict working memory (WM) *improvements* following cognitive training.  
**Pivoted Hypothesis**: Individual differences in baseline resting-state functional connectivity (RSFC), specifically the strength of the frontoparietal network (FPN) and default mode network (DMN), are **associated with baseline working memory capacity**.

**Rationale for Pivot**: The dataset `ds000277` (HCP-1200) is a cross-sectional dataset. It contains resting-state fMRI and baseline behavioral tasks but **does not contain** a longitudinal cognitive training intervention with pre/post scores. Therefore, the outcome variable "WM Gain" (Post - Pre) does not exist. The hypothesis has been pivoted to test for cross-sectional associations between baseline connectivity and baseline cognition.

**Key Variables**:
- **Predictors**: Global Efficiency, Modularity (Q), FPN Strength, DMN Strength.
- **Outcome**: Baseline WM Score (not Gain).
- **Covariates**: Age, Sex.

## 2. Dataset Strategy

### Verified Datasets
Per the project's verified dataset block, the following sources are available. **CRITICAL NOTE**: The spec explicitly assumes `ds000277` contains training data. The verified dataset block provided in the prompt **does NOT list a verified source for `ds000277`** (it states "NO verified source found").

**Action**: The plan proceeds with `ds000277` as the only available source matching the rs-fMRI requirement, but explicitly acknowledges the lack of training variables. The pipeline will attempt to fetch from OpenNeuro, but the *verification* step will flag this as "Unverified Source" if the checksum is not pre-registered. If the URL is unreachable or checksums fail, the pipeline halts with a clear error.

**Dataset Selection**:
- **Name**: OpenNeuro ds000277 (HCP-1200).
- **Source**: OpenNeuro (https://openneuro.org/datasets/ds000277). *Note: This URL is not in the "Verified datasets" block. The implementation will attempt to download via `openneuro-ds` or `curl`. If unreachable, the pipeline halts.*
- **Content Verification**:
  - **rs-fMRI**: Present (Required).
  - **Behavioral**: Present (Baseline WM, Age, Sex).
  - **Training**: **Absent**. The dataset does not contain `wm_pre` and `wm_post` columns for a training intervention.

**Variable Fit Check**:
- **Required**: rs-fMRI NIfTI, Baseline WM score, Age, Sex.
- **Mismatch**: The dataset lacks the "training response" variable.
- **Mitigation**: The pipeline will pivot to the baseline association hypothesis. If the dataset lacks the required baseline WM score, the pipeline will halt with a `FatalError: Missing required baseline behavioral variables`.

**Contingency Plan**:
- If training data is missing (confirmed), the study is limited to cross-sectional association.
- If baseline WM score is also missing, the pipeline will halt with a `FatalError`.
- No alternative verified dataset with a cognitive training intervention exists in the verified list.

### Data Access Strategy
- **Protocol**: HTTP/HTTPS.
- **Method**: Use `requests` to fetch files from OpenNeuro's CDN.
- **Checksum**: Verify MD5/SHA256 if available.

## 3. Statistical & Methodological Rigor

### Model Specification
- **Model**: Multiple Linear Regression (OLS).
- **Formula**: `Baseline_WM ~ FPN_Strength + DMN_Strength + Global_Eff + Modularity + Age + Sex`.
- **Collinearity Check**: FPN and DMN strengths are derived from the same matrix. VIF will be calculated. If VIF > 5, report descriptive correlations only.

### Statistical Significance & Correction
- **Permutation Testing**: 1,000 iterations to generate a null distribution for coefficients.
- **Correction**: Holm-Bonferroni applied across the 4 primary predictors.
- **Power Analysis**:
 - **Target**: N ≥ 30 for minimum viability; N ≥ 85 for [deferred] power at r=0.30.
  - **Method**: `statsmodels.stats.power.tt_solve_power` for *a priori* calculation (N=85) and *achieved* power (actual N).

### Multiple Comparison & Error Control
- **Family-wise**: 4 predictors. Holm-Bonferroni applied.
- **Alpha**: 0.05 (two-tailed).

## 4. Compute Feasibility (CPU-Only Constraint)

- **Environment**: GitHub Actions Free Tier (2 CPU, 7GB RAM).
- **fMRIPrep**: Heavy.
  - **Strategy**: Run full N=85. If >5.5h, downsample to N=30.
- **Network Metrics**: `bctpy` and `networkx` are CPU-optimized.
- **Regression**: `scikit-learn` OLS and permutation are trivial for N=85.

## 5. Decision Log

| Decision | Rationale | Alternative Rejected |
|----------|-----------|----------------------|
| Pivot to Baseline Association | Dataset lacks training data. | Using a different dataset (no verified source available). |
| Motion Threshold 0.3mm | Scientific standard; 3.0mm is invalid. | 3.0mm (would include motion artifacts). |
| Use fMRIPrep 23.1.3 | Mandated by Constitution Principle VI. | Custom preprocessing (violates reproducibility). |
| Permutation Test (1000 iter) | Robust for small N. | Asymptotic p-values. |
| N=30 fallback | Ensures CI completion within 6h. | Running full N=85 (risk of timeout). |
| No GPU | CI environment is CPU-only. | GPU-accelerated libraries. |

## 6. Scientific Validity & Causal Claims

- **Original Claim**: Baseline connectivity *predicts* training response.
- **Revised Claim**: Baseline connectivity is *associated with* baseline working memory capacity.
- **Justification**: The dataset ds000277 is cross-sectional. It contains no longitudinal training data. Therefore, the study cannot test for prediction of change. The analysis is strictly correlational.
- **Limitation**: Results cannot be interpreted as causal or predictive of training outcomes.
