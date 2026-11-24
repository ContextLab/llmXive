# Feature Specification: Investigating the Relationship Between Plant Secondary Metabolite Profiles and Herbivore Resistance

**Feature Branch**: `001-investigating-plant-metabolite-herbivore-resistance`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Investigating the Relationship Between Plant Secondary Metabolite Profiles and Herbivore Resistance"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) (US-1)

The system must successfully ingest raw metabolomics and herbivory data from multiple public repositories (MetaboLights, PMN, HPID), filter for complete cases, and normalize the data for analysis.

**Why this priority**: Without a clean, unified dataset, no statistical analysis or modeling can occur. This is the foundational step that enables all subsequent research.

**Independent Test**: The pipeline can be fully tested by running the ingestion script against a small, known subset of CSV/TSV files and verifying the output is a single normalized DataFrame with no missing values in the required columns.

**Acceptance Scenarios**:

1. **Given** raw CSV/TSV files containing metabolite concentrations and herbivory scores, **When** the ingestion script is executed, **Then** the system outputs a consolidated DataFrame with a substantial set of plant species and no missing values in the target columns.
2. **Given** a dataset with inconsistent column names across sources, **When** the preprocessing module runs, **Then** all metabolite concentrations are standardized to z-scores and herbivory scores are mapped to a unified scale.
3. **Given** a dataset exceeding 7 GB RAM, **When** the batch processing logic is triggered, **Then** the system processes data in batches of **≤ 20 species** and completes without memory overflow.

---

### User Story 2 - Exploratory Analysis and Correlation Visualization (Priority: P2) (US-2)

The system must compute correlation matrices between metabolite classes (alkaloids, terpenes, phenolics, benzoxazinoids) and herbivory damage indices, generating visual heatmaps for immediate inspection.

**Why this priority**: This provides the first empirical insight into the research question, allowing researchers to identify potential biomarkers before running complex models.

**Independent Test**: The analysis can be tested by running the correlation module on the preprocessed dataset and verifying that a heatmap PNG is generated showing significant negative correlations for at least one metabolite class.

**Acceptance Scenarios**:

1. **Given** the preprocessed dataset with z-scored metabolite concentrations, **When** the correlation analysis is executed, **Then** a correlation matrix is computed and a heatmap PNG is saved to the `outputs/` directory.
2. **Given** a metabolite class with no significant correlation to herbivory (q > 0.05 after correction), **When** the analysis runs, **Then** the heatmap visually distinguishes non‑significant correlations from significant ones (e.g., via color intensity or annotation).
3. **Given** a dataset with >100 plant species, **When** the analysis runs with parallelization (n_jobs=2) on a **standard CPU: 2.9 GHz Intel Xeon E5‑2686 v4 (28 cores) on the GitHub Actions Ubuntu‑latest runner**, **Then** the computation completes within 15 minutes.

---

### User Story 3 - Predictive Modeling and Feature Importance Ranking (Priority: P3) (US-3)

The system must fit a multiple linear regression model and a Random Forest regressor to predict herbivory scores from metabolite profiles, ranking predictors by feature importance.

**Why this priority**: This directly addresses the "predictive power" aspect of the research question, identifying which metabolite signatures are the strongest biomarkers.

**Independent Test**: The modeling pipeline can be tested by splitting the data 80/20, training the models, and verifying that the Random Forest model outputs a ranked list of features and the regression model achieves an R² > 0.3 on an **independent validation set**.

**Acceptance Scenarios**:

1. **Given** the preprocessed dataset, **When** the multiple linear regression model is trained, **Then** the model outputs coefficients, p‑values, and an R² value, with multicollinearity diagnostics (VIF) calculated for all predictors.
2. **Given** the preprocessed dataset, **When** the Random Forest regressor (max_depth=5) is trained with 5‑fold cross‑validation, **Then** the model outputs a ranked list of metabolite predictors by feature importance and an adjusted R² score.
3. **Given** a model with low predictive power (R² < 0.1) on the independent validation set, **When** the validation step runs, **Then** the system logs a warning indicating that no strong biomarkers were identified in the current dataset.

---

### Edge Cases

