# Research: Predicting Chemical Reaction Yields from Spectroscopic Data with Attention Mechanisms

## 1. Research Question & Hypothesis

**Question**: Can **real** spectroscopic data (IR, Raman, NMR) provide independent predictive signal for chemical reaction yields beyond molecular structure (fingerprints) and reaction conditions, and can attention mechanisms identify the specific spectral regions responsible?

**Hypothesis**:
1.  **H1**: A multi-modal attention model will outperform unimodal baselines (fingerprint-only, spectrum-only, condition-only) on held-out test data (RMSE reduction > 5%) **IF** a sufficient dataset of real paired samples exists (N >= 500) AND the model converges (R² > 0).
2.  **H2**: Attention weights will correlate significantly with yield residuals and localize to known functional group frequencies (e.g., carbonyl, amide stretches) within ±50 cm⁻¹ **IF** the dataset is sufficient (N >= 500) and the model converges (R² > 0).
3.  **H3**: The model will not learn spurious correlations (R² < 0.05) when labels are permuted.

**Reframed Research Question for N < 500**:
If the number of verified real paired samples is < 500, the quantitative hypothesis (H1) is **not tested**. The research question is pivoted to: **"Can the attention-based model architecture successfully process and converge on small real experimental datasets, and what qualitative insights can be drawn from its attention weights?"** In this scenario, H1 and H2 are not validated, and the report will explicitly state that the "independent signal" claim is untested due to data scarcity.

## 2. Dataset Strategy

### 2.1 Verified Sources & Fit Analysis

The spec requires **paired** data: `SMILES` + `Spectra` + `Conditions` + `Yield`.
The verified dataset list provides:
- **SMILES**: USPTO, ZINC, ChEMBL (verified).
- **Spectra**: NMR_demo (verified), Tokenized NMR (verified).
- **Yield/Conditions**: USPTO (verified).
- **DFT/Simulated**: `dftest` (verified).

**Critical Mismatch**: No single verified dataset contains *all* four fields for the same reaction instance.
- `USPTO` has SMILES + Yield + Conditions, but **no spectra**.
- `NMR_demo` has Spectra + SMILES, but **no yield/conditions** (or yield is missing).
- `dftest` likely has DFT-calculated spectra + SMILES, but **yield labels are missing**.

**Strategy**:
1.  **Primary Path (Real Data Merge)**: Attempt to merge `USPTO` (for SMILES, Yield, Conditions) with `NMR_demo` or `MolSpectra` (for Spectra) by matching SMILES strings.
    - *Constraint*: **NO simulated spectra will be generated.** If a SMILES from USPTO does not have a matching real spectrum in the verified spectral datasets, that sample is **dropped**.
    - *Rationale*: This ensures we have *real* yield labels and *real* spectra, even if the sample size is small. This is scientifically valid for testing the architecture, provided the limitation is explicitly stated.
2.  **Fallback Path (Qualitative Validation / Data Insufficiency)**: If the number of successfully merged samples is < 500:
    - **If N == 0**: Halt training. Generate a **Data Insufficiency Report**.
    - **If 0 < N < 500**: Proceed with **Qualitative Architecture Validation**. Train the model on the small real dataset. Report performance metrics but explicitly state that quantitative claims (H1, H2) are not supported due to low power.
    - *Decision*: The project defaults to **Path 1 (Real Data Merge)**. If the merge yields < 500 samples, the project pivots to Path 2 (Qualitative Validation or Report).

### 2.2 Data Acquisition Plan

- **Source 1 (Yields/Conditions)**: `https://huggingface.co/datasets/trentmkelly/uspto-patent-data/resolve/main/data/2021-00000.parquet` (USPTO).
  - *Action*: Filter for reactions with yield > 0. Extract `reaction_smiles`, `yield`, `solvent`, `catalyst`, `temperature`.
- **Source 2 (Spectra)**: `NMR_demo` (verified) and `MolSpectra` (if available in verified block).
  - *Action*: Load spectra. Match against USPTO SMILES.
  - *Constraint*: **If no match is found, the sample is dropped.** No simulation.
