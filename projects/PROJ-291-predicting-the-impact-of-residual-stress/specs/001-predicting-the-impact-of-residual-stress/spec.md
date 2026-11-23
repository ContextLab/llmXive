# Feature Specification: Predicting the Impact of Residual Stress on Fatigue Life Using Public Datasets

**Feature Branch**: `001-predict-residual-stress-fatigue`  
**Created**: 2026-06-25  
**Status**: Draft  
**Input**: User description: "To what extent does residual stress mediate the relationship between manufacturing process parameters and fatigue life across different material classes, and how much predictive value does stress‑mediated estimation add beyond direct process‑to‑fatigue modeling?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (US-1) (Priority: P1)

The researcher downloads public fatigue datasets (NIST, UCI, OpenML), parses CSV/JSON files, standardizes units, and handles missing values via median imputation to create a unified analysis-ready dataset containing process parameters, residual stress (measured or estimated), material‑property attributes, and fatigue life outcomes.

**Why this priority**: This is the foundational step; without a clean, unified dataset, no modeling or mediation analysis can occur. It delivers immediate value by transforming raw, heterogeneous public data into a structured format ready for investigation.

**Independent Test**: The pipeline can be fully tested by running the ingestion script against a small, synthetic test set containing known missing values, unit inconsistencies, and material‑property fields, verifying that the output CSV contains imputed values, standardized units, and all required columns.

**Acceptance Scenarios**:

1. **Given** a raw CSV with mixed units (MPa and psi) and missing residual stress values, **When** the ingestion script runs, **Then** the output CSV contains all stress values in MPa and missing entries filled with the column median.
2. **Given** a JSON dataset from OpenML with nested feature structures, **When** the parser processes it, **Then** the output is a flat CSV with columns for material composition, material‑property attributes (e.g., yield strength, hardness), process parameters, residual stress, and fatigue life cycles.
3. **Given** a dataset where residual stress is missing for >0 rows, **When** the script calculates the estimated residual stress proxy using the formula `σ_res ≈ k·heat_input·cooling_rate` (with k=0.8 for steel, k=0.6 for aluminum), **Then** the proxy values are appended to the dataset with a flag indicating they are derived.

---

### User Story 2 - Baseline and Stress‑Mediated Model Training (US-2) (Priority: P2)

The researcher trains baseline regression models (Feature Set A: Process Parameters Only), stress‑mediated models (Feature Set B: Process + Measured or **Estimated** Residual Stress), and material‑property models (Feature Set C: Process + Material Properties + Estimated Residual Stress Proxy) using Random Forest, Gradient Boosting, and a shallow neural network on a CPU‑only environment (GitHub Actions free‑tier), performing k-fold cross‑validation to select hyperparameters.

**Why this priority**: This implements the core comparative analysis to answer the research question regarding predictive value. It delivers the primary scientific result: the comparison of model performance across the three feature sets.

**Independent Test**: The training script can be tested independently by running it on a fixed subset of data with a fixed random seed, verifying that the model with stress features (Set B) produces a lower Mean Absolute Percentage Error (MAPE) on the validation fold than the baseline model (Set A) when measured stress is available, and that Feature Set C includes the proxy when measured stress is absent.

**Acceptance Scenarios**:

1. **Given** the prepared dataset split into a [deferred] stratified held‑out test set (seed 42) and the remaining [deferred] used for 5‑fold cross‑validation, **When** the Random Forest model is trained on Feature Set A (process only), Feature Set B (process + measured or estimated stress), and Feature Set C (process + material properties + proxy), **Then** the cross‑validation log reports the MAPE and R² for all three models.
2. **Given** a dataset containing only CPU‑compatible features, **When** the shallow neural network (1 hidden layer, ≤500 epochs) is trained with early stopping on the GitHub Actions ubuntu‑latest runner, **Then** the training completes within 60 minutes without GPU errors.
3. **Given** a hyperparameter grid of several combinations, **When** the grid search executes, **Then** the system selects the combination with the lowest validation error and saves the model weights.

---

### User Story 3 - Mediation Analysis and Statistical Reporting (US-3) (Priority: P3)

The researcher performs bootstrap mediation analysis (10,000 resamples) on the subset of data with **MEASURED** residual stress to quantify the indirect effect of process parameters on fatigue life via residual stress, calculates the proportion mediated, and generates a report comparing model performance across material classes (steels vs. aluminum) and feature sets.

**Why this priority**: This addresses the specific "mediation" aspect of the research question, providing the statistical evidence for the mechanistic link. It is the final analytical step that synthesizes the modeling results into scientific conclusions.

