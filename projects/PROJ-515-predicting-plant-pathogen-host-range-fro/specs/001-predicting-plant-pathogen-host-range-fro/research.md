# Research: Predicting Plant Pathogen Host Range from Genomic Data

## 1. Scientific Background & Rationale

Predicting host range is critical for biosecurity and crop protection. Current methods rely on manual literature review or limited experimental data. Genomic signatures (effectors, secondary metabolites) are hypothesized to correlate with host range breadth. This project tests whether a logistic regression model trained on these features can predict infection likelihood with >0.70 AUPRC.

**Key Hypothesis**: Pathogens with higher counts of specific effector families and secondary metabolism clusters possess broader host ranges.

## 2. Dataset Strategy

### 2.1. Pathogen Genomes (FR-001)
*   **Source**: NCBI GenBank.
*   **Selection**: A diverse set of plant pathogens (fungi, oomycetes, bacteria) with complete genomes.
*   **Access**: Downloaded via `Entrez` (BioPython) using accession list.
*   **Constraint**: Must be high-quality assemblies (no fragmented drafts).

### 2.2. Host-Pathogen Interactions (FR-002)
*   **Primary Source**: PHI-base (Pathogen-Host Interactions).
*   **Supplemental**: Interactome3D, NCBI BioSample.
*   **Data Format**: Binary matrix (Pathogen ID × Host ID).
*   **Missing Data Handling (FR-013)**: Missing entries are treated as 'unknown' (excluded from training labels), not false negatives.
*   **Gap Analysis**: If a pathogen has 0 interactions after merging sources, the pipeline halts for that pathogen (FR-011).

> **Verified Datasets Note**: The "Verified datasets" block provided for this project does **not** contain URLs for NCBI GenBank, PHI-base, or Interactome3D. These are standard public repositories. The plan adheres to the rule: *Do NOT fabricate a URL*. We will use the official programmatic interfaces (NCBI Entrez, PHI-base FTP/API) as the "verified source" by referencing their official documentation.

### 2.3. Feasibility & Data Strategy (Pre-computed Cache)
*   **Constraint**: The full feature extraction (EffectorP, antiSMASH) is computationally intensive and may exceed the standard CI runtime.
*   **Strategy**: 
    1.  **Offline Pre-computation**: Run the full feature extraction pipeline on a high-performance node (outside CI) for the full -pathogen dataset.
    2.  **Commit to Repository**: Save the resulting feature vectors to `data/raw/` with checksums. These vectors are the "Single Source of Truth" for features.
    3.  **CI Validation**: The CI pipeline consumes these pre-computed vectors and runs the modeling/evaluation steps. This satisfies SC-004 (full pipeline logic validated on full dataset) within the CI limit.
*   **Validity**: No proxies (e.g., motif counters) are used. The features are derived from the official tools (EffectorP 3.0, antiSMASH 7.0) as required by FR-003. If the pre-computed cache cannot be generated, the project scope must be reduced or the hypothesis abandoned.

## 3. Methodological Rigor

### 3.1. Statistical Design
*   **Model**: L2-regularized Logistic Regression (scikit-learn).
*   **Validation**: 5-fold Cross-Validation (inner) for hyperparameter tuning; Independent Hold-out set (a subset of pathogens) for final evaluation (FR-012).
*   **Metric**: AUPRC (Area Under Precision-Recall Curve) due to class imbalance.
*   **Significance**: Permutation testing (sufficient iterations for robust inference) with Benjamini-Hochberg FDR correction (FR-006).
*   **Collinearity**: Variance Inflation Factor (VIF) analysis (threshold ≥ 5) performed **strictly within the training fold** of the cross-validation loop (FR-014).
*   **Dimensionality Reduction**: PCA is applied to k-mer features **strictly within the training fold**, retaining components that explain >= 95% of the variance. VIF is then calculated on the reduced features.

