# Research: Predicting Molecular Packing Efficiency in Crystals from SMILES Representations

## 1. Scientific Question

**Primary Question**: How does molecular topology encoded in SMILES representations (derived from 2D connectivity), when augmented with 3D geometric descriptors (derived from experimental coordinates), predict the **Raw Packing Coefficient (PC_raw)** of organic crystals, *beyond* the geometric determinants captured by the 3D descriptors themselves?

**Hypothesis**: SMILES-derived features (capturing connectivity and functional groups) combined with D geometric descriptors (capturing shape and size) contain sufficient *residual* signal to predict PC_raw with a Pearson correlation coefficient $r \ge 0.4$. The SMILES signal is expected to capture subgraph-level topological features (e.g., ring systems, functional groups) that influence packing, independent of the experimental three-dimensional geometry used for the target. The "residual" signal is the variance in PC_raw not explained by the 3D geometric descriptors alone.

**Null Hypothesis**: There is no predictive relationship ($r \approx 0$) between the combined feature set and PC_raw after controlling for 3D geometry and elemental composition.

## 2. Dataset Strategy

### 2.1 Source Verification
The project relies on the **Crystallography Open Database (COD)** for crystal structures. To ensure feasibility within the 6-hour runtime and 7 GB RAM constraints, we use the official COD bulk download.

**Verified Datasets**:
- **COD (Official Bulk Download)**: `ftp://ftp.ccdc.cam.ac.uk/pub/structures/cod/` (Official COD FTP).
  - *Verification*: The pipeline includes a checksum verification step against the official COD manifest. The data is streamed and filtered on-the-fly to extract only the required fields (unit cell, atomic coordinates, formula).
  - *Usage*: Streamed to `data/raw/`. Filtered for organic molecules with ≤50 non-hydrogen atoms.
- **SMILES Transformer Weights**: `seyonec/ChemBERTa-zinc-base-v1` (Hugging Face Model Repository).
  - *Usage*: Provides the frozen pre-trained weights for the SMILES Transformer (FR-004). This model was trained on the **ZINC** database of organic drug-like molecules, making it highly relevant for the COD organic subset. The frozen weights capture subgraph-level topological features relevant to packing.

**Data Availability Note**: The pipeline filters for entries with valid spatial coordinates. If 3D coordinates are missing but a valid 2D SMILES exists, the pipeline generates a 3D conformer using RDKit's ETKDG algorithm **solely to generate a canonical SMILES**. This generated 3D structure is **discarded**. The experimental 3D coordinates (if available) are used for all target and descriptor calculations. If neither exists, the entry is skipped and logged. This introduces a selection bias (only molecules that crystallized with 3D determination or valid 2D SMILES are included), which is acknowledged as a limitation. The final `dataset.csv` will be limited to the first [deferred] valid records (or all if <1,000) to ensure the 6-hour runtime constraint (SC-005).

### 2.2 Data Processing Pipeline
1.  **Download & Filter**: Fetch the COD bulk archive. Parse each record.
    -   *Filter 1*: Must contain `_cell_length_a`, `_cell_length_b`, `_cell_length_c`, `_cell_angle_alpha`, `_cell_angle_beta`, `_cell_angle_gamma` (to calculate unit cell volume).
    -   *Filter 2*: Must contain atomic coordinates.
    -   *Filter 3*: Count non-hydrogen atoms $\le 50$.
    -   *Fallback*: If 3D coordinates are missing but `_chemical_structure_SMILES` exists, generate 3D coordinates via RDKit ETKDG **only to generate a canonical SMILES**. The generated 3D structure is **discarded**. If 3D coordinates exist, use the bond graph from the CIF to generate a 2D representation for SMILES generation.
2.  **SMILES Generation (Leakage Mitigation)**:
    -   **Strict Rule**: SMILES are generated **exclusively from 2D connectivity graphs**.
    -   If `_chemical_structure_SMILES` exists, use it.
    -   Else, if 3D coordinates exist: Extract the bond graph from the CIF (bond orders inferred from distances). Convert to a 2D RDKit molecule. Generate canonical SMILES. **Do not use the 3D coordinates for SMILES generation.**
    -   Else (no 3D, but 2D SMILES exists): Use the 2D SMILES.
    -   Else: Skip.
    -   *Note*: This ensures the SMILES predictor is independent of the experimental 3D geometry used for the target.