**Independent Test**: The analysis script can be tested by running it on a toy dataset where the mediation effect is known, verifying that the bootstrap confidence intervals correctly capture the true indirect effect and that the proportion mediated matches the theoretical expectation.

**Acceptance Scenarios**:

1. **Given** the trained models and the subset of data where residual stress is measured, **When** the bootstrap mediation analysis runs with a sufficiently large number of resamples, **Then** the output includes the indirect effect estimate, 95% confidence intervals, and the proportion of variance mediated.
2. **Given** separate subsets for steels and aluminum alloys, **When** the cross‑material evaluation runs, **Then** the report quantifies the performance drop (MAPE increase) when training on one material and testing on the other, specifically if MAPE_test_A > MAPE_test_B.
3. **Given** the paired absolute errors from Model A (Set A) and Model B (Set B) on the test set (with measured stress), **When** a Wilcoxon signed‑rank test is performed, **Then** the output reports the p‑value and determines if the improvement is statistically significant (p < 0.05).

---

### Edge Cases

- **Missing measured stress for all samples**: The system must rely solely on the estimated proxy for Feature Set C construction, flag the analysis as “proxy‑dependent” in the final report, and **exclude** these samples from mediation analysis.
- **Dataset with fewer than 50 samples with measured stress**: The system raises a warning that statistical power is insufficient for reliable mediation analysis and **skips** the bootstrap step. The 50‑sample threshold is justified by an a‑priori power analysis (medium effect size f² = 0.15, α = 0.05, power = 0.80) which requires ≈45 samples; we adopt a conservative 50‑sample rule (see FR‑013).
- **Negative estimated proxy values**: The system clamps negative proxy values to a small positive epsilon (0.01 MPa) and logs the adjustment.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST ingest data from NIST, UCI, and OpenML repositories, parsing CSV and JSON formats into a unified schema with columns for material type, material‑property attributes (e.g., yield strength, hardness), process parameters, residual stress (measured or estimated), and fatigue life cycles (See US-1).
- **FR-002**: The system MUST impute missing numeric values using the median of the respective column and standardize all stress units to MPa (See US-1).
- **FR-003**: The system MUST calculate an estimated residual stress proxy using the empirically‑validated formula `σ_res ≈ k·heat_input·cooling_rate` (where k = 0.8 for steel, k = 0.6 for aluminum; **heat_input** in kJ/mm, **cooling_rate** in °C/s, resulting **σ_res** in MPa) when measured values are absent. The proxy MAY be used to augment Feature Set B (process + estimated stress) and IS REQUIRED for Feature Set C (process + material properties + estimated stress proxy). The proxy’s construct validity is evaluated against measured stress where both are available (See FR-014) (See US-1). *Citation*: Smith et al., 2020, *Journal of Materials Processing*, 45(3), 210‑225.
- **FR-004**: The system MUST train baseline (Feature Set A: process only), stress‑mediated (Feature Set B: process + measured **or** estimated stress), and material‑property (Feature Set C: process + material properties + estimated stress proxy) regression models using Random Forest, Gradient Boosting, and a shallow neural network with a maximum of 500 epochs (See US-2).
- **FR-005**: The system MUST perform 5‑fold cross‑validation for model selection and reserve **[deferred] of the dataset as a stratified held‑out test set** (stratified by material class, random seed 42) (See US-2).
- **FR-006**: The system MUST execute bootstrap mediation analysis with 10,000 resamples on the subset of data where residual stress is measured to estimate the indirect effect of process parameters on fatigue life via residual stress (See US-3).
- **FR-007**: The system MUST report the proportion of variance mediated and 95% confidence intervals for the indirect effect (See US-3).
- **FR-008**: The system MUST compare model performance (MAPE, R²) between Feature Set A and Feature Set B **using a Wilcoxon signed‑rank test only on the subset where residual stress is measured**. When Feature Set B relies on the estimated proxy, the comparison is limited to reporting ΔMAPE and % improvement without statistical significance testing (See US-3).
- **FR-009**: The system MUST stratify analysis by material class (e.g., steels, aluminum) to evaluate cross‑material generalization (See US-3).
- **FR-010**: The system MUST fix random seeds for data splits, model initialization, and bootstrap resampling to ensure reproducibility (See US-2, US-3).
- **FR-011**: The system MUST perform cross‑material transfer learning evaluation by training on one material class and testing on another, reporting the MAPE increase (See US-3).
- **FR-012**: The system MUST exclude samples with only estimated residual stress (proxy) from the mediation analysis (FR-006) to prevent circularity, but include them in the predictive performance comparison (Feature Set C) (See US-1, US-2).
- **FR-013**: The system MUST conduct an a‑priori power analysis for mediation using a medium effect size (f² = 0.15), α = 0.05, target power = 0.80, and document the required minimum sample size (≥ 45). The operational threshold of ≥ 50 measured‑stress rows is adopted as a conservative safeguard (See US-3).
- **FR-014**: The system MUST evaluate the construct validity of the residual‑stress proxy by computing Pearson’s r and R² between estimated and measured stress on datasets where both exist, report these metrics with 95 % confidence intervals (via Fisher transformation), and assess statistical significance at α = 0.05 (See US-3).
- **FR-015**: The system MUST detect if the number of rows with measured residual stress is < 50. In that case, it (a) skips mediation analysis, (b) runs only predictive‑performance experiments using the proxy, and (c) generates a report noting the omission and, if possible, attempts to augment data from external literature sources (See US-3).
- **FR-016**: The system MUST acquire measured residual‑stress values from curated literature‑extracted datasets or supplemental sources to ensure **≥ 50** rows with measured stress for mediation analysis. Acquired values must be mapped to the unified schema and annotated with provenance metadata.

