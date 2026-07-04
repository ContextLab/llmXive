# Research: Influence of Microstructural Features on Fatigue Life in Aluminum Alloys

## 1. Dataset Strategy

The project requires a dataset containing:
- **Outcome**: Fatigue life cycles (N_f).
- **Predictors**: Grain size (μm), Secondary phase distribution (fraction/area%), Dislocation density (or proxy).
- **Metadata**: Alloy composition, heat treatment/batch ID (for grouped CV).

### Verified Datasets Analysis

Based on the provided verified dataset list, the following sources were examined:
- **NIST (jsonl)**: `
- **HuggingFace (parquet)**: `
- **HuggingFace (parquet)**: `

**Critical Gap Analysis**:
The verified datasets listed above are **NOT** suitable for this project.
- `opusdiseaseconversations.jsonl` contains medical doctor-patient conversations.
- The `shqiponja` and `bigdoc` parquet files contain LLM evaluation metrics (ARC challenge, harness details), not materials science data.
- **None** of these sources contain aluminum alloy fatigue data, microstructural features, or microscopy images.

**Decision**:
The project **cannot proceed** with the currently verified dataset URLs. The spec assumes the existence of "publicly available aluminum alloy fatigue datasets" (FR-001), but the verified list provided for this execution context contains no such data.

**Action Required**:
1. **Stop**: The implementation plan cannot fetch data from the provided URLs as they do not match the domain.
2. **Alternative**: The project will use a **Synthetic Dataset** generation script to demonstrate the pipeline logic, explicitly noting the synthetic nature in this document and all outputs.
3. **Future Path**: A "Real Data Acquisition Path" is defined below for when verified domain data becomes available.

### Scope Limitation

**This project is currently a Pipeline Validation and Methodological Demonstration.**
- **Synthetic Data**: The dataset is generated using `numpy` and `pandas` with assumed relationships.
- **Limitation**: Results (R², p-values, feature importance) are mathematical artifacts of the generator, not empirical findings about aluminum alloys.
- **Goal**: The goal is to validate the *code logic* (data cleaning, image processing, model training, statistical testing) and *resource constraints* (RAM, CPU time), not to discover physical laws.

### Dataset Strategy Table (Synthetic)

| Source | Type | Variables Present | Status | Action |
|:--- |:--- |:--- |:--- |:--- |
| NIST (Verified URL) | Medical Conversations | N/A | **Mismatch** | Skip |
| HF (Verified URL) | LLM Eval Metrics | N/A | **Mismatch** | Skip |
| **Synthetic Generator** | Simulated | All Required | **Selected** | **Generate** |

### Real Data Acquisition Path (Future)

If a verified domain dataset becomes available, the following criteria must be met:
1. **Source**: Must be from a verified URL (e.g., NIST Materials Data Repository, specific HuggingFace materials science datasets).
2. **Variables**: Must contain `grain_size`, `secondary_phase_fraction`, `fatigue_life_cycles`, and ideally `microscopy_image_path`.
3. **Dislocation Density**: If not present, a proxy (e.g., texture analysis) must be justifiable with literature, or the feature must be excluded.
4. **Images**: If image processing is required, the dataset must contain 512×512 (or rescalable) microscopy images with ground truth labels.

## 2. Feature Engineering & Methodology

### Microstructural Features (Synthetic)
- **Grain Size**: Simulated as log-normal distribution (typical for metals).
- **Secondary Phase**: Simulated as uniform distribution [0, 1] (fraction).
- **Dislocation Density Proxy**: Simulated as a **non-linear function** of grain size and secondary phase (to avoid simple linear collinearity), plus noise. Explicitly labeled as `dislocation_proxy` (FR-013).
 - *Construct Validity Limitation*: This proxy is an approximation. In real materials, dislocation density and grain size have complex, non-linear, and often competing relationships. The synthetic generator mimics this complexity but cannot replicate true physical mechanisms.
- **Fatigue Life**: Simulated as `10^(a + b*log(grain) + c*phase + d*proxy + interaction_terms)`.

### Image Processing (FR-004, FR-005)
- Since real microscopy images are unavailable in the verified list, the pipeline will:
 1. Generate synthetic 512×512 grayscale "images" using Voronoi tessellation (via `scikit-image`) to simulate grain boundaries.
 2. Apply OpenCV thresholding and contour detection to extract "grain size" and "texture metrics".
 3. Log a fallback event if real images are missing (FR-004b), but proceed with synthetic generation for demonstration.
 - *Ground Truth Limitation*: Texture metrics extracted from synthetic Voronoi patterns cannot be validated against real dislocation density (which requires TEM/XRD). This is a known limitation of the synthetic approach.

### Statistical Rigor
- **Multiple Comparison**: Bonferroni correction applied to ANOVA p-values (FR-012).
- **Causal Framing**: All results framed as associational (FR-011) and explicitly as "parameter recovery" from synthetic data.
- **Collinearity**: VIF (Variance Inflation Factor) calculated; if high, joint effects described rather than independent coefficients. **Collinearity Limitation**: The synthetic proxy may still exhibit correlation with grain size, which will be reported.
- **Sample Size**: N=150 chosen for **pipeline robustness** (testing memory constraints and stability), not statistical power. Power analysis is not applicable to synthetic data where effect sizes are defined by the generator.

### Tautology Avoidance
- **Goal**: The analysis will not claim to "discover" that grain size affects fatigue life (since this is true by definition in the generator).
- **Metric**: Success is defined as the model's ability to **recover the known generator coefficients** (within a tolerance) and correctly identify the significance of features as defined by the generator.

## 3. Model Strategy

- **Algorithms**: Random Forest, Gradient Boosting, ElasticNet (FR-006).
- **Constraints**: ≤100 trees/estimators. CPU-only.
- **Validation**: 5-fold Grouped CV (stratified by synthetic `batch_id`).
- **Metrics**: R², RMSE, MAE with Confidence intervals via 1000-resample bootstrapping (FR-009).
- **Sensitivity**: Compare performance with/without `dislocation_proxy` (FR-014).
- **Parameter Recovery**: The model's ability to approximate the generator's coefficients will be evaluated.

## 4. Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **No Verified Domain Data** | Critical | Use synthetic data for pipeline validation; document clearly as "Synthetic-Only". |
| **RAM Exceedance** | High | Limit N to 150; use `float32`; batch processing if needed. |
| **Image Processing Failure** | Medium | Fallback to tabular-only mode; log exclusion. |
| **Low R² (<0.7)** | Medium | Report actual performance; analyze feature importance; adjust thresholds in sensitivity analysis. |
| **Scientific Validity** | High | Explicitly state that results are not empirical findings; focus on pipeline validation. |

## 5. Citation Mismatch Log

| Cited Source | Status | Reason |
|:--- |:--- |:--- |
| NIST (Verified URL) | Mismatch | Contains medical data, not materials science. |
| HF (Verified URL) | Mismatch | Contains LLM evaluation data, not materials science. |
| **Synthetic Generator** | **N/A** | **Used as fallback due to mismatch.** |