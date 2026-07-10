# Feature Specification: Neural Oscillations as a Biomarker for Predicting Response to Transcranial Direct Current Stimulation

**Feature Branch**: `001-neural-oscillations-tDCS-biomarker`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Can resting‑state and task‑related EEG oscillatory features predict an individual’s motor performance improvement after a single session of anodal tDCS over the primary motor cortex?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

The system must ingest raw EEG and tDCS performance data from verified public repositories. The system MUST first perform a **Source Verification Task** to explicitly identify and verify the existence of a single-source dataset containing BOTH raw EEG time-series and paired tDCS outcome scores for the same subjects. The system MUST search OpenNeuro, PhysioNet, and Kaggle using the query "EEG AND tDCS AND motor". If such a dataset exists, the system proceeds to **Primary Mode**. If no such single-source paired dataset exists in the public domain, the system MUST NOT attempt to pair data from separate repositories (e.g., PhysioNet EEG + OpenNeuro tDCS). Instead, it MUST switch to **Data Insufficient Mode**, log the specific reason (lack of paired data), and terminate the statistical modeling pipeline without generating synthetic data for inference.

**Why this priority**: Without clean, aligned data from a single verified source, no statistical modeling is possible. Cross-dataset matching is scientifically invalid due to differing subject populations and protocols. This step ensures the project does not proceed with invalid data assumptions.

**Independent Test**: Can be fully tested by running the ingestion script against the canonical PhysioNet EEG Motor Movement/Imagery Dataset (BIDS/EDF) and a verified tDCS source. If no single source contains both, the system MUST log "Data Insufficient: No single-source paired dataset found" and exit with code 0 (success of validation) but no statistical output. The system MUST output a `verified_source_manifest.json` file.

**Acceptance Scenarios**:

1. **Given** a verified single-source dataset containing both raw EEG (BIDS/EDF) and paired tDCS motor scores, **When** the preprocessing script runs, **Then** it outputs aligned epochs with bad channels marked and filtered (1–45 Hz) in **Primary Mode**.
2. **Given** only unpaired datasets (e.g., EEG from PhysioNet, tDCS from a separate study), **When** the ingestion script runs, **Then** it logs "Data Insufficient", switches to **Data Insufficient Mode**, and explicitly halts the statistical modeling pipeline. No synthetic data is generated for inference.
3. **Given** a dataset with missing channel metadata, **When** the preprocessing script runs, **Then** it logs a warning and proceeds with common average referencing rather than failing.
4. **Given** the search scope (OpenNeuro, PhysioNet, Kaggle) and query ("EEG AND tDCS AND motor"), **When** the verification task runs, **Then** it outputs a `verified_source_manifest.json` listing the identified canonical sources or confirming absence.

---

### User Story 2 - Feature Extraction and Statistical Modeling (Priority: P2)

The system must compute spectral power (delta, theta, alpha, beta, gamma) and connectivity metrics (PLV, wPLI) from the preprocessed EEG. It must fit a ridge regression model to predict tDCS response. This step ONLY executes in **Primary Mode**. If the system is in **Data Insufficient Mode**, this step is skipped entirely. If the data is non-normal, the system MUST switch to **Rank-Ridge regression** (a non-parametric multivariate alternative) instead of abandoning the model.

**Why this priority**: This implements the core scientific hypothesis (EEG features → tDCS response) ONLY when valid paired data exists. Preventing execution in invalid modes ensures no spurious results are generated.

**Independent Test**: Can be fully tested by executing the feature extraction module on a small valid dataset (n=10) and verifying the model outputs coefficients, R², and p-values. If run in **Data Insufficient Mode**, the test must confirm the module is skipped and no output is produced. If data is non-normal, the test must confirm the system uses Rank-Ridge.

**Acceptance Scenarios**:

