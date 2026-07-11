# Feature Specification: Predicting Molecular Halide Binding Affinities with Machine Learning

**Feature Branch**: `001-predicting-halide-binding-affinities`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "Predicting Molecular Halide Binding Affinities with Machine Learning"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

A researcher downloads experimental halide binding constants from NIST Chemistry WebBook and PubChem, filters records by solvent consistency (acetonitrile, chloroform, or dichloromethane), parses molecular structures from SMILES/InChI records, generates molecular fingerprints and descriptors, and filters the dataset to hosts with ≥3 different halide measurements for within-host comparison. If no verified data source is found or data is insufficient, the system triggers a simulated data fallback with explicit physics constraints and logs a failure to answer the primary research question.

**Why this priority**: This is the foundational data layer; without a clean, validated dataset, no modeling or analysis can proceed. It delivers the core research asset.

**Independent Test**: Can be fully tested by running the data pipeline on a small sample subset (or simulated data) and verifying the output CSV contains valid binding constants, halide identities, solvent tags, and molecular descriptors for ≥3 halides per host.

**Acceptance Scenarios**:

1. **Given** a query for "halide binding constant" on NIST/PubChem, **When** the pipeline downloads and parses records, **Then** the output CSV contains columns for host SMILES, halide identity (F⁻/Cl⁻/Br⁻/I⁻), binding constant (log K or ΔG), solvent type (acetonitrile, chloroform, or DCM), and source reference
2. **Given** a host molecule with measurements for F⁻, Cl⁻, and Br⁻ in the same solvent, **When** the filtering step runs, **Then** the host is retained in the dataset; hosts with a limited number of halide measurements or mixed solvents are excluded
3. **Given** a host molecule record without a valid SMILES string, **When** the pipeline validates molecular structures, **Then** the record is logged as invalid and excluded from the final dataset
4. **Given** a record with a binding constant measured in water, **When** the solvent filter runs, **Then** the record is excluded as water is not in the allowed solvent list (acetonitrile, chloroform, DCM)

---

### User Story 2 - Model Training and Cross-Validation (Priority: P2)

A researcher trains random forest and gradient boosting models using scikit-learn to predict binding affinity from structural features, with k-fold cross-validation split by host molecule identity (not by measurement) to avoid data leakage, ensuring the process completes within the documented compute budget.

**Why this priority**: This delivers the core predictive capability and model performance metrics that answer the research question. It depends on US-1 but is independently testable once data exists.

**Independent Test**: Can be fully tested by training a random forest model on the preprocessed dataset and verifying that cross-validation produces R² and RMSE metrics without data leakage (i.e., same host identity does not appear in both train and test folds) and completes within the defined time/RAM limits.

**Acceptance Scenarios**:

1. **Given** the preprocessed dataset with ≥3 halides per host, **When** the 5-fold cross-validation split runs, **Then** no host molecule identity appears in both training and validation sets within the same fold
2. **Given** a trained random forest model, **When** cross-validation completes, **Then** the output includes R² and RMSE metrics for each fold and their mean/std across folds
3. **Given** the full dataset, **When** model training completes, **Then** the process finishes within ≤6 hours on a GitHub Actions free-tier runner (2 vCPU, 7 GB RAM) with ≤7 GB RAM peak usage

---

### User Story 3 - Feature Importance Analysis and Visualization (Priority: P3)

A researcher performs feature stability analysis to identify robust predictive determinants of halide selectivity, generates partial dependence plots showing affinity trends across the halide series (F⁻→Cl⁻→Br⁻→I⁻), and produces interpretable associational insights into which molecular features correlate with halide preference.

**Why this priority**: This delivers the mechanistic insights that answer "what structural features determine affinity" and "how does this vary across halide identity." It depends on US-2 but can be independently tested once models exist.

**Independent Test**: Can be fully tested by running feature stability analysis on a trained model and verifying the output includes a ranked list of top features with stability scores (coefficient of variation < 0.3), plus partial dependence plots for at least 2 key features.

**Acceptance Scenarios**:

1. **Given** a trained gradient boosting model, **When** feature stability analysis (multiple bootstrap resamples) runs, **Then** the output includes a ranked list of top 10 features with stability scores (coefficient of variation)
2. **Given** the fitted model and test set, **When** partial dependence plots are generated, **Then** the plots show affinity trends for at least 2 features (e.g., hydrogen-bond donor count, cavity size) across the halide series
3. **Given** the feature importance results, **When** the researcher reviews the top determinants, **Then** the output includes a summary table mapping features to their hypothesized chemical interpretation (e.g., "cationic center density → electrostatic attraction")

---

### User Story 4 - Statistical Rigor & Reporting (Priority: P4)

A researcher performs pairwise statistical comparisons of model performance across halide ions using **Bootstrap Confidence Intervals (95% CI, 10,000 resamples)** to compare mean R²/RMSE values, and generates a final report that explicitly states the findings are associational and includes a confidence interval summary for performance differences.

