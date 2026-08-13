# Research: Predicting Chemical Reaction Yields from Spectroscopic Data with Attention Mechanisms

## 1. Problem Statement & Hypothesis

**Problem**: Can spectroscopic data (IR, NMR, Raman) provide *independent* predictive signal for chemical reaction yields beyond what is available from molecular structure (fingerprints) and reaction conditions?

**Hypothesis**: A multi-head self-attention model, when trained on concatenated inputs of resampled spectra, ECFP4 fingerprints, and condition vectors, will significantly outperform baselines trained on single modalities, and its attention weights will correlate with known functional group frequencies (or simulation injection points).

**Scope**: This research is limited to reactions where both spectral data and yield are available. Given that verified open datasets (ZINC, SMILES) do not contain paired yield/spectrum data, the project defaults to a **Simulated Data Path** using a physics-based simulator with stochastic noise. The simulation logic is explicitly designed to ensure spectra are NOT deterministic functions of fingerprints, preserving the testability of the "independent signal" hypothesis.

## 2. Dataset Strategy

### 2.1 Verified Sources & Feasibility
Per the project constraints, we will utilize **only** the following verified datasets or their verified sources. 

| Dataset | Type | Verified URL | Usage |
| :--- | :--- | :--- | :--- |
| **ZINC (Canonicalized)** | Reaction SMILES | `https://huggingface.co/datasets/sagawa/ZINC-canonicalized/resolve/main/data/train-00000-of-00003-1dd8e62fc2556455.parquet` | Source for reaction templates (SMILES only). **No yields or spectra.** |
| **SMILES Transformers** | SMILES | `https://huggingface.co/datasets/maykcaldas/smiles-transformers/resolve/main/data/test-00000-of-00015-27ed436361d9186e.parquet` | Supplemental structural data. **No yields or spectra.** |
| **NMR (Tokenized)** | NMR Spectra | `https://huggingface.co/datasets/Tomoqt/tokenized_NMR_resample1000/resolve/main/tokenized_dataset.tar.gz` | Source for NMR spectral data. **No yields.** |
| **NMR Demo** | NMR Spectra | `https://huggingface.co/datasets/Marshtomp/chemistry_nmr_demo/resolve/main/nmr.csv` | Supplemental NMR data. **No yields.** |
| **NIST Chemistry WebBook** | Functional Group Frequencies | `https://webbook.nist.gov/` (Public Documentation) | Source for static lookup table of functional group frequencies (FR-012). |

**Critical Feasibility Note**: 
- **Real Data Path**: Joining ZINC (SMILES) with NMR (Spectra) yields **zero** valid samples because neither dataset contains the other's required fields (Yield vs. Spectrum). 
- **Conclusion**: The "Real Data Path" is infeasible. The project will **default to the Simulated Data Path**.

### 2.2 Simulated Data Path (Default Execution)
Since real paired data is unavailable, we will generate a **real** synthetic dataset using a physics-based spectral simulator. This data will be generated *on-the-fly* during the pipeline run (not hardcoded) and treated as the "ground truth" for the simulation hypothesis.

**Simulation Logic Design (Critical for Hypothesis Validity)**:
To ensure the "independent predictive signal" hypothesis is testable, the simulation **must not** generate spectra as a deterministic function of the fingerprint alone. The simulator will:
1.  **Base Spectrum**: Generate a base spectrum based on functional groups (derived from SMILES).
2.  **Stochastic Noise**: Inject random Gaussian noise to simulate instrument variability and conformational effects not captured by static fingerprints.
3.  **Environment-Dependent Shifts**: Apply random shifts to peak positions and intensities based on simulated solvent/catalyst conditions (e.g., hydrogen bonding effects). These shifts are **not** encoded in the ECFP4 fingerprint.
4.  **Yield Labeling**: Assign yield based on a complex function of structure, conditions, and the *perturbed* spectral features.

This design ensures that the spectral input contains information (noise, environment shifts) that is **independent** of the fingerprint input, allowing the model to learn a genuine signal.

### 2.3 Data Integration & Feasibility
- **Strategy**:
  1.  **Generate Synthetic Data**: Use `src/data/ingestion.py` to generate 5k-10k reactions with SMILES, yields, and perturbed spectra.
  2.  **Verify Integrity**: Perform FR-015 (Simulated Data Integrity Check) to ensure spectra are not perfectly collinear with fingerprints.
  3.  **Streaming**: Data is generated and streamed to avoid memory spikes.

### 2.4 Data Integrity Checks
- **FR-015**: A collinearity check will be performed on the generated synthetic data to ensure spectra are not deterministic functions of fingerprints. If collinearity is too high, the simulation parameters will be adjusted (increase noise).
- **FR-016**: Variance Inflation Factor (VIF) will be computed between spectral and fingerprint inputs for all models.

## 3. Methodology

