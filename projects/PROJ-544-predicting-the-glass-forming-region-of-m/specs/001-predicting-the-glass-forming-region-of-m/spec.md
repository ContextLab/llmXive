# Feature Specification: Predicting the Glass Forming Region of Multi-Component Alloys via Machine Learning

**Feature Branch**: `001-predicting-glass-forming-region`  
**Created**: 2026-05-15  
**Status**: Draft  
**Input**: User description: "Predicting the Glass Forming Region of Multi-Component Alloys via Machine Learning"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Compute thermodynamic descriptors for alloy compositions (Priority: P1)

A materials researcher uploads alloy composition data and receives computed thermodynamic descriptors (atomic size mismatch, mixing enthalpy, electronegativity variance) for each composition.

**Why this priority**: This is the foundational capability without which no prediction model can be trained. All subsequent analysis depends on correctly computed descriptors.

**Independent Test**: Can be fully tested by providing a CSV of alloy compositions and verifying that descriptor values match known calculations for benchmark alloys (e.g., Cu-Zr systems).

**Acceptance Scenarios**:

1. **Given** a CSV file containing 100 alloy compositions with elemental stoichiometries, **When** the descriptor computation script is executed, **Then** each composition has exactly 3 computed descriptors (atomic size mismatch, mixing enthalpy, electronegativity variance) with valid numeric values.
2. **Given** a composition with invalid elemental symbols (e.g., "XX" or "Element99"), **When** the script is executed, **Then** the composition is flagged with an error code and excluded from the output dataset.
3. **Given** a known benchmark composition (e.g., Cu50Zr50 from DScribe validation data), **When** descriptors are computed, **Then** the atomic size mismatch value falls within ±0.02 of the published reference value.

---

### User Story 2 - Train and evaluate glass-forming classifier on CPU (Priority: P2)

A researcher trains a Random Forest classifier on the descriptor dataset and receives performance metrics (ROC-AUC, precision-recall) on held-out test data.

**Why this priority**: This delivers the core predictive capability. Without classification, the research question about descriptor-predictor relationships cannot be answered.

**Independent Test**: Can be fully tested by running the training pipeline on a subset of 200 samples and verifying that the model achieves ≥0.75 ROC-AUC on a held-out test split.

**Acceptance Scenarios**:

1. **Given** a labeled dataset of 1000 alloy compositions (500 glass-forming, 500 crystalline), **When** the Random Forest classifier is trained with 5-fold cross-validation, **Then** the model completes training within 6 hours on a 2-core CPU.
2. **Given** a trained model, **When** evaluated on a held-out test set, **Then** ROC-AUC and precision-recall metrics are reported with standard deviation across cross-validation folds.
3. **Given** a composition with missing phase label data, **When** the dataset is loaded, **Then** the composition is excluded and a count of excluded samples is logged.

---

### User Story 3 - Generate feature importance and SHAP visualization (Priority: P3)

A researcher requests feature importance rankings and SHAP summary plots to understand which descriptors most strongly influence glass-forming predictions.

**Why this priority**: This enables scientific interpretation of the model's decisions. While the model can predict without this, understanding *why* is essential for materials discovery.

**Independent Test**: Can be fully tested by generating SHAP plots for a trained model and verifying that feature importance rankings are reproducible across runs.

**Acceptance Scenarios**:

1. **Given** a trained Random Forest model with 3 descriptors, **When** permutation importance is computed, **Then** each descriptor receives a numeric importance score ranked from highest to lowest.
2. **Given** a trained model, **When** SHAP summary plots are generated, **Then** the plots are saved as PNG files and display descriptor values on the x-axis with prediction impact on the y-axis.
3. **Given** two descriptors that are definitionally related (e.g., mixing enthalpy components), **When** collinearity diagnostics are run, **Then** a variance inflation factor (VIF) is computed and reported for each descriptor.

---

### Edge Cases

