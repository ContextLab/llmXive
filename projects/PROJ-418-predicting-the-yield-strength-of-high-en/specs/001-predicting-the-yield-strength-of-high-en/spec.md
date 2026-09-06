# Specification for Predicting the Yield Strength of High‑Entropy Alloys

## Research Question
*How do elemental mixing parameters correlate with the yield strength of single‑phase high‑entropy alloys (HEAs), and can a composition‑only predictor achieve robust predictive performance (R² ≥ 0.6, |r| ≥ 0.5, p < 0.05) on an independent validation set?* (See US-1)

**Restated Idea:**
The original proposal aims to develop a fast, composition‑only predictor of HEA yield strength to enable rapid screening of candidate alloys for experimental synthesis while also identifying the most informative compositional descriptors. Expected performance targets are a coefficient of determination **R² ≥ 0.6**, absolute Pearson correlation **|r| ≥ 0.5**, and statistical significance **p < 0.05** on an independent held‑out test set. Additionally, at least two descriptors must show **|r| > 0.5** with **p < 0.01** in direct descriptor‑target correlation analysis.

**Expected Results (restated):**
The system should achieve a coefficient of determination **R² ≥ 0.6**, an absolute Pearson correlation **|r| ≥ 0.5**, and statistical significance **p < 0.05** on the external validation set. The top‑5 feature rankings should be stable (rank‑difference ≤ 1) across three independent runs. No missing‑field validation errors should occur, and the reproducibility manifest (now logged to console) must be present and correct. At least two compositional descriptors must exhibit **|r| > 0.5** and **p < 0.01**.

## User Scenarios & Testing

### User Story 1 – Predict HEA Yield Strength (Priority: P1) (See US-1)

**As a** materials scientist,
**I want** to obtain a reliable prediction of the yield strength for a given HEA composition,
**so that** I can prioritize experimental synthesis of promising candidates.

**Why this priority**: Yield‑strength prediction directly accelerates alloy design cycles and reduces costly experiments.

**Independent Test**: Execute the end‑to‑end pipeline on a held‑out test set of HEA compositions of adequate size and verify that the reported performance metrics satisfy the Success Criteria.

**Acceptance Scenarios**:

1. **Given** a valid CSV file containing alloy compositions, **When** the pipeline is run with default settings, **Then** a markdown report is produced that includes model performance, descriptor‑target correlations, feature importances, and reproduces the console provenance log.
2. **Given** a composition missing a required element field, **When** the pipeline validates the input, **Then** it aborts with a clear error message indicating the missing field.

## Edge Cases

- **Unknown element**: If an alloy composition contains an element not present in the training data, the system issues a warning and proceeds with a best‑effort prediction. *(See FR‑007)*
- **Duplicate rows**: Duplicate rows are retained; the model treats them as independent observations. *(See FR‑012)*
- **Missing required fields**: The system aborts with a clear error if any input record lacks required fields. *(See FR‑009)*

## Assumptions

- The adaptive permutation count is allowed; the implementation will use a standard budget of permutations that provides sufficient statistical power.
- The curated HEA yield‑strength dataset (identifier omitted) is representative of single‑phase alloys and contains experimentally measured `yield_strength` values.
- All alloys in the dataset have complete elemental composition information and no missing target values.
- The computational environment provides at least 8 CPU cores and 16 GB RAM.
- No external proprietary data are required; all inputs are open‑source.
- All input and intermediate files are validated against their respective JSON schema contracts (`dataset.schema.yaml`, `elemental_properties.schema.yaml`, `hea_composition.schema.yaml`, `metrics.schema.yaml`, `importance.schema.yaml`, `manifest.schema.yaml`, `runtime.schema.yaml`, `processed_data.schema.yaml`). *(see FR‑013)*
- Codebase linting is performed; the number of warnings must be ≤ 5 and formatting must pass. *(See FR‑020, SC‑012)*
- The dataset source is a publicly accessible Zenodo archive:. *(See FR‑017)*

## Methodology

1. **Data Acquisition**
 - Download the experimentally curated HEA yield‑strength dataset from the Zenodo archive ().
 - Validate that each record contains a numeric `yield_strength` target and complete elemental fractions.
 - All files are validated against their JSON schema contracts (FR‑013).

2. **Descriptor Calculation**
 - For each alloy, compute composition‑based descriptors (e.g., atomic radius variance, electronegativity difference) using the `elemental_properties.schema.yaml`.

3. **Statistical Power Analysis**
 - Perform a power analysis (target power ≥ 0.8, α = 0.05) to confirm that the dataset size is sufficient to detect an effect size corresponding to **R² ≥ 0.6**. *(See FR‑015, SC‑009)*

4. **Multicollinearity Assessment**
 - Compute Variance Inflation Factor (VIF) for each descriptor.
 - If any descriptor has **VIF > 5**, it is either removed or regularized before model training. *(See FR‑016, SC‑010)*

