# Feature Specification: The Effect of Simulated Social Rejection on Neural Responses to Positive Feedback (Neural inferences derived from behavioral proxies)

**Feature Branch**: `001-social-rejection-reward`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Secondary analysis of existing behavioral datasets (OpenNeuro/ICPSR) to investigate how simulated social rejection (Cyberball) modulates subsequent behavioral responses to positive feedback (reaction times, mood ratings) using CPU‑tractable statistical methods (ANOVA, FDR). Neural responses are inferred from these behavioral proxies."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Variable Validation (US-1)

The researcher MUST be able to download and validate the selected behavioral datasets (e.g., OpenNeuro ds000208 for rejection + ds003392 for reward) to ensure they contain the necessary variables and matching Participant IDs for the analysis before any processing begins.

**Why this priority**: Without verified data and valid ID matching, the analysis cannot proceed. This is the foundational step that gates all downstream research activities.

**Independent Test**: Can be fully tested by executing the data download script against a mock server or local file and verifying the presence of required columns (Condition, Reaction Time, Mood) AND the existence of matching Participant IDs across the composite datasets without running the statistical models.

**Acceptance Scenarios**:

1. **Given** the composite dataset URLs are provided, **When** the ingestion script runs, **Then** the script verifies the presence of Cyberball condition, reaction time, and mood rating variables in both datasets.
2. **Given** the datasets lack matching Participant IDs, **When** the ingestion script runs, **Then** the script flags the design as 'Between‑Subjects' and proceeds to validate the separate schema.
3. **Given** the dataset lacks a required variable, **When** the ingestion script runs, **Then** the script halts and logs an error with exit code 1.

---

### User Story 2 - Preprocessing and Feature Extraction (US-2)

The researcher MUST be able to clean the behavioral data, normalize reaction times, and extract summary features (mean RT per condition, average mood score) while respecting CPU and memory constraints.

**Why this priority**: Raw behavioral logs often contain noise and outliers. This step prepares the data for statistical testing and ensures the dataset fits within the compute box.

**Independent Test**: Can be fully tested by running the preprocessing script on a sample subset of the data and verifying the output CSV structure, memory usage logs, and correct grouping for outlier detection.

**Acceptance Scenarios**:

1. **Given** raw behavioral logs, **When** the preprocessing script runs, **Then** outliers are flagged using the IQR method calculated **per Condition group** and removed or capped.
2. **Given** the dataset size, **When** the preprocessing script runs, **Then** memory usage remains ≤7 GB RAM throughout execution.

---

### User Story 3 - Statistical Analysis and Reporting (US-3)

The researcher MUST be able to execute the appropriate statistical models (One‑Way ANOVA for Between‑Subjects data), apply multiplicity corrections, generate sensitivity analyses, and export the final results report.

**Why this priority**: This delivers the core research value (hypothesis testing) and ensures methodological soundness (FDR, sensitivity, correct test selection).

**Independent Test**: Can be fully tested by running the analysis script on preprocessed data and verifying the output report contains p‑values, effect sizes, sensitivity tables, and the correct test selection logic.

**Acceptance Scenarios**:

1. **Given** matched Participant IDs across datasets, **When** the analysis script runs, **Then** a Two‑Sample (Between‑Subjects) ANOVA is performed, and the limitation that IDs come from separate studies is documented.
2. **Given** unmatched Participant IDs, **When** the analysis script runs, **Then** a One‑Way ANOVA (Between‑Subjects) is performed.
3. **Given** a significance threshold, **When** the analysis script runs, **Then** a sensitivity report is generated sweeping α ∈ {0.01, 0.05, 0.1}.
4. **Given** the final report, **When** generated, **Then** the Limitations section contains the exact phrase "associational" and the Results section does not contain the word "causal".

---

### Edge Cases

