# Research: Comparative Analysis of Molecular Fingerprints for Pesticide Toxicity Prediction

## Research Question
Do Morgan fingerprints (radius=2, 2048 bits), which encode topological context, provide statistically significant better predictive performance for organophosphate toxicity compared to MACCS keys (166 bits), which encode local substructures, when evaluated on the Tox21 dataset using a **5-Fold Cross-Validation** strategy with structural independence constraints?

## Dataset Strategy

The primary dataset is **Tox21**, a collection of compounds with toxicity assay results. The specific source is the Tox21 dataset hosted on HuggingFace.

| Dataset Name | Source URL | Load Method | Notes |
|:--- |:--- |:--- |:--- |
| Tox21 (Raw) | ` | `pandas.read_csv` | Contains SMILES and 12 toxicity endpoints. Used for filtering. |
| Tox21 (Alternative) | ` | `pandas.read_csv` | Fallback if primary URL is unreachable. |

**Variable Fit Verification**:
- **SMILES**: Present in Tox21. Required for fingerprint generation.
- **Toxicity Labels**: Present (12 endpoints). Required for supervised learning.
- **Organophosphate Filter**: The dataset must be filtered using the SMARTS pattern `[P](=O)([O,SC])[O,SC]`.
- **Missing Data Handling**: The Tox21 dataset contains missing values (NaN) for some endpoints. The plan will implement a strategy of either dropping rows with missing labels for a specific endpoint or imputing with the mode, depending on the missingness ratio, to ensure balanced classes where possible.

**Dataset Limitations**:
- The dataset is observational. No causal claims will be made.
- Measurement uncertainty (standard deviation) of the original assays is not provided in the dataset metadata. Per the "Assumptions" in the spec, assay uncertainty is treated as inherent and not recalculated. The analysis focuses on the relative performance of fingerprints, not absolute toxicity thresholds.

## Methodology

### 1. Data Preprocessing
- **Filtering**: Apply SMARTS pattern `[P](=O)([O,SC])[O,SC]` to isolate organophosphates.
- **5-Fold Cross-Validation with Greedy Splitting**:
 - The dataset will be split into 5 folds.
 - For **each fold**, a **Greedy Maximal Dissimilarity Split** will be performed:
 - Sort compounds by a random seed.
 - Iteratively assign compounds to the test set only if their maximum Tanimoto similarity to *any* compound currently in the training set is **< 0.85**.
 - Target split ratio: [deferred] train / [deferred] test.
 - **Edge Case**: If the test set size < 20 samples for any fold, the pipeline halts and reports "Insufficient Structural Diversity".
 - **Applicability Domain Check**: For each fold, calculate and report the **distribution of Tanimoto similarities** (mean, max, min, histogram) between the training and test sets. If the mean similarity is < 0.2, a warning is issued regarding potential performance collapse due to excessive structural divergence.

### 2. Feature Generation
- **Morgan Fingerprints**: Radius=2, 2048 bits, using `rdkit.Chem.AllChem.GetMorganFingerprintAsBitVect`.
- **MACCS Keys**: 166 bits, using `rdkit.Chem.rdMolDescriptors.GetMACCSKeysFingerprint`.
- **Bit-to-Substructure Mapping (SC-003)**:
 - Use `rdkit.Chem.AllChem.GetMorganFingerprintAsBitVect` with `bitInfo` to generate a mapping of bit indices to atom indices and radii.
 - Identify bits corresponding to subgraphs centered on Phosphorus (P) atoms within radius 2.
 - Store this mapping to enable aggregation of Gini importance for "P-center bits" vs. "non-P-center bits".

### 3. Model Training
- **Algorithm**: Random Forest Classifier.
- **Hyperparameters**: `n_estimators=100`, `max_depth=15`, `random_state=42`.
- **Constraints**: CPU-only execution. No GPU acceleration.
- **Class Imbalance**: If a toxicity endpoint has a positive:negative ratio > 10:1, use `class_weight='balanced'` and report Balanced Accuracy.
- **Loop**: Train one model per fingerprint type per fold per endpoint.

### 4. Statistical Evaluation
- **Metric**: **ROC-AUC** (primary), **Precision-Recall AUC** (PR-AUC), and **Balanced Accuracy** (secondary).
- **Comparison**:
 - **Corrected Resampled t-test (Nadeau & Bengio)**: Applied to the 5-fold CV scores (one score per fold). The Nadeau & Bengio correction adjusts the variance estimate to account for the correlation between training sets in cross-validation, preventing inflated Type I error rates.
 - **Bootstrap Confidence Intervals**: 1,000 resamples of the 5-fold CV scores to derive a 95% CI for the performance difference (Morgan - MACCS).
 - **Significance Threshold**: p < 0.05.
- **Sample Size Check**: If n < 50 (organophosphate subset), flag "Low Sample Size" and skip the t-test, reporting only descriptive statistics.

### 5. Feature Importance Analysis (SC-003)
- **Metric**: Sum of Gini importance for Morgan bits identified as "P-center" (from Step 2) vs. the sum of Gini importance for all other bits.
- **Hypothesis**: The predictive power of Morgan fingerprints for organophosphates is driven significantly by the topological context around the phosphorus atom.
- **Method**: Aggregate Gini importance across all 5 folds for the identified P-center bits. Compare the aggregated importance to the average importance of non-P-center bits. Report the ratio and statistical significance if applicable.

## Decision/Rationale

**Why Random Forest?**
Random Forests are robust to high-dimensional sparse data (fingerprints) and do not require GPU acceleration, fitting the 7GB RAM/2 CPU constraint. They provide feature importance scores which are necessary for the "Feature Importance Distribution" success criterion (SC-003).

**Why 5-Fold CV with Nadeau & Bengio?**
A single split is insufficient for the Nadeau & Bengio correction, which requires repeated samples to estimate variance properly. 5-Fold CV provides the necessary repeated samples (5 distinct train/test pairs) while maintaining the structural independence constraint (Tanimoto < 0.85) in each fold. This satisfies Constitution Principle VII.

**Why Tanimoto < 0.85?**
This threshold is a standard in cheminformatics for scaffold splitting. It ensures that the test set contains structurally distinct molecules, testing the model's ability to generalize to new chemical space rather than memorizing similar structures. The added "Applicability Domain Check" ensures we do not split so aggressively that the test set becomes unlearnable.

**Addressing Reviewer Concerns (marie-curie-simulated)**:
- **Measurement Uncertainty**: The plan acknowledges that the standard deviation of toxicity measurements is not available in the dataset. The analysis focuses on *relative* model performance (AUC difference) rather than absolute toxicity prediction accuracy. This mitigates the impact of unknown assay noise on the comparative conclusion.
- **Calibration**: The RDKit library is the industry standard. The plan explicitly fixes the random seed and parameters to ensure reproducibility, serving as the "calibration" for the algorithmic implementation.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Low Organophosphate Count** | Study fails statistical power. | Check count early; if < 50, switch to descriptive analysis and report limitation. |
| **Memory Overflow** | Pipeline crashes on CI. | Implement chunked fingerprint generation (batch size 500) if RAM > 6GB. |
| **Structural Homogeneity** | Cannot achieve Tanimoto < 0.85 split. | Halt execution; report "Insufficient Structural Diversity". Do not relax threshold. |
| **Class Imbalance** | Model biased to majority class. | Use stratified sampling and `class_weight='balanced'`; report Balanced Accuracy. |
| **Excessive Structural Divergence** | Test set too dissimilar (Mean Tanimoto < 0.2). | Report "Applicability Domain Warning"; do not relax threshold but interpret results with caution. |