5. **Model Training**
 - Train a Random Forest regressor with a suitably large number of trees on the descriptor matrix after VIF handling.
 - Perform k‑fold cross‑validation to estimate out‑of‑fold performance.

6. **Descriptor‑Target Correlation Analysis**
 - Compute Pearson correlation and two‑tailed p‑value for each descriptor against `yield_strength`.
 - Report descriptors satisfying **|r| > 0.5** and **p < 0.01**. *(See FR‑014, SC‑007)*

7. **External Validation**
 - Obtain an independent external validation dataset from a separate open source (e.g., a later release of the same Zenodo collection).
 - Evaluate the trained model on this dataset and record performance metrics. *(See FR‑017, SC‑008)*

8. **Performance Evaluation**
 - Report coefficient of determination (R²), Pearson correlation coefficient (r), and two‑tailed p‑value on the held‑out test set.
 - Success thresholds: **R² ≥ 0.6**, **|r| ≥ 0.5**, **p < 0.05** (SC‑001, SC‑002, SC‑003).

9. **Permutation Importance**
 - Compute feature importance via permutation importance using a standard permutation budget (e.g., 1000 permutations) per feature on the held‑out test set to avoid data leakage.
 - Assess statistical significance using a non‑parametric permutation test with Holm‑Bonferroni correction (α = 0.05) and flag features with p < 0.05. *(See FR‑006, SC‑003)*

10. **Reproducibility & Reporting**
 - Record random seeds, hyperparameters, software versions, and execution timestamps to the console log. *(See FR‑010)*
 - Generate a markdown report (`report.md`) summarizing dataset statistics, model performance, descriptor‑target correlations, feature importances, VIF summary, and provenance log. *(See FR‑008, SC‑004)*
 - Verify that every numeric value in `report.md` is generated programmatically and linked to a provenance ID, satisfying Principle IV (Single Source of Truth). *(See FR‑019, SC‑011)*

## Contract Validation Mapping

| Contract File | Purpose | Mapped Requirement(s) |
|------------------------------|-------------------------------------------|-----------------------|
| `dataset.schema.yaml` | Validates raw HEA dataset records (composition fractions, target values) | FR‑001, FR‑009 |
| `elemental_properties.schema.yaml` | Validates descriptor calculation inputs/outputs | FR‑002 |
| `hea_composition.schema.yaml`| Validates composition CSV input format | FR‑009 |
| `metrics.schema.yaml` | Validates model performance metrics (`r2`, `pearson_r`, `p_value`) | SC‑001, SC‑002, SC‑003 |
| `importance.schema.yaml` | Validates permutation‑importance results (importance scores, p‑values) | SC‑003 |
| `manifest.schema.yaml` | Validates provenance manifest (seeds, versions, checksums) | FR‑010 |
| `runtime.schema.yaml` | Validates runtime summary (status, duration) | FR‑020 |
| `processed_data.schema.yaml` | Validates intermediate processed datasets | FR‑018 |

## Expected Results

| Metric | Target | Linked Success Criterion |
|--------|--------|--------------------------|
| R² | ≥ 0.6 | SC‑001 (See US‑1) |
| |r| | ≥ 0.5 | SC‑002 (See US‑1) |
| p‑value for each importance | < 0.05 | SC‑003 (See US‑1) |
| Missing required fields | None | SC‑005 (See US‑1) |
| Top‑5 feature ranking stability | ≤ 1 difference across runs | SC‑006 (See US‑1) |
| Lint warnings | ≤ 5 | SC‑012 (See US‑1) |
| Report completeness | Present & correct | SC‑004 (See US‑1) |
| Descriptor‑target correlation | ≥ 2 descriptors with |r| > 0.5 and p < 0.01 | SC‑007 (See US‑1) |
| External validation performance | R² ≥ 0.6, |r| ≥ 0.5, p < 0.05 | SC‑008 (See US‑1) |
| Power analysis justification | ≥ 80 % power for R² ≥ 0.6 | SC‑009 (See US‑1) |
| VIF handling | No descriptor with VIF > 5 in final model | SC‑010 (See US‑1) |
| Single source of truth | All numbers in report have provenance IDs | SC‑011 (See US‑1) |
| CI pipeline success | CI workflow passes all tests on each push | SC‑013 (See US‑1) |

## Functional Requirements

- **FR-001**: The system **MUST** download and validate the curated HEA yield‑strength dataset containing experimentally measured `yield_strength` values. (See US‑1)
- **FR-002**: The system **MUST** compute composition‑based descriptors for each alloy entry according to `elemental_properties.schema.yaml`. (See US‑1)
- **FR-003**: The system **MUST** train a Random Forest regression model using k‑fold cross‑validation (with the number of folds to be determined during the implementation phase) and store the trained model artifact. (See US‑1)
- **FR-004**: The system **MUST** evaluate the model on a held‑out test set and report R², Pearson r, and associated p‑value. (See US‑1)
- **FR-005**: The system **MUST** compute permutation importance for each descriptor using a standard permutation budget (e.g., 1000 permutations) per feature on the held‑out test set. (See US‑1)
 *Justification:* A conventional permutation budget provides adequate statistical power while keeping runtime reasonable.
