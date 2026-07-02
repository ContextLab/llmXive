# Feature Specification: Predicting Molecular Conductivity from Graph-Based Features

**Feature Branch**: `001-predict-molecular-conductivity`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: "$ARGUMENTS"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Load molecular structures and compute graph-based descriptors (Priority: P1)

A researcher uploads or downloads a dataset of organic molecules in SMILES format and obtains a structured table of graph-based topological descriptors for each molecule, including conjugation length, aromatic ring count, degree distribution statistics, and average path length.

**Why this priority**: This is the foundational data preparation step. Without valid descriptors computed from the molecular graph, no predictive analysis can proceed. This story delivers the core data transformation that enables all downstream modeling.

**Independent Test**: Can be fully tested by running the descriptor computation pipeline on a sample of SMILES strings and verifying that the output table contains all required descriptor columns with valid numeric values for each molecule.

**Acceptance Scenarios**:

1. **Given** a CSV file containing 500 SMILES strings in a column named "smiles", **When** the descriptor computation script is executed, **Then** an output CSV is produced with 500 rows and at least 10 descriptor columns including aromaticity index, conjugation path length, and ring count.
2. **Given** a SMILES string representing a molecule with aromatic rings (e.g., "c1ccccc1"), **When** descriptors are computed, **Then** the aromaticity index is non-zero and the aromatic ring count is ≥ 1.
3. **Given** a SMILES string with invalid syntax, **When** descriptor computation is attempted, **Then** the molecule is logged as an error and excluded from the output table with a clear error message.

---

### User Story 2 - Train regression models and evaluate predictive performance (Priority: P2)

A researcher splits the dataset into train/test sets using molecular scaffold splitting, trains Random Forest and Gradient Boosting regressors to predict log-transformed conductivity values, and obtains performance metrics including R², mean absolute error, and 5-fold cross-validation scores on the test set.

**Why this priority**: This is the core predictive modeling step that directly addresses the research question. It produces the quantitative evidence needed to determine whether graph topology correlates with conductivity.

**Independent Test**: Can be fully tested by running the training pipeline on a fixed dataset and verifying that both models produce R² scores, MAE values, and cross-validation metrics in a structured results file.

**Acceptance Scenarios**:

1. **Given** a dataset of 1000 molecules with conductivity values, **When** the training pipeline is executed with an 80/20 scaffold split, **Then** both Random Forest and Gradient Boosting models are trained and their test set R² and MAE are recorded in a JSON results file.
2. **Given** the same dataset, **When** 5-fold cross-validation is performed on the training set, **Then** mean and standard deviation of R² across folds are computed and stored.
3. **Given** a test set containing molecules not seen during training, **When** predictions are generated, **Then** all predicted conductivity values are finite numbers without NaN or infinity.
4. **Given** a dataset with outliers, **When** the training pipeline is executed, **Then** the system performs a sensitivity analysis sweeping the outlier exclusion threshold over {2.5σ, 3.0σ, 3.5σ} and reports the variance in model R² across these cutoffs.

---

### User Story 3 - Generate feature importance analysis and correlation plots (Priority: P3)

A researcher obtains a ranked list of topological features by predictive importance and generates correlation plots showing the relationship between key descriptors (conjugation length, aromatic ring count) and conductivity with 95% confidence intervals.

**Why this priority**: This delivers the interpretability layer that answers which features drive predictions. It transforms raw model performance into scientific insight about structure-property relationships.

**Independent Test**: Can be fully tested by running the analysis script on a trained model and verifying that feature importance rankings are exported and correlation plots are generated as image files.

**Acceptance Scenarios**:

1. **Given** a trained Random Forest model on molecular descriptors, **When** feature importance analysis is run, **Then** a ranked CSV file is produced listing all descriptors sorted by importance with numeric scores.
2. **Given** the top 5 features by importance, **When** correlation plots are generated, **Then** PNG images are created showing scatter plots with regression lines and 95% confidence intervals for each feature vs. conductivity.
3. **Given** the feature importance results, **When** the top 3 features are identified, **Then** their names and importance scores are logged in the analysis summary.
4. **Given** a set of feature-conductivity correlations, **When** statistical analysis is performed, **Then** the system applies Benjamini-Hochberg false discovery rate correction and reports adjusted p-values.

---

### Edge Cases