3.  **Volume Calculation**:
    -   Calculate Unit Cell Volume ($V_{cell}$) from lattice parameters.
    -   Calculate Sum of Van der Waals Volumes ($\sum V_{vdW}$) using Bondi radii (FR-018, DOI: 10.1021/j100785a001).
    -   Compute $PC_{raw} = V_{cell} / \sum V_{vdW}$ (Target Variable).
    -   Compute $CAPE = PC_{raw} / (\sum V_{vdW} / N_{atoms})$ (Diagnostic Covariate, FR-011).
4.  **3D Descriptors (Experimental Only)**:
    -   Compute Radius of Gyration, Asphericity, Principal Moments of Inertia from the **experimental CIF coordinates** (FR-012).
    -   *Note*: **No gas-phase minimization** is performed. All 3D descriptors are derived strictly from the experimental coordinates to preserve the environmental context (FR-013).
5.  **Confounder Extraction**:
    -   Extract Lattice System, Temperature (if available), Solvent presence (FR-013).
    -   Extract **Elemental Atom Counts** (C, N, O, S, etc.) as a vector covariate (for partial correlation).
    -   Extract Mean Atomic Volume ($\sum V_{vdW} / N_{atoms}$) as a covariate.

### 2.3 Dataset Fit & Limitations
-   **Fit**: The official COD source contains the necessary geometric data to compute PC_raw and generate SMILES. It directly addresses the requirement for "organic molecules" (via formula parsing).
-   **Limitation**: The dataset may lack explicit temperature or solvent metadata for some entries. These will be recorded as `None` or `unknown` and handled as covariates (FR-013).
-   **Selection Bias**: The exclusion of entries without valid 3D coordinates (or valid 2D SMILES for generation) may skew the distribution of packing efficiencies. This is acknowledged as a limitation.
-   **Power**: A target sample size of N ≥ 500 is achievable. Based on Cohen's f2, this sample size provides >90% power to detect an effect size of r=0.4 with a 2-layer MLP (approx. 25k trainable parameters).

## 3. Methodology

### 3.1 Feature Engineering
-   **SMILES Encoding**: Use a frozen pre-trained SMILES Transformer (ChemBERTa-Zinc, `seyonec/ChemBERTa-zinc-base-v1`). The output is a fixed-length vector representing molecular topology. The model was trained on ZINC, a database of organic drug-like molecules, making it well-suited to capture subgraph-level features (functional groups, ring systems) relevant to packing. The frozen weights are justified by the need to stay within the <100k parameter constraint (FR-005) and CPU feasibility, and by the high relevance of the training domain.
-   **3D Descriptors**: Radius of Gyration, Asphericity, Principal Moments (3 values). Derived from **experimental** CIF coordinates.
-   **Covariates**: One-hot encoded Lattice System, Binary Solvent flag, Temperature (scaled), Mean Atomic Volume (to control for size), **Elemental Atom Counts** (to control for composition).
-   **Collinearity Check**: Calculate VIF for all features. Flag any $VIF > 5$ (FR-009).

### 3.2 Model Architecture & Analysis Strategy
-   **Type**: 2-Layer Multi-Layer Perceptron (MLP).
-   **Input**: Concatenation of SMILES vector + 3D descriptors + covariates.
-   **Hidden Layers**: Two layers with 32 units each (total parameters $\le 100k$ as per FR-005).
-   **Activation**: ReLU.
-   **Regularization**: L2 penalty (1e-4) and Dropout (0.1) to prevent overfitting the high-dimensional SMILES input.
-   **Output**: Single scalar (PC_raw).
-   **Loss**: Mean Squared Error (MSE).
-   **Optimizer**: Adam.
-   **Constraints**: Train on CPU only.
-   **Two-Stage Analysis**:
    1.  **Baseline Model**: Train MLP using only 3D descriptors + covariates. Record $R^2_{geo}$.
    2.  **Full Model**: Train MLP using 3D descriptors + covariates + SMILES embeddings. Record $R^2_{full}$.
    3.  **Incremental Signal**: Calculate $\Delta R^2 = R^2_{full} - R^2_{geo}$. This measures the unique contribution of topology.
    4.  **Baseline Comparison**: Train a model using **ECFP4 fingerprints** instead of the SMILES transformer to validate that the frozen transformer captures the necessary signal.