- **FR-006**: The system **MUST** perform a non‑parametric permutation test to assess significance of permutation‑importance scores with Holm‑Bonferroni correction (α = 0.05) and flag features with p < 0.05. (See US‑1)
- **FR-007**: The system **MUST** issue a warning and proceed with a best‑effort prediction when an alloy composition contains an element not present in the training data. (See US‑1)
- **FR-008**: The system **MUST** produce a markdown `report.md` that includes dataset statistics, model performance metrics, descriptor‑target correlations, importance rankings, VIF summary, and a console‑logged provenance summary. (See US‑1)
- **FR-009**: The system **MUST** abort with a clear error if any input record lacks required fields (e.g., missing element fraction or target). (See US‑1)
- **FR-010**: The system **MUST** log random seeds, hyperparameters, software versions, and execution timestamps to the console provenance log. (See US‑1)
- **FR-011**: The system **MUST** include inline code comments and a `README.md` describing usage, dependencies, and execution steps. (See US‑1)
- **FR-012**: The system **MUST** retain duplicate rows in the input CSV and treat them as independent observations. (See US‑1)
- **FR-013**: The system **MUST** validate all input files **and** all intermediate and output artifact files against their respective JSON schema contracts (`dataset.schema.yaml`, `elemental_properties.schema.yaml`, `hea_composition.schema.yaml`, `metrics.schema.yaml`, `importance.schema.yaml`, `manifest.schema.yaml`, `runtime.schema.yaml`, `processed_data.schema.yaml`). (See US‑1)
- **FR-014**: The system **MUST** compute Pearson correlation and two‑tailed p‑value for each descriptor against `yield_strength`, reporting descriptors with **|r| > 0.5** and **p < 0.01**. (See US‑1)
- **FR-015**: The system **MUST** perform a statistical power analysis (target power ≥ 0.8, α = 0.05) to justify that the dataset size is sufficient to detect **R² ≥ 0.6**. (See US‑1)
- **FR-016**: The system **MUST** assess multicollinearity via Variance Inflation Factor (VIF) for each descriptor; descriptors with **VIF > 5** shall be removed or regularized before model training. (See US‑1)
- **FR-017**: The system **MUST** obtain an external validation dataset from a separate open source (e.g.,) and evaluate model performance on it. (See US‑1)
- **FR-018**: The system **MUST** validate all intermediate and output artifacts (e.g., `metrics.json`, `importance.json`, `manifest.json`, `runtime.json`, `processed_data.json`) against their respective JSON schema contracts. (See US‑1)
- **FR-019**: The system **MUST** verify that every numeric value in `report.md` is generated programmatically and linked to a provenance ID, satisfying Principle IV (Single Source of Truth). (See US‑1)
- **FR-020**: The system **MUST** run linting (ruff) and formatting (black) checks; the number of warnings must be ≤ 5 and formatting must pass. Results are recorded in `pipeline_runtime.json`. (See US‑1)
- **FR-021**: The system **MUST** generate a `requirements.txt` file listing all Python dependencies and a CI workflow skeleton (GitHub Actions) for automated testing. (See US‑1)

## Success Criteria

- **SC-001**: R² on the held‑out test set is **≥ 0.6**. (See US‑1)
- **SC-002**: Absolute Pearson correlation |r| on the held‑out test set is **≥ 0.5**. (See US‑1)
- **SC-003**: All flagged feature importances have p‑value **< 0.05**. (See US‑1)
- **SC-004**: The markdown `report.md` is present, correctly formatted, and contains all required sections (dataset stats, performance metrics, descriptor‑target correlations, importance rankings, VIF summary, provenance log). (See US‑1)
- **SC-005**: No input record triggers a missing‑field error during validation. (See US‑1)
- **SC-006**: The top‑5 important features are stable across three independent runs (maximum rank difference ≤ 1). (See US‑1)
- **SC-007**: At least two compositional descriptors have **|r| > 0.5** and **p < 0.01** in descriptor‑target correlation analysis. (See US‑1)
- **SC-008**: Model performance on the external validation set meets **R² ≥ 0.6**, **|r| ≥ 0.5**, **p < 0.05**. (See US‑1)
- **SC-009**: Power analysis demonstrates **≥ 80 %** power to detect **R² ≥ 0.6** at **α = 0.05**. (See US‑1)
- **SC-010**: No descriptor with **VIF > 5** remains in the final model; any such descriptor is removed or regularized. (See US‑1)
- **SC-011**: All numbers in `report.md` have associated provenance IDs linking back to source data rows and code blocks. (See US‑1)
- **SC-012**: Linting produces **≤ 5** warnings and formatting passes; results recorded in `pipeline_runtime.json`. (See US‑1)
- **SC-013**: CI workflow runs all unit tests and linting checks on each push; passes status recorded in `pipeline_runtime.json`. (See US‑1)
