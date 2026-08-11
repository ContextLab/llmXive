# Specification for Predicting the Yield Strength of High‑Entropy Alloys

## Research Question
*What is the predictive performance of a machine‑learning model for estimating the yield strength of single‑phase high‑entropy alloys (HEAs) from their elemental composition?* (See US-1)

**Restated Idea:**
The original proposal aims to develop a fast, composition‑only predictor of HEA yield strength to enable rapid screening of candidate alloys for experimental synthesis. Expected performance targets are a coefficient of determination **R² ≥ 0.6**, absolute Pearson correlation **|r| ≥ 0.5**, and statistical significance **p < 0.05** on a held‑out test set, with a complete end‑to‑end run time of **≤ 2 hours** on an Multi‑core CPU.

**Expected Results (restated):**
The system should achieve a coefficient of determination **R² ≥ 0.6**, an absolute Pearson correlation **|r| ≥ 0.5**, and statistical significance **p < 0.05** on the held‑out test set. The end‑to‑end pipeline must complete within **2 hours** on an 8‑core CPU, and the top‑5 feature rankings should be stable (rank‑difference ≤ 1) across three independent runs. No missing‑field validation errors should occur, and the reproducibility manifest must be present and correct.

## User Scenarios & Testing

### User Story 1 – Predict HEA Yield Strength (Priority: P1) (See US-1)

**As a** materials scientist,
**I want** to obtain a reliable prediction of the yield strength for a given HEA composition,
**so that** I can prioritize experimental synthesis of promising candidates.

**Why this priority**: Yield‑strength prediction directly accelerates alloy design cycles and reduces costly experiments.

**Independent Test**: Execute the end‑to‑end pipeline on a held‑out test set of HEA compositions of adequate size and verify that the reported performance metrics satisfy the Success Criteria.

**Acceptance Scenarios**:

1. **Given** a valid CSV file containing alloy compositions, **When** the pipeline is run with default settings, **Then** a markdown report is produced that includes model performance, feature importances, and reproduces the manifest file.
2. **Given** a composition missing a required element field, **When** the pipeline validates the input, **Then** it aborts with a clear error message indicating the missing field.

## Edge Cases

- What happens when an alloy composition contains an element not present in the training data?
 *The system aborts with a descriptive error (FR‑009).*

- How does the system handle a CSV file with duplicate rows?
 *Duplicates are deduplicated before model training (FR‑009).*

## Assumptions

- The adaptive permutation count is **not** permitted; the implementation must always run **1000 permutations** (FR‑012).
- The curated HEA yield‑strength dataset (‑020‑00374‑5) is representative of single‑phase alloys and contains experimentally measured `yield_strength` values.
- All alloys in the dataset have complete elemental composition information and no missing target values.
- The computational environment provides at least 8 CPU cores and 16 GB RAM.
- No external proprietary data are required; all inputs are open‑source.
- All input and intermediate files are validated against their respective JSON schema contracts (`dataset.schema.yaml`, `elemental_properties.schema.yaml`, `hea_composition.schema.yaml`). *(see FR‑013)*
- **Dataset Note:** The Matbench HEA benchmark does **not** provide experimentally measured yield‑strength values and is therefore **not** used. The pipeline relies exclusively on the curated HEA yield‑strength dataset cited above.

## Methodology

1. **Data Acquisition**
 - Download the experimentally curated HEA yield‑strength dataset (‑020‑00374‑5).
 - Validate that each record contains a numeric `yield_strength` target and complete elemental fractions.
 - All files are validated against their JSON schema contracts (FR‑013).

2. **Descriptor Calculation**
 - For each alloy, compute composition‑based descriptors (e.g., atomic radius variance, electronegativity difference) using the `elemental_properties.schema.yaml`.

3. **Model Training**
 - Train a Random Forest regressor with a suitably large number of trees.
 - Perform k‑fold cross‑validation to estimate out‑of‑fold performance.

4. **Performance Evaluation**
 - Report coefficient of determination (R²), Pearson correlation coefficient (r), and two‑tailed p‑value on the held‑out test set.
 - Success thresholds: **R² ≥ 0.6**, **|r| ≥ 0.5**, **p < 0.05** (SC‑001, SC‑002).