### 3.2. Sample Size & Power Analysis
*   **Assumption**: 50 pathogens.
*   **Power Calculation**: With N=50 (A moderate number of training iterations., 10 hold-out) and feature categories (plus reduced k-mers), the power to detect a medium effect size (Cohen's d = 0.4) at alpha=0.05 is approximately **45%**.
*   **Mitigation**: 
    *   The study is framed as **Exploratory**. The primary goal is to generate hypotheses and rank feature importance, not to claim definitive p-values.
    *   Effect sizes (Cohen's d) are reported alongside p-values to contextualize the low power.
    *   Strict regularization (L2) and nested feature selection (PCA+VIF) are used to minimize overfitting.
*   **Limitation**: The low power increases the risk of false negatives (Type II errors). Non-significant features should be interpreted as "not detected with current sample size" rather than "no effect".

### 3.3. Causal vs. Associational
*   **Observational**: The study is observational. Claims are strictly **associational** (e.g., "Feature X is associated with host range"). No causal inference is claimed.

### 3.4. Multiple Comparison Correction
*   **Method**: Benjamini-Hochberg FDR at α = 0.05.
*   **Scope**: Applied to the 5 feature categories (Effector, Pfam, GC, k-mer, SM) and individual features within categories.

### 3.5. Host-Range Breadth & Known Host Universe Limitation
*   **Definition**: 'Host-Range Breadth' (FR-017) is defined as the mean predicted infection probability across all unique hosts in the reference interaction matrix.
*   **Ground Truth**: The 'Observed Host-Range Breadth' (ground truth) is the count of *unique known hosts* in the interaction matrix for a pathogen.
*   **Limitation**: The model predicts 'likelihood of infecting known hosts'. The 'Predicted Breadth' is a proxy for 'True Biological Breadth'. Validation against an external 'True Breadth' (e.g., experimental inoculation) is not possible with this dataset. The plan explicitly acknowledges this limitation: the model validates *recall of known interactions*, not the absolute extent of biological host range.

## 4. Risk Assessment & Mitigation

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Dataset Mismatch** | Fatal: Required variables missing. | Pre-check: Script to verify NCBI entries. If missing, log error and skip (FR-011). |
| **Runtime Exceeded** | High: Full tools take >5h. | **Pre-computed Cache**: Heavy extraction done offline; CI runs modeling on cached vectors. |
| **Class Imbalance** | High: Few positive interactions. | Use AUPRC; stratified CV; class weights in Logistic Regression. |
| **Collinearity** | High: k-mer frequencies correlated. | **Nested PCA + VIF**: PCA (% variance) then VIF (threshold 5) strictly within CV folds. |
| **Missing Data** | Medium: Many interactions unknown. | Treat as 'unknown' (FR-013); report missingness % in Data-Quality Report (FR-013). |
| **Low Power** | High: Small sample size. | Frame as exploratory; report effect sizes; use strict regularization. |

## 5. Decision Log

1.  **Decision**: Use Pre-computed Feature Cache.
    *   **Rationale**: Ensures construct validity (EffectorP 3.0, antiSMASH 7.0) while meeting CI time limits. No proxies used.
2.  **Decision**: Treat missing interactions as 'unknown'.
    *   **Rationale**: Absence of evidence is not evidence of absence (FR-013). Treating as negative would introduce massive bias.
3.  **Decision**: Use L2 Regularization only.
    *   **Rationale**: L1 (Lasso) may zero out too many features in small N settings; L2 provides stable coefficients for interpretability.
4.  **Decision**: Nested PCA + VIF.
 * **Rationale**: Prevents data leakage. PCA ([deferred] variance) reduces k-mer dimensionality; VIF removes collinear features. Both done strictly within training folds.
5.  **Decision**: Exploratory Framing.
    *   **Rationale**: Acknowledges low power (N=50) and frames results as hypothesis-generating with effect size reporting.
6.  **Decision**: 'Known Host Universe' Limitation.
    *   **Rationale**: Explicitly acknowledges that 'Predicted Breadth' is a proxy for 'True Breadth' and cannot be validated against external experimental data.