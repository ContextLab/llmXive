# Feature Specification: The Effect of Simulated Social Rejection on Neural Responses to Positive Feedback

**Feature Branch**: `001-social-rejection-reward`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Secondary analysis of existing behavioral datasets (OpenNeuro/ICPSR) to investigate how simulated social rejection (Cyberball) modulates subsequent behavioral responses to positive feedback (reaction times, mood ratings) using CPU-tractable statistical methods (ANOVA, FDR)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Variable Validation (Priority: P1)

The researcher MUST be able to download and validate the selected behavioral dataset (e.g., OpenNeuro ds000208 for rejection + ds003392 for reward) to ensure it contains the necessary variables and matching Participant IDs for the analysis before any processing begins.

**Why this priority**: Without verified data and valid ID matching, the analysis cannot proceed. This is the foundational step that gates all downstream research activities.

**Independent Test**: Can be fully tested by executing the data download script against a mock server or local file and verifying the presence of required columns (Condition, Reaction Time, Mood) AND the existence of matching Participant IDs across the composite datasets without running the statistical models.

**Acceptance Scenarios**:

1. **Given** the composite dataset URLs are provided, **When** the ingestion script runs, **Then** the script verifies the presence of Cyberball condition, reaction time, and mood rating variables in both datasets.
2. **Given** the datasets lack matching Participant IDs, **When** the ingestion script runs, **Then** the script flags the design as 'Between-Subjects' and proceeds to validate the separate schema.
3. **Given** the dataset lacks a required variable, **When** the ingestion script runs, **Then** the script halts and logs an error with exit code 1.

---

### User Story 2 - Preprocessing and Feature Extraction (Priority: P2)

The researcher MUST be able to clean the behavioral data, normalize reaction times, and extract summary features (mean RT per condition, average mood score) while respecting CPU and memory constraints.

**Why this priority**: Raw behavioral logs often contain noise and outliers. This step prepares the data for statistical testing and ensures the dataset fits within the compute box.

**Independent Test**: Can be fully tested by running the preprocessing script on a sample subset of the data and verifying the output CSV structure, memory usage logs, and correct grouping for outlier detection.

**Acceptance Scenarios**:

1. **Given** raw behavioral logs, **When** the preprocessing script runs, **Then** outliers are flagged using the IQR method calculated **per Condition group** and removed or capped.
2. **Given** the dataset size, **When** the preprocessing script runs, **Then** memory usage remains ≤7 GB RAM throughout execution.

---

### User Story 3 - Statistical Analysis and Reporting (Priority: P3)

The researcher MUST be able to execute the appropriate statistical models (Mixed ANOVA for matched data; One-Way ANOVA for unmatched data), apply multiplicity corrections, generate sensitivity analyses, and export the final results report.

**Why this priority**: This delivers the core research value (hypothesis testing) and ensures methodological soundness (FDR, sensitivity, correct test selection).

**Independent Test**: Can be fully tested by running the analysis script on preprocessed data and verifying the output report contains p-values, effect sizes, sensitivity tables, and the correct test selection logic.

**Acceptance Scenarios**:

1. **Given** matched Participant IDs across datasets, **When** the analysis script runs, **Then** a 2×2 Mixed ANOVA is performed.
2. **Given** unmatched Participant IDs, **When** the analysis script runs, **Then** a One-Way ANOVA (Between-Subjects) is performed.
3. **Given** a significance threshold, **When** the analysis script runs, **Then** a sensitivity report is generated sweeping α ∈ {0.01, 0.05, 0.1}.
4. **Given** the final report, **When** generated, **Then** the Limitations section contains the exact phrase "associational" and the Results section does not contain the word "causal".

---

### Edge Cases

