# Feature Specification: Predicting Coating Adhesion Strength from Composition and Surface Features

**Feature Branch**: `001-predicting-coating-adhesion`  
**Created**: 2026-06-25  
**Status**: Draft  
**Input**: User description: "Predicting Coating Adhesion Strength from Composition and Surface Features"

## User Scenarios & Testing

### User Story 1 - Dataset Curation and Alignment (Priority: P1)

The researcher MUST be able to ingest raw data from three distinct sources (Materials Project API, NIST Surface Metrology Repository, and open-access literature sources), clean the records, and align them into a single, validated CSV dataset where every row represents a unique coating-substrate pair with complete feature vectors.

**Why this priority**: Without a unified, clean dataset, no modeling or feature importance analysis can occur. This is the foundational data engineering step.

**Independent Test**: The system can be tested by running the ingestion pipeline on a mock set of input files and verifying the output CSV contains the expected columns, no duplicate keys, and handles missing values according to the defined strategy.

**Acceptance Scenarios**:

1. **Given** raw CSV/JSON files from Materials Project API, NIST Surface Metrology Repository, and open-access literature sources, **When** the ingestion script executes, **Then** a unified `coating_adhesion_dataset.csv` is produced with at least 1,000 rows (up to a maximum of 5,000) and zero rows containing null values in the target variable (adhesion strength).
2. **Given** a coating-substrate pair with missing surface roughness data, **When** the preprocessing step runs, **Then** the record is either imputed using the median of the same substrate class or excluded, and a log entry is generated detailing the count of excluded records. Records with missing target variables (adhesion strength) MUST be excluded and logged.
3. **Given** duplicate entries for the same coating-substrate pair with conflicting adhesion values, **When** the deduplication step runs, **Then** the record with the most recent publication date or highest sample count is retained, and the others are discarded.

---

### User Story 2 - Predictive Modeling and Feature Importance (Priority: P2)

The researcher MUST be able to train a Gradient Boosting Regressor and a Random Forest Regressor on the curated dataset, perform nested cross-validation, and generate a ranked list of the top predictive features (compositional and surface) with their SHAP values.

**Why this priority**: This is the core scientific inquiry—identifying which variables drive adhesion. It directly addresses the research question.

**Independent Test**: The model training pipeline can be tested by running it on a small subset of the data (e.g., 100 rows) and verifying that the output includes a non-empty ranked feature list and that the cross-validation scores are within a plausible range (e.g., R² > -1).

**Acceptance Scenarios**:

1. **Given** the unified dataset, **When** the training script executes with -fold nested cross-validation, **Then** the system outputs a JSON report containing the mean R², RMSE, and MAE for both the Gradient Boosting and Random Forest models.
2. **Given** a trained model, **When** SHAP analysis is performed, **Then** the system generates a ranked list of the top features, distinguishing between compositional (e.g., crosslinker density proxy) and surface (e.g., RMS roughness) categories based on the defined Feature Categorization Schema.
3. **Given** the feature importance results, **When** the permutation importance test is run, **Then** the ranking of the top features remains stable (Spearman correlation > 0.8) compared to the SHAP ranking, confirming robustness.

---

### User Story 3 - Statistical Comparison and Baseline Benchmarking (Priority: P3)

The researcher MUST be able to compare the full-feature model against two baseline models (composition-only and surface-only) using a corrected statistical test to determine if the joint feature set provides a statistically significant improvement in predictive performance.

**Why this priority**: This validates the hypothesis that combining composition and surface data yields superior insights, fulfilling the "gap analysis" motivation.

**Independent Test**: The comparison logic can be tested by feeding the cross-validated RMSE scores from the three models into a Nadeau & Bengio corrected t-test function and verifying the output includes a p-value and a clear pass/fail conclusion based on the alpha threshold.

**Acceptance Scenarios**:

1. **Given** the RMSE scores from the full, composition-only, and surface-only models across 5 folds, **When** the statistical comparison script runs, **Then** it outputs a Nadeau & Bengio corrected t-test result with a p-value < 0.05 indicating the full model is significantly better than at least one baseline.
2. **Given** a null result where the full model does not outperform the baselines, **When** the script completes, **Then** it explicitly flags this outcome as "Informative Null" and records the specific hypothesis that interfacial chemistry (unmeasured variables) may dominate.
3. **Given** multiple hypothesis tests are performed (comparing full vs. comp-only, full vs. surface), **When** the analysis runs, **Then** a multiple-comparison correction (e.g., Bonferroni) is applied to the p-values before drawing conclusions.

---

### Edge Cases