**Why this priority**: This ensures the scientific validity of the comparative claims required by the Constitution (Principle VI) and addresses the risk of small sample sizes and correlated data. It depends on US-2.

**Independent Test**: Can be fully tested by running the comparison script on the cross-validation results and verifying the output report contains 95% confidence intervals for performance differences and an associational disclaimer.

**Acceptance Scenarios**:

1. **Given** the per-halide R² and RMSE metrics from 5-fold cross-validation, **When** the comparison script runs, **Then** it calculates the difference in mean R²/RMSE between halide pairs and computes 95% confidence intervals using bootstrap resampling
2. **Given** the final report generation, **When** the report is rendered, **Then** it explicitly states that all findings are associational and not causal
3. **Given** a pairwise comparison of performance metrics, **When** the discrepancy is calculated, **Then** any absolute difference in R² or RMSE ≥ 0.1 is flagged in the report with its 95% CI
4. **Given** the smallest halide-specific test set, **When** the analysis runs, **Then** the report includes 95% confidence intervals for the performance difference; if the CI includes zero, the difference is reported as "not statistically distinguishable"

---

### Edge Cases

- What happens when NIST/PubChem records have inconsistent units for binding constants (some report log K, others ΔG in kcal/mol)?
- How does the system handle host molecules with ambiguous halide identity labels (e.g., "halide" without specifying F⁻/Cl⁻/Br⁻/I⁻)?
- What happens when the dataset contains fewer than 50 host molecules after filtering (insufficient for 5-fold cross-validation)?
- How does the system handle duplicate records for the same host-halide pair with different reported binding constants?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST attempt to download data from NIST Chemistry WebBook and PubChem using specific scraping logic: `requests` library with 2s delay between requests, exponential backoff (max limited number of retries) for 429/503 errors, and `BeautifulSoup` parsing of HTML tables. Filter records to those measured in consistent solvent conditions: **acetonitrile, chloroform, or dichloromethane**. If no verified URL is found or data is insufficient (0 records found after scraping), trigger FR-011 immediately. (See US-1)
- **FR-002**: System MUST generate molecular fingerprints (ECFP) and RDKit descriptors from SMILES/InChI records for each host molecule (See US-1)
- **FR-003**: System MUST filter the dataset to retain only host molecules with ≥3 different halide measurements (F⁻, Cl⁻, Br⁻, I⁻) for within-host comparison (See US-1)
- **FR-004**: System MUST split data by host molecule identity (not by measurement) during k-fold cross-validation to prevent data leakage (See US-2)
- **FR-005**: System MUST train random forest and gradient boosting models using scikit-learn>=1.4.0 with default hyperparameters, without GPU/CUDA acceleration, on a GitHub Actions free-tier runner (2 vCPU, 7 GB RAM) (See US-2)
- **FR-006**: System MUST perform feature stability analysis (multiple bootstrap resamples) to identify robust predictive determinants of halide selectivity (See US-3)
- **FR-007**: System MUST generate partial dependence plots for at least 2 key features showing affinity trends across the halide series (See US-3)
- **FR-008**: System MUST frame all predictive findings as associational (not causal) in documentation, given the observational nature of the dataset (See US-4)
- **FR-009**: System MUST compare R² and RMSE metrics across halide ions using **Bootstrap Confidence Intervals (95% CI, 10,000 resamples)** to assess if differences are statistically distinguishable from zero. The system MUST NOT use the Paired Wilcoxon signed-rank test on fold-level aggregates due to insufficient sample size (N=5) and invalid pairing assumptions. (See US-4)
- **FR-010**: System MUST verify presence of raw SMILES or InChI strings for every host record; if missing, exclude the record and log the exclusion count (See US-1)
- **FR-011**: System MUST verify the primary dataset contains ≥50 host molecules with ≥3 halides each and the `binding_constant` column. **IF** this fails, the system MUST: (1) Log the exact warning: "WARNING: Insufficient data (<50 hosts). Comparative analysis aborted. Switching to single-halide prediction mode with simulated data."; (2) Identify the most abundant halide in the available data; (3) Generate a simulated dataset where `log K_sim = 0.5 * charge_density + 0.3 * cavity_volume + N(0, 0.2)` (Gaussian noise). Here, `charge_density` is defined as the sum of Gasteiger charges on the host molecule, and `cavity_volume` is defined as the molecular volume (Å³) calculated via RDKit; (4) Validate the simulated data against `dataset.schema.yaml` before use; (5) Mark all outputs as "Simulated Data Mode" and explicitly state that the project FAILS to answer the primary comparative research question. (See US-1)
- **FR-012**: System MUST verify that the dataset contains at least 10 host molecules per halide group before attempting detailed analysis; if N < 10 for any group, the system MUST report the analysis as "underpowered" and focus on reporting 95% Confidence Intervals for performance differences rather than significance testing. Post-hoc power analysis is explicitly excluded. (See US-4)
- **FR-013**: System MUST report feature stability (coefficient of variation) for the top features across multiple bootstrap resamples; features with CV ≥ 0.3 are flagged as "unstable". Additionally, the system MUST perform a **Physical Plausibility Check**: verify that the sign of the coefficient for the top feature aligns with first-principles electrostatics (e.g., positive charge density correlates with increased anion affinity). This replaces the undefined 'curated list' validation. (See US-3)