- **Dataset Variable Mismatch**: What happens when the selected dataset (e.g., OpenNeuro ds000208) contains the Cyberball task but lacks the subsequent reward feedback task variables? (System switches to Between‑Subjects design).
- **Memory Overflow**: How does the system handle datasets that exceed 7 GB RAM during loading? (System halts with a specific error code).
- **Statistical Convergence**: How does the system handle ANOVA convergence failures due to small sample sizes (N < 30 per condition)? (System reports convergence warning and effect size confidence intervals).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-000**: System MUST verify the downloaded datasets contain Cyberball condition, reaction time, and mood rating variables AND verify matching Participant IDs across datasets if a Within‑Subjects design is attempted (See US-1). *(Note: Within‑Subjects design is not performed; this clause remains for completeness but will trigger a fallback to Between‑Subjects.)*
- **FR-001**: System MUST halt execution with exit code 1 if the combined dataset size exceeds 7 GB RAM or if required variables are missing (See US-1).
- **FR-002**: System MUST normalize reaction times and flag outliers using the Interquartile Range (IQR) method (1.5× IQR) calculated **per Condition group** (See US-2).
- **FR-003**: System MUST generate a report where the Limitations section contains the exact phrase "associational" and the Results section does not contain the word "causal" (See US-3).
- **FR-004**: System MUST apply Benjamini‑Hochberg False Discovery Rate (FDR) correction to all hypothesis test p‑values (See US-3).
- **FR-005**: System MUST restrict execution to CPU‑only resources with ≤7 GB RAM usage and ≤6 hours total runtime for datasets with N ≤ 500 participants (See US-2, US-3).
- **FR-006**: System MUST perform sensitivity analysis sweeping significance threshold α over {0.01, 0.05, 0.1} and report result consistency (See US-3).
- **FR-007**: System MUST detect if Participant IDs do not match across the composite datasets and automatically select a Between‑Subjects analysis (One‑Way ANOVA); if IDs do match, the same Between‑Subjects analysis is used but the report notes the matching and the associated limitation (See US-3).
- **FR-008**: System MUST report the design type (Between‑Subjects) in the final output based on the ID matching status (See US-3).
- **FR-009**: System MUST explicitly state in the final report that “Neural responses are inferred from behavioral proxies (reaction times, mood ratings) and no direct neural measurement was performed” to satisfy Constitution VI (Behavioral Proxy Transparency). (See US-3)

### Key Entities

- **Dataset**: Represents the raw behavioral data file (e.g., CSV/TSV) containing participant IDs, task conditions, and response metrics.
- **Preprocessed Record**: Represents the cleaned row‑level data with normalized reaction times and flagged outliers.
- **Analysis Result**: Represents the output statistics (F‑values, p‑values, effect sizes) and sensitivity reports.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Dataset variable availability is measured against the required schema; Script exits with code 0 only if all 3 required variables are present; otherwise exits with code 1 (See US-1).
- **SC-002**: Total compute time is measured by summing the `duration_ms` fields from each GitHub Actions step log (available via `${{ github.run_id }}` API) and stored in `runtime_report.json`; the summed time must be ≤ 6 hours (21 600 seconds) (See US-1, US-2, US-3).
- **SC-003**: FDR correction application is measured against the raw p‑value output; The output file MUST contain a column `p_fdr` where every value is **≥** the corresponding raw p‑value, as guaranteed by the Benjamini‑Hochberg procedure (See US-3).
- **SC-004**: Sensitivity analysis report coverage is measured against the required α set {0.01, 0.05, 0.1} (See US-3).

## Assumptions

- Secondary analysis relies on existing OpenNeuro or ICPSR datasets being publicly accessible without authentication barriers.
- The primary dataset lacks the subsequent reward feedback task variables required for a Within‑Subjects analysis.
- **Composite Dataset Strategy**: The analysis will combine the rejection dataset (ds000208) with a separate reward‑feedback dataset (e.g., ds003392). Participant IDs will be matched where possible; regardless of matching, the statistical test remains Between‑Subjects.
- **Fallback Strategy**: If Participant IDs do not match, the system proceeds with a Between‑Subjects design (One‑Way ANOVA). If they do match, the same analysis is performed but the report notes the matching and the limitation that the data originate from separate studies.
- GitHub Actions free tier limits (2 CPU, 7 GB RAM) are sufficient for N ≤ 500 participants per condition.
- Validated instruments (e.g., PANAS) are used for mood ratings if available in the dataset; otherwise, limitations are explicitly documented in the final report.
- Neural response claims are **only** derived from the measured behavioral proxies; no direct neuroimaging data are collected.