- What happens when a dataset lacks a specific metabolite class (e.g., no benzoxazinoids for a specific plant family)? The system must handle missing columns gracefully by imputing zeros for the absent class or excluding the class for that species, rather than crashing.
- How does the system handle datasets with extreme outliers in herbivory scores? The preprocessing step must include an outlier detection mechanism (e.g., IQR method) to flag or cap values before normalization.
- What happens if the public repository APIs (MetaboLights, HPID) are temporarily unavailable? The system must implement a retry logic (max 3 attempts with 30‑second backoff) and fail gracefully with a clear error message.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and parse metabolomics and herbivory data from MetaboLights, PMN, and HPID repositories, **ensuring at least 50 plant species with paired data are obtained**; if fewer than 50 are available, the system MUST abort and report “insufficient paired data” (See US-1).
- **FR-002**: System MUST normalize metabolite concentrations using z‑score standardization and handle missing values by filtering rows with any missing required predictor or outcome; for metabolite‑class columns absent from a dataset, the system shall impute zeros for those classes (See US-1).
- **FR-003**: System MUST compute correlation matrices between metabolite classes and herbivory indices, generate a heatmap visualization, and automatically identify **3‑5 metabolite classes** that show a statistically significant **negative** correlation **after multiple‑comparison correction (q < 0.05)**. The identified classes shall be listed in a summary report (See US-2).
- **FR-004**: System MUST perform a baseline multiple linear regression (ordinary least squares) with herbivory score as the dependent variable and metabolite concentrations as predictors, calculating VIF to assess multicollinearity (See US-3).
- **FR-005**: System MUST train a Random Forest regressor (max_depth=5) with 5‑fold cross‑validation to rank metabolite predictors by feature importance (See US-3).
- **FR-006**: System MUST apply a multiple‑comparison correction (Benjamini‑Hochberg) to all p‑values derived from correlation and regression tests to control the false discovery rate (See US-2, US-3).
- **FR-007**: System MUST validate the dataset‑variable fit by explicitly checking that every required predictor and outcome variable is present in the source data before analysis begins (See US-1).
- **FR-008**: System MUST additionally account for phylogenetic non‑independence among plant species by employing a phylogenetic generalized least squares (PGLS) regression or a mixed‑effects model with a species‑level random effect when estimating relationships between metabolites and herbivory. Results from the phylogenetic model must be reported alongside the baseline OLS results and any substantial differences (e.g., changes in coefficient significance or effect size) must be documented (See US-3).
- **FR-009**: System MUST validate the metabolite classes identified in FR-003 against an external curated literature list of known plant defense compounds (e.g., the PlantCyc defense metabolite database) and report the overlap percentage in the summary report (See US-2).
- **FR-010**: System MUST evaluate predictive performance on an **independent validation set** that was not used for training or cross‑validation, reporting R² for both the linear regression and Random Forest models (See US-3).
- **FR-011**: System MUST limit the number of predictor variables to **≤ 20 total** (no more than 5 metabolites per class) selected by highest variance across species; if the raw feature set exceeds this bound, the system shall perform variance‑based selection before modeling (See US-3).

### Key Entities

- **PlantSpecies**: Represents a distinct plant species, containing attributes for species name, family, and unique identifier.
- **MetaboliteProfile**: Represents the chemical composition of a plant, containing attributes for concentrations of alkaloids, terpenes, phenolics, and benzoxazinoids.
- **HerbivoryScore**: Represents the quantified damage level caused by herbivores, containing attributes for the damage index and measurement method.
- **AnalysisResult**: Represents the output of the statistical analysis, containing attributes for correlation coefficients, p‑values, regression coefficients, and feature importance scores.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The number of plant species with complete paired data is measured against the target of **≥ 50 species** (See FR-001).
- **SC-002**: The predictive performance of the regression models (R²) is measured against the threshold of **> 0.3 on the independent validation set** (See FR-010).
- **SC-003**: The false discovery rate (FDR) of significant correlations is measured against the corrected q‑value threshold (**q < 0.05**) and the summary report must list the metabolite classes meeting the negative‑correlation criterion after correction (See FR-003, FR-009).
- **SC-004**: The multicollinearity among predictors is measured against the VIF threshold of **< 5** to ensure model stability (See FR-004).
- **SC-005**: The runtime of the analysis pipeline is measured as wall‑clock elapsed time recorded by start/end timestamps in the pipeline log; the logged duration must not exceed **6 hours on the standard GitHub Actions runner (2 vCPU, 7 GB RAM, Ubuntu‑latest)** (See FR-005).

## Assumptions

- **Assumption about data availability**: Public repositories (MetaboLights, PMN, HPID) contain sufficient paired data for at least **50 plant species** across the four specified metabolite classes; if this threshold cannot be met, the analysis aborts as per FR-001.
- **Assumption about measurement validity**: The herbivory damage scores in the source datasets are derived from validated, standardized protocols (e.g., visual scoring, leaf area loss) and are comparable across different studies.
- **Assumption about computational constraints**: The analysis can be completed within the 7 GB RAM and 6‑hour runtime limits of a GitHub Actions free‑tier runner by processing data in batches of ≤ 20 species and using CPU‑tractable methods (scikit‑learn, statsmodels).
- **Assumption about methodological framing**: Since the data is observational, all findings regarding metabolite‑herbivore relationships will be framed as associational rather than causal.
- **Assumption about threshold justification**: The VIF threshold of **< 5** for multicollinearity is based on standard statistical practice for regression diagnostics in biological studies.
- **Assumption about sensitivity analysis**: A sensitivity analysis will be performed on the q‑value threshold (sweeping between 0.01 and 0.10) to assess the robustness of the identified biomarkers.
- **Assumption about phylogenetic correction**: Phylogenetic relationships among plant species are obtained from the Open Tree of Life and incorporated via PGLS or mixed‑effects models to control for non‑independence. Both the baseline OLS analysis (FR-004) and the phylogenetically corrected analysis (FR-008) will be performed to assess robustness of findings (justified by scientific‑soundness concern).
- **Assumption about external validation list**: The external curated list of known defense metabolites is sourced from the PlantCyc database (accessed 2023‑10‑01) and is considered authoritative for FR-009.
- **Assumption about US‑N convention**: User Story identifiers (US‑1, US‑2, US‑3) correspond to the three user stories above; this mapping resolves earlier terminology inconsistencies.
