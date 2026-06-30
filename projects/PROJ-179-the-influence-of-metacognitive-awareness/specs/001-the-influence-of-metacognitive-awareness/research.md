# Research: The Influence of Metacognitive Awareness on Reality Testing

## Dataset Strategy

| Dataset | Purpose | Source URL | Availability Notes |
|---------|---------|------------|-------------------|
| OpenNeuro ds003386 | Primary data source for source-monitoring trials, confidence ratings, and participant demographics | NO verified source found (do NOT cite a URL for it). | **UNAVAILABLE FOR THIS FEATURE**. ds003386 is a structural MRI dataset. It does **not** contain trial-wise behavioral data (confidence ratings, source labels) required for the analysis. The pipeline will fail validation. **No alternative dataset is available in the verified list.** |

> **Critical Note**: As per the spec, OpenNeuro ds003386 does **not** contain the Metacognitive Awareness Questionnaire (MAQ) or the required behavioral trial data. The analysis is **blocked** until a valid dataset containing trial-wise confidence and source labels is identified.

## Variable Mapping

| Spec Variable | Dataset Field | Transformation | Notes |
|---------------|---------------|----------------|-------|
| Metacognitive Score | `confidence_rating` (trial-level) | Calculate Type-2 AUC (meta-d' sensitivity) on [deferred] training split | **Hypothetical**: Requires data that is missing. |
| Source-Monitoring Accuracy | `source_label` (true), `participant_response` (observed) | Calculate d' on [deferred] held-out test split | **Hypothetical**: Requires data that is missing. |
| d' (d-prime) | `source_label`, `participant_response` | Signal detection theory formula | Calculated on held-out set. |
| Criterion | `source_label`, `participant_response` | Signal detection theory formula | Calculated on held-out set. |
| Age | `age` (participant metadata) | Direct | Hypothetical. |
| Gender | `gender` (participant metadata) | One-hot encoded | Hypothetical. |
| Working Memory | `working_memory_span` (if available) | Direct | Hypothetical. |

## Methodological Decisions

### 1. Hold-Out Accuracy Design (Replaces K-fold CV & Split-Half)
- **Decision**: 90/10 Train/Test Split per participant.
- **Rationale**: To avoid circularity when correlating metacognitive sensitivity (Type-2 AUC) with accuracy (d'), the predictor and outcome must be derived from disjoint trial sets.
 - **Predictor (Type-2 AUC)**: Calculated on [deferred] of trials (Training Set).
 - **Outcome (d')**: Calculated on [deferred] of trials (Test Set).
- **Implementation**: For each participant, randomly split trials into [deferred] training and [deferred] test. Compute Type-2 AUC on training. Compute d' on test. Correlate these two independent estimates across participants.
- **Note**: This design is statistically valid for the hypothesis but requires the dataset to contain the necessary trial-wise data, which ds003386 does not.

### 2. Metacognitive Score Definition
- **Decision**: Use Type-2 AUC (Area Under the Type-2 ROC Curve), not mean confidence.
- **Rationale**: Mean confidence measures response bias, not metacognitive *sensitivity* (awareness). Type-2 AUC measures how well confidence ratings discriminate between correct and incorrect trials, which is the standard operationalization of "metacognitive awareness" in signal detection theory.
- **Citation**: Maniscalco, B., & Lau, H. (2012). A signal detection theoretic approach for estimating metacognitive sensitivity. *Consciousness and Cognition*. **Status**: To be verified by Reference-Validator Agent.

### 3. Hierarchical Regression (FR-005)
- **Step 1**: Age, Gender (one-hot), Working Memory (if available).
- **Step 2**: Add Metacognitive Score (Type-2 AUC).
- **Output**: ΔR², F-change, coefficients (β, SE, t, p).
- **Fallback**: If working memory data is missing, exclude it and report n-1 model with adjusted R².

### 4. Multiple-Comparison Correction (FR-006)
- **Method**: Benjamini-Hochberg (BH) procedure.
- **Rationale**: More powerful than Bonferroni for exploratory analyses; controls false discovery rate (FDR).
- **Application**: Applied to p-values from modality-specific correlations (visual, auditory) and regression coefficients.

### 5. Bootstrap Confidence Intervals (FR-004)
- **Resamples**: 1,000.
- **Fallback**: If runtime exceeds a significant duration, reduce to 500.
- **Method**: Percentile bootstrap for correlation coefficient (r) and ΔR².

### 6. Assumption Checks (FR-008, FR-009)
- **Normality**: Shapiro-Wilk test on residuals.
- **Homoscedasticity**: Breusch-Pagan test.
- **Collinearity**: VIF ≥ 5 threshold; if violated, report descriptive relationship and flag collinearity.

## Power and Sample Size Considerations

- **Target Sample**: n = 120 participants (per SC-005).
- **Power Analysis**: To detect r ≈ 0.30 at α = 0.05 with 80% power, n ≈ 85 is required.
- **Attenuation Correction**: Type-2 AUC is a noisier metric than mean accuracy. The effective reliability of the predictor is lower, which attenuates the observed correlation. The sample size of 120 is calculated to account for this attenuation. If the effective n drops below 85, the study will be underpowered for detecting small effects. This limitation will be explicitly reported.
- **Data Constraint**: The current dataset (ds003386) does not provide the required data, so the power analysis is hypothetical.

## Causal Inference Statement

- **Verdict**: Observational study; **no causal claims**.
- **Rationale**: No randomization of metacognitive awareness; all findings are associational. The analysis will frame results as "metacognitive awareness is associated with..." rather than "causes...".

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| **Dataset Unavailable** | Pipeline performs strict validation; fails with clear error if required fields are missing. No fallback dataset. |
| **Working memory data missing** | FR-005 fallback: exclude covariate; report adjusted model. |
| **Runtime > 6 hours** | Reduce bootstrap resamples to 500; log warning. |
| **Non-normal residuals** | Use bootstrap CIs; report assumption violation. |
| **Collinearity (VIF ≥ 5)** | Flag in report; describe relationship descriptively. |
| **Data Validation Failure** | **Primary Risk**: The pipeline will halt immediately if ds003386 lacks the required fields. |