- What happens when the dataset contains molecules with missing conductivity values? → These are excluded from training with a warning count logged.
- How does the system handle molecules with extreme conductivity values (outliers beyond 3 standard deviations)? → The system executes a mandatory sensitivity analysis sweeping the outlier exclusion threshold over a range of standard deviation multiples and reports how model R² varies across these cutoffs.
- What happens when all molecules in a scaffold split have identical conductivity values? → The split is rejected with an error and the random seed is advanced for retry.
- How does the system handle resonance-related structural features not captured by basic graph topology? → The system includes aromaticity indices (e.g., Hückel aromaticity, number of aromatic rings) and topological conjugation path lengths as proxies for resonance-related electronic delocalization. If quantum-derived descriptors (e.g., HOMO-LUMO gap) are missing from the dataset, the system falls back to these topological proxies and logs a warning that quantum validation is pending. If *both* the proxy and primary data are missing or invalid for a specific molecule, that molecule is excluded from the analysis.
- What happens when a molecule lacks required quantum-derived descriptors? → The system defaults to topological proxy mode (as per FR-014) and logs a warning. The molecule is only excluded if the topological proxy computation also fails or yields invalid values.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST parse SMILES strings into molecular graphs using RDKit and compute at least 10 graph-based descriptors including degree distribution, average path length, ring count, longest conjugated path length (defined as the longest simple path in the subgraph induced by conjugated bonds), and aromaticity indices (See US-1)
- **FR-002**: System MUST implement molecular scaffold splitting for train/test partitioning with an approximate majority/minority ratio to prevent data leakage from structurally similar molecules (See US-2)
- **FR-003**: System MUST train both Random Forest and Gradient Boosting regressors on log-transformed charge carrier mobility (cm²/V·s) or intrinsic conductivity of doped states as the target variable, ensuring the dataset contains a non-trivial dynamic range (≥ 3 orders of magnitude) (See US-2)
- **FR-004**: System MUST evaluate model performance using R², mean absolute error, and k-fold cross-validation on the test set (See US-2)
- **FR-005**: System MUST output feature importance rankings and generate correlation plots with confidence intervals for the top 5 descriptors (See US-3)
- **FR-006**: System MUST implement Benjamini-Hochberg false discovery rate correction when reporting multiple feature-conductivity correlations to control family-wise error (See US-3)
- **FR-007**: System MUST perform a sensitivity analysis sweeping the outlier exclusion threshold over a range of standard deviation multiples and report how model R² varies across these cutoffs. (See US-2)
- **FR-008**: System MUST include aromaticity descriptors that capture resonance-related structural features as recommended by reviewer linus-pauling-simulated (See US-1)
- **FR-009**: System MUST run all computations on CPU-only infrastructure without GPU/CUDA dependencies (See US-1, US-2, US-3)
- **FR-010**: System MUST complete the full analysis pipeline within 6 hours on a 2-core, 7 GB RAM runner (See US-1, US-2, US-3)
- **FR-011**: System MUST validate that the target variable (conductivity) has a non-trivial dynamic range (≥ 3 orders of magnitude) before training (See US-2)
- **FR-012**: System MUST exclude molecules with missing conductivity values or invalid descriptors from the training set (See US-1)
- **FR-013**: System MUST calculate Variance Inflation Factor (VIF) for all predictor pairs; if any feature has VIF > 10, it MUST be excluded from the final importance ranking, and the model MUST be retrained on the reduced feature set (See US-3)
- **FR-014**: System MUST include at least one quantum-derived descriptor (e.g., HOMO-LUMO gap) if available in the dataset; if not, it MUST fall back to topological proxies and log a warning regarding the limitation (See US-1, US-3)

### Key Entities

- **Molecule**: A chemical compound with SMILES string identifier, computed graph descriptors, and measured conductivity value
- **Descriptor**: A numeric topological feature computed from the molecular graph (e.g., aromaticity index, conjugation length, ring count)
- **Model**: A trained regression model (Random Forest or Gradient Boosting) mapping descriptors to log-conductivity predictions
- **PerformanceMetric**: A quantitative measure of model fit (R², MAE, cross-validation score) computed on held-out test data

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Model R² on test set is measured against the baseline of random prediction (R² = 0) to quantify predictive power (See US-2)
- **SC-002**: Feature importance rankings are measured against permutation importance scores to verify that top descriptors are robust to feature shuffling (See US-3)
- **SC-003**: Correlation confidence interval coverage is measured against the [deferred] nominal coverage target to verify statistical calibration (See US-3)
- **SC-004**: Family-wise error rate is measured against 0.05 threshold after Benjamini-Hochberg correction to verify multiplicity control (See US-3)
- **SC-005**: Pipeline execution time is measured against the 6-hour limit to verify compute feasibility on free-tier CI (See US-1, US-2, US-3)
- **SC-006**: Sensitivity analysis R² variance across outlier thresholds is measured to verify model robustness to preprocessing choices (See US-2)
- **SC-007**: Collinearity diagnostics (VIF scores) are measured for all predictor pairs to verify no spurious independent effects are claimed for definitionally related features (See US-3)
- **SC-008**: Dependent feature pairs (VIF > 10) are reported, and the final importance ranking excludes these features to ensure statistical independence (See US-3)
- **SC-009**: The presence or absence of quantum-derived descriptors is measured and reported to verify theoretical validity of the proxy approach (See US-1, US-3)

## Assumptions

- The Materials Project or PubChem dataset contains both molecular SMILES strings AND measured or DFT-derived conductivity values (charge carrier mobility or intrinsic conductivity of doped states) for the same molecules; if conductivity is missing for a compound, it is excluded from analysis
- Graph-based descriptors computed by RDKit (aromaticity, conjugation, ring systems) are sufficient proxies for electronic delocalization without requiring quantum mechanical calculations, provided a fallback warning is logged
- All molecular conductivity values are positive numbers that can be log-transformed; zero or negative conductivity values are excluded from the dataset
- The random forest and gradient boosting models will fit within 7 GB RAM when trained on a dataset of up to 5000 molecules with 10-20 descriptors each
- The analysis is observational and associative only; no causal claims about topology causing conductivity are made without randomization or identification strategy
- Aromaticity and resonance-related features will be included in the descriptor set as per reviewer feedback; if the dataset lacks resonance energy measurements, aromaticity indices serve as proxies
- The 80/20 train/test split with scaffold splitting will produce ≥ 100 molecules in the test set to support meaningful performance evaluation
- No GPU acceleration is available or required; all models run in default precision on CPU cores
- The target variable (conductivity) exhibits a non-trivial dynamic range (≥ 3 orders of magnitude) in the source dataset, ensuring the regression problem is not dominated by noise