1. **Given** preprocessed EEG epochs from a paired dataset, **When** the feature extraction module runs, **Then** it outputs a feature matrix with power density and PLV values for all subjects.
2. **Given** the system is in **Data Insufficient Mode**, **When** the modeling module runs, **Then** it is skipped, and a log entry confirms "Modeling Skipped: No valid paired data".
3. **Given** non-normal tDCS response data, **When** the modeling module runs, **Then** it automatically switches to Rank-Ridge regression and outputs coefficients, R², and p-values.
4. **Given** the permutation testing module runs, **When** it completes, **Then** it outputs the Kolmogorov-Smirnov (KS) test statistic and p-value for the null distribution.

---

### User Story 3 - Validation, Sensitivity Analysis, and Reporting (Priority: P3)

The system must validate the model using permutation testing, apply multiplicity correction for multiple EEG features (conditional on power analysis), and perform sensitivity analysis on significance thresholds to ensure robustness. This step ONLY executes in **Primary Mode**. The system MUST generate a pre-registration document before data processing begins.

**Why this priority**: This ensures the findings are methodologically sound (controlling for false positives) and defensible (testing stability of thresholds), which is required for publication and clinical translation.

**Independent Test**: Can be fully tested by running the validation module on a valid dataset and verifying the output report contains a sensitivity sweep table (e.g., R² at p < 0.01, 0.05, 0.1) and a corrected p-value. The test must also verify the existence of a `pre-registration.json` file.

**Acceptance Scenarios**:

1. **Given** the fitted regression model in **Primary Mode**, **When** the validation module runs, **Then** it produces a sensitivity analysis table sweeping p-value thresholds across {0.01, 0.05, 0.1} and variance explained thresholds (R²) and reports stability.
2. **Given** multiple feature tests, **When** the validation module runs, **Then** it applies False Discovery Rate (FDR) correction using the Benjamini-Hochberg procedure to the final model coefficients and reports the adjusted p-value, provided the power analysis (US-4) confirms sufficient sample size.
3. **Given** the start of data processing, **When** the system runs, **Then** it generates a `pre-registration.json` file containing the analysis plan hash and timestamp before any data ingestion.

---

### User Story 4 - Power Analysis & Feasibility Gate (Priority: P1)

The system MUST perform a prospective power analysis to determine the minimum sample size required to detect an expected R² of 0.1 with 80% power at α=0.05 BEFORE any data ingestion. If the available dataset size (N) is less than the calculated minimum, the system MUST flag the study as 'Underpowered' and skip statistical inference (FDR, p-values), reporting the 'Minimum N required' instead. This ensures the project does not proceed with an unanswerable hypothesis.

**Why this priority**: This addresses the critical scientific gap where a study might run but yield a false negative due to insufficient data. It provides a rigorous 'Go/No-Go' gate before expensive statistical modeling.

**Independent Test**: Can be fully tested by running the power analysis module with parameters (R²=0.1, power=0.8, alpha=0.05) and verifying the output reports the calculated minimum N (e.g., N≈64). If the input dataset has N < 64, the system must report 'Underpowered'.

**Acceptance Scenarios**:

1. **Given** a dataset with N=100 subjects, **When** the power analysis runs, **Then** it reports 'Sufficient Power' and allows the statistical modeling pipeline to proceed.
2. **Given** a dataset with N=20 subjects, **When** the power analysis runs, **Then** it reports 'Underpowered', calculates the minimum N required (e.g., 64), and flags all subsequent statistical results as 'Not Valid for Inference'.
3. **Given** the power analysis module runs, **When** it completes, **Then** it explicitly uses the expected R² metric (not Cohen's d) to calculate the minimum sample size.

---

### Edge Cases

- **What happens when no single-source paired dataset is found?** The system MUST NOT halt with an error. It MUST log "Data Insufficient: No single-source paired dataset found in public repositories", switch to **Data Insufficient Mode**, and terminate the pipeline. No synthetic data is generated for inference, and no claims about individual biomarkers are made. The hypothesis remains scientifically valid, but the current data is insufficient.
- **How does system handle memory overflow during permutation testing on a large cohort of subjects?** The system MUST process in batches or downsample epochs to stay within memory limits (see NFR-001).
- **What happens if the available dataset is small or from a single population?** The system MUST flag the dataset as potentially biased and report this in the final output (see FR-021).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST verify that the input datasets contain paired EEG recordings and tDCS outcome scores for the same subjects within a SINGLE verified source. If pairing is confirmed, the system MUST proceed in **Primary Mode**. If no single-source paired dataset exists, the system MUST switch to **Data Insufficient Mode** and terminate the statistical pipeline. The system MUST explicitly state that the primary research question (predicting individual response) is **currently unanswerable due to data insufficiency**, not hypothesis invalidity (See US-1).
- **FR-002**: System MUST band-pass filter EEG data between 1 Hz and 45 Hz and re-reference to common average before feature extraction (See US-1).
- **FR-003**: System MUST compute spectral power density for delta, theta, alpha, beta, and gamma bands using Welch's method (See US-2).
- **FR-004**: System MUST fit a multivariate linear regression with L2 regularization (ridge) using k-fold cross-validation and nested hyperparameter tuning (inner loop for alpha selection, outer loop for evaluation) to predict tDCS response percentage change. This requirement is ONLY active in **Primary Mode** (See US-2).
- **FR-005**: System MUST apply False Discovery Rate (FDR) correction to the p-values of the final multivariate model coefficients when testing multiple EEG features to control family-wise error, PROVIDED that the power analysis (FR-008) confirms sufficient sample size. If underpowered, FDR is skipped and the result is flagged with a JSON output: `{"status": "underpowered", "reason": "N < required"}` (See US-3).
- **FR-006**: System MUST perform sensitivity analysis sweeping the significance threshold (p) over the set {0.01, 0.05, 0.1} and the variance explained threshold (R²) over a configurable set. The system MUST define 'justified stability' as the primary finding (p < 0.05) holding across at least 2 out of 3 tested thresholds, or report the specific threshold range where significance is lost (See US-3).
- **FR-007**: System MUST perform a power analysis to calculate the minimum sample size required to detect an expected R² of 0.1 with 80% power at α=0.05. The system MUST output this value and compare it against the actual N BEFORE data ingestion (See US-4).
- **FR-008**: System MUST flag the study as 'Underpowered' and suppress statistical inference (p-values, FDR) if the actual N is less than the minimum required by FR-007 (See US-4).
- **FR-009**: System MUST perform a normality check (Shapiro-Wilk) on the tDCS response metric. If the data is non-normal (p < 0.05), the system MUST apply a rank-based transformation and use **Rank-Ridge regression** (a non-parametric multivariate alternative) instead of Pearson/linear regression (See US-2).
- **FR-010**: System MUST define the primary outcome and analysis plan as pre-registration before data processing begins. This MUST be implemented as a distinct artifact (See US-3).
- **FR-011**: System MUST perform a 'Data Alignment Check' to verify subject overlap between EEG and tDCS sources within a single study. If no overlap is found, the system MUST default to **Data Insufficient Mode** and log the specific reason (See US-1).
- **FR-012**: System MUST explicitly identify the canonical source for the tDCS motor performance data (e.g., specific OpenNeuro accession or meta-analysis) and verify it contains raw behavioral scores, not structural templates (See US-1).
- **FR-013**: System MUST explicitly identify the canonical source for the raw EEG time-series data (e.g., PhysioNet BIDS/EDF) and verify it contains raw voltage data, not pre-processed features or CSV proxies (See US-1).
- **FR-014**: System MUST implement the Benjamini-Hochberg procedure for FDR correction and output the corrected p-values in the final report (See US-3).
- **FR-015**: System MUST NOT attempt to align subjects across different public repositories (e.g., PhysioNet and OpenNeuro) due to lack of shared IDs and differing protocols. If a single-source paired dataset is not found, the system MUST declare the data insufficient for current analysis (See US-1).
- **FR-016**: System MUST generate a `pre-registration.json` artifact containing the analysis plan hash, timestamp, and parameter list BEFORE data processing begins. This artifact MUST be stored in the output directory (See US-3).
- **FR-017**: System MUST generate a `verified_source_manifest.json` artifact containing the identified canonical sources for EEG and tDCS data after the verification task completes (See US-1).
- **FR-018**: System MUST explicitly record the search scope (OpenNeuro, PhysioNet, Kaggle) and query ("EEG AND tDCS AND motor") in the `verified_source_manifest.json` (See US-1).
- **FR-019**: System MUST output the Kolmogorov-Smirnov (KS) test statistic and p-value for the null distribution in the final report to validate permutation testing (See US-2).
- **FR-020**: System MUST attempt evaluation on an independent public dataset (e.g., Kaggle EEG Motor Imagery) for generalizability if the primary dataset is sufficient for training but lacks an independent test split. If no independent dataset is available, the system MUST flag the generalizability check as "Skipped: No independent dataset found" (See Constitution Principle VII).
- **FR-021**: System MUST perform a 'Dataset Representativeness Check' that flags if the available dataset is small (<50 subjects) or from a single population (e.g., healthy young adults). The system MUST report this flag in the final output (See US-1).

### Non-Functional Requirements

- **NFR-001**: System MUST execute all computations on CPU-only infrastructure with a maximum runtime of a few hours. and ≤7 GB RAM usage across all User Stories. If memory usage approaches 7 GB, the system MUST downsample epochs or process in batches (See US-1, US-2, US-3).

### Key Entities *(include if data)*

- **EEG Epoch**: Represents a 2-second window of filtered EEG data with associated subject ID and condition (rest/task).
- **tDCS Response**: Represents the percentage change in motor task score (pre vs. post) for a specific subject.
- **Feature Vector**: Represents the aggregated spectral and connectivity metrics for one subject.
- **Analysis Mode**: Represents the current state of the system: 'Primary Mode' (valid single-source paired data exists), 'Data Insufficient Mode' (no valid paired data found, pipeline halted), or 'Underpowered' (insufficient N for statistical inference).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Data integrity is measured against the raw dataset checksums and subject count consistency (See US-1).
- **SC-002**: In **Primary Mode**, model predictive performance is measured against the observed adjusted R² and permutation test p-value. Success is defined as the *correct computation* of the p-value and the *uniformity* of the null distribution (See US-2).
- **SC-003**: Computational feasibility is measured against the 6-hour runtime limit and ≤7 GB RAM usage (See NFR-001).
- **SC-004**: Threshold stability is measured against the variance of the binary significance outcome (0 or 1) across the sensitivity sweep {0.01, 0.05, 0.1}. Success is defined as the *reporting* of the variance value and the presence of FDR-corrected p-values (See US-3).
- **SC-005**: Power analysis feasibility is measured against the calculated minimum N. Success is defined as the system correctly reporting 'Underpowered' if N < required and 'Sufficient' otherwise (See US-4).
- **SC-006**: Null distribution validity is measured against the Kolmogorov-Smirnov test for uniformity of the permutation test p-values under the null hypothesis. Success is defined as a KS-test p-value > 0.05, indicating the null distribution is uniform (See US-2).

## Assumptions

- The PhysioNet EEG Motor Movement/Imagery Dataset (Canonical Accession: eegmmidb, BIDS/EDF format) provides sufficient raw resting-state baseline data.
- The tDCS motor performance data must be sourced from a verified single study (e.g., specific OpenNeuro accession) that contains both EEG and tDCS outcomes for the same subjects. If no such single-source dataset exists in the public domain, the primary research question is currently unanswerable due to data insufficiency.
- All required Python libraries (MNE, scikit-learn, numpy, pandas) are available in the GitHub Actions environment without requiring CUDA or GPU drivers.
- The dataset size for the target cohort fits within the available RAM constraint after epoching and filtering; if not, subsampling of epochs will be applied.
- The tDCS response metric (percentage change) may require rank-based transformation if non-normal (see FR-009).
- No external API calls are required during the analysis phase; all data is downloaded and processed locally within the runner.
- The 'Primary Mode' is contingent on finding a single verified source containing both EEG and tDCS data for the same subjects.
- All constitutional references in this document adhere to the project constitution's Roman Numeral structure (Principle I, II, etc.).