- **Source 3 (Validation)**: `NMR_demo` (held-out portion) or a separate small curated set from the verified block.
  - *Action*: Use a subset of the verified spectral data (not used in training) to validate the model (FR-010).
  - *Fallback for FR-010*: If no independent dataset exists, perform a **Temporal Split** or **Source-Stratified Split** on the available real data (e.g., using older USPTO reactions for training and newer ones for validation) **ONLY IF** the source distribution is demonstrably different. If no such split is possible, FR-010 is marked "Not Applicable".

### 2.3 Preprocessing & Splitting

- **Resampling**: All spectra resampled to the standard IR and NMR spectral ranges using linear interpolation.
- **Normalization**: Unit variance scaling per feature (spectrum channel).
- **Splitting**:
  - Extract reaction center substructures (templates) from `reaction_smiles`.
  - Cluster templates or hash them.
  - Split 70/15/15 ensuring **zero intersection** of template hashes between Train/Val/Test.
  - *Verification*: `src/utils/validators.py` checks `len(set(train_templates) & set(test_templates)) == 0`.
  - *Constraint*: Splitting is performed **only** on the verified subset of real paired data. No synthetic data is included.
  - *Small N Handling*: If N < 500, a **Template Diversity Check** is performed. If unique templates < 3, splitting is halted, and a single-set qualitative analysis is performed.
  - *Artifacts*: `data/processed/split_indices.parquet`, `data/artifacts/split_manifest.json`, `data/artifacts/leakage_report.json`.

## 3. Statistical Rigor & Methodology

### 3.1 Model Architecture (CPU-Feasible)
- **Input**: Concatenated `[ECFP4 (2048), Condition_Embed (64), Spectral_Tensor (N_channels x Grid_Size)]`.
- **Backbone**: 2-layer Multi-Head Self-Attention (4 heads, hidden_dim=128).
- **Output**: Regression head (1 unit, yield %).
- **Optimizer**: Adam (LR=1e-3), Batch Size=32, Max Epochs=10, Early Stopping (patience=3).
- **Feasibility**: Small model size ensures < 1GB RAM and < 2h training time on 2 CPU cores.

### 3.2 Evaluation Metrics & Tests
- **Primary Metrics**: RMSE, MAE, R² (FR-005).
- **Statistical Test**: Paired t-test on absolute errors (Attention vs. Best Baseline) with **Bonferroni correction** for multiple comparisons (3 baselines) (FR-006, SC-002). **Only performed if N >= 500.**
- **Permutation Test**: Shuffle yield labels 10 times; retrain/evaluate. Expect R² < 0.05 (FR-008, SC-004).
- **Interpretability**:
  - Attention weight heatmaps (FR-007).
  - Correlation analysis: Attention weights vs. Yield residuals (controlling for ECFP4).
  - Peak validation: Top 5 attention peaks vs. literature functional group frequencies (±50 cm⁻¹) (SC-003). **Conditional**: Only performed if N >= 500 and the model achieves R² > 0. If N < 500 or R² <= 0, the report will state that literature validation was not possible.

### 3.3 Power & Limitations
- **Sample Size**: Determined by the number of successfully merged real paired samples.
- **Power Analysis**: If N < 500, the study is underpowered for quantitative claims. The project will report this limitation and output a **Qualitative Architecture Validation Report** instead of a full quantitative study.
- **Causal Claim**: Observational (real data). Claims limited to "predictive association," not causation.

## 4. Decision Rationale (Compute Feasibility)

- **CPU-First**: The model is a small Transformer (2 layers, 4 heads). No GPU needed for inference or training of this scale.
- **Data Streaming**: `datasets` library with `streaming=True` used to load USPTO if it exceeds RAM, though we expect to filter to < 50k samples.
- **No Fabrication**: If experimental spectra are missing, we do **not** invent them. We drop the sample. If the dataset is too small, we report "Data Insufficiency" or "Qualitative Validation". This satisfies Constitution II (Verified Accuracy) by being honest about data provenance.
