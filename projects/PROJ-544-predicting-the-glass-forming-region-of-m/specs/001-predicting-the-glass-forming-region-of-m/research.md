# Research: Predicting the Glass Forming Region of Multi-Component Alloys via Machine Learning

## Summary

This research document identifies datasets, validates methodological approaches, and documents constraints for the glass-forming region prediction pipeline. Key findings include: (1) no verified materials science alloy datasets exist in the current verified datasets block; (2) compositional descriptors are statistically correlational, not causally determinative; (3) CPU‑tractable methods (scikit‑learn Random Forest/Gradient Boosting) are appropriate for the compute constraints; (4) fundamental limitations exist due to missing cooling-rate data and Materials Project label mismatch.

## Dataset Strategy

| Dataset Name | Required Variables | Verified URL | Status |
|--------------|-------------------|--------------|--------|
| Materials Project Alloy Compositions | Elemental stoichiometries, phase labels (glass‑forming/crystalline), thermodynamic properties | NO verified source found | GAP: Spec assumes availability but URL not in verified block; Materials Project primarily contains DFT-calculated crystal structures, not experimental glass-forming labels |
| NIST Alloy Database | Elemental stoichiometries, phase labels, processing parameters | NO verified source found | GAP: Spec assumes availability but URL not in verified block |
| DScribe Benchmark Data | Atomic radii, electronegativity, mixing enthalpy parameters | NO verified source found | GAP: Required for SC‑002 validation |

**Dataset Gap Resolution**: The spec states "The Materials Project and NIST Alloy Database contain phase labels for at least 1000 multi‑component metallic compositions" as an assumption. However, neither database appears in the verified datasets block provided. Implementation will:

1. Use placeholder synthetic alloy compositions for CI testing (documented as synthetic).
2. Add download scripts to `code/scripts/` that will fetch real data once verified sources are identified.
3. Document the gap explicitly in the paper as a limitation on causal inference.
4. **Critical Note**: Materials Project primarily contains DFT-calculated ground-state crystal structures, not experimental glass-forming propensity labels. Glass formation is kinetically controlled and may not be represented in thermodynamic databases. This fundamental mismatch between validation target (phase labels) and research question (glass-forming propensity) is documented as a limitation.

**Fallback Strategy**: If no verified alloy dataset is available by implementation time, the pipeline will generate synthetic data matching the expected schema (≥ 3 elements, phase label, computed descriptors) for testing purposes only. Results will be clearly marked as "synthetic validation" in all outputs.

## Methodological Approach

### Descriptor Computation (FR‑001, FR‑002, SC‑002)

**Method**: Atomic size mismatch (δ), mixing enthalpy (ΔH_mix), and electronegativity variance (Δχ) computed from elemental properties using DScribe library.

**Formulas**:
- Atomic size mismatch: δ = √[Σ c_i (1 - r_i / r̄)²] where c_i is atomic fraction, r_i is atomic radius, r̄ is weighted mean radius
- Mixing enthalpy: ΔH_mix = Σ Σ 4 Ω_ij c_i c_j where Ω_ij is interaction parameter
- Electronegativity variance: Δχ = √[Σ c_i (χ_i - χ̄)²] where χ_i is electronegativity

**Validation**: Computed values compared against DScribe benchmark alloys (e.g., Cu₅₀Zr₅₀) with tolerance ±0.02 (US‑1, SC‑002). Validation is performed in Phase 1 and logged.

**Collinearity Note**: Mixing enthalpy components may be definitionally related; VIF diagnostics (Phase 3) will quantify redundancy. If all three descriptors exceed VIF > 5, a PCA fallback (2 components) will be applied (see Phase 3).

**Shared Input Data Note**: The three descriptors (δ, ΔH_mix, Δχ) are all computed from the same elemental property tables. While they measure different physical quantities, they share common input data sources. The validation target independence cannot be guaranteed; VIF diagnostics address collinearity but target independence remains a potential limitation.

### Power Analysis & Sample‑Size Justification (Methodology‑56e2afaf)

