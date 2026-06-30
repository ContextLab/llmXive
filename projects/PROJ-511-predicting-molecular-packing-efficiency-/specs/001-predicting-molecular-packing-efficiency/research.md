# Research: Predicting Molecular Packing Efficiency in Crystals from SMILES Representations

## Research Question
Can a lightweight regression model, trained on frozen SMILES-transformer embeddings **alone**, predict the **Composition-Adjusted Packing Efficiency (CAPE)** of organic crystals with statistical significance (r ≥ 0.4, p ≤ 0.05)? Additionally, what is the specific contribution of SMILES topology compared to 3D geometric descriptors?

## Dataset Strategy

The project relies on the **Crystallography Open Database (COD)** for source data. Per Constitution Principle VI, data must be sourced directly from COD.

**Verified Sources & Loading Strategy:**
- **Primary Source**: Crystallography Open Database (COD) - **Organic Subset**.
 - **URL**: ` (Official Mirror for Organic Subset).
 - **Loading Method**: The pipeline downloads the pre-filtered organic subset (approx. 50-100MB) and filters locally for ≤50 non-H atoms. This avoids downloading terabytes of inorganic data.
 - **Filter**: Organic molecules, ≤50 non-H atoms.
 - **Provenance**: `data_provenance.json` records the exact URL, version, and checksum to satisfy FR-017.

**Gap Analysis:**
- The verified block does not contain a direct link to the raw COD CIF archive. The plan uses the official COD Organic Subset URL as per FR-017.
- **SMILES**: Required. COD entries often lack this tag. Strategy: Generate via RDKit from 3D coordinates (FR-002).
- **Packing Coefficient**: Required. Derived from Unit Cell Volume and VdW volumes (FR-003).
- **3D Geometry**: Required. Derived from CIF coordinates (FR-012).
- **Confounders**: Lattice system, temperature, solvent. Must be present in CIF metadata (FR-013).

## Feature Engineering Strategy

1. **SMILES Embeddings**:
 - Model: Pre-trained SMILES Transformer (frozen).
 - Rationale: Captures topological connectivity.
 - Constraint: Runs on CPU; inference only. **Batched** to fit 7GB RAM.

2. **3D Geometric Descriptors** (FR-012):
 - Radius of Gyration ($R_g$): Measures compactness.
 - Asphericity: Measures deviation from spherical shape.
 - Principal Moments of Inertia: Captures shape anisotropy.
 - *Source*: Calculated from 3D coordinates in CIF using RDKit.

3. **Composition-Adjusted Packing Efficiency (CAPE)** (FR-011):
 - Formula: $\text{CAPE} = \frac{\text{PC}}{\frac{1}{N_{atoms}}\sum V_{vdW}}$.
 - Rationale: Normalizes for molecular size.
 - **Critical Note**: For all CAPE models (Baseline, Control, Upper Bound), the features `sum_vdw_volume` and `n_atoms` are **excluded** from the input to prevent the model from trivially learning the denominator of the target.

4. **Confounders** (FR-013):
 - Categorical: Lattice system (One-hot encoded).
 - Continuous: Temperature (K).
 - Binary: Solvent presence.

## Statistical Methodology

1. **Models**:
 - **Baseline**: 2-layer MLP (≤100k params) on **SMILES embeddings ONLY** to predict **CAPE**.
 - **Control**: 2-layer MLP on **3D descriptors ONLY** to predict **CAPE**.
 - **Upper Bound**: 2-layer MLP on **SMILES + 3D Descriptors** (excluding denominator terms) to predict **CAPE**.

2. **Significance Testing** (FR-006, FR-016):
 - Metric: Pearson $r$ and Spearman $\rho$.
 - Test: Conditional Permutation Test.
 - Stage 1: [deferred] shuffles.
 - If $p \ge 0.05$: Report $p$ and stop.
 - If $p < 0.05$: Run full [deferred] shuffles to achieve $p$-value resolution of 0.0001.
 - Null Hypothesis: No relationship between features and target.
 - P-value: Proportion of permuted correlations ≥ observed correlation.

3. **Robustness** (FR-007, FR-008):
 - Sweep thresholds: {, 0.6, 0.7}.
 - Correction: Bonferroni (alpha / k) for the k tests.

4. **Diagnostics** (FR-009, FR-014, FR-015):
 - VIF: Flag multicollinearity (VIF > 5).
 - Partial Correlation: Control for atom-type composition.
 - Normality: Shapiro-Wilk on residuals.
 - **Residual Spearman**: Compute Spearman's $\rho$ specifically on the residuals of the CAPE model.

## Decision Rationale

- **CPU-Only**: The spec and CI constraints forbid GPU. The model is lightweight (MLP) to ensure feasibility.
- **Frozen Transformer**: Training a transformer from scratch is infeasible on CPU with this data size. Frozen weights provide robust embeddings.
- **Three-Model Strategy**: The Baseline model isolates the SMILES signal. The Control model isolates the 3D signal. The Upper Bound model shows the combined potential. This separation resolves the concern that 3D features might dominate the signal, ensuring the primary research question (SMILES -> CAPE) is answered by the Baseline, while the Control quantifies the confounding 3D effect.
- **Circularity Resolution**: By excluding `sum_vdw_volume` and `n_atoms` from all CAPE model inputs, we prevent the model from simply re-calculating the target formula.
- **SMILES Generation**: Since COD lacks SMILES for many entries, generating them from 3D coordinates is the only valid strategy to meet the "SMILES-based" requirement without discarding data.
- **Permutation Test Logic**: The conditional test ensures that any claim of significance (p < 0.05) is supported by high-resolution data (10k shuffles), addressing the concern about marginal significance and computational cost.
