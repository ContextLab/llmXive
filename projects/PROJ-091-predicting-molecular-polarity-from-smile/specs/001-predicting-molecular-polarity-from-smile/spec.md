# Feature Specification: Predicting Molecular Polarity from SMILES Strings with Machine Learning

**Feature Branch**: `001-predict-molecular-polarity`  
**Created**: 2026-07-13  
**Status**: Draft  
**Input**: User description: "Predicting Molecular Polarity from SMILES Strings with Machine Learning"

## User Scenarios & Testing

### User Story 1 - 2D Descriptor Generation from SMILES (Priority: P1)

The system must parse raw SMILES strings from a standard molecular dataset and compute a comprehensive set of 2D topological descriptors (e.g., connectivity indices, shape descriptors, atom counts) without generating 3D conformers, while explicitly excluding Topological Polar Surface Area (TPSA), TPSA_E, and direct functional group identifiers (SMARTS patterns for specific polar groups like -OH, -C=O) to prevent tautological validation or trivial lookup-table behavior.

**Why this priority**: This is the foundational data pipeline. Without a valid 2D feature matrix derived strictly from 2D topology and excluding target-redundant proxies, no model can be trained, and the core research question (2D vs. 3D information) cannot be addressed. It represents the "minimum viable" data preparation.

**Independent Test**: Can be tested by running the preprocessing script on a small batch of 100 SMILES strings and verifying the output is a numeric matrix where every column corresponds to a defined 2D descriptor, no 3D geometry data is present, and TPSA/functional group counts are absent.

**Acceptance Scenarios**:

1. **Given** a valid SMILES string from the QM9 dataset, **When** the preprocessing module parses it using `rdkit.Chem.Descriptors` and `rdkit.Chem.rdMolDescriptors` (excluding 3D functions and target-correlated proxies), **Then** it outputs a feature vector containing at least 200 2D topological descriptors, zero 3D coordinates, and explicitly excludes TPSA, TPSA_E, and direct functional group identifiers (e.g., SMARTS patterns for -OH, -C=O).
2. **Given** a malformed SMILES string, **When** the preprocessing module attempts parsing, **Then** the system logs the error and skips the record without crashing the batch process.
3. **Given** a batch of SMILES strings, **When** processed, **Then** the peak memory usage remains ≤ 6 GB and the output matrix is saved to disk within 15 minutes.

---

### User Story 2 - 2D‑Only Regression Model Training (Priority: P2)

The system must train a Gradient Boosting Regressor (LightGBM) using only the generated **2D** descriptors to predict quantum‑mechanically calculated dipole moments, ensuring no data leakage from 3D information and using a standard random split (no target binning) for train/test separation.

**Why this priority**: This implements the core predictive engine. It tests the hypothesis that 2D features alone can capture significant variance in dipole moments. It is the primary mechanism for generating the research results.

**Independent Test**: Can be tested by training the model on the training split, evaluating it on the test split, and verifying that the model's performance metrics (R², RMSE) are computed solely against the 2D feature matrix and the target dipole values, with no stratification by target value.

**Acceptance Scenarios**:

1. **Given** the preprocessed 2D feature matrix and target dipole moments, **When** the training pipeline executes with a standard random split (no stratification) and k‑fold cross‑validation, **Then** the model completes training with `num_iterations ≤ 500`, achieves a validation R² ≥ 0.10 (exceeding the null‑model baseline), and logs the optimal hyperparameters to a reproducible configuration file.
2. **Given** the trained model, **When** it predicts on the held‑out test set, **Then** the predictions are strictly based on the 2D descriptor inputs, with no implicit reliance on 3D geometry.
3. **Given** the training process, **When** hyperparameter tuning is performed, **Then** the system logs the optimal parameters (e.g., `num_leaves`, `learning_rate`) to a reproducible configuration file.

---

### User Story 3 - Feature Importance and Sensitivity Analysis (Priority: P3)

The system must apply SHAP (SHapley Additive exPlanations) to quantify the contribution of individual descriptors to the dipole prediction and perform a sensitivity analysis on the feature set stability using bootstrapping to validate the 'strongest signal' claim.

