# Research: Predicting the Impact of Alloying on High-Temperature Oxidation Resistance

## 1. Problem Statement & Scientific Context

The development of nickel-based superalloys for high-temperature applications (e.g., turbine blades) is bottlenecked by the slow, empirical process of physical testing for oxidation resistance. While composition is a primary driver of oxidation behavior (specifically the formation of protective alumina/chromia scales), microstructural factors (grain size, precipitate distribution) also play a critical role.

**Research Question**: To what extent can high-temperature oxidation weight gain be predicted using *only* elemental composition and derived thermodynamic descriptors, and where does this composition-only model fail due to missing microstructural information?

**Hypothesis**: A machine learning model trained on composition and thermodynamic descriptors will achieve moderate predictive accuracy (R² ≥ 0.5) but will exhibit systematic residuals for alloys with specific microstructural anomalies (e.g., fine grain sizes or specific precipitate distributions) that are not captured by bulk composition.

**Critical Scope Note**: The validation of this hypothesis is contingent on the availability of real-world experimental data. If no such data is found, the project will proceed in "Pipeline Validation Mode" using synthetic data, and the results will be explicitly labeled as **not** validating the scientific hypothesis.

## 2. Dataset Strategy

The project relies on tabular data containing elemental weight percentages (Ni, Cr, Al, Co, Ti, etc.) and measured oxidation weight gain (mg/cm²).

**Verified Datasets**:
Per the project constraints, we must use only the verified sources listed in the input. However, a critical review of the `# Verified datasets` block reveals a significant mismatch:
- The provided URLs (e.g., `medical-5day-zeroshot...`, `nist_800_53`, `arc:challenge`) correspond to **medical NLP benchmarks** and **security policy documents**, not materials science alloy data.
- **CRITICAL MISMATCH**: The `spec.md` assumes the existence of a "NIST Materials Data Repository" or "Zenodo" dataset containing alloy oxidation data. The provided `# Verified datasets` block **does not contain** any such dataset.

**Decision & Fallback Strategy**:
1.  **Data Sourcing Fallback**: The implementation will first attempt to fetch data from the specified URLs. If the fetch fails or the data is irrelevant (as expected), the system will trigger a **Synthetic Data Generator**.
2.  **Synthetic Data Purpose**: The synthetic generator is designed **strictly for Pipeline Validation**. It will mimic the schema and physical trends (e.g., higher Al/Cr correlates with lower weight gain) to test the code's robustness, feature engineering logic, and statistical methods.
3.  **Scientific Validity Warning**: **Synthetic data CANNOT validate the scientific hypothesis.** The generator's internal logic is a tautology of the researcher's assumptions. Therefore, any results derived from synthetic data will be labeled as "Pipeline Stress Test Results" and will not be used to claim support for the "Microstructural Gap" hypothesis.
4.  **Real Data Contingency**: If a real, public alloy oxidation dataset is identified during the research phase (outside the provided input block), the project will switch to "Scientific Inquiry Mode" and re-run the analysis. If no real data is found, the project will terminate with a "Data Gap Report" stating the hypothesis is unanswerable.

**Rationale**: The project cannot invent a URL. The spec requires the *methodology* of composition-only vs. microstructural modeling. By using a synthetic generator for pipeline testing, we can validate the *code* and the *statistical rigor* (CV, SHAP, Gap Analysis) without fabricating a URL for a non-existent dataset or making false scientific claims.

## 3. Methodological Rigor

### 3.1 Statistical Approach
- **Models**: Random Forest (RF), Gradient Boosting (GB), Gaussian Process (GP).
- **Validation**: **Nested Cross-Validation (5x2 CV)** will be used for unbiased model selection to prevent data dredging. A pre-registered primary metric (RMSE) will be used for comparison.
- **Multiple Comparison Correction**: Since we are comparing 3 models on the same dataset, we will use a non-parametric test (e.g., Friedman test followed by Nemenyi post-hoc) if the number of folds/samples permits.
- **Causal Framing**: All results will be explicitly labeled as **associational**. No causal claims (e.g., "Aluminum *causes* reduced oxidation") will be made; instead, we will state "Aluminum is *associated* with reduced oxidation."