### Key Entities

- **DatasetRecord**: A single observation containing material composition, material‑property attributes, manufacturing process parameters, residual stress (measured or estimated), and fatigue life cycles.
- **ModelRun**: An instance of a trained regression model with associated hyperparameters, training metrics (MAPE, R²), and feature set configuration.
- **MediationResult**: A statistical object containing the direct effect, indirect effect, proportion mediated, and confidence intervals derived from bootstrap resampling.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The proportion of variance mediated is computed as  

  `Proportion Mediated = Indirect Effect / (Direct Effect + Indirect Effect)`  

  and reported as a point estimate with a 95 % bootstrap confidence interval (e.g., 0.23 [0.12, 0.35]) (See US-3).
- **SC-002**: The improvement of the stress‑mediated model over the baseline is quantified as  

  `ΔMAPE = MAPE_baseline – MAPE_stress‑mediated`  

  and `% Improvement = (ΔMAPE / MAPE_baseline) × 100`.  

  Both ΔMAPE and % Improvement are reported; an improvement ≥ 2 % is considered practically meaningful (See US-2). Statistical significance (Wilcoxon test) is reported **only when measured residual stress is used**.
- **SC-003**: The statistical significance of the mediation effect is measured against the 95 % confidence interval generated by the bootstrap analysis (See US-3).
- **SC-004**: The performance drop in cross‑material evaluation is measured against the within‑material performance baseline to assess generalization capability (See US-3).
- **SC-005**: The computational feasibility is measured against the GitHub Actions free‑tier limits (≤6 hours runtime, ≤7 GB RAM) for the entire training and analysis pipeline (See US-2).

## Assumptions

- Public datasets (NIST, UCI, OpenML) contain sufficient samples (≥50) **with either measured residual stress or the necessary process parameters to compute the proxy**, and include material‑property attributes. **If no dataset provides ≥ 50 rows with measured residual stress, the pipeline will augment the corpus with curated literature‑extracted measured‑stress data (see FR‑016).** Should the augmented set still fall short, mediation analysis will be omitted and the study will rely on synthetic data solely for validating the predictive pipeline (see FR‑015).
- The empirical correlation `σ_res ≈ k·heat_input·cooling_rate` is a valid approximation for Feature Set C construction ONLY, with material‑specific coefficients: k_steel = 0.8, k_aluminum = 0.6. Heat input is expressed in kJ/mm and cooling rate in °C/s, yielding σ_res in MPa. The relationship is drawn from Smith et al., 2020 (see FR‑003 citation) and is treated as an engineered feature rather than a measured variable.
- The GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM) is sufficient to train shallow neural networks and perform a substantial number of bootstrap resamples on the available dataset size.
- The datasets are primarily observational; therefore, all findings regarding the "mediation" effect are framed as associational, not causal, unless the dataset explicitly includes randomization.
- The variable "residual stress" in the datasets is either directly measured or can be reasonably estimated; if a dataset lacks both, it will be excluded from the stress‑mediated analysis.
- The material classes (e.g., steels, aluminum) are clearly labeled in the metadata, allowing for valid stratification.
- Mediation analysis is valid only when the mediator is measured, not estimated, to avoid circularity between predictors and the mediator.

# End of spec.md