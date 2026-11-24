# Feature Specification: Predicting the Influence of Composition on the Thermal Expansion of Metallic Glasses

**Feature Branch**: `001-gene-regulation`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Predicting the Influence of Composition on the Thermal Expansion of Metallic Glasses"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Feature Extraction (Priority: P1) (US-1)

The system must retrieve metallic glass composition and CTE data from a **curated literature dataset** (provided as a CSV file) and supplement this with any additional entries identified via text‑search for the keyword “glass” in the Materials Project and AFLOWlib APIs. It must filter specifically for entries flagged as amorphous or metallic glass (via the curated dataset) and extract compositional descriptors (weighted mean atomic radius, electronegativity variance, valence electron concentration, **atomic size coefficient of variation** (referred to as “atomic size mismatch” in Constitution VI) for every entry.

**Why this priority**: Without a clean, feature‑rich dataset filtered for the correct material state, no modeling or analysis can occur. This is the foundational step for the entire research pipeline.

**Independent Test**: Can be fully tested by running the data ingestion script and verifying that the output CSV contains exactly the required columns (composition, CTE, weighted mean atomic radius, electronegativity variance, VEC, atomic size coefficient of variation) with no missing values for the selected metallic‑glass subset, and that the ‘amorphous state flag’ is present and used for filtering. Note: the atomic size coefficient of variation is defined as the standard deviation of atomic radii divided by the weighted mean atomic radius, providing an independent descriptor from the mean radius.

**Acceptance Scenarios**:

1. **Given** valid API credentials for Materials Project and AFLOWlib, **When** the ingestion script runs, **Then** the output dataset contains **all available unique metallic‑glass entries** (≥ 500 entries) with valid CTE values and amorphous state flags. If fewer than 500 entries are retrieved, the pipeline **fails** and logs an error indicating insufficient data (target: ≥ 500 entries).

2. **Given** a raw composition string (e.g., "Zr50Cu40Al10"), **When** the feature extraction module processes it, **Then** it calculates and appends the weighted mean atomic radius, electronegativity variance, valence electron concentration, and atomic size coefficient of variation.

3. **Given** a dataset entry where the CTE value is missing, unreliable, or not flagged as amorphous in the source, **When** the ingestion script runs, **Then** that entry is excluded from the final training dataset.

---

### User Story 2 - Model Training and Cross-Validation (Priority: P2) (US-2)

The system must train baseline linear regression and random forest models using scikit-learn on CPU, performing k-fold cross-validation to tune hyperparameters within strict resource limits.

**Why this priority**: This step establishes the predictive capability of the composition‑CTE mapping and determines if the relationship is learnable from composition alone.

**Independent Test**: Can be fully tested by executing the training pipeline on a sample subset and verifying that the k-fold cross-validation scores (R², MAE) are generated as non‑null, finite numbers, and that the final model is saved without exceeding standard RAM or CPU core constraints.

**Acceptance Scenarios**:

1. **Given** a preprocessed dataset split into training (a majority split) and testing (a minority split) sets, **When** the training pipeline runs, **Then** it completes k-fold cross-validation with a grid search over a range of parameter combinations for both linear regression and random forest models.

2. **Given** a random forest model with a specific `max_depth` and `n_estimators`, **When** the model is trained, **Then** the training job completes within 30 minutes on a 2‑core CPU environment.

3. **Given** the trained models, **When** the evaluation step runs, **Then** it outputs the R², MAE, and RMSE metrics for the held‑out test set.

---

### User Story 3 - Statistical Significance and Feature Importance Analysis (Priority: P3) (US-3)

The system must perform permutation testing (≥ 1000 iterations) to validate that model performance exceeds random chance and generate feature importance rankings to identify key compositional drivers.

**Why this priority**: This step provides the statistical rigor required to claim that the observed composition‑CTE relationship is real and not an artifact of overfitting or noise.

**Independent Test**: Can be fully tested by running the significance analysis script on the trained model and verifying that a p‑value is reported for all models (flagging “Null Result” if R² < 0.3), and that a ranked list of feature importances is generated. The system must output the Spearman rank correlation between feature importance and absolute correlation coefficients as a diagnostic metric, and also report Kendall‑τ for the same rankings.

**Acceptance Scenarios**:

1. **Given** a trained model, **When** the permutation test (≥ 1000 iterations) runs, **Then** it reports a p‑value; if R² < 0.3, the system flags a “Null Result” status; otherwise, it reports the p‑value.

2. **Given** the trained random forest model, **When** the feature importance analysis runs, **Then** it outputs a ranked list of compositional descriptors (e.g., “atomic size coefficient of variation” ranked #1) with their relative importance scores.

3. **Given** a null result (R² < 0.3), **When** the analysis runs, **Then** the system correctly flags the model as not significantly better than random chance and outputs a “Null Result” status.

---

### Edge Cases

- What happens when the API returns no data for a specific alloy family (e.g., Pd‑based)? The system must skip that family and log a warning, rather than crashing.
- How does the system handle alloys with undefined or ambiguous chemical formulas? The system must exclude these entries during the ingestion phase.
- What happens if the dataset size exceeds 7 GB RAM? The system must implement a sampling strategy to reduce the dataset to ≤ 10 000 rows before training (randomly sample without replacement) and log the reduction; this ensures the pipeline stays within memory limits.

## Requirements

### Functional Requirements

- **FR-001**: System MUST retrieve metallic‑glass composition and CTE data from a curated literature dataset (CSV) and augment it with any additional entries identified via a text‑search for “glass” in the Materials Project and AFLOWlib APIs. The system must achieve **≥ 95 % coverage of the curated dataset** (i.e., retrieve at least 95 % of known metallic‑glass entries) (See US-1). *Justification*: Direct API flags for amorphous materials are unavailable; a curated dataset ensures reliable ground‑truth while the supplemental search maximizes coverage of additional entries. *Note*: If the total number of ingested entries after filtering is **< 500**, the downstream power analysis (FR-011) will report the resulting statistical power and the study will proceed with a documented limitation.

- **FR-002**: System MUST extract compositional descriptors including weighted mean atomic radius, electronegativity variance, valence electron concentration, and **atomic size coefficient of variation** (σ/μ) for each alloy (See US-1). *Note*: This descriptor corresponds to “atomic size mismatch” referenced in Constitution VI.

- **FR-003**: System MUST split the dataset into training and testing sets using a **stratified split by alloy family** (defined as the set of constituent elements, e.g., Zr‑Cu‑Al vs. Pd‑Ni‑P). The stratification uses the alloy‑family identifier as the grouping key for GroupKFold. If a family has insufficient samples to form both folds, the system MUST revert to a random split (See US-2).

- **FR-004**: System MUST train linear regression and random forest models using scikit-learn, performing k-fold cross-validation with a grid search over a range of parameter combinations (See US-2).

- **FR-005**: System MUST execute a permutation test with **≥ 1000 iterations** to assess whether model performance exceeds random chance, reporting p‑values (See US-3).

- **FR-006**: System MUST generate feature importance rankings for the trained models to identify the most influential compositional descriptors (See US-3).

- **FR-007**: System MUST enforce resource constraints, ensuring the entire pipeline runs on **≤ 2 CPU cores** and **≤ 7 GB RAM** without GPU acceleration (See US-2).

- **FR-008**: System MUST calculate Variance Inflation Factors (VIF) for all compositional descriptors and remove any feature with VIF > 5.0 prior to model training to address multicollinearity (See US-1). **Fallback**: if *all* descriptors exceed VIF > 5.0, apply Principal Component Analysis retaining the first two components and use these components as predictors. When a descriptor is removed due to high VIF, priority is given to retaining the weighted mean atomic radius; the atomic size coefficient of variation is dropped only if its VIF exceeds the threshold after the mean radius is retained.

- **FR-009**: System MUST record the source method (DFT vs. Experimental) and thermal‑history metadata for each CTE entry **when available**. If **more than 20 %** of entries lack this metadata, the system performs a sensitivity analysis on the subset with metadata and reports the ΔR² impact; otherwise, it flags the incomplete entries and proceeds (See US-1).

- **FR-010**: System MUST set fixed random seeds for all stochastic operations (train_test_split, GroupKFold, permutation testing, model initialization) using the seed value **42** to satisfy reproducibility requirements (Principle I) (See US-2, US-3).

- **FR-011**: System MUST conduct a statistical power analysis prior to modeling, targeting a minimum sample size of **500 metallic‑glass entries** to detect an effect size of **f² = 0.15** with **power ≥ 0.8** at **α = 0.05** (See US-2). If the available sample size is below 500, the analysis must report the resulting power and the study proceeds only with a documented limitation.

- **FR-012**: System MUST record the source method (DFT vs. Experimental) and thermal‑history metadata for each CTE entry; if metadata is inconsistent across the dataset, the system MUST flag these entries and perform a sensitivity analysis by training models with and without the flagged entries and reporting the ΔR² (See US-1). *(Retained for explicitness; see FR-009 for primary handling.)*

### Key Entities

- **MetallicGlassEntry**: Represents a single alloy sample with attributes for composition (chemical formula), CTE (thermal expansion coefficient), and derived compositional descriptors.
- **ModelPerformance**: Represents the evaluation results of a trained model, including R², MAE, RMSE, and p‑values from permutation tests.
- **FeatureImportance**: Represents the ranking of compositional descriptors by their contribution to the model's predictive power.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Predictive accuracy (R²) is measured against a *baseline model* that predicts CTE as a weighted average of elemental CTE values sourced from the NIST Thermophysical Properties of Substances database (external, not derived from the alloy dataset). The baseline R² is reported and the primary model must improve **by at least ΔR² > 0.05** over this baseline (See US-2).

- **SC-002**: Statistical significance (p‑value) of the model's performance is measured against the null hypothesis of random chance via permutation testing using **≥ 1000 iterations** (See US-3).

- **SC-003**: Feature importance rankings (using SHAP values for linear regression and permutation importance for random forest) are compared against the magnitude of absolute correlation coefficients between each descriptor and CTE; the system MUST report both the Spearman rank correlation coefficient (ρ) **and** the Kendall‑τ correlation between the two rankings as diagnostic metrics (See US-3). For linear regression, standardized coefficients are used as the model‑agnostic importance to avoid deterministic correlation.

- **SC-004**: Computational efficiency (runtime and memory usage) is measured against the GitHub Actions free‑tier limits (≤ 2 cores, ≤ 7 GB RAM, ≤ 6 hours). The pipeline must log actual runtime and peak memory and report a pass/fail status relative to these limits (See US-2).

- **SC-005**: Ingestion completeness – the pipeline must retrieve and successfully process **≥ 95 %** of metallic‑glass entries from the curated dataset, and the final processed dataset must contain **≥ 500** entries with no missing descriptor values (See US-1).

## Assumptions

- The curated literature dataset provides metallic‑glass composition and experimentally measured CTE values for at least 500 entries. The Materials Project and AFLOWlib APIs are used **only** for supplemental text‑search retrieval of additional glass entries; they do **not** provide a dedicated `material_type` flag nor experimental CTE values for glasses.
- The compositional descriptors (weighted mean atomic radius, electronegativity variance, VEC, atomic size coefficient of variation) are sufficient to capture the non‑linear relationships between composition and CTE in amorphous alloys.
- The dataset size can be reduced to ≤ 10 000 samples via random sampling if the full dataset exceeds 7 GB RAM, without significantly biasing the results.
- The random forest and linear regression models can be trained effectively on CPU without requiring GPU acceleration or specialized hardware.
- The CTE values in the curated dataset are consistent and comparable across different alloy families, allowing for a unified analysis. **Note**: This assumption is mitigated by FR‑009, which tracks source method and thermal history to identify inconsistencies.
- The curated literature dataset is the primary source for metallic‑glass data because external APIs lack amorphous‑material flags; supplemental API searches are used only to increase coverage where possible.