Using a two‑tailed α = 0.05, power = 0.80, and a medium effect size (Cohen's d = 0.5) for binary classification, the required sample size per class is ≈ 64 (total ≈ 128). This calculation follows standard power‑analysis formulas for ROC‑AUC comparisons. If the available minority class < 100 samples, we will prioritize precision‑recall metrics (as per spec) and note the reduced power in the manuscript.

### Class Imbalance Handling (FR‑006, Methodology‑96335b5f)

- **Detection**: Ratio > 3:1 triggers a flag.
- **Alternative Paths**:
  1. Apply `class_weight='balanced'` in Random Forest / Gradient Boosting.
  2. Use SMOTE oversampling via `imbalanced-learn`.
  3. Switch to a one‑class anomaly‑detection model (Isolation Forest) and report anomaly scores.
- The chosen strategy is logged; if none improve performance, the dataset is flagged as unsuitable for binary classification and the analysis is reported as exploratory. The 3:1 threshold is a soft flag, not a hard stop.

### Missing Cooling‑Rate Data (Methodology‑e7ee9237)

Cooling rate and thermal‑history data are not present in the Materials Project or NIST databases. To mitigate this confound:

- **Stratification**: Analyses stratified by alloy system type (transition‑metal vs. rare‑earth) and report system‑specific performance.
- **Sensitivity analysis**: Discussion section includes sensitivity analysis on how plausible cooling‑rate variations could shift the decision boundary, acknowledging the limitation.
- **Explicit Statement**: The model predicts compositional correlates of glass formation rather than the actual phenomenon; discussion emphasizes this interpretability limitation.

### Model Training (FR‑003)

**Algorithm**: Random Forest and Gradient Boosting classifiers via scikit‑learn.

**Hyperparameters**:
- Random Forest: `n_estimators=100`, `max_depth=None`, `min_samples_split=2`, `random_state=42`
- Gradient Boosting: `n_estimators=100`, `learning_rate=0.1`, `max_depth=3`, `random_state=42`

**Validation**: 5‑fold cross‑validation; metrics reported with standard deviation across folds.

**Compute Constraint**: Training designed for ≤ 6 hours on 2‑core CPU (SC‑004); dataset sampled to ≤ 7 GB RAM (FR‑007, SC‑005).

### Model Evaluation (FR‑004, SC‑001)

**Metrics**: ROC‑AUC, precision, recall on held‑out test set; standard deviation across folds recorded. If minority class < 100, precision‑recall curves will be emphasized.

### Feature Importance & Interpretation (FR‑005, SC‑003)

**Methods**:
1. Permutation importance (numeric scores, ranked highest to lowest).
2. SHAP summary plots (PNG files, descriptor values on x‑axis, impact on y‑axis).
3. Sensitivity analysis of δ threshold variations {0.01, 0.05, 0.1} to assess robustness of ROC‑AUC and precision‑recall (Phase 7).

**Multiple‑Comparison Correction**: Bonferroni correction (α/3) applied when testing significance of the three descriptor importance scores.

**Reproducibility**: Several independent training runs; feature‑importance rankings compared for consistency (SC protocol). Results aggregated in `results/reproducibility_summary.json`.

### Causal Inference Limitation (Reviewer Feedback)

Per reviewer rosalind‑franklin‑simulated: "The model assumes atomic size mismatch and mixing enthalpy are the primary drivers of the glass‑forming region. This is a statistical correlation, not a structural determination… cooling rate and thermal history must be measured."  

**Resolution**: The analysis is explicitly framed as **ASSOCIATIONAL** only; no causal claims about descriptor → glass formation are made. The missing cooling‑rate variables are acknowledged as a fundamental limitation, and the discussion will emphasize that predictions reflect compositional propensity under unknown processing conditions. The model predicts compositional correlates of glass formation rather than the actual phenomenon.

## Statistical Rigor Checklist

| Requirement | Method | Status |
|-------------|--------|--------|
| Multiple‑comparison correction | Bonferroni (α/3 for 3 descriptors) | Planned |
| Sample‑size/power justification | Power analysis (α = 0.05, power = 0.80, d = 0.5 → ≈ 128 total) | Implemented in Phase 0 |
| Causal inference assumptions | Framed as associational; no randomization/identification strategy | Documented |
| Measurement validity | DScribe benchmark validation (SC‑002) | Planned |
| Predictor collinearity | VIF computed; PCA fallback if all VIF > 5 (FR‑008) | Planned |
| Target independence | Acknowledged as potential limitation; shared input data sources documented | Documented |

## Decision Log

| Decision | Rationale | Alternatives Rejected |
|----------|-----------|----------------------|
| scikit‑learn over PyTorch/TensorFlow | CPU‑only constraint; no GPU available on GitHub Actions free tier | Deep learning frameworks would exceed runtime and memory limits |
| Random Forest/Gradient Boosting over neural networks | CPU‑tractable; interpretable feature importance; suited for tabular data | Neural networks would require GPU or excessive CPU time |
| DScribe for descriptor computation | Industry standard; benchmark values available for validation | Manual computation would increase error risk |
| SHAP over LIME | SHAP provides theoretically grounded, reproducible attributions | LIME less stable across runs |
| Synthetic data for CI | No verified alloy dataset available; enables pipeline testing | Real data cannot be used until verified sources are added |

## Known Limitations

1. **Dataset Availability**: No verified sources for Materials Project or NIST Alloy Database in the provided verified datasets block. Production deployment requires external verification; current runs use synthetic data.
2. **Materials Project Label Mismatch**: Materials Project primarily contains DFT-calculated ground-state crystal structures, not experimental glass-forming propensity labels. This fundamental mismatch between validation target and research question is documented as a limitation.
3. **Causal Inference**: Model predicts associational propensity only; cooling rate and thermal history are missing confounds, limiting causal interpretation. The model predicts compositional correlates rather than the actual phenomenon.
4. **Power Analysis**: Minimum sample size ≈ 128 for medium effect; if unavailable, precision‑recall metrics are emphasized.
5. **Collinearity**: If all descriptors exceed VIF > 5, a PCA fallback to two components is used; independent effect claims are avoided.
6. **Class Imbalance**: Severe imbalance (> 3:1) triggers alternative handling (class weighting, SMOTE, or anomaly detection) rather than aborting analysis. The 3:1 threshold is a soft flag with fallback strategies.
7. **Shared Input Data**: Descriptors share elemental property input sources; validation target independence cannot be guaranteed. VIF addresses collinearity but target independence remains a potential limitation.