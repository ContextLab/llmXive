# Research: Assessing the Impact of Sample Size on Meta-Analytic Reliability

## 1. Problem Statement & Methodology

### 1.1 Research Question
How does the number of component studies (`k`) in a meta-analysis affect the stability of the pooled effect size and the agreement rate of its confidence interval? Specifically, at what `k` does the stability curve exhibit "diminishing returns" (derivative < 0.05)?

### 1.2 Methodological Approach
The study employs a **simulation-based subsampling design** using real-world meta-analyses as the population (if available) or a parameterized simulation (if not).
1.  **Population**: 
    *   **Primary**: A corpus of ≥50 meta-analyses from public repositories.
    *   **Fallback**: A parameterized synthetic dataset mimicking real-world heterogeneity and bias distributions.
2.  **Intervention**: Systematic bootstrap subsampling of component studies at `k` ∈ {3, 4, ..., N}.
3.  **Outcome Measures**:
    *   **Stability**: Standard deviation (SD) of pooled effect sizes across 100 subsamples for a given `k`.
    *   **Reference Agreement Rate (RAR)**: Proportion of 95% CIs from subsamples that contain the full-sample (k=N) estimate. *Note: This measures concordance between subsamples and the aggregate reference, acknowledging the reference is a noisy estimator.*
    *   **True Coverage Rate** (Simulation Mode Only): Proportion of 95% CIs containing the known ground truth parameter used to generate the data. *This is the only metric that validates actual coverage probability.*
4.  **Analysis**: 
    *   **Primary Fit**: Parametric non-linear least squares fit to a `1/sqrt(k)` model (theoretical expectation for SE decay).
    *   **Secondary Fit**: Generalized Additive Model (GAM) to detect non-linearities not captured by the parametric form.
    *   **Threshold Detection**: Identify the `k` where the derivative of the stability curve drops below 0.05. The final threshold is selected based on the model with the lower AIC and significant improvement over a linear fit (p < 0.05).

### 1.3 Statistical Rigor & Assumptions
*   **Multiple Comparisons**: While we run multiple tests (one per meta-analysis), the primary outcome is the *aggregate* threshold distribution. We will report the median threshold and interquartile range rather than testing each meta-analysis individually for significance, avoiding family-wise error inflation.
*   **Power Justification**: With 50 meta-analyses (or simulation instances), we have sufficient power to estimate the median threshold with a margin of error of ~±1 study (assuming normal distribution of thresholds). If <50 instances are available, we will explicitly state the reduced precision.
*   **Causal Inference**: This is an **observational simulation**. We treat the full-sample estimate as the "reference truth" (acknowledging its uncertainty). Claims are framed as *associational* between `k` and stability, not causal effects of `k` on the "true" effect size.
*   **Measurement Validity**: 
    *   **Real Data**: Effect sizes and SEs are extracted directly from published meta-analyses. We assume the reported SEs are accurate.
    *   **Synthetic Data**: Parameters (heterogeneity, publication bias) are derived from cited meta-epidemiological literature (e.g., Ioannidis et al., 2008; Huedo-Medina et al., 2006) to ensure realism. The synthetic data generation process will be validated against these benchmarks.
*   **Collinearity**: `k` is the independent variable. Stability metrics are dependent. No collinearity issues exist between predictors as we model `k` vs stability directly.
*   **Estimator Continuity**: To address the potential artifact at the k=10 boundary (REML vs DL), a parallel analysis will use REML for all `k`. The threshold detected by both methods will be compared to ensure robustness.
*   **Reference Value Sensitivity**: To address the circularity of using the full-sample estimate as truth (FR-009), we will perturb the reference value by ± its standard error and re-calculate the Reference Agreement Rate. If the rate changes significantly, we will flag the result as sensitive to reference noise.

## 2. Dataset Strategy

### 2.1 Verified Datasets
*Note: The "Verified datasets" block provided in the prompt context contains URLs for gaming data (GAM, Steam, Chess), which are **irrelevant** to this meta-analysis study. The project spec explicitly requires **Cochrane/Campbell** meta-analyses. Since no verified URL for a Cochrane/Campbell meta-analysis corpus was provided in the prompt's "# Verified datasets" block, we must explicitly state the gap and define the strategy for acquisition.*

**Gap Statement**: The provided verified dataset list does not contain a source for Cochrane/Campbell meta-analyses. The spec requires machine-readable data (CSV/JSON) for ≥50 meta-analyses.