-   **Model Capacity Note**: The 2-layer MLP with 32 units is justified by power analysis (Cohen's f2) for N≥500 to detect r=0.4. The frozen weights prevent overfitting. If the model fails to reach r >= 0.4, it may indicate that the frozen features are insufficient, but the permutation test will still validly assess significance.

### 3.3 Statistical Evaluation
-   **Metrics**: MAE, Pearson $r$, Spearman $\rho$ (FR-006) on the Full Model.
-   **Normality**: Shapiro-Wilk test on residuals (FR-015).
-   **Significance**: Permutation test with **10,000 shuffles** (FR-016).
    -   Null distribution generated by shuffling PC_raw labels.
    -   Two-sided p-value calculated.
-   **Sensitivity**: Sweep threshold $\{0.5, 0.6, 0.7\}$ for "high packing".
    -   Report $r$, $\rho$, MAE, $p$ for each.
    -   Apply Bonferroni correction for 3 tests (FR-008).
-   **Partial Correlation**: Control for **elemental atom counts** (C, N, O, etc.) to ensure the SMILES signal is not merely a proxy for elemental composition. This is distinct from CAPE (which normalizes for size) and tests if the topological signal remains after removing the linear effect of elemental identity.
-   **Metric Limitation**: PC_raw is the standard metric. CAPE is used only as a covariate to avoid spurious correlations.

## 4. Compute Feasibility & Rationale

### 4.1 CPU-First Strategy
- **Transformer Inference**: The frozen transformer is run in inference mode on CPU. With a batch size of 1 or small batches, and a dataset of [deferred] records, this fits within the 7 GB RAM and 6-hour runtime.
-   **MLP Training**: A 100k parameter model trains instantly on CPU (seconds/minutes).
- **Permutation Test**: 10,000 shuffles on a [deferred]-row dataset is computationally trivial on 2 CPU cores (estimated <1 hour).
-   **No GPU Needed**: The model is too small to require a GPU, and the dataset size is manageable on CPU. No "GPU escape hatch" is required.

### 4.2 Data Streaming
-   The pipeline uses streaming to process the official COD archive on-the-fly, avoiding loading the entire archive into RAM. Only the filtered subset is materialized.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Dataset Size < 500** | Pipeline aborts; no results. | Pre-check count in `data_ingestion.py`. If <500, log error and exit. |
| **SMILES Generation Failure** | Missing target variable. | RDKit fallback; log failures. If >10% fail, abort. |
| **Runtime > 6 Hours** | CI job timeout. | Limit dataset to 1,000 records. Optimize permutation test (vectorized numpy). |
| **Collinearity (VIF > 5)** | Model instability. | Detect in `features.py`. If VIF > 5, flag in report but proceed (FR-009 requires flagging, not removal). |
| **No Significant Signal** | Null result (SC-003). | Report p-value $\ge 0.05$ as a valid scientific outcome. |
| **Selection Bias (2D-only)** | Skewed distribution. | Acknowledge in report; use ETKDG generation for valid 2D SMILES. |
| **Frozen Transformer Under-representation** | Failure to capture signal. | Include ECFP4 baseline comparison. If transformer underperforms, report as limitation. |

## 6. Decision Rationale

-   **Frozen Transformer vs. Fine-tuning**: Frozen weights chosen to reduce parameter count and training time, ensuring the model stays within the 100k trainable parameter limit (FR-005) and fits the CPU budget. The ZINC training domain provides high relevance for organic molecules.
-   **PC_raw vs. CAPE**: PC_raw is the standard target. CAPE is used as a covariate to control for size, avoiding the tautology of defining the target as a function of the predictors.
-   **Permutation Test**: 10,000 shuffles chosen to achieve $p \le 0.0001$ resolution, satisfying FR-016 (superseding Constitution Principle VII).
-   **Bonferroni Correction**: Required for the 3 threshold tests to control family-wise error rate (FR-008).
-   **3D Descriptors as Covariates**: 3D descriptors are included to control for the geometric determinants of PC_raw, allowing the model to isolate the *residual* topological signal from SMILES. The two-stage analysis explicitly measures this residual.
-   **Partial Corration**: Controls for elemental composition (atom counts), distinct from CAPE (size normalization), to ensure the SMILES signal is not a proxy for elemental identity.
-   **Model Capacity**: Justified by power analysis (Cohen's f2) for N≥500. Regularization (L2, Dropout) prevents overfitting.