### 3.1 Preprocessing (FR-001, FR-002)
1.  **Resampling**: All spectra resampled to fixed grids (IR/Raman: 400–4000 cm⁻¹, NMR: standard chemical shift range) using linear interpolation.
2.  **Normalization**: Unit variance normalization per spectrum.
3.  **Condition Encoding**: Solvent, catalyst, and temperature encoded as one-hot or embedding vectors.
4.  **Stratified Splitting**:
    -   Extract reaction templates (reaction center substructures) from SMILES.
    -   Compute MD5 hashes of templates.
    -   **Stratify** splits by `template_id` AND `condition_bucket` (solvent/catalyst classes) to prevent distribution shift confounds.
    -   **FR-014**: Verify zero template overlap using MD5 hashing.

### 3.2 Model Architecture (FR-003)
-   **Input**: Concatenated tensor `[Spectrum_vector, Fingerprint_vector, Condition_vector]`.
-   **Backbone**: Multi-head Self-Attention network (Transformer encoder style).
-   **Head**: Regression head for yield (0–100).
-   **Baselines**:
    -   *Fingerprint-only*: MLP on ECFP4.
    -   *Spectrum-only*: MLP on resampled spectrum.
    -   *Condition-only*: MLP on condition vector.

### 3.3 Training (FR-004)
-   **Optimizer**: Adam (lr=1e-3).
-   **Batch Size**: 32.
-   **Epochs**: Max 10, with early stopping on validation RMSE.
-   **Hardware**: CPU-only (PyTorch CPU backend).
-   **Reproducibility**: All seeds pinned.

### 3.4 Evaluation & Interpretability (FR-005, FR-006, FR-007, FR-008, FR-009, FR-012, FR-013, FR-016)
-   **Metrics**: RMSE, MAE, R².
-   **Statistical Test**: 
    -   Paired t-test on absolute errors (Attention vs. Best Baseline) with **Bonferroni correction**.
    -   **Robustness Check**: Wilcoxon signed-rank test and bootstrap confidence intervals (95%) to handle heteroscedasticity.
-   **Permutation Test**: Shuffle yield labels; re-evaluate. Expect R² < 0.05.
-   **Attention Visualization**:
    -   Map attention weights to spectral axis.
 - **FR-009 Sensitivity Analysis**: Perform analysis over three thresholds: **Top 1%**, **Top 5%**, **Top [deferred]** of attention weights. Report robustness of identified regions across these sets.
    -   **FR-012 NIST Validation**: 
        -   *For Simulated Data*: Compare attention peaks against the **known injection parameters** of the simulation (the ground truth of the synthetic data).
        -   *For Real Data (if ever obtained)*: Compare peaks against literature values from the NIST Chemistry WebBook (retrieved via `src/data/nist_references.py` static lookup table).
    -   **FR-013**: Compute Pearson correlation between attention weights and yield residuals.
-   **FR-016 VIF**: Compute VIF for all models. If VIF > 5, report collinearity and avoid claiming independent effects.

## 4. Statistical Rigor & Limitations

-   **Multiple Comparisons**: Bonferroni correction applied to t-tests.
-   **Power Analysis**: Given the dataset size constraints (likely < 10k samples for paired data), the plan acknowledges limited statistical power. Results will be reported with confidence intervals.
-   **Causal Claims**: No causal claims will be made. Claims are strictly associational.
-   **Collinearity**: If VIF > 5, the plan will report the collinearity and avoid claiming "independent" effects for correlated features.
-   **Dataset Mismatch**: The plan explicitly states that the "Real Data Path" is infeasible and the results are derived from a **Simulated Data Path** with explicit limitation reporting.
-   **Simulation Limitations**: The "independent signal" is validated against the simulation's injection logic, not external chemical reality. This is a limitation of the study design due to data availability.

## 5. Compute Feasibility

-   **CPU-First**: The model is designed to be small (few layers, low hidden dimension) to fit within 2 CPU cores and 7GB RAM.
-   **No GPU**: The plan does not rely on GPU acceleration.
-   **Streaming**: Data is generated and streamed to avoid memory spikes.
-   **Time Limit**: The pipeline is designed to complete in < 4 hours to allow for CI overhead.

## 6. Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **Simulated Data Path** | Real open datasets lack paired yield/spectrum data. Simulation with stochastic noise is the only valid path. |
| **Template-based Splitting** | Essential to prevent data leakage and ensure generalization to new reaction types (FR-002). |
| **Stratified Splitting** | Prevents confounding by reaction conditions (solvent/catalyst) in addition to template leakage. |
| **Attention Mechanism** | Required to provide interpretability (SC-003) and identify spectral regions. |
| **Static NIST Lookup** | Satisfies FR-012 and Constitution Principle II without dynamic scraping; ensures reproducibility. |
| **Simulation Logic Design** | Stochastic noise and solvent effects ensure spectra are not deterministic functions of fingerprints, preserving the hypothesis. |
| **Sensitivity Analysis** | Required by FR-009 to ensure robustness of identified spectral regions (Top [deferred], [deferred], [deferred]). |
| **VIF Computation** | Required by FR-016 for all models to detect lack of independent variance. |
| **Non-Parametric Tests** | Wilcoxon and bootstrap methods added for robustness against heteroscedasticity. |