**Acquisition Strategy**:
1.  **Primary Source**: We will attempt to download a pre-curated dataset of Cochrane meta-analyses from a known repository (e.g., `osf.io` or a specific GitHub repository cited in meta-epidemiological literature) if a verified link can be found during the `research` phase.
2.  **Fallback (Simulation Mode)**: If no verified, machine-readable corpus of 50+ meta-analyses is found, the system will:
    *   Generate a **Parameterized Synthetic Dataset**.
    *   **Parameters**: Effect sizes drawn from a normal distribution with mean 0.2, heterogeneity (tau) drawn from an inverse-gamma distribution (parameters based on [Citation]), and a publication bias mechanism (selection model) applied to mimic real-world skew.
    *   **Validation**: The synthetic data generation process will be validated against the cited literature to ensure the "realism" of the distribution.
    *   **Labeling**: The output will be explicitly labeled as "Methodological Simulation" in all reports.

*Decision*: For the purpose of this plan, the project will default to **Simulation Mode** unless a verified URL is found during Phase 0. The research question is reframed as "Assessing the reliability of meta-analytic estimators under realistic simulation parameters."

### 2.2 Variable Mapping
| Variable | Source | Description |
|----------|--------|-------------|
| `study_id` | Raw Data | Unique identifier for the component study. |
| `effect_size` | Raw Data | Pooled effect (e.g., logOR, SMD) for the study. |
| `se_effect` | Raw Data | Standard error of the effect size. |
| `true_effect` | Simulation | The ground truth parameter used to generate the study (only in Simulation Mode). |
| `k` | Derived | Number of studies in the subsample. |
| `pooled_effect` | Model | Weighted mean of `effect_size` for the subsample. |
| `ci_lower`, `ci_upper` | Model | 95% CI bounds for the subsample. |
| `agreement_flag` | Metric | 1 if `pooled_effect` CI contains full-sample estimate, 0 otherwise. |
| `coverage_flag` | Metric | 1 if `pooled_effect` CI contains `true_effect` (Simulation Mode only). |

## 3. Computational Feasibility

### 3.1 Resource Constraints
*   **CPU**: 2 cores (GitHub Actions Free).
*   **RAM**: ~7 GB.
*   **Disk**: ~14 GB.
*   **Time**: ≤ 6 hours.

### 3.2 Optimization Strategy
*   **Vectorization**: All subsampling and model fitting will use `numpy`/`pandas` vectorization.
*   **Chunking**: Meta-analyses will be processed one-by-one (or in small batches of 5) to keep RAM usage low. Intermediate results (subsampled data) will be written to disk immediately and not held in memory.
*   **Model Selection**:
    *   **FE Model**: Closed-form solution (inverse-variance weighting) → O(1) per subsample.
    *   **RE Model**:
        *   `k < 10`: REML (iterative). We will limit iterations to a fixed maximum and use a tight tolerance to speed up convergence.
        *   `k ≥ 10`: DerSimonian-Laird (closed-form) → O(1) per subsample.
* **GAM Fitting**: We will fit the GAM on the **aggregated** stability metrics (one row per `k` per meta-analysis), not on every single subsample. This reduces the dataset size from [deferred] rows to [deferred] rows (50 MA × 50 `k` values), making `pygam` or `statsmodels` feasible on CPU.
*   **Parametric Fit**: A non-linear least squares fit (1/sqrt(k)) will be performed in parallel to the GAM to validate the threshold.
*   **Fallback**: If `pygam` fails to converge or is too slow, the plan switches to `statsmodels` GLM with splines or segmented regression (`segmented` package) as per FR-006.

## 4. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| **No verified dataset** | High (cannot run real analysis) | Switch to **Parameterized Simulation** mode; clearly label results as "Simulation". |
| **GAM convergence failure** | Medium (no threshold detected) | Fallback to segmented regression (FR-006) or rely on the Parametric Fit (1/sqrt(k)). |
| **Runtime > 6h** | High (CI failure) | Reduce bootstrap iterations from 100 to 50 for `k` > 15 (where stability is high); log the reduction. |
| **Zero-variance studies** | Medium (math error) | Add epsilon (1e-8) to SEs or exclude zero-variance studies (log exclusion). |
| **Estimator Boundary Artifact** | Medium (false threshold) | Run parallel REML-only analysis; compare thresholds. |

## 5. Success Metrics Alignment

*   **SC-001**: Track count of successfully processed meta-analyses (or simulation instances). Target: ≥50.
*   **SC-002**: Plot SD vs `k`. Expect negative exponential decay.
*   **SC-003**: Plot **Reference Agreement Rate** vs `k`. Expect convergence to a stable value. (In Simulation Mode, also plot **True Coverage Rate**).
*   **SC-004**: Monitor runtime; log if > 6h (fail).
*   **SC-005**: Count inflection points. Expect >0.
*   **SC-006**: Perturb reference value by ±SE; check stability of agreement rate.