### Key Entities *(include if feature involves data)*

- **HostMolecule**: Represents an organic host compound with attributes SMILES, InChI, molecular descriptors (ECFP4 fingerprint, RDKit descriptors), and associated binding measurements
- **BindingMeasurement**: Represents a single experimental measurement with attributes host_id, halide_identity (F⁻/Cl⁻/Br⁻/I⁻), binding_constant (log K or ΔG), units, source (NIST/PubChem/Simulated), solvent, and reference DOI
- **ModelRun**: Represents a trained model instance with attributes model_type (random_forest/gradient_boosting), cross_validation_folds, R²_mean, R²_std, RMSE_mean, RMSE_std, and feature_stability_ranking

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Out-of-sample R² is measured against the 5-fold cross-validation held-out host molecule identities to assess predictive performance on unseen hosts (See US-2)
- **SC-002**: Feature stability ranking is measured against the coefficient of variation (CV) of importance scores across multiple bootstrap resamples. to identify robust determinants of halide selectivity (See US-3)
- **SC-003**: Model training runtime is measured against the documented compute budget (hours on 2 vCPU, 7 GB RAM, GitHub Actions ubuntu-latest runner) defined in Assumptions (See US-2)
- **SC-004**: Dataset completeness is measured against the required variables (host SMILES, halide identity, binding constant, solvent) to verify dataset-variable fit (See US-1)
- **SC-005**: Performance differences between halide ions MUST be reported with 95% Confidence Intervals (sufficient bootstrap resamples); if the CI includes zero, the difference is reported as "not distinguishable" (See US-4)
- **SC-006**: 95% Confidence Intervals for performance differences MUST be reported for the smallest halide-specific test set; if the sample size is < 10, the CI width is reported as "wide" (See US-4)
- **SC-007**: Feature stability is measured against the coefficient of variation (CV) of top 10 features; features with CV < 0.3 are considered "stable". Additionally, the top feature's sign MUST align with Coulombic attraction principles (See US-3)

## Assumptions

- **Data Availability Contingency**: We assume that NIST Chemistry WebBook and PubChem contain binding constants for all four halide ions (F⁻, Cl⁻, Br⁻/I⁻) for a sufficient number of host molecules (≥50 hosts with ≥3 halides each) to support 5-fold cross-validation. **IF** this assumption fails (i.e., <50 hosts or missing columns), the project scope reduces to single-halide prediction using a simulated dataset (FR-011), and the comparative analysis (US-4) is explicitly aborted and flagged as unanswerable.
- The filtering threshold of ≥3 different halide measurements per host is justified by the need for within-host comparison across the halide series, enabling analysis of how affinity varies by halide identity for the same receptor
- All molecular structure data in NIST/PubChem records is provided in valid SMILES or InChI format parseable by RDKit; records with invalid structures are excluded from the dataset
- The scikit-learn random forest and gradient boosting implementations can complete training on the full dataset within ≤6 hours on a GitHub Actions free-tier runner (2 vCPU, 7 GB RAM) without GPU acceleration
- Binding constants in NIST/PubChem records are reported in consistent units (log K or ΔG) that can be standardized; any records with ambiguous or non-standard units are excluded
- The observational nature of the dataset (no random assignment of hosts to halides) means all reported structure-affinity relationships are associational, not causal; no identification strategy or randomization is available to support causal claims
- Molecular descriptors (ECFP4 fingerprints, RDKit descriptors) may exhibit collinearity; the analysis will report joint relationships descriptively and include a collinearity diagnostic (e.g., variance inflation factor) rather than claiming independent predictive effects for definitionally related descriptors
- The dataset size after filtering will fit within available RAM and disk on the GitHub Actions runner; if the full dataset exceeds this, a representative subset will be sampled and the scoping decision will be documented
- No validated questionnaires or psychometric instruments are used in this study (chemistry domain), so the measurement validity requirement for citable validation does not apply; molecular descriptors are standard computational chemistry tools with established community usage
- The primary solvent for halide binding constants in the target literature is non-aqueous (e.g., acetonitrile, chloroform, DCM); water-based measurements are excluded to avoid confounding by solvation effects
- **Constitution Compliance**: The `Advancement-Evaluator Agent` MUST update `state.yaml` on every artifact change (Constitution Principle V), specifically by appending a content hash of the modified file to the `artifacts` list in `state.yaml` upon every commit. The `Reference-Validator Agent` MUST validate all citations against primary sources (Constitution Principle II), specifically by verifying DOI existence and abstract match for all citations, and failing the build if validation fails.