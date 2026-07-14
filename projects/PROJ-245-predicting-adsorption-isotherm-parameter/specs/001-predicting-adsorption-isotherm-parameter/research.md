# Research: Predicting Adsorption Isotherm Parameters from Molecular Features

## 1. Problem Statement & Hypothesis

**Problem**: Predicting adsorption isotherm parameters (Langmuir capacity, Henry's constant) for gas-adsorbent systems is computationally expensive using molecular dynamics or quantum chemistry.
**Hypothesis**: A set of easily calculable molecular descriptors (polarizability, van der Waals volume, etc.) and adsorbent properties (surface area, pore volume) can serve as effective predictors for these thermodynamic parameters using standard machine learning regression models.

**Critical Distinction**: This research is divided into **Pipeline Validation** (verifying code logic on synthetic data) and **Scientific Validation** (verifying the hypothesis on real literature data). Success criteria SC-002 and SC-003 apply *only* to the Scientific Validation phase.

## 2. Dataset Strategy

### 2.1 Verified Sources & Gaps

The project specification relies on two primary data sources:
1.  **NIST Adsorption Database**
2.  **MOF-1000 Zenodo Repository**

**Verification Status**:
-   **NIST Adsorption Database**: **NO VERIFIED SOURCE** found in the provided `# Verified datasets` block.
-   **MOF-1000**: **NO VERIFIED SOURCE** found in the provided `# Verified datasets` block.

**Decision**:
To satisfy **Constitution Principle II (Verified Accuracy)** and ensure the project is **runnable on CI**, the implementation will:
1.  **Attempt Fetch**: The `download.py` script will attempt to fetch these sources.
2.  **Audit Log**: If fetch fails, a `verification_log.json` will be written, explicitly recording the failure and the decision to use synthetic data.
3.  **Synthetic Fallback**: A `synthetic_gen.py` module will generate a dataset with the exact schema required by the spec (FR-001, FR-002).
    *   *Generator Logic*: The generator simulates realistic correlations **with added random noise and variable feature importance** to prevent the model from trivially memorizing the "correct" answer. This ensures the pipeline is tested for robustness, not just correctness.
4.  **External Validation**: A small, manually curated literature dataset (e.g., Kr on CNTs) will be used in **Phase 3** to validate the scientific hypothesis.

**Dataset Schema (Simulated)**:
-   **Adsorbate**: SMILES string, Molecular Weight, Polarizability, VdW Volume, Kinetic Diameter.
-   **Adsorbent**: Surface Area (m²/g), Pore Volume (cm³/g), Material ID.
-   **Target**: Langmuir Capacity (mmol/g), Henry's Constant (mmol/kg/bar).
-   **Filter**: Type I Isotherm flag.

### 2.2 Variable Fit & Mismatch Handling

-   **Required Variables**: Polarizability, VdW Volume, Surface Area, Langmuir Capacity.
-   **Gap**: The simulated dataset will explicitly generate these variables with known correlations to ensure the model can learn (meeting SC-001 for pipeline).
-   **Mismatch**: The `preprocess.py` script will implement logic to drop rows with missing targets (FR-002) to match the spec's robustness requirements.

## 3. Statistical Methodology & Rigor

### 3.1 Model Selection
-   **Baseline**: Linear Regression.
-   **Non-Linear**: Random Forest.
-   **Advanced**: Gradient Boosting.
-   **Rationale**: CPU-tractable, interpretable. Deep learning excluded due to CI constraints.

### 3.2 Data Splitting (Leakage Prevention)
-   **Strategy**: **Material-Level Splitting**.
-   **Method**: Group by `Material ID`. Split groups into Train (majority) and Test (minority).
-   **Justification**: FR-003. Prevents data leakage and ensures generalization to new materials.

### 3.3 Statistical Rigor & Corrections
-   **Multiple Comparisons**: FR-006 requires FDR correction.
    -   **Method**: Benjamini-Hochberg procedure on permutation-based p-values for the top 5 features.
    -   **Rationale**: Testing an increased number of features increases false positive risk.
    -   **Synthetic Context**: In the synthetic run, this step verifies the *implementation* of FDR logic. It does **not** claim scientific significance of the features.
    -   **External Context**: In Phase 3, this step is used for scientific inference, with explicit acknowledgment of power limitations if N is small.
-   **Power Analysis**:
    -   **Synthetic Limitation**: The synthetic dataset (N~5,000) is sized for CI feasibility but is **insufficient** for robust statistical power in real-world discovery.
    -   **External Validation**: Final statistical claims (SC-003) will be made on the external validation dataset. If N is small, the report will explicitly acknowledge power limitations and focus on qualitative feature ranking.
-   **Causal Claims**:
    -   **Constraint**: This is an **observational** (simulated) study.
    -   **Framing**: Claims will be framed as "associational" or "predictive". No causal claims will be made.

### 3.4 Measurement Validity
-   **Descriptors**: Calculated via RDKit.
-   **Targets**: Simulated based on known thermodynamic relationships (with noise) for pipeline testing.
-   **Plausibility**: **Phase 3** (External Validation) will compare SHAP rankings against literature consensus to satisfy Constitution Principle VII. The synthetic run will **not** be used for this check to avoid circular validation.

## 4. Compute Feasibility

-   **Hardware**: GitHub Actions Free Tier (limited CPU, constrained RAM).
-   **Library Choices**: `scikit-learn`, `rdkit`, `shap` (CPU mode).
-   **Data Volume**: Synthetic dataset ~5,000 rows; External dataset < 500 rows.
-   **Runtime**: Estimated < 1 hour for full pipeline.

## 5. Decision Log

| Decision | Rationale | Alternative Rejected |
| :--- | :--- | :--- |
| **Synthetic Data** | No verified URLs. Ensures reproducibility and CI runnability. | Using unverified URLs (Violates Constitution II). |
| **Material-Level Split** | Required by FR-003. | Random split (Invalidates generalization). |
| **FDR Correction** | Required by FR-006. | Raw p-values (High false positive risk). |
| **External Validation Phase** | Required by Constitution Principle VII. | Relying solely on synthetic data (Circular logic). |
| **Deferred SC-002/003** | Synthetic data cannot validate scientific hypothesis. | Measuring SC-002/003 on synthetic data (Tautology). |
| **Randomized Synthetic Correlations** | Prevents circular validation where the model is guaranteed to find the "right" features. | Deterministic generator (Circular validation). |