### 3.2 Feature Engineering & Collinearity
- **Descriptors**:
  - Raw: Ni, Cr, Al, Co, Ti (wt%).
  - Derived: Oxide Formation Enthalpy (ΔHf) for NiO, Cr2O3, Al2O3, etc. (using standard reference values).
  - Periodic: Atomic radius, Electronegativity, Valence electron count.
- **Collinearity Check**: Since Al and Al2O3 enthalpy are definitionally linked, we will not claim "independent effects" for both. We will report the SHAP values for the *raw* composition and the *derived* descriptors separately but acknowledge the high correlation.
- **Synthetic Data Noise**: To prevent the model from trivially learning the target in the synthetic mode, the generator will introduce **uncorrelated noise** to the microstructural features, ensuring the "Gap" is not a mathematical certainty but a statistical challenge.
- **Zero Variance**: The pipeline will detect and exclude features with zero variance.

### 3.3 Statistical Power & Sample Size
- **Power Analysis**: The plan includes a formal power calculation to determine the minimum sample size required to detect a specific effect size (Cohen's d) for the microstructural gap.
- **Limitation**: With a cap of 500 samples (CI mode), the power to detect small microstructural effects (especially if the microstructural subset is < 30) is limited.
- **Mitigation**: The plan explicitly implements the "Inconclusive" logic (US-2, SC-002) if the microstructural subset size < 30. In this case, the report will state: "Inconclusive due to insufficient microstructural data (n < 30). Calculated power to detect effect size d=0.5 is [X]%." This prevents the 'Inconclusive' verdict from being misinterpreted as a true absence of effect.

## 4. Compute Feasibility

- **Hardware**: GitHub Actions Free Tier (2 CPU, 7 GB RAM).
- **Strategy**:
  - Dataset capped at 500 rows for CI.
  - Models: `scikit-learn` defaults (CPU only). No GPU.
  - SHAP: Use `KernelExplainer` with a representative subsample of instances for speed, or `TreeExplainer` for RF/GB which is fast.
  - Runtime: Estimated < 30 minutes for full pipeline (fetch, train, eval, plot).

## 5. Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Synthetic Data for Pipeline Validation** | No verified materials science dataset URL exists in the input block. To satisfy the *mechanism* of the spec (FR-001 to FR-007) without fabricating a URL, we generate synthetic data that mimics the expected schema and physical trends. **Crucially, this is NOT for scientific validation.** |
| **Nested Cross-Validation** | To avoid overfitting and data dredging when comparing 3 models on a small dataset (n ≤ 500), nested CV is mandated over simple CV. |
| **Associational Framing Only** | The synthetic data is observational. No randomized trials exist. Claims are strictly correlational. |
| **Gap Analysis Logic** | Explicitly checks `n < 30` for microstructural subset to prevent statistical overfitting/invalid inference. Includes power calculation to contextualize the "Inconclusive" verdict. |
| **Data Gap Report** | If no real dataset is found, the project will output a formal "Data Gap Report" rather than claiming scientific results from synthetic data. |

## 6. Scientific Validity Warning

**IMPORTANT**: This project's primary research question (validating the "Microstructural Gap" hypothesis) **cannot be answered** using the synthetic data fallback. The synthetic data generator is designed to follow known physical trends, meaning any model trained on it will inevitably achieve high R² and "recover" those trends by construction. This is a tautological validation of the *code*, not the *hypothesis*. 

If the project proceeds in "Pipeline Validation Mode" (due to lack of real data), all outputs will be clearly labeled as such, and no scientific claims regarding real-world oxidation resistance will be made. The project will terminate with a "Data Gap" status if no real dataset is found.