5. **Permutation Importance**
 - Compute feature importance via permutation importance with exactly **1000 permutations** per feature (FR‑005, FR‑012).
 - Assess statistical significance using a two‑tailed t‑test with α = 0.05; flag features with p < 0.05 (FR‑006, SC‑003).

6. **Reproducibility & Reporting**
 - Record random seeds, hyperparameters, and software versions in `manifest.json` (FR‑007, SC‑007).
 - Generate a markdown report (`report.md`) summarizing dataset statistics, model performance, and importance results (FR‑008, SC‑004, SC‑008).

7. **Runtime Constraint**
 - The entire pipeline must complete within **2 hours** on a standard 8‑core CPU (SC‑004).

## Expected Results

| Metric | Target | Linked Success Criterion |
|--------|--------|--------------------------|
| R² | ≥ 0.6 | SC‑001 (See US‑1) |
| |r| | ≥ 0.5 | SC‑002 (See US‑1) |
| p‑value for each importance | < 0.05 | SC‑003 (See US‑1) |
| Runtime | ≤ 2 h | SC‑004 (See US‑1) |
| Missing required fields | None | SC‑005 (See US‑1) |
| Top‑5 feature ranking stability | ≤ 1 difference across runs | SC‑006 (See US‑1) |
| Manifest completeness | Present & correct | SC‑007 (See US‑1) |
| Lint warnings | ≤ 5 | SC‑008 (See US‑1) |

## Functional Requirements

- **FR-001**: The system **MUST** download and validate the curated HEA yield‑strength dataset containing experimentally measured `yield_strength` values. (See US‑1)
- **FR-002**: The system **MUST** compute composition‑based descriptors for each alloy entry according to `elemental_properties.schema.yaml`. (See US‑1)
- **FR-003**: The system **MUST** train a Random Forest regression model using k‑fold cross‑validation (with the number of folds to be determined during the implementation phase). and store the trained model artifact. (See US‑1)
- **FR-004**: The system **MUST** evaluate the model on a held‑out test set and report R², Pearson r, and associated p‑value. (See US‑1)
- **FR-005**: The system **MUST** compute permutation importance for each descriptor with exactly **1000 permutations** per feature. (See US‑1)
- **FR-006**: The system **MUST** perform a two‑tailed t‑test on permutation importance scores with significance level α = 0.05 and flag features with p < 0.05. (See US‑1)
- **FR-007**: The system **MUST** generate a reproducibility manifest recording random seeds, hyperparameters, software versions, and execution timestamps. (See US‑1)
- **FR-008**: The system **MUST** produce a markdown `report.md` that includes dataset statistics, model performance metrics, importance rankings, and the reproducibility manifest. (See US‑1)
- **FR-009**: The system **MUST** abort with a clear error if any input record lacks required fields (e.g., missing element fraction or target). (See US‑1)
- **FR-010**: The system **MUST** complete training and permutation‑importance computation within **2 hours** on a standard 8‑core CPU. (See US‑1)
- **FR-011**: The system **MUST** include inline code comments and a `README.md` describing usage, dependencies, and execution steps. (See US‑1)
- **FR-012**: The system **MUST** enforce a fixed permutation count of **1000**; adaptive counts are prohibited. (See US‑1)
- **FR-013**: The system **MUST** validate all input files and intermediate artifacts against their respective JSON schema contracts (`dataset.schema.yaml`, `elemental_properties.schema.yaml`, `hea_composition.schema.yaml`). (See US‑1)

## Success Criteria

- **SC-001**: R² on the held‑out test set is **≥ 0.6**. (See US‑1)
- **SC-002**: Absolute Pearson correlation |r| on the held‑out test set is **≥ 0.5**. (See US‑1)
- **SC-003**: All flagged feature importances have p‑value **< 0.05**. (See US‑1)
- **SC-004**: The end‑to‑end pipeline completes within **2 hours** on the specified hardware. (See US‑1)
- **SC-005**: No input record triggers a missing‑field error during validation. (See US‑1)
- **SC-006**: The top‑5 important features are stable across three independent runs (maximum rank difference ≤ 1). (See US‑1)
- **SC-007**: The reproducibility manifest (`manifest.json`) is present, correctly formatted, and contains all required entries. (See US‑1)
- **SC-008**: The codebase passes linting with **≤ 5** warnings. (See US‑1)