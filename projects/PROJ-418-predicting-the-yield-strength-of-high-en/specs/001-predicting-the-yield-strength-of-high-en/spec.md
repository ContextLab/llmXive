# Specification for Predicting the Yield Strength of High‑Entropy Alloys

## Research Question
*How do elemental mixing parameters correlate with the yield strength of single‑phase high‑entropy alloys (HEAs), and can a composition‑only predictor achieve robust predictive performance (R² ≥ 0.6, |r| ≥ 0.5, p < 0.05) on an independent validation set?* (See US-1)

**Restated Idea:**
The original proposal aims to develop a fast, composition‑only predictor of HEA yield strength to enable rapid screening of candidate alloys for experimental synthesis while also identifying the most informative compositional descriptors. Expected performance targets are a coefficient of determination **R² ≥ 0.6**, absolute Pearson correlation **|r| ≥ 0.5**, and statistical significance **p < 0.05** on an independent held‑out test set. Additionally, at least two descriptors must show **|r| > 0.5** with **p < 0.01** in descriptor‑target correlation analysis performed on the training data.

## User Scenarios & Testing

### User Story 1 – Predict HEA Yield Strength (Priority: P1) (See US-1)

**As a** materials scientist,
**I want** to obtain a reliable prediction of the yield strength for a given HEA composition,
**so that** I can prioritize experimental synthesis of promising candidates.

**Why this priority**: Yield‑strength prediction directly accelerates alloy design cycles and reduces costly experiments.

**Independent Test**: Execute the end‑to‑end pipeline on a held‑out test set of HEA compositions of adequate size and verify that the reported performance metrics satisfy the Success Criteria.

**Acceptance Scenarios**:

1. **Given** a valid CSV file containing alloy compositions, **When** the pipeline is run with default settings, **Then** a markdown report is produced that includes model performance, descriptor‑target correlations (computed on training data), feature importances, VIF summary, provenance log, and the power‑analysis justification.
2. **Given** a composition missing a required element fraction, **When** the pipeline validates the input, **Then** it aborts with a clear error message indicating the missing field.

## Edge Cases

- **Missing required fields**: The system aborts with a clear error if any input record lacks required fields. *(See FR‑009)*
- **Dataset size insufficient**: Power analysis will flag insufficient sample size and abort execution. *(See FR‑015, FR‑023)*

## Assumptions

- The adaptive permutation count is allowed; the implementation will use a standard budget of permutations that provides sufficient statistical power.
- The curated HEA yield‑strength dataset is publicly available at ** and contains experimentally measured `yield_strength` values for single‑phase alloys.
- All alloys in the dataset have complete elemental composition information and no missing target values.
- The computational environment provides at least Several CPU cores and 16 GB RAM.
- No external proprietary data are required; all inputs are open‑source.
- All input and intermediate files are validated against their respective JSON schema contracts (`dataset.schema.yaml`, `elemental_properties.schema.yaml`, `hea_composition.schema.yaml`, `metrics.schema.yaml`, `importance.schema.yaml`, `manifest.schema.yaml`). *(see FR‑013)*
- The dataset source is a publicly accessible Zenodo archive. *(See FR‑001)*

## Methodology

1. **Data Acquisition**
 - Download the experimentally curated HEA yield‑strength dataset from Zenodo (**).
 - Validate the raw dataset against `dataset.schema.yaml` (FR‑001).

2. **Descriptor Calculation**
 - For each alloy, compute composition‑based descriptors (e.g., atomic radius variance, electronegativity difference) using the `elemental_properties.schema.yaml`.
 - Validate the descriptor table against `elemental_properties.schema.yaml`.

3. **Statistical Power Analysis**
 - Perform a power analysis targeting **power ≥ 0.80**, α = 0.05, to detect an effect size corresponding to **R² ≥ 0.6**.
 - Compute the required minimum sample size; compare with the actual dataset size and record the achieved power. (FR‑015, FR‑022, FR‑023)

4. **Train‑Test Split & Multicollinearity Assessment**
 - Split the dataset into training ([deferred]) and held‑out test ([deferred]) sets using a fixed random seed.
 - Compute Variance Inflation Factor (VIF) for each descriptor on the training set.
 - Remove or regularize any descriptor with **VIF > 5** before model training. (FR‑016)

5. **Model Training**
 - Train a Random Forest regressor with a sufficiently large number of trees on the descriptor matrix after VIF handling.
 - Perform k‑fold cross‑validation on the training set to estimate out‑of‑fold performance.