- What happens when the dataset contains only glass-forming compositions (no crystalline samples)? The system MUST detect class imbalance and flag the dataset as unsuitable for binary classification.
- How does the system handle missing elemental property data (e.g., unknown electronegativity for a rare earth element)? The system MUST use a fallback value from the nearest periodic table neighbor and log a warning.
- What happens when the dataset exceeds 7 GB RAM on the GitHub Actions runner? The system MUST sample compositions to fit within 7 GB RAM before processing and log the sampling ratio.
- How does the system handle cooling rate data that is missing from source databases? The system MUST record this as a known limitation and exclude cooling rate from predictor variables.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST compute atomic size mismatch, mixing enthalpy, and electronegativity variance for each alloy composition from elemental properties and stoichiometry (See US-1)
- **FR-002**: System MUST validate all elemental symbols against a periodic table database before descriptor computation (See US-1)
- **FR-003**: System MUST train Random Forest and Gradient Boosting classifiers using scikit-learn with 5-fold cross-validation (See US-2)
- **FR-004**: System MUST report ROC-AUC, precision, and recall metrics on a held-out test set (See US-2)
- **FR-005**: System MUST compute permutation importance scores, generate SHAP summary plots, AND perform sensitivity analysis on the atomic size mismatch threshold δ across variations {0.01, 0.05, 0.1} to evaluate prediction metric robustness (See US-3)
- **FR-006**: System MUST detect and flag datasets with class imbalance ratio >3:1 as unsuitable for binary classification (See US-2)
- **FR-007**: System MUST sample compositions to ensure total dataset size does not exceed available memory capacity before processing (See US-2)
- **FR-008**: System MUST remove features with Variance Inflation Factor (VIF) > 5.0 to prevent multicollinearity bias (See US-3)
- **FR-009**: System MUST filter compositions to retain only those with experimentally validated phase labels where available, or document DFT-derived labels as lower confidence (See US-2)

### Key Entities *(include if feature involves data)*

- **Alloy Composition**: Represents a multi-component metallic system with key attributes: elemental stoichiometries (≥3 elements), phase label (glass-forming/crystalline), and computed thermodynamic descriptors.
- **Descriptor Vector**: Represents the feature representation of an alloy with attributes: atomic size mismatch (unitless ratio), mixing enthalpy (kJ/mol), electronegativity variance (unitless), and VIF scores for collinearity diagnostics.
- **Model Performance Record**: Represents evaluation metrics with attributes: ROC-AUC score, precision, recall, standard deviation across folds, and training time in seconds.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Model ROC-AUC is measured against the held-out test set (See US-2)
- **SC-002**: Descriptor computation accuracy is measured against DScribe library benchmark values (See US-1)
- **SC-003**: Feature importance rankings are measured for reproducibility across multiple independent model training runs (See US-3)

### Operational Feasibility

- **SC-004**: Training job completion time is measured against the GitHub Actions free-tier job limit (See US-2)
- **SC-005**: Dataset memory footprint is measured against the specified RAM runner constraint (See US-2)

---

## Assumptions

- Cooling rate and thermal history data are NOT available in the Materials Project and NIST Alloy Database; therefore, the model predicts glass-forming propensity based solely on compositional descriptors, not processing parameters. This limitation is documented as a known constraint on causal inference.
- The Materials Project and NIST Alloy Database contain phase labels (glass-forming vs. crystalline) for at least 1000 multi-component metallic compositions to enable binary classification training.
- All elemental properties required for descriptor computation (atomic radii, electronegativity values, mixing enthalpy parameters) are available in the DScribe library or pymatgen periodic table data.
- The analysis is framed as ASSOCIATIONAL rather than causal: findings about descriptor-predictor relationships do not imply causal mechanisms for glass formation, per reviewer feedback from rosalind-franklin-simulated regarding the distinction between statistical correlation and structural determination. Glass formation is kinetically controlled; the model predicts associational propensity based on composition, not causal determination of phase boundaries.
- If the dataset contains fewer than 100 glass-forming samples, the power analysis is deferred and the model is evaluated on precision-recall metrics rather than ROC-AUC to account for class imbalance.
- The Materials Project database contains DFT-calculated thermodynamic and electronic properties but does NOT include experimental processing parameters such as cooling rates or thermal history for metallic glass compositions. This limitation is documented and the model predicts glass-forming propensity based solely on compositional descriptors. Source: Materials Project API documentation confirms absence of processing parameter data in standard datasets.
- No universal atomic size mismatch (δ) threshold defines the glass-forming boundary across all alloy systems. Literature consensus treats δ as a continuous ML predictor rather than a binary classifier threshold (Inoue et al., Acta Materialia; Zhang et al., Intermetallics). For systems requiring threshold-based analysis, community-standard values apply: δ > 6.5% correlates with glass formation in transition metal alloys. FR-005 shall include sensitivity analysis across δ variations of {0.01, 0.05, 0.1} to evaluate threshold robustness and report how prediction metrics vary across this range.