# Research: Predicting Molecular Toxicity from Structural Alerts via Rule-Based Systems

## Dataset Strategy

To satisfy FR-001 and the dataset variable fit requirement, we require a dataset containing:
1.  **SMILES strings** (to derive structural alerts and descriptors).
2.  **Binary mutagenicity labels** (active/inactive) for supervised learning.
3.  **Sufficient sample size** (N > 1000) for stratified cross-validation.

**Selected Dataset**: ToxCast (MoleculeNet subset)  
**Source URL**: https://huggingface.co/datasets/scikit-fingerprints/MoleculeNet_ToxCast/resolve/main/toxcast.csv  
**Rationale**: This dataset is verified in the input block, contains SMILES and binary activity labels, and is widely used in cheminformatics benchmarks. It aligns with the spec's requirement for a public mutagenicity dataset. The "PubChem BioAssay AID 1851" mentioned in the spec is a specific assay within the broader ToxCast/Tox21 programs; the MoleculeNet subset provides a pre-curated, clean version of this data suitable for immediate use without complex API scraping, ensuring reproducibility (Constitution Principle I).

**Dataset Verification**:
-   **SMILES**: Present in the `smiles` column.
-   **Label**: Present in the `active` column (binary).
- **Size**: [deferred] compounds (sufficient for 5-fold CV repeated 3 times).
-   **Fit**: The dataset contains the necessary structural information to derive both feature sets and the outcome variable is independent of the derivation.

**Alternative Considered**: PubChem BioAssay (AID 1851) via API.  
**Rejection**: API scraping introduces non-determinism (rate limits, changes in response format) and complexity. The HuggingFace MoleculeNet subset is a static, checksummable artifact that better satisfies the Reproducibility principle.

## Feature Engineering Strategy

### Structural Alerts (Rule-Based)
-   **Source**: Curated `config/structural_alerts.json`.
-   **Patterns**: Must include at least 10 distinct toxicophores (e.g., nitroaromatics, epoxides, primary aromatic amines) as per FR-003.
-   **Logic**: For each molecule, generate a binary vector where `1` indicates the presence of the SMARTS pattern.
-   **Weighting**: Sum of weights (default 1.0) to produce a risk score.
-   **Constraint**: Patterns are treated as independent; no interaction terms are modeled (per Assumptions).

### Global Descriptors (Data-Driven)
-   **Source**: `rdkit.Chem.Descriptors`.
-   **Selection**: **Fixed, pre-defined set of 20 descriptors** (e.g., MW, LogP, TPSA, NumHDonors, NumHAcceptors, etc.) based on literature precedence.
-   **Rationale**: We explicitly avoid selecting the "first 20 non-correlated" based on a global correlation matrix to prevent data leakage (look-ahead bias). The set is fixed a priori and remains identical across all CV folds, ensuring the model definition is stable and the comparison fair.
-   **Preprocessing**: StandardScaler (zero mean, unit variance) applied to the training folds only to prevent data leakage.

## Model Strategy

### Rule-Based Scoring Model
-   **Method**: Deterministic scoring.
-   **Input**: Binary alert vector.
-   **Output**: Risk score (sum of weights).
-   **ROC-AUC Calculation**: Threshold is swept over the **entire continuous range** of possible scores (0 to K) to generate a smooth ROC curve. This ensures an accurate, threshold-independent AUC metric comparable to Logistic Regression.
-   **F1/Recall Calculation**: Thresholds swept over discrete values (0.3, 0.5, 0.7) **only** for error analysis and F1 reporting, not for the primary AUC metric.
-   **Evaluation**: ROC-AUC, F1-score, Recall.

### Logistic Regression Model
-   **Method**: `sklearn.linear_model.LogisticRegression`.
-   **Input**: Scaled global descriptors (fixed set of 20).
-   **Validation**: 5-fold stratified cross-validation, repeated 3 times (15 total folds).
-   **Regularization**: L2 penalty (default) to prevent overfitting on small descriptors.
-   **ROC-AUC Calculation**: Threshold swept over [0, 1] continuous range.
-   **Evaluation**: ROC-AUC, F1-score, Recall.

## Statistical Analysis Strategy

### Hypothesis Test
-   **Test**: DeLong's test for comparing two correlated ROC curves.
-   **Null Hypothesis ($H_0$)**: The ROC-AUC of the rule-based model is equal to the ROC-AUC of the descriptor-based model.
-   **Alternative Hypothesis ($H_1$)**: The ROC-AUCs are different.
-   **Data Source**: **Out-of-Fold (OOF) predictions**. For each instance in the dataset, we collect exactly one predicted probability from the fold where that instance was held out. We **do NOT average** predictions across folds for this test, as averaging invalidates the covariance estimation required by DeLong's test.
-   **Correction**: No multiple-comparison correction applied (FR-009) as only one primary hypothesis is tested.
-   **Output**: P-value and 95% Confidence Interval.
-   **Decision Rule**: If $p < 0.05$, reject $H_0$ and claim statistical significance.

### Recall Comparison (SC-002)
-   **Metric**: Difference in Recall (Descriptor Recall - Rule Recall).
-   **Threshold**: 5%.
-   **Decision**: If difference > 5%, the descriptor model provides a "marginal gain" in recall.

### Power Consideration
-   **Limitation**: If the dataset size is small (N < 200), the power of DeLong's test may be low. The final report will explicitly state this limitation if the effective sample size after filtering is small.

## Error Analysis Strategy

### False Negative Identification (SC-003)
-   **Target**: Compounds labeled "active" (mutagenic) but predicted "inactive" by the rule-based model.
-   **Method**: Extract Murcko scaffolds from these false negatives.
-   **Measurement**:
    1.  Count total False Negatives (FN).
    2.  Count unique missing structural motifs (scaffolds) identified in FNs.
    3.  Compare FN count vs. Motif count to determine feasibility of rule-set expansion.
-   **Output**: Frequency distribution of top 10 unique scaffolds and the specific count comparison.
-   **Goal**: Identify missing toxicophores (e.g., "sulfonamides") to inform future rule updates (US-3).

## Compute Feasibility & Constraints

-   **Hardware**: GitHub Actions free-tier (2 CPU, 7 GB RAM).
-   **Memory Management**:
    -   Data is loaded in chunks if > 1GB.
    -   Feature matrices are stored as `float32` to reduce memory footprint.
    -   Only the necessary subset of molecules is kept in memory during model training.
-   **Runtime**:
    -   SMILES standardization: O(N).
    -   SMARTS matching: O(N * K) where K=10 patterns (fast).
    -   Descriptor calculation: O(N * C) (fast), where C represents a constant number of features.
    -   Model training: multiple folds * Logistic Regression (fast on CPU).
    -   **Estimated Total Runtime**: < 2 hours.
-   **No GPU**: All operations are CPU-native (RDKit, Scikit-learn).