6. **Descriptor‑Target Correlation Analysis**
 - Compute Pearson correlation **r** and two‑tailed p‑value for each descriptor **using only the training data**.
 - Report descriptors satisfying **|r| > 0.5** and **p < 0.01**. (FR‑014)

7. **External Validation**
 - Obtain an independent external validation dataset from a later Zenodo release (**).
 - Document measurement protocols, processing conditions, and phase‑purity information for both training and external datasets to assess comparability. (FR‑024)
 - Evaluate the trained model on this external set and record performance metrics. (FR‑017)

8. **Performance Evaluation**
 - Report coefficient of determination (R²), Pearson correlation coefficient (r), and two‑tailed p‑value on the held‑out test set.
 - Success thresholds: **R² ≥ 0.6**, **|r| ≥ 0.5**, **p < 0.05** (SC‑001, SC‑002, SC‑003).

9. **Permutation Importance**
 - Compute feature importance via permutation importance using **A large set of permutations** per feature on the held‑out test set.
 - Assess statistical significance with a non‑parametric permutation test and Holm‑Bonferroni correction (α = 0.05); flag features with **p < 0.05**. (FR‑005, FR‑006)

10. **Stability Assessment**
 - Run the entire training‑evaluation pipeline **three independent times** with distinct random seeds.
 - Record the top‑5 feature rankings for each run in `output/stability_rankings.json`.
 - Compute the maximum rank difference across runs; require **≤ 1**. (FR‑021, SC‑006)

11. **Reproducibility & Reporting**
 - Record random seeds, hyperparameters, software versions, and execution timestamps to the console provenance log. (FR‑010)
 - Generate a markdown report (`report.md`) summarizing dataset statistics, model performance, descriptor‑target correlations, feature importances, VIF summary, power‑analysis justification, external‑validation documentation, stability assessment, and provenance log. (FR‑008)
 - Verify that every numeric value in `report.md` is generated programmatically and linked to a provenance ID, satisfying Principle IV (Single Source of Truth). (FR‑019)

## Contract Validation Mapping

| Contract File | Purpose | Mapped Requirement(s) |
|-----------------------------------|--------------------------------------------|-----------------------|
| `dataset.schema.yaml` | Validates raw HEA dataset records | FR‑001 |
| `elemental_properties.schema.yaml`| Validates descriptor calculation inputs/outputs| FR‑002 |
| `hea_composition.schema.yaml` | Validates composition CSV input format | FR‑009 |
| `metrics.schema.yaml` | Validates model performance metrics (`r2`, `pearson_r`, `p_value`) | SC‑001, SC‑002, SC‑003 |
| `importance.schema.yaml` | Validates permutation‑importance results (scores, p‑values) | FR‑006 |
| `manifest.schema.yaml` | Validates provenance manifest (seeds, versions, checksums) | FR‑010 |

## Expected Results

| Metric | Target | Linked Success Criterion |
|----------------------------------------|----------------------------------------|--------------------------|
| R² | ≥ 0.6 | SC‑001 (See US‑1) |
| |r| (test set) | ≥ 0.5 | SC‑002 (See US‑1) |
| p‑value (test set) | < 0.05 | SC‑003 (See US‑1) |
| Top‑5 feature rank stability | max rank difference ≤ 1 across three runs | SC‑006 (See US‑1) |
| Descriptor‑target correlation | ≥ 2 descriptors with |r| > 0.5 and p < 0.01 (training data) | SC‑007 (See US‑1) |
| External validation performance | R² ≥ 0.6, |r| ≥ 0.5, p < 0.05 | SC‑008 (See US‑1) |
| Power analysis | Achieved power ≥ 0.80 | SC‑009 (See US‑1) |
| VIF handling | No descriptor with VIF > 5 in final model| SC‑010 (See US‑1) |
| Single source of truth | All numbers in report have provenance IDs| SC‑011 (See US‑1) |
| CI pipeline success | All unit tests and linting pass (if present) | SC‑013 (removed as out‑of‑scope) |

## Functional Requirements