**Why this priority**: This addresses the "which features carry the strongest signal" part of the research question. It provides the interpretability required to understand the physical meaning of the 2D model's success or failure and ensures the results are not artifacts of a single data split.

**Independent Test**: Can be tested by generating a SHAP summary plot and a stability report that shows the consistency of the top 10 SHAP features across 100 bootstrap resamples of the dataset.

**Acceptance Scenarios**:

1. **Given** the trained LightGBM model and the test set, **When** SHAP analysis is executed, **Then** the output identifies the most influential 2D descriptors with their mean absolute SHAP values.
2. **Given** the dataset, **When** the sensitivity analysis bootstraps the dataset multiple times (sample size equal to the full dataset size), **Then** the system reports the Jaccard similarity of the top 10 SHAP features across resamples, requiring a similarity ≥ 0.7 to confirm stability.
3. **Given** the feature importance results, **When** the report is generated, **Then** it explicitly distinguishes between descriptors that are definitionally related (collinear) and frames their joint contribution descriptively rather than claiming independent causal effects.

### Edge Cases

- **Undefined stereochemistry**: If a SMILES string lacks stereochemical specification, the system normalizes it to the most common stereoisomer or flags it for manual review without crashing.
- **Highly flexible molecules**: Molecules with rotatable‑bond count ≥ 5 are identified as flexible; the model still produces predictions, and the error analysis highlights these outliers for separate inspection.
- **NaN descriptor values**: If the 2D descriptor calculation (via RDKit) returns `NaN` for a specific molecule, the system imputes the median value of that descriptor across the batch or drops the record, logging the action.

## Requirements

### Functional Requirements

- **FR-001**: System MUST parse SMILES strings and generate a feature matrix of ≥ 200 2D topological descriptors using `rdkit.Chem.Descriptors` and `rdkit.Chem.rdMolDescriptors` (excluding 3D functions). The system MUST explicitly exclude: (a) TPSA, TPSA_E, and any surface‑area proxies (justified because TPSA is highly correlated with dipole and would bias the 2D‑vs‑3D comparison); (b) direct functional group identifiers (SMARTS patterns for -OH, -C=O, etc.); and (c) any feature with a Pearson correlation |r| > 0.85 **computed only on the training split** to avoid target leakage (See US-1).
- **FR-002**: System MUST train a Gradient Boosting Regressor (LightGBM) on the 2D feature matrix to predict dipole moments, ensuring strict separation between training and test sets using a standard random split (no target binning or stratification) (See US-2).
- **FR-003**: System MUST implement cross‑validation to tune hyperparameters and prevent overfitting, logging all random seeds for reproducibility (See US-2).
- **FR-004**: System MUST apply SHAP analysis to the trained model to quantify the contribution of individual 2D descriptors to the dipole moment prediction (See US-3).
- **FR-005**: System MUST perform a feature‑set stability analysis by bootstrapping the dataset repeatedly (sample size equal to full dataset) and verifying that the top SHAP features remain consistent (Jaccard similarity ≥ 0.7) across resamples (See US-3).
- **FR-006**: System MUST process the QM dataset in batches to ensure peak memory usage remains strictly under **6 GB**. The system MUST implement NaN handling (median imputation or record drop) as a prerequisite for stable batch processing, and MUST include a runtime assertion and a dedicated unit test that asserts no 3D conformer generation functions (e.g., `rdkit.Chem.AllChem.EmbedMolecule`, `Get3DConformer`) are called during the descriptor generation pipeline (See US-1, Edge Cases: NaN handling).
- **FR-007**: System MUST calculate Variance Inflation Factor (VIF) for all generated descriptors, iteratively removing the feature with the highest VIF if VIF > 5.0 until all remaining features have VIF ≤ 5.0, retaining at least **150** descriptors after pruning (See US-3).
- **FR-008**: System MUST detect SMILES strings with undefined stereochemistry, normalize them to the most common stereoisomer or flag them, and record the proportion of such cases (≤ 5 % of total) (See US-1).
- **FR-009**: System MUST identify highly flexible molecules (rotatable‑bond count ≥ 5), still generate predictions, and log them as outliers for downstream error analysis (See US-3).
- **FR-010**: System MUST train a complementary Gradient Boosting Regressor using 3D conformer‑derived descriptors (e.g., 3D autocorrelation, torsion angles) on the same target dipole moments, following the same training‑test split protocol (See US-2).
- **FR-011**: System MUST compare the 2D‑only model against the 3D baseline and report the performance gap (ΔR²) to quantify information loss due to omission of 3D geometry (See US-2).
- **FR-012**: System MUST evaluate each of the top 10 SHAP features individually by training a single‑feature model and recording its R²; these single‑feature R² values must be reported to corroborate SHAP rankings (See US-3).
- **FR-013**: System MUST ensure that any feature with correlation |r| > 0.85 is filtered **only on the training split**; this filter is applied before model training to avoid leakage (See US-1).