- **Dataset Variable Mismatch**: What happens when the selected dataset (e.g., OpenNeuro ds000208) contains the Cyberball task but lacks the subsequent reward feedback task variables? (System switches to Between-Subjects design).
- **Memory Overflow**: How does the system handle datasets that exceed 7 GB RAM during loading? (System halts with a specific error code).
- **Statistical Convergence**: How does the system handle ANOVA convergence failures due to small sample sizes (N < 30 per condition)? (System reports convergence warning and effect size confidence intervals).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-000**: System MUST verify the downloaded datasets contain Cyberball condition, reaction time, and mood rating variables AND verify matching Participant IDs across datasets if a Within-Subjects design is attempted (See US-1).
- **FR-001**: System MUST halt execution with exit code 1 if the combined dataset size exceeds 7 GB RAM or if required variables are missing (See US-1).
- **FR-002**: System MUST normalize reaction times and flag outliers using the Interquartile Range (IQR) method (1.5× IQR) calculated **per Condition group** (See US-2).
- **FR-003**: System MUST generate a report where the Limitations section contains the exact phrase "associational" and the Results section does not contain the word "causal" (See US-3).
- **FR-004**: System MUST apply Benjamini-Hochberg False Discovery Rate (FDR) correction to all hypothesis test p-values (See US-3).
- **FR-005**: System MUST restrict execution to CPU-only resources with ≤7 GB RAM usage and ≤6 hours total runtime for datasets with N ≤ 500 participants (See US-2, US-3).
- **FR-006**: System MUST perform sensitivity analysis sweeping significance threshold α over {0.01, 0.05, 0.1} and report result consistency (See US-3).
- **FR-007**: System MUST detect if Participant IDs do not match across the composite datasets and automatically switch the statistical test from 2×2 Mixed ANOVA to One-Way ANOVA (Between-Subjects) (See US-3).
- **FR-008**: System MUST report the design type (Within-Subjects or Between-Subjects) in the final output based on the ID matching status (See US-3).

### Key Entities

- **Dataset**: Represents the raw behavioral data file (e.g., CSV/TSV) containing participant IDs, task conditions, and response metrics.
- **Preprocessed Record**: Represents the cleaned row-level data with normalized reaction times and flagged outliers.
- **Analysis Result**: Represents the output statistics (F-values, p-values, effect sizes) and sensitivity reports.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Dataset variable availability is measured against the required schema; Script exits with code 0 only if all 3 required variables are present; otherwise exits with code 1 (See US-1).
- **SC-002**: Total compute time is measured against the 6-hour GitHub Actions free-tier limit for the entire workflow (Ingestion + Preprocessing + Analysis) (See US-1, US-2, US-3).
- **SC-003**: FDR correction application is measured against the raw p-value output; The output file MUST contain a column "p_fdr" where every value is ≤ the corresponding raw p-value (See US-3).
- **SC-004**: Sensitivity analysis report coverage is measured against the required α set {0.01, 0.05, 0.1} (See US-3).

## Assumptions

- Secondary analysis relies on existing OpenNeuro or ICPSR datasets being publicly accessible without authentication barriers.
- The primary dataset (ds000208) likely lacks the subsequent reward feedback task variables required for a Within-Subjects analysis.
- **Composite Dataset Strategy**: The analysis will attempt to match Participant IDs between the rejection dataset and a separate reward dataset. If IDs match, a 2×2 Mixed ANOVA (Within-Subjects) is used to test modulation.
- **Fallback Strategy**: If Participant IDs do not match, the system MUST switch to a Between-Subjects design (One-Way ANOVA) to test group differences, acknowledging this cannot directly test the "modulation" hypothesis but serves as a proxy.
- GitHub Actions free tier limits (2 CPU, 7 GB RAM) are sufficient for N ≤ 500 participants per condition.
- Validated instruments (e.g., PANAS) are used for mood ratings if available in the dataset; otherwise, limitations are explicitly documented in the final report.
- The dataset OpenNeuro (Cyberball) contains the social rejection task but lacks the subsequent reward feedback task variables required for this analysis. Therefore, the analysis scope is revised to use a composite dataset approach: ds000208 for the rejection condition and a separate, publicly available reward task dataset (e.g., ds003392) for the feedback condition, ensuring participant IDs are matched where possible. If matching fails, the analysis is treated as a Between-Subjects design. This boundary is documented as a limitation in the final report (See US-1).