- **FR-001**: The system **MUST** download and validate the curated HEA yield‑strength dataset from the Zenodo URL ** using `dataset.schema.yaml`. (See US‑1)
- **FR-002**: The system **MUST** compute composition‑based descriptors for each alloy entry according to `elemental_properties.schema.yaml`. (See US‑1)
- **FR-003**: The system **MUST** train a Random Forest regression model using k‑fold cross‑validation on the training split and store the trained model artifact. (See US‑1)
- **FR-004**: The system **MUST** evaluate the model on a held‑out test set and report R², Pearson r, and associated p‑value. (See US‑1)
- **FR-005**: The system **MUST** compute permutation importance for each descriptor using **1000 permutations** per feature on the held‑out test set. (See US‑1)
- **FR-006**: The system **MUST** perform a non‑parametric permutation test to assess significance of permutation‑importance scores with Holm‑Bonferroni correction (α = 0.05) and flag features with p < 0.05. (See US‑1)
- **FR-008**: The system **MUST** produce a markdown `report.md` that includes dataset statistics, model performance metrics, descriptor‑target correlations (training data only), importance rankings, VIF summary, power‑analysis justification, external‑validation documentation, stability assessment, and a provenance summary. (See US‑1)
- **FR-009**: The system **MUST** abort with a clear error if any input record lacks required fields (e.g., missing element fraction or target). (See US‑1)
- **FR-010**: The system **MUST** log random seeds, hyperparameters, software versions, and execution timestamps to the console provenance log. (See US‑1)
- **FR-014**: The system **MUST** compute Pearson correlation and two‑tailed p‑value for each descriptor **using only the training data**, reporting descriptors with **|r| > 0.5** and **p < 0.01**. (See US‑1)
- **FR-015**: The system **MUST** perform a statistical power analysis (target power ≥ 0.8, α = 0.05) to justify that the dataset size is sufficient to detect **R² ≥ 0.6**. (See US‑1)
- **FR-016**: The system **MUST** assess multicollinearity via Variance Inflation Factor (VIF) for each descriptor on the training set; descriptors with **VIF > 5** shall be removed or regularized before model training. (See US‑1)
- **FR-017**: The system **MUST** obtain an external validation dataset from a separate Zenodo release (**) and evaluate model performance on it. (See US‑1)
- **FR-018**: The system **MUST** validate all input files and intermediate/output artifacts against their respective JSON schema contracts (`dataset.schema.yaml`, `elemental_properties.schema.yaml`, `hea_composition.schema.yaml`, `metrics.schema.yaml`, `importance.schema.yaml`, `manifest.schema.yaml`). (See US‑1)
- **FR-021**: The system **MUST** execute three independent training/evaluation runs with distinct random seeds, record the top‑5 feature rankings per run in `output/stability_rankings.json`, and ensure the maximum rank difference across runs is ≤ 1. (See US‑1)
- **FR-022**: The system **MUST** include the achieved statistical power value (≥ 0.8) in `report.md` and confirm it meets the target. (See US‑1)
- **FR-023**: The system **MUST** document provenance, measurement protocols, and any processing‑condition differences between the primary and external validation datasets, noting potential confounds. (See US‑1)
- **FR-024**: The system **MUST** verify that every numeric value in `report.md` is generated programmatically and linked to a provenance ID, satisfying Principle IV (Single Source of Truth). (See US‑1)

## Success Criteria

- **SC-001**: R² on the held‑out test set is **≥ 0.6**. (See US‑1)
- **SC-002**: Absolute Pearson correlation |r| on the held‑out test set is **≥ 0.5**. (See US‑1)
- **SC-003**: All flagged feature importances have p‑value **< 0.05**. (See US‑1)
- **SC-004**: The markdown `report.md` is present, correctly formatted, and contains all required sections (dataset stats, performance metrics, descriptor‑target correlations, importance rankings, VIF summary, power‑analysis justification, external‑validation documentation, stability assessment, provenance log). (See US‑1)
- **SC-005**: No input record triggers a missing‑field error during validation. (See US‑1)
- **SC-006**: The top‑5 important features are stable across three independent runs (maximum rank difference ≤ 1). (See US‑1, FR‑021)
- **SC-007**: At least two compositional descriptors have **|r| > 0.5** and **p < 0.01** in descriptor‑target correlation analysis on the training data. (See US‑1)
- **SC-008**: Model performance on the external validation set meets **R² ≥ 0.6**, **|r| ≥ 0.5**, **p < 0.05**. (See US‑1)
- **SC-009**: Power analysis demonstrates **achieved power ≥ 0.80** for detecting **R² ≥ 0.6** at **α = 0.05**. (See US‑1, FR‑022)
- **SC-010**: No descriptor with **VIF > 5** remains in the final model; any such descriptor is removed or regularized. (See US‑1)
- **SC-011**: All numbers in `report.md` have associated provenance IDs linking back to source data rows and code blocks. (See US‑1)
- **SC-012**: CI workflow runs all unit tests on each push and records a passing status in `pipeline_runtime.json`. (Out‑of‑scope; removed)
- **SC-013**: Linting produces **≤ 5** warnings and formatting passes; results recorded in `pipeline_runtime.json`. (Out‑of‑scope; removed)