### Key Entities

- **Molecule**: A chemical entity represented by a SMILES string and a set of derived 2D descriptors.
- **Dipole Moment**: The target continuous variable (in Debye) derived from QM9 quantum mechanical calculations.
- **Descriptor Matrix**: A numeric table where rows are molecules and columns are 2D topological features.
- **Model**: The trained LightGBM regressor instance mapping descriptors to dipole moments.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The variance explained (R²) by the 2D‑only model is measured against the variance explained by a null model that predicts the mean dipole moment of the training set (See US-2).
- **SC-002**: The contribution of specific 2D descriptors is measured against the SHAP value magnitude to identify the "strongest signal" features (See US-3).
- **SC-003**: The sensitivity of the model to the feature set is measured by the Jaccard similarity of the **top 10** SHAP features across 100 bootstrap resamples (See US-3).
- **SC-004**: The computational feasibility is measured by the total runtime on the GitHub Actions free‑tier runner (CPU only, ≤ 6 h) and peak memory usage (≤ 6 GB) (See US-1, US-2).
- **SC-005**: The methodological validity is measured by an automated unit test that asserts no function in the pipeline calls RDKit's `EmbedMolecule` or `Get3DConformer`, verifying the absence of 3D geometry leakage (See US-1).
- **SC-006**: The proportion of molecules with undefined stereochemistry that are successfully normalized or flagged must be ≤ 5 % (See FR-008).
- **SC-007**: The proportion of identified flexible‑molecule outliers must be reported, and their detection must be reproducible across two independent heuristics (rotatable‑bond count ≥ 5 and a torsional‑flexibility score) with Jaccard similarity ≥ 0.8 (See FR-009).
- **SC-008**: The performance gap ΔR² between the 2D‑only model and the 3D‑baseline model must be reported; a gap ≥ 0.05 is considered evidence of 3D information value (See FR-011).
- **SC-009**: Single‑feature predictive‑power validation: each of the top 10 SHAP features must achieve an individual model R² ≥ 0.02; this confirms that SHAP rankings reflect genuine predictive signal (See FR-012).
- **SC-010**: Peak memory usage during preprocessing must stay ≤ 6 GB (See FR-006).

## Assumptions

- The QM9 dataset is available via `wget`/`curl` from the Maxwell Institute or Zenodo without requiring authentication or paid access.
- The QM9 dataset contains the necessary dipole moment values (target variable) and SMILES strings (source) for all molecules required for the analysis.
- RDKit is available in the GitHub Actions environment with sufficient functionality to compute a broad suite of 2D descriptors without 3D conformer generation.
- The GitHub Actions free‑tier runner provides at least 2 CPU cores and 6 GB of RAM, sufficient for LightGBM training on the sampled dataset.
- The relationship between 2D topological features and dipole moments is empirically testable without requiring random assignment (observational study framing).
- The QM9 dataset's dipole moments are calculated using a consistent quantum mechanical method, ensuring the target variable is homogeneous.
- No GPU acceleration is required or available; all computations must be CPU‑tractable.
- The dataset variables (predictors and outcomes) are fully contained within the QM9 release; no external data sources are needed for the 2D descriptors.
- Schema contracts reside in `tests/contract/` relative to the project root, ensuring compatibility with the `quickstart.md` and `data-model.md` test runners.