- What happens when the dataset size exceeds the GB RAM limit of the GitHub Actions runner? (The system must implement chunked processing or sampling to stay within memory bounds).
- How does the system handle a scenario where the NIST repository returns a 404 error or an unexpected CSV schema? (The ingestion script must catch the error, log it, and halt with a clear message rather than crashing silently).
- What if the Materials Project API rate limit is hit during ingestion? (The script must implement exponential backoff retry logic, up to 3 attempts, before failing).

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest and merge data from the Materials Project API, NIST Surface Metrology Repository, and open-access literature sources into a single unified dataset, ensuring every row contains a valid adhesion strength target (See US-1).
- **FR-002**: System MUST encode compositional data using elemental one-hot vectors and derived descriptors (e.g., atomic radius variance, crosslinker density proxy) and standardize surface metrics (See US-1).
- **FR-003**: System MUST perform nested 5-fold cross-validation to train Gradient Boosting and Random Forest Regressors without data leakage (See US-2).
- **FR-004**: System MUST compute SHAP values and permutation importance to rank the top 10 predictive features, distinguishing between compositional and surface categories (See US-2).
- **FR-005**: System MUST execute a Nadeau & Bengio corrected t-test or permutation test with multiple-comparison correction (Bonferroni) to compare the full-feature model against composition-only and surface-only baselines (See US-3).
- **FR-006**: System MUST enforce a memory ceiling of 7 GB by sampling the dataset to ≤ 5,000 records maximum regardless of raw volume to ensure memory safety (See US-1).
- **FR-007**: System MUST implement a Mapping Protocol that documents the heuristic linking bulk properties (Materials Project) and surface data (NIST) to specific coating-substrate pairs in the literature, explicitly acknowledging the lack of unique identifiers (See US-1).
- **FR-008**: System MUST perform a sensitivity analysis on the 'crosslinker density' heuristic proxy by testing at least three different ratio-based definitions and reporting the variance in model performance (See US-2).
- **FR-009**: System MUST filter out all adhesion data not derived from ASTM pull-off tests to ensure methodological consistency of the target variable (See US-1).

### Key Entities

- **CoatingSubstratePair**: A unique record linking a specific coating formulation to a substrate material. Attributes: `coating_id`, `substrate_id`, `adhesion_strength`, `compositional_features`, `surface_features`.
- **FeatureDescriptor**: A quantitative metric used for prediction. Attributes: `name`, `type` (compositional/surface), `value`, `source`.
- **ModelRun**: A specific execution of the training pipeline. Attributes: `model_type`, `hyperparameters`, `cv_scores`, `feature_importance_ranking`.

#### Feature Categorization Schema
To ensure deterministic verification of feature categories:
- **Compositional Features**: Includes elemental one-hot vectors, atomic radius variance, electronegativity variance, and heuristic proxies for topology (e.g., crosslinker density derived from C/H/O ratios).
- **Surface Features**: Includes RMS roughness (Ra, Rq), skewness (Rsk), kurtosis (Rku), and bearing area curve parameters derived from NIST metrology data.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The pipeline must successfully process at least 95% of available valid records (defined as records with non-null targets in the raw input files) that fit within the 7 GB memory constraint (See US-1).
- **SC-002**: The predictive performance (R²) of the full-feature model is measured against the baseline models; a statistically significant improvement (p < 0.05 after correction) confirms the joint predictive signal (See US-3).
- **SC-003**: The top 10 feature list is measured for stability; the Spearman correlation between SHAP and permutation importance rankings must be ≥ 0.8 (See US-2).
- **SC-004**: The total runtime of the analysis pipeline is measured against the -hour GitHub Actions free-tier limit; the job must complete within 4 hours to ensure safety margin (See Assumptions).
- **SC-005**: The number of excluded records due to missing target variables is measured against the total raw records with valid target variables; this ratio must be < 10% to ensure sufficient statistical power (See US-1).

## Assumptions

- The Materials Project REST API and NIST Surface Metrology Repository remain accessible and do not change their data schema during the execution window.
- The dataset, even after merging, can be reduced to ≤ 5,000 records without losing the statistical power required to detect the expected effect size (R² is expected to indicate a moderate to strong fit.).
- **Construct Validity**: The lack of unique identifiers between bulk databases and specific coating formulations is acknowledged; the Mapping Protocol (FR-007) provides a defensible heuristic for linking these sources.
- **Methodological Consistency**: Only adhesion strength values derived from ASTM pull-off tests are included; scratch test or other method data is excluded to prevent systematic bias.
- The GitHub Actions free-tier runner provides sufficient disk I/O speed for the CSV read/write operations within the 6-hour time limit.
- No GPU is available; all machine learning models (Gradient Boosting, Random Forest, SHAP) are executed in CPU-only mode using scikit-learn and shap libraries.
- The 'crosslinker density' and 'atomic radius variance' are treated as heuristic proxies derived from elemental composition data, not direct physical